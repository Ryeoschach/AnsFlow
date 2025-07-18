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
        execution.status = 'running'
        execution.started_at = timezone.now()
        execution.save()
        
        logger.info(f"开始执行Ansible playbook: {execution.playbook.name}")
        
        # TODO: 实现真正的Ansible执行逻辑
        # 这里先使用模拟执行
        import time
        import random
        
        # 模拟执行过程
        time.sleep(random.uniform(2, 5))
        
        # 模拟执行结果
        success = random.choice([True, True, True, False])  # 75%成功率
        
        if success:
            execution.status = 'success'
            execution.stdout = """
PLAY [all] *********************************************************************

TASK [Gathering Facts] *********************************************************
ok: [localhost]

TASK [Debug message] ***********************************************************
ok: [localhost] => {
    "msg": "Hello from Ansible!"
}

PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
"""
            execution.return_code = 0
        else:
            execution.status = 'failed'
            execution.stderr = """
ERROR! the playbook could not be found
"""
            execution.return_code = 1
        
        execution.completed_at = timezone.now()
        execution.save()
        
        logger.info(f"Ansible playbook执行完成: {execution.playbook.name}, 状态: {execution.status}")
        
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
            'return_code': execution.return_code
        }
        
    except Exception as e:
        logger.error(f"Ansible playbook执行失败: {str(e)}")
        
        try:
            execution.status = 'failed'
            execution.stderr = str(e)
            execution.completed_at = timezone.now()
            execution.save()
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
        
        logger.info(f"开始检查主机连通性: {host.hostname} ({host.ip_address})")
        
        # 使用ansible ping模块检查连通性
        result = subprocess.run([
            'ansible', f'{host.ip_address}',
            '-m', 'ping',
            '-u', host.username,
            '-p', str(host.port),
            '--timeout=10'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            host.status = 'active'
            host.check_message = '连接成功'
            success = True
        else:
            host.status = 'failed'
            host.check_message = result.stderr or result.stdout
            success = False
            
        host.last_check = timezone.now()
        host.save()
        
        logger.info(f"主机连通性检查完成: {host.hostname}, 状态: {host.status}")
        
        return {
            'host_id': host_id,
            'hostname': host.hostname,
            'success': success,
            'status': host.status,
            'message': host.check_message
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"主机连通性检查超时: host_id={host_id}")
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
        logger.error(f"主机连通性检查失败: {str(e)}")
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
        
        logger.info(f"开始收集主机Facts: {host.hostname} ({host.ip_address})")
        
        # 使用ansible setup模块收集信息
        result = subprocess.run([
            'ansible', f'{host.ip_address}',
            '-m', 'setup',
            '-u', host.username,
            '-p', str(host.port),
            '--timeout=30'
        ], capture_output=True, text=True, timeout=35)
        
        if result.returncode == 0:
            import json
            # 解析ansible facts
            facts_output = result.stdout
            try:
                facts_start = facts_output.find('{')
                facts_json = facts_output[facts_start:]
                facts = json.loads(facts_json)
                
                ansible_facts = facts.get('ansible_facts', {})
                
                # 更新主机信息
                host.os_family = ansible_facts.get('ansible_os_family', '')
                host.os_distribution = ansible_facts.get('ansible_distribution', '')
                host.os_version = ansible_facts.get('ansible_distribution_version', '')
                host.ansible_facts = ansible_facts
                host.status = 'active'
                host.last_check = timezone.now()
                host.save()
                
                logger.info(f"主机Facts收集完成: {host.hostname}")
                
                return {
                    'host_id': host_id,
                    'hostname': host.hostname,
                    'success': True,
                    'facts': ansible_facts
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Facts数据解析失败: {str(e)}")
                return {
                    'host_id': host_id,
                    'success': False,
                    'message': 'Facts数据解析失败'
                }
        else:
            logger.error(f"Facts收集失败: {result.stderr}")
            return {
                'host_id': host_id,
                'success': False,
                'message': result.stderr or result.stdout
            }
            
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
        import yaml
        
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