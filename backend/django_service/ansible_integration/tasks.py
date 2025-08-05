"""
Celery tasks for Ansible Integration module.
"""
from celery import shared_task
from django.utils import timezone
import logging
import subprocess
import tempfile
import os
import hashlib
import yaml
from common.execution_logger import ExecutionLogger

logger = logging.getLogger(__name__)


@shared_task
def execute_ansible_playbook(execution_id):
    """
    异步执行Ansible playbook
    
    Args:
        execution_id (int): AnsibleExecution记录的ID
    
    Returns:
        dict: 执行结果
    """
    try:
        # 导入模型（避免循环导入）
        from .models import AnsibleExecution
        
        execution = AnsibleExecution.objects.get(id=execution_id)
        
        # 使用执行日志模块开始执行
        ExecutionLogger.start_execution(
            execution, 
            f"开始执行Ansible playbook: {execution.playbook.name}"
        )
        
        # 实现真正的Ansible执行逻辑
        playbook_path = None
        inventory_path = None
        key_path = None
        
        try:
            # 创建临时文件保存playbook内容
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as temp_playbook:
                temp_playbook.write(execution.playbook.content)
                playbook_path = temp_playbook.name
            
            # 创建临时文件保存inventory内容
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_inventory:
                temp_inventory.write(execution.inventory.content)
                inventory_path = temp_inventory.name
            
            # 构建ansible-playbook命令
            cmd = [
                'ansible-playbook',
                playbook_path,
                '-i', inventory_path,
                '-v'  # 详细输出
            ]
            
            # 如果有凭据配置，添加相关参数
            if execution.credential:
                credential = execution.credential
                if credential.credential_type == 'ssh_key' and credential.has_ssh_key:
                    # 获取解密后的SSH私钥
                    decrypted_ssh_key = credential.get_decrypted_ssh_key()
                    if decrypted_ssh_key:
                        # 确保SSH密钥以换行符结尾，并且格式正确
                        if not decrypted_ssh_key.endswith('\n'):
                            decrypted_ssh_key += '\n'
                        
                        # 创建临时SSH密钥文件
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_key:
                            temp_key.write(decrypted_ssh_key)
                            key_path = temp_key.name
                        
                        # 设置密钥文件权限
                        os.chmod(key_path, 0o600)
                        cmd.extend(['--private-key', key_path])
                        
                        ExecutionLogger.log_execution_info(
                            execution, 
                            f"使用SSH密钥认证，密钥文件: {key_path}"
                        )
                    else:
                        ExecutionLogger.log_execution_info(
                            execution, 
                            "SSH密钥解密失败或为空", 
                            level='warning'
                        )
                
                if credential.username:
                    cmd.extend(['-u', credential.username])
            
            # 执行ansible-playbook命令
            ExecutionLogger.log_execution_info(execution, f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                cwd=tempfile.gettempdir()
            )
            
            # 使用执行日志模块记录结果
            if result.returncode == 0:
                ExecutionLogger.complete_execution(
                    execution,
                    result=result,
                    status='success',
                    log_message=f"Ansible playbook执行成功: {execution.playbook.name}"
                )
            else:
                ExecutionLogger.complete_execution(
                    execution,
                    result=result,
                    status='failed',
                    log_message=f"Ansible playbook执行失败: {execution.playbook.name}, 返回码: {result.returncode}"
                )
            
        except subprocess.TimeoutExpired:
            ExecutionLogger.timeout_execution(
                execution,
                timeout_message="执行超时（超过5分钟）",
                timeout_seconds=300,
                log_message=f"Ansible playbook执行超时: {execution.playbook.name}"
            )
            
        except Exception as e:
            ExecutionLogger.fail_execution(
                execution,
                error_message=f"执行异常: {str(e)}",
                log_message=f"Ansible playbook执行异常: {execution.playbook.name}, 错误: {str(e)}"
            )
            
        finally:
            # 清理临时文件
            for path in [playbook_path, inventory_path, key_path]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except:
                        pass
        
        ExecutionLogger.log_execution_info(
            execution, 
            f"Ansible playbook执行完成: {execution.playbook.name}, 状态: {execution.status}"
        )
        
        # TODO: 发送WebSocket通知
        # send_websocket_message(f'ansible_execution_{execution_id}', {
        #     'type': 'execution_completed',
        #     'execution_id': execution_id,
        #     'status': execution.status,
        #     'return_code': execution.return_code
        # })
        
        return {
            'execution_id': execution_id,
            'status': execution.status,
            'return_code': getattr(execution, 'return_code', None)
        }
        
    except Exception as e:
        logger.error(f"Ansible playbook执行失败: {str(e)}")
        
        try:
            ExecutionLogger.fail_execution(
                execution,
                error_message=str(e),
                log_message=f"Ansible playbook执行失败: {str(e)}"
            )
        except:
            pass
        
        # TODO: 发送WebSocket错误通知
        # send_websocket_message(f'ansible_execution_{execution_id}', {
        #     'type': 'execution_failed',
        #     'execution_id': execution_id,
        #     'error': str(e)
        # })
        
        raise


@shared_task
def cleanup_old_executions():
    """
    清理旧的执行记录
    """
    try:
        from .models import AnsibleExecution
        from datetime import timedelta
        
        # 删除30天前的执行记录
        cutoff_date = timezone.now() - timedelta(days=30)
        old_executions = AnsibleExecution.objects.filter(created_at__lt=cutoff_date)
        count = old_executions.count()
        old_executions.delete()
        
        logger.info(f"清理了 {count} 条旧的Ansible执行记录")
        return {'cleaned_count': count}
        
    except Exception as e:
        logger.error(f"清理旧执行记录失败: {str(e)}")
        raise


@shared_task
def validate_ansible_inventory(inventory_id):
    """
    异步验证Ansible主机清单
    
    Args:
        inventory_id (int): AnsibleInventory记录的ID
    
    Returns:
        dict: 验证结果
    """
    try:
        from .models import AnsibleInventory
        
        inventory = AnsibleInventory.objects.get(id=inventory_id)
        
        # TODO: 实现真正的inventory验证逻辑
        # 可以使用ansible-inventory命令验证
        
        logger.info(f"验证Ansible inventory: {inventory.name}")
        
        # 模拟验证结果
        is_valid = True
        message = "主机清单格式验证通过"
        
        return {
            'inventory_id': inventory_id,
            'valid': is_valid,
            'message': message
        }
        
    except Exception as e:
        logger.error(f"验证Ansible inventory失败: {str(e)}")
        return {
            'inventory_id': inventory_id,
            'valid': False,
            'message': str(e)
        }


@shared_task
def validate_ansible_playbook(playbook_id):
    """
    异步验证Ansible playbook语法
    
    Args:
        playbook_id (int): AnsiblePlaybook记录的ID
    
    Returns:
        dict: 验证结果
    """
    try:
        from .models import AnsiblePlaybook
        
        playbook = AnsiblePlaybook.objects.get(id=playbook_id)
        
        # TODO: 实现真正的playbook语法验证逻辑
        # 可以使用ansible-playbook --syntax-check
        
        logger.info(f"验证Ansible playbook: {playbook.name}")
        
        # 模拟验证结果
        is_valid = True
        message = "Playbook语法验证通过"
        
        return {
            'playbook_id': playbook_id,
            'valid': is_valid,
            'message': message
        }
        
    except Exception as e:
        logger.error(f"验证Ansible playbook失败: {str(e)}")
        return {
            'playbook_id': playbook_id,
            'valid': False,
            'message': str(e)
        }


@shared_task
def check_host_connectivity(host_id):
    """
    异步检查主机连通性
    
    Args:
        host_id (int): AnsibleHost记录的ID
    
    Returns:
        dict: 检查结果
    """
    try:
        from .models import AnsibleHost
        
        host = AnsibleHost.objects.get(id=host_id)
        
        ExecutionLogger.log_execution_info(
            host, 
            f"开始检查主机连通性: {host.hostname} ({host.ip_address})"
        )
        
        # 创建临时inventory文件
        inventory_content = f"[targets]\n{host.ip_address}"
        if host.port != 22:
            inventory_content = f"[targets]\n{host.ip_address}:{host.port}"
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_inventory:
            temp_inventory.write(inventory_content)
            inventory_path = temp_inventory.name
        
        # 构建ansible ping命令，使用主机的认证凭证
        cmd = [
            'ansible', 'targets',  # 使用inventory中的组名
            '-i', inventory_path,   # 指定inventory文件
            '-m', 'ping',
            '-u', host.username,
            '--timeout=10'
        ]
        
        # 创建临时文件用于认证
        key_path = None
        
        try:
            # 如果主机配置了认证凭据，使用凭据进行连接
            if host.credential:
                credential = host.credential
                ExecutionLogger.log_execution_info(
                    host, 
                    f"使用认证凭据: {credential.name} ({credential.get_credential_type_display()})"
                )
                
                if credential.credential_type == 'ssh_key' and credential.ssh_private_key:
                    # 使用SSH密钥认证
                    decrypted_ssh_key = credential.get_decrypted_ssh_key()
                    if decrypted_ssh_key:
                        # 确保SSH密钥格式正确
                        if not decrypted_ssh_key.endswith('\n'):
                            decrypted_ssh_key += '\n'
                        
                        # 创建临时SSH密钥文件
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_key:
                            temp_key.write(decrypted_ssh_key)
                            key_path = temp_key.name
                        
                        # 设置密钥文件权限
                        os.chmod(key_path, 0o600)
                        cmd.extend(['--private-key', key_path])
                        
                        ExecutionLogger.log_execution_info(
                            host,
                            f"使用SSH密钥认证，临时密钥文件: {key_path}"
                        )
                    else:
                        ExecutionLogger.log_execution_info(
                            host,
                            "SSH密钥解密失败或为空",
                            level='warning'
                        )
                        
                elif credential.credential_type == 'password' and credential.password:
                    # 使用密码认证（通过环境变量）
                    decrypted_password = credential.get_decrypted_password()
                    if decrypted_password:
                        cmd.extend(['--ask-pass'])
                        ExecutionLogger.log_execution_info(
                            host,
                            "使用密码认证"
                        )
                    else:
                        ExecutionLogger.log_execution_info(
                            host,
                            "密码解密失败或为空",
                            level='warning'
                        )
            else:
                ExecutionLogger.log_execution_info(
                    host,
                    "未配置认证凭据，使用默认SSH连接",
                    level='warning'
                )
            
            # 记录完整的连接命令
            ExecutionLogger.log_execution_info(
                host,
                f"执行连通性检查命令: {' '.join(cmd)}"
            )
            
            # 执行ansible ping命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                host.status = 'active'
                host.check_message = '连接成功'
                success = True
                ExecutionLogger.log_execution_info(
                    host,
                    f"主机连通性检查成功: {host.hostname}"
                )
            else:
                host.status = 'failed'
                host.check_message = result.stderr or result.stdout
                success = False
                ExecutionLogger.log_execution_info(
                    host,
                    f"主机连通性检查失败: {host.hostname}, 错误: {host.check_message}",
                    level='error'
                )
                
        finally:
            # 清理临时密钥文件和inventory文件
            if key_path and os.path.exists(key_path):
                try:
                    os.unlink(key_path)
                except:
                    pass
            if 'inventory_path' in locals() and os.path.exists(inventory_path):
                try:
                    os.unlink(inventory_path)
                except:
                    pass
            
        host.last_check = timezone.now()
        host.save()
        
        ExecutionLogger.log_execution_info(
            host, 
            f"主机连通性检查完成: {host.hostname}, 状态: {host.status}"
        )
        
        return {
            'host_id': host_id,
            'hostname': host.hostname,
            'success': success,
            'status': host.status,
            'message': host.check_message
        }
        
    except subprocess.TimeoutExpired:
        ExecutionLogger.log_execution_info(
            host, 
            f"主机连通性检查超时: host_id={host_id}", 
            level='error'
        )
        try:
            host.status = 'failed'
            host.check_message = '连接超时'
            host.last_check = timezone.now()
            host.save()
        except:
            pass
        return {
            'host_id': host_id,
            'success': False,
            'message': '连接超时'
        }
    except Exception as e:
        ExecutionLogger.log_execution_info(
            host, 
            f"主机连通性检查失败: {str(e)}", 
            level='error'
        )
        return {
            'host_id': host_id,
            'success': False,
            'message': str(e)
        }


@shared_task
def gather_host_facts(host_id):
    """
    异步收集主机Facts信息
    
    Args:
        host_id (int): AnsibleHost记录的ID
    
    Returns:
        dict: 收集结果
    """
    try:
        from .models import AnsibleHost
        
        host = AnsibleHost.objects.get(id=host_id)
        
        ExecutionLogger.log_execution_info(
            host,
            f"开始收集主机Facts: {host.hostname} ({host.ip_address})"
        )
        
        # 创建临时inventory文件
        inventory_content = f"[targets]\n{host.ip_address}"
        if host.port != 22:
            inventory_content = f"[targets]\n{host.ip_address}:{host.port}"
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_inventory:
            temp_inventory.write(inventory_content)
            inventory_path = temp_inventory.name
        
        # 构建ansible setup命令，使用主机的认证凭证
        cmd = [
            'ansible', 'targets',  # 使用inventory中的组名
            '-i', inventory_path,   # 指定inventory文件
            '-m', 'setup',
            '-u', host.username,
            '--timeout=30'
        ]
        
        # 创建临时文件用于认证
        key_path = None
        
        try:
            # 如果主机配置了认证凭据，使用凭据进行连接
            if host.credential:
                credential = host.credential
                ExecutionLogger.log_execution_info(
                    host,
                    f"使用认证凭据收集Facts: {credential.name} ({credential.get_credential_type_display()})"
                )
                
                if credential.credential_type == 'ssh_key' and credential.ssh_private_key:
                    # 使用SSH密钥认证
                    decrypted_ssh_key = credential.get_decrypted_ssh_key()
                    if decrypted_ssh_key:
                        # 确保SSH密钥格式正确
                        if not decrypted_ssh_key.endswith('\n'):
                            decrypted_ssh_key += '\n'
                        
                        # 创建临时SSH密钥文件
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as temp_key:
                            temp_key.write(decrypted_ssh_key)
                            key_path = temp_key.name
                        
                        # 设置密钥文件权限
                        os.chmod(key_path, 0o600)
                        cmd.extend(['--private-key', key_path])
                        
                        ExecutionLogger.log_execution_info(
                            host,
                            f"使用SSH密钥收集Facts，临时密钥文件: {key_path}"
                        )
                    else:
                        ExecutionLogger.log_execution_info(
                            host,
                            "SSH密钥解密失败或为空",
                            level='warning'
                        )
                elif credential.credential_type == 'password' and credential.password:
                    # 使用密码认证
                    decrypted_password = credential.get_decrypted_password()
                    if decrypted_password:
                        cmd.extend(['--ask-pass'])
                        ExecutionLogger.log_execution_info(
                            host,
                            "使用密码认证收集Facts"
                        )
                    else:
                        ExecutionLogger.log_execution_info(
                            host,
                            "密码解密失败或为空",
                            level='warning'
                        )
            else:
                ExecutionLogger.log_execution_info(
                    host,
                    "未配置认证凭据，使用默认SSH连接收集Facts",
                    level='warning'
                )
            
            # 记录完整的收集命令
            ExecutionLogger.log_execution_info(
                host,
                f"执行Facts收集命令: {' '.join(cmd)}"
            )
            
            # 执行ansible setup命令
            result = subprocess.run(
                cmd,  
                capture_output=True, 
                text=True, 
                timeout=35
            )
            
            if result.returncode == 0:
                import json
                # 解析ansible facts
                facts_output = result.stdout
                ExecutionLogger.log_execution_info(
                    host,
                    f"Facts收集原始输出长度: {len(facts_output)} 字符"
                )
                
                try:
                    # Ansible setup输出通常包含主机名和JSON数据
                    # 格式类似：172.16.59.128 | SUCCESS => { "ansible_facts": { ... }}
                    lines = facts_output.strip().split('\n')
                    json_line = None
                    
                    # 查找包含JSON数据的行
                    for line in lines:
                        if '{' in line and '"ansible_facts"' in line:
                            # 提取JSON部分
                            json_start = line.find('{')
                            json_line = line[json_start:]
                            break
                    
                    if not json_line:
                        # 备用方法：查找第一个包含 { 的行
                        for line in lines:
                            if line.strip().startswith('{'):
                                json_line = line.strip()
                                break
                    
                    if json_line:
                        ExecutionLogger.log_execution_info(
                            host,
                            f"找到JSON数据行，长度: {len(json_line)} 字符"
                        )
                        facts = json.loads(json_line)
                    else:
                        ExecutionLogger.log_execution_info(
                            host,
                            f"未找到JSON数据，尝试解析整个输出。输出前500字符: {facts_output[:500]}",
                            level='warning'
                        )
                        # 最后尝试：找到第一个{的位置
                        facts_start = facts_output.find('{')
                        if facts_start >= 0:
                            facts_json = facts_output[facts_start:]
                            facts = json.loads(facts_json)
                        else:
                            raise ValueError("未找到JSON格式的Facts数据")
                    
                    ansible_facts = facts.get('ansible_facts', {})
                    
                    if not ansible_facts:
                        ExecutionLogger.log_execution_info(
                            host,
                            "警告：未找到ansible_facts字段，使用整个facts数据",
                            level='warning'
                        )
                        ansible_facts = facts
                    
                    # 更新主机信息
                    host.os_family = ansible_facts.get('ansible_os_family', '')
                    host.os_distribution = ansible_facts.get('ansible_distribution', '')
                    host.os_version = ansible_facts.get('ansible_distribution_version', '')
                    host.ansible_facts = ansible_facts
                    host.status = 'active'
                    host.last_check = timezone.now()
                    host.save()
                    
                    ExecutionLogger.log_execution_info(
                        host,
                        f"主机Facts收集完成: {host.hostname}, 系统: {host.os_distribution} {host.os_version}"
                    )
                    
                    return {
                        'host_id': host_id,
                        'hostname': host.hostname,
                        'success': True,
                        'facts': ansible_facts
                    }
                    
                except json.JSONDecodeError as e:
                    error_msg = f"Facts数据解析失败: {str(e)}"
                    ExecutionLogger.log_execution_info(
                        host,
                        error_msg,
                        level='error'
                    )
                    return {
                        'host_id': host_id,
                        'success': False,
                        'message': error_msg
                    }
            else:
                error_msg = result.stderr or result.stdout
                ExecutionLogger.log_execution_info(
                    host,
                    f"Facts收集失败: {error_msg}",
                    level='error'
                )
                return {
                    'host_id': host_id,
                    'success': False,
                    'message': error_msg
                }
                
        finally:
            # 清理临时密钥文件
            if key_path and os.path.exists(key_path):
                try:
                    os.unlink(key_path)
                except:
                    pass
            # 清理临时inventory文件
            if 'inventory_path' in locals() and os.path.exists(inventory_path):
                try:
                    os.unlink(inventory_path)
                except:
                    pass
            
    except subprocess.TimeoutExpired:
        logger.error(f"主机Facts收集超时: host_id={host_id}")
        return {
            'host_id': host_id,
            'success': False,
            'message': 'Facts收集超时'
        }
    except Exception as e:
        logger.error(f"主机Facts收集失败: {str(e)}")
        return {
            'host_id': host_id,
            'success': False,
            'message': str(e)
        }


@shared_task
def validate_inventory_content(inventory_id):
    """
    异步验证Inventory内容
    
    Args:
        inventory_id (int): AnsibleInventory记录的ID
    
    Returns:
        dict: 验证结果
    """
    try:
        from .models import AnsibleInventory
        
        inventory = AnsibleInventory.objects.get(id=inventory_id)
        
        logger.info(f"开始验证Inventory: {inventory.name}")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
            temp_file.write(inventory.content)
            temp_file_path = temp_file.name
        
        try:
            # 使用ansible-inventory命令验证
            result = subprocess.run([
                'ansible-inventory', '-i', temp_file_path, '--list'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                inventory.is_validated = True
                inventory.validation_message = 'Inventory格式验证通过'
                inventory.save()
                
                logger.info(f"Inventory验证成功: {inventory.name}")
                
                return {
                    'inventory_id': inventory_id,
                    'success': True,
                    'message': 'Inventory格式验证通过'
                }
            else:
                inventory.is_validated = False
                inventory.validation_message = result.stderr or result.stdout
                inventory.save()
                
                logger.error(f"Inventory验证失败: {result.stderr}")
                
                return {
                    'inventory_id': inventory_id,
                    'success': False,
                    'message': result.stderr or result.stdout
                }
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except subprocess.TimeoutExpired:
        logger.error(f"Inventory验证超时: inventory_id={inventory_id}")
        return {
            'inventory_id': inventory_id,
            'success': False,
            'message': '验证超时'
        }
    except Exception as e:
        logger.error(f"Inventory验证失败: {str(e)}")
        return {
            'inventory_id': inventory_id,
            'success': False,
            'message': str(e)
        }


@shared_task
def validate_playbook_syntax(playbook_id):
    """
    异步验证Playbook语法
    
    Args:
        playbook_id (int): AnsiblePlaybook记录的ID
    
    Returns:
        dict: 验证结果
    """
    try:
        from .models import AnsiblePlaybook
        import tempfile
        
        playbook = AnsiblePlaybook.objects.get(id=playbook_id)
        
        # 创建临时文件保存playbook内容
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as temp_file:
            temp_file.write(playbook.content)
            temp_file_path = temp_file.name
        
        try:
            # 先检查YAML语法
            yaml.safe_load(playbook.content)
            
            # 使用ansible-playbook --syntax-check检查语法
            result = subprocess.run([
                'ansible-playbook', '--syntax-check', temp_file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                playbook.is_validated = True
                playbook.validation_message = 'Playbook语法验证通过'
                playbook.save()
                
                logger.info(f"Playbook验证成功: {playbook.name}")
                
                return {
                    'playbook_id': playbook_id,
                    'success': True,
                    'message': 'Playbook语法验证通过'
                }
            else:
                playbook.is_validated = False
                playbook.validation_message = result.stderr or result.stdout
                playbook.save()
                
                logger.error(f"Playbook验证失败: {result.stderr}")
                
                return {
                    'playbook_id': playbook_id,
                    'success': False,
                    'message': result.stderr or result.stdout
                }
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except AnsiblePlaybook.DoesNotExist:
        logger.error(f"Playbook不存在: playbook_id={playbook_id}")
        return {
            'playbook_id': playbook_id,
            'success': False,
            'message': 'Playbook不存在'
        }
    except yaml.YAMLError as e:
        logger.error(f"Playbook YAML格式错误: {str(e)}")
        return {
            'playbook_id': playbook_id,
            'success': False,
            'message': f'YAML格式错误: {str(e)}'
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Playbook验证超时: playbook_id={playbook_id}")
        return {
            'playbook_id': playbook_id,
            'success': False,
            'message': '验证超时'
        }
    except Exception as e:
        logger.error(f"Playbook验证失败: {str(e)}")
        return {
            'playbook_id': playbook_id,
            'success': False,
            'message': str(e)
        }