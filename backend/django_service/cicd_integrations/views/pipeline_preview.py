from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json
import logging

from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters.base import PipelineDefinition
from cicd_integrations.models import CICDTool

# 引入并行执行服务
from pipelines.services.parallel_execution import ParallelExecutionService
from pipelines.services.jenkins_sync import JenkinsPipelineSyncService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def pipeline_preview(request):
    """
    生成Pipeline预览
    支持两种模式：
    1. preview_mode=true: 使用前端传递的临时步骤数据（编辑器预览）
    2. preview_mode=false: 使用数据库中已保存的步骤数据（与实际执行一致）
    """
    try:
        data = json.loads(request.body)
        
        pipeline_id = data.get('pipeline_id')
        steps = data.get('steps', [])
        execution_mode = data.get('execution_mode', 'local')
        execution_tool_id = data.get('execution_tool')
        preview_mode = data.get('preview_mode', True)  # 默认为预览模式
        
        # 如果不是预览模式，从数据库获取实际步骤数据
        if not preview_mode and pipeline_id:
            try:
                from pipelines.models import Pipeline
                pipeline = Pipeline.objects.get(id=pipeline_id)
                # 获取数据库中的实际步骤 - 使用steps而不是atomic_steps
                db_steps = pipeline.steps.all().order_by('order')
                steps = []
                for db_step in db_steps:
                    steps.append({
                        'name': db_step.name,
                        'step_type': db_step.step_type,
                        'parameters': db_step.environment_vars or {},  # 使用environment_vars作为parameters
                        'order': db_step.order,
                        'description': db_step.description or '',
                        'parallel_group': db_step.parallel_group or ''  # 这个字段存在于PipelineStep中
                    })
                    
                logger.info(f"从数据库获取到 {len(steps)} 个步骤")
                for step in steps:
                    logger.info(f"数据库步骤: {step['name']}, parallel_group: {step['parallel_group']}")
                    
            except Exception as e:
                logger.warning(f"无法从数据库获取流水线 {pipeline_id} 的步骤: {e}")
                # 如果数据库获取失败且前端没有提供steps，使用空列表
                if not steps:
                    logger.error(f"数据库获取失败且前端未提供步骤数据，pipeline_id={pipeline_id}")
                    steps = []
        
        # 创建Pipeline定义对象
        pipeline_definition = PipelineDefinition(
            name=f"Pipeline {pipeline_id} Preview",
            steps=steps,
            triggers=data.get('triggers', {}),
            environment=data.get('environment', {}),
            artifacts=data.get('artifacts', []),
            timeout=data.get('timeout', 3600)
        )
        
        result = {
            'workflow_summary': {
                'total_steps': len(steps),
                'estimated_duration': f"{len(steps) * 2}分钟",  # 假设每个步骤2分钟
                'step_types': list(set(step.get('step_type', 'unknown') for step in steps)),
                'triggers': ['manual'],  # 默认触发方式
                'preview_mode': preview_mode,  # 返回当前预览模式
                'data_source': 'frontend' if preview_mode else 'database'  # 数据来源
            }
        }
        
        # 如果有Jenkins工具，生成Jenkinsfile
        ci_tool_type = data.get('ci_tool_type', 'jenkins')  # 默认为Jenkins
        
        # 使用并行执行服务来分析并行组和生成Jenkins Pipeline
        try:
            parallel_service = ParallelExecutionService()
            
            # 分析并行组
            parallel_groups = parallel_service.analyze_parallel_groups(steps)
            
            logger.info(f"Pipeline预览分析到并行组: {len(parallel_groups)}")
            for group in parallel_groups:
                logger.info(f"并行组 {group['name']}: {len(group['steps'])} 个步骤")                # 使用Jenkins同步服务生成Pipeline
                if ci_tool_type == 'jenkins':
                    # 创建一个临时的CICDTool对象用于Jenkins同步
                    from cicd_integrations.models import CICDTool
                    
                    # 尝试获取真实的Jenkins工具，如果没有则创建临时对象
                    if execution_tool_id:
                        try:
                            jenkins_tool = CICDTool.objects.get(id=execution_tool_id)
                        except CICDTool.DoesNotExist:
                            # 创建临时Jenkins工具对象
                            jenkins_tool = CICDTool(
                                name='Mock Jenkins',
                                tool_type='jenkins',
                                base_url='http://mock-jenkins:8080',
                                username='mock',
                                token='mock'
                            )
                    else:
                        # 创建临时Jenkins工具对象
                        jenkins_tool = CICDTool(
                            name='Mock Jenkins',
                            tool_type='jenkins',
                            base_url='http://mock-jenkins:8080',
                            username='mock',
                            token='mock'
                        )
                    jenkins_sync = JenkinsPipelineSyncService(jenkins_tool)
                    
                    # 构建Pipeline配置数据
                    pipeline_config = {
                        'id': pipeline_id,
                        'name': f"Pipeline {pipeline_id} Preview",
                        'steps': steps,
                        'parallel_groups': parallel_groups,
                        'execution_mode': execution_mode,
                        'environment': data.get('environment', {}),
                        'timeout': data.get('timeout', 3600)
                    }
                    
                    # 创建一个临时的Pipeline对象用于生成Jenkins脚本
                    from pipelines.models import Pipeline, PipelineStep
                    
                    # 模拟Pipeline对象
                    class MockPipeline:
                        def __init__(self, pipeline_config):
                            self.id = pipeline_config.get('id', 123)
                            self.name = pipeline_config.get('name', 'Mock Pipeline')
                            self.execution_mode = pipeline_config.get('execution_mode', 'jenkins')
                            self.environment = pipeline_config.get('environment', {})
                            self.timeout = pipeline_config.get('timeout', 3600)
                            self._steps = pipeline_config.get('steps', [])
                            
                        @property
                        def steps(self):
                            # 创建原子步骤的QuerySet模拟
                            class MockQuerySet:
                                def __init__(self, steps_data):
                                    self.steps_data = steps_data
                                    self._mock_steps = None
                                    
                                def _create_mock_steps(self):
                                    """创建MockPipelineStep对象列表"""
                                    if self._mock_steps is None:
                                        self._mock_steps = []
                                        for step_data in self.steps_data:
                                            step = type('MockPipelineStep', (), {
                                                'id': step_data.get('id', 1),
                                                'name': step_data.get('name', ''),
                                                'step_type': step_data.get('step_type', ''),
                                                'parameters': step_data.get('parameters', {}),
                                                'order': step_data.get('order', 0),
                                                'description': step_data.get('description', ''),
                                                'parallel_group': step_data.get('parallel_group', None)
                                            })()
                                            self._mock_steps.append(step)
                                    return self._mock_steps
                                    
                                def all(self):
                                    return self._create_mock_steps()
                                
                                def order_by(self, field):
                                    mock_steps = self._create_mock_steps()
                                    if field == 'order':
                                        return sorted(mock_steps, key=lambda x: getattr(x, 'order', 0))
                                    return mock_steps
                                
                                def __iter__(self):
                                    return iter(self._create_mock_steps())
                                
                                def __len__(self):
                                    return len(self.steps_data)
                            
                            return MockQuerySet(self._steps)
                    
                    mock_pipeline = MockPipeline(pipeline_config)
                    
                    # 生成Jenkins脚本
                    jenkinsfile = jenkins_sync._convert_steps_to_jenkins_script(mock_pipeline)
                    result['jenkinsfile'] = jenkinsfile
                    result['content'] = jenkinsfile  # 为了兼容前端
                
                # 添加并行组信息到摘要
                result['workflow_summary']['parallel_groups'] = len(parallel_groups)
                result['workflow_summary']['parallel_steps'] = sum(len(group['steps']) for group in parallel_groups)
                
                logger.info(f"成功生成Jenkins Pipeline，包含 {len(parallel_groups)} 个并行组")
                
        except Exception as e:
            logger.error(f"使用并行执行服务生成Pipeline失败: {e}")
            # 回退到原有逻辑
            
            try:
                tool = CICDTool.objects.get(id=execution_tool_id)
                ci_tool_type = tool.tool_type
                
                if tool.tool_type == 'jenkins':
                    jenkins_adapter = JenkinsAdapter(
                        base_url=tool.base_url,
                        username=tool.username,
                        token=tool.token
                    )
                    
                    # 生成Jenkinsfile
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        jenkinsfile = loop.run_until_complete(
                            jenkins_adapter.create_pipeline_file(pipeline_definition)
                        )
                        result['jenkinsfile'] = jenkinsfile
                        result['content'] = jenkinsfile  # 为了兼容前端
                    finally:
                        loop.close()
                        
            except CICDTool.DoesNotExist:
                logger.warning(f"CI/CD工具 {execution_tool_id} 不存在")
                # 生成模拟文件
                mock_result = generate_mock_pipeline_files(steps, ci_tool_type)
                result.update(mock_result)
                result['content'] = mock_result.get('jenkinsfile', '')
            except Exception as e:
                logger.error(f"生成Pipeline文件失败: {e}")
                # 生成模拟文件
                mock_result = generate_mock_pipeline_files(steps, ci_tool_type)
                result.update(mock_result)
                result['content'] = mock_result.get('jenkinsfile', '')
        else:
            # 生成模拟Pipeline文件用于预览
            # 但在非预览模式时，尝试使用真实的Jenkins适配器逻辑
            if not preview_mode and ci_tool_type == 'jenkins':
                try:
                    # 使用真实的Jenkins适配器逻辑，但不连接实际的Jenkins
                    from cicd_integrations.adapters.jenkins import JenkinsAdapter
                    
                    # 创建一个临时适配器，用于生成Jenkinsfile
                    temp_adapter = JenkinsAdapter(
                        base_url="http://mock-jenkins:8080",
                        username="mock",
                        token="mock"
                    )
                    
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        jenkinsfile = loop.run_until_complete(
                            temp_adapter.create_pipeline_file(pipeline_definition)
                        )
                        result['jenkinsfile'] = jenkinsfile
                        result['content'] = jenkinsfile
                    finally:
                        loop.close()
                        
                except Exception as e:
                    logger.warning(f"使用真实Jenkins适配器失败: {e}")
                    # 回退到模拟生成
                    mock_result = generate_mock_pipeline_files(steps, ci_tool_type)
                    result.update(mock_result)
                    result['content'] = mock_result.get('jenkinsfile', '')
            else:
                # 生成模拟Pipeline文件用于预览
                mock_result = generate_mock_pipeline_files(steps, ci_tool_type)
                result.update(mock_result)
                result['content'] = mock_result.get('jenkinsfile', '')
        
        # 添加支持的工具信息
        result['supported_tools'] = ['jenkins', 'gitlab', 'github']
        result['current_tool'] = ci_tool_type
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Pipeline预览生成失败: {e}")
        return JsonResponse({
            'error': str(e),
            'message': 'Pipeline预览生成失败'
        }, status=500)

def generate_mock_pipeline_files(steps, tool_type='jenkins'):
    """生成多种CI/CD工具的Pipeline文件"""
    result = {}
    
    # 首先分析并行组
    try:
        from pipelines.services.parallel_execution import ParallelExecutionService
        parallel_service = ParallelExecutionService()
        parallel_groups = parallel_service.analyze_parallel_groups(steps)
        
        logger.info(f"Mock生成: 分析到 {len(parallel_groups)} 个并行组")
        
        if tool_type == 'jenkins':
            result['jenkinsfile'] = generate_mock_jenkinsfile_with_parallel(steps, parallel_groups)
        elif tool_type == 'gitlab':
            result['gitlab_ci'] = generate_mock_gitlab_ci(steps)
        elif tool_type == 'github':
            result['github_actions'] = generate_mock_github_actions(steps)
        else:
            # 默认生成所有类型
            result['jenkinsfile'] = generate_mock_jenkinsfile_with_parallel(steps, parallel_groups)
            result['gitlab_ci'] = generate_mock_gitlab_ci(steps)
            result['github_actions'] = generate_mock_github_actions(steps)
            
    except Exception as e:
        logger.warning(f"并行组分析失败，使用简单模式: {e}")
        # 回退到原有逻辑
        if tool_type == 'jenkins':
            result['jenkinsfile'] = generate_mock_jenkinsfile(steps)
        elif tool_type == 'gitlab':
            result['gitlab_ci'] = generate_mock_gitlab_ci(steps)
        elif tool_type == 'github':
            result['github_actions'] = generate_mock_github_actions(steps)
        else:
            result['jenkinsfile'] = generate_mock_jenkinsfile(steps)
            result['gitlab_ci'] = generate_mock_gitlab_ci(steps)
            result['github_actions'] = generate_mock_github_actions(steps)
    
    return result

def generate_mock_jenkinsfile_with_parallel(steps, parallel_groups):
    """生成支持并行组的Jenkins Pipeline - 简化版本"""
    try:
        logger.info(f"开始生成并行组Jenkins Pipeline，步骤数: {len(steps)}, 并行组数: {len(parallel_groups)}")
        
        # 构建Jenkins Pipeline脚本
        script_lines = [
            "pipeline {",
            "    agent any",
            "    ",
            "    options {",
            "        timeout(time: 60, unit: 'MINUTES')",
            "        buildDiscarder(logRotator(numToKeepStr: '10'))",
            "    }",
            "    ",
            "    environment {",
            "        APP_ENV = 'development'",
            "    }",
            "    ",
            "    stages {"
        ]
        
        # 分离并行组步骤和顺序步骤
        parallel_steps_map = {}
        sequential_steps = []
        
        logger.info(f"输入的并行组数量: {len(parallel_groups)}")
        for i, group in enumerate(parallel_groups):
            logger.info(f"并行组 {i}: {group}")
        
        # 构建并行组映射
        for group in parallel_groups:
            group_name = group.get('name', f'Unknown Group')
            for step in group.get('steps', []):
                step_name = step.get('name', '')
                parallel_steps_map[step_name] = group_name
                logger.info(f"映射并行步骤: {step_name} -> {group_name}")
        
        logger.info(f"并行步骤映射: {parallel_steps_map}")
        
        # 分类步骤
        for step in steps:
            step_name = step.get('name', '')
            if step_name in parallel_steps_map:
                logger.info(f"步骤 {step_name} 将在并行组中处理")
                continue  # 并行步骤会在并行组中处理
            else:
                logger.info(f"步骤 {step_name} 作为顺序步骤")
                sequential_steps.append(step)
        
        # 创建执行序列（包含顺序步骤和并行组）
        execution_sequence = []
        
        # 添加顺序步骤
        for step in sequential_steps:
            execution_sequence.append({
                'type': 'sequential',
                'order': step.get('order', 0),
                'step': step
            })
        
        # 添加并行组
        for group in parallel_groups:
            min_order = min(step.get('order', 0) for step in group['steps'])
            execution_sequence.append({
                'type': 'parallel',
                'order': min_order,
                'group': group
            })
        
        # 按order排序
        execution_sequence.sort(key=lambda x: x['order'])
        
        # 生成stages
        for item in execution_sequence:
            if item['type'] == 'sequential':
                # 顺序步骤
                step = item['step']
                command = _generate_step_command_simple(step)
                safe_shell_cmd = _safe_shell_command(command)
                
                script_lines.extend([
                    f"        stage('{step.get('name', 'Unknown Step')}') {{",
                    "            steps {",
                    f"                {safe_shell_cmd}",
                    "            }",
                    "        }"
                ])
            else:
                # 并行组
                group = item['group']
                group_name = group.get('name', '并行执行组')
                
                script_lines.extend([
                    f"        stage('{group_name}') {{",
                    "            parallel {"
                ])
                
                for step in group['steps']:
                    command = _generate_step_command_simple(step)
                    step_name = step.get('name', 'Unknown Step')
                    safe_shell_cmd = _safe_shell_command(command)
                    
                    script_lines.extend([
                        f"                stage('{step_name}') {{",
                        "                    steps {",
                        f"                        {safe_shell_cmd}",
                        "                    }",
                        "}"
                    ])
                
                script_lines.extend([
                    "            }",
                    "        }"
                ])
        
        script_lines.extend([
            "    }",
            "    ",
            "    post {",
            "        always {",
            "            cleanWs()",
            "        }",
            "        success {",
            "            echo 'Pipeline 执行成功!'",
            "        }",
            "        failure {",
            "            echo 'Pipeline 执行失败!'",
            "        }",
            "    }",
            "}"
        ])
        
        jenkinsfile = "\n".join(script_lines)
        
        logger.info(f"成功生成并行组Jenkins Pipeline，包含 {len(parallel_groups)} 个并行组")
        return jenkinsfile
        
    except Exception as e:
        logger.warning(f"生成并行组Jenkins Pipeline失败，回退到简单模式: {e}")
        return generate_mock_jenkinsfile(steps)

def _generate_step_command_simple(step):
    """为步骤生成简单的命令"""
    step_type = step.get('step_type', 'custom')
    parameters = step.get('parameters', {})
    
    if step_type == 'ansible':
        playbook = parameters.get('playbook_path', 'playbook.yml')
        inventory = parameters.get('inventory_path', 'hosts')
        return f"ansible-playbook -i {inventory} {playbook}"
    elif step_type == 'fetch_code':
        repo = parameters.get('repository', '')
        if repo:
            branch = parameters.get('branch', 'main')
            return f"git clone --branch {branch} {repo} ."
        return "echo '执行代码检出'"
    elif step_type == 'test':
        test_cmd = parameters.get('test_command', 'npm test')
        return test_cmd
    elif step_type == 'build':
        build_tool = parameters.get('build_tool', 'npm')
        if build_tool == 'npm':
            return "npm ci && npm run build"
        elif build_tool == 'maven':
            return "mvn clean package"
        return f"{build_tool} build"
    elif step_type == 'deploy':
        deploy_cmd = parameters.get('deploy_command', 'kubectl apply -f deployment.yaml')
        return deploy_cmd
    elif step_type == 'shell_script':
        return parameters.get('script', 'echo "Shell脚本执行"')
    else:
        command = parameters.get('command', f'echo "执行{step_type}步骤"')
        return command

def generate_mock_gitlab_ci(steps):
    """生成GitLab CI配置文件"""
    stages = []
    jobs = []
    
    for i, step in enumerate(steps):
        step_name = step.get('name', f'step-{i+1}').lower().replace(' ', '-')
        step_type = step.get('step_type', 'custom')
        parameters = step.get('parameters', {})
        
        stage_name = f"stage-{i+1}"
        stages.append(stage_name)
        
        # 根据步骤类型生成脚本
        script_lines = []
        if step_type == 'ansible':
            playbook = parameters.get('playbook_path', 'playbook.yml')
            inventory = parameters.get('inventory_path', 'hosts')
            script_lines.append(f"ansible-playbook -i {inventory} {playbook}")
        elif step_type == 'shell_script':
            script_lines.append(parameters.get('script', 'echo "Shell脚本执行"'))
        elif step_type == 'docker_build':
            tag = parameters.get('tag', 'latest')
            script_lines.extend([
                f"docker build -t $CI_REGISTRY_IMAGE:{tag} .",
                f"docker push $CI_REGISTRY_IMAGE:{tag}"
            ])
        elif step_type == 'test':
            script_lines.append(parameters.get('test_command', 'npm test'))
        else:
            script_lines.append(f'echo "执行{step_type}步骤"')
        
        script_str = '\n    - '.join([''] + script_lines)
        
        job = f"""{step_name}:
  stage: {stage_name}
  script:{script_str}
"""
        
        if step_type == 'test':
            job += """  coverage: '/Coverage: \\d+\\.\\d+%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
"""
        elif step_type == 'build':
            job += """  artifacts:
    paths:
      - dist/
    expire_in: 1 week
"""
        
        jobs.append(job)
    
    gitlab_ci = f"""# GitLab CI/CD Pipeline Configuration
# Generated by AnsFlow CI/CD Platform

stages:
{chr(10).join(f'  - {stage}' for stage in stages)}

variables:
  NODE_VERSION: "18"
  
before_script:
  - echo "Starting pipeline..."

{chr(10).join(jobs)}

# Deploy job (if needed)
deploy:
  stage: deploy
  script:
    - echo "Deploying application..."
  only:
    - main
  when: manual
"""
    
    return gitlab_ci

def generate_mock_github_actions(steps):
    """生成GitHub Actions工作流配置"""
    jobs = []
    
    for i, step in enumerate(steps):
        step_name = step.get('name', f'step-{i+1}').lower().replace(' ', '-')
        step_type = step.get('step_type', 'custom')
        parameters = step.get('parameters', {})
        
        # 根据步骤类型生成步骤
        step_actions = []
        
        if step_type == 'ansible':
            playbook = parameters.get('playbook_path', 'playbook.yml')
            inventory = parameters.get('inventory_path', 'hosts')
            step_actions.append(f"""      - name: Run Ansible Playbook
        run: ansible-playbook -i {inventory} {playbook}""")
        elif step_type == 'shell_script':
            script = parameters.get('script', 'echo "Shell脚本执行"')
            step_actions.append(f"""      - name: Run Shell Script
        run: {script}""")
        elif step_type == 'docker_build':
            tag = parameters.get('tag', 'latest')
            step_actions.extend([
                f"""      - name: Build Docker Image
        run: docker build -t myapp:{tag} .""",
                f"""      - name: Push Docker Image
        run: docker push myapp:{tag}"""
            ])
        elif step_type == 'test':
            test_cmd = parameters.get('test_command', 'npm test')
            step_actions.append(f"""      - name: Run Tests
        run: {test_cmd}""")
        else:
            step_actions.append(f"""      - name: {step.get('name', f'Step {i+1}')}
        run: echo "执行{step_type}步骤" """)
        
        job = f"""  {step_name}:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
{chr(10).join(step_actions)}"""
        
        jobs.append(job)
    
    github_actions = f"""# GitHub Actions Workflow
# Generated by AnsFlow CI/CD Platform

name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

env:
  NODE_VERSION: '18'

jobs:
{chr(10).join(jobs)}
"""
    
    return github_actions

def generate_mock_jenkinsfile(steps):
    """生成模拟的Jenkinsfile用于预览"""
    
    stages = []
    for step in steps:
        step_name = step.get('name', 'Unknown Step')
        step_type = step.get('step_type', 'custom')
        parameters = step.get('parameters', {})
        
        # 根据步骤类型生成模拟命令
        if step_type == 'ansible':
            # 先尝试获取实际的ansible配置数据
            playbook_path = parameters.get('playbook_path', parameters.get('playbook', ''))
            inventory_path = parameters.get('inventory_path', 'hosts')
            extra_vars = parameters.get('extra_vars', {})
            
            # 如果有ID参数，尝试获取实际数据
            playbook_id = parameters.get('playbook_id')
            inventory_id = parameters.get('inventory_id')
            credential_id = parameters.get('credential_id')
            
            if playbook_id:
                try:
                    from ansible_integration.models import AnsiblePlaybook
                    playbook_obj = AnsiblePlaybook.objects.get(id=playbook_id)
                    playbook_path = playbook_obj.file_path or playbook_obj.name
                except Exception as e:
                    logger.warning(f"无法获取playbook {playbook_id}: {e}")
                    playbook_path = f"playbook-{playbook_id}.yml"
            
            if inventory_id:
                try:
                    from ansible_integration.models import AnsibleInventory
                    inventory_obj = AnsibleInventory.objects.get(id=inventory_id)
                    inventory_path = inventory_obj.file_path or 'hosts'
                    # 如果inventory有默认用户，添加到命令中
                    if hasattr(inventory_obj, 'default_user') and inventory_obj.default_user:
                        extra_vars['ansible_user'] = inventory_obj.default_user
                except Exception as e:
                    logger.warning(f"无法获取inventory {inventory_id}: {e}")
                    inventory_path = f"inventory-{inventory_id}"
            
            if credential_id:
                try:
                    from ansible_integration.models import AnsibleCredential
                    credential_obj = AnsibleCredential.objects.get(id=credential_id)
                    # 添加认证相关的参数
                    if credential_obj.username:
                        extra_vars['ansible_user'] = credential_obj.username
                except Exception as e:
                    logger.warning(f"无法获取credential {credential_id}: {e}")
            
            # 构建ansible命令
            ansible_cmd_parts = ['ansible-playbook']
            
            if inventory_path:
                ansible_cmd_parts.extend(['-i', inventory_path])
            
            # 添加用户参数
            if 'ansible_user' in extra_vars:
                ansible_cmd_parts.extend(['-u', extra_vars.pop('ansible_user')])
            
            # 添加extra_vars
            if extra_vars:
                if isinstance(extra_vars, dict):
                    vars_str = ' '.join([f'{k}={v}' for k, v in extra_vars.items()])
                    ansible_cmd_parts.extend(['--extra-vars', f'"{vars_str}"'])
                else:
                    ansible_cmd_parts.extend(['--extra-vars', f'"{extra_vars}"'])
            
            # 添加其他参数
            tags = parameters.get('tags', '')
            if tags:
                ansible_cmd_parts.extend(['--tags', tags])
            
            verbose = parameters.get('verbose', False)
            if verbose:
                ansible_cmd_parts.append('-v')
            
            # 添加playbook路径
            if playbook_path:
                ansible_cmd_parts.append(playbook_path)
            else:
                ansible_cmd_parts.append('playbook.yml')  # 默认值
            
            command = ' '.join(ansible_cmd_parts)
                
        elif step_type == 'fetch_code':
            # 代码拉取步骤
            custom_command = parameters.get('command', '')
            if custom_command:
                command = custom_command
            else:
                repo_url = parameters.get('repository', parameters.get('repository_url', ''))
                branch = parameters.get('branch', 'main')
                if repo_url:
                    command = f'git clone --branch {branch} {repo_url} .'
                else:
                    command = 'echo "执行代码拉取步骤"'
                    
        elif step_type == 'custom':
            command = parameters.get('command', parameters.get('script', f'echo "执行{step_type}步骤"'))
            
        elif step_type == 'shell_script':
            command = parameters.get('script', 'echo "Shell脚本执行"')
            
        elif step_type == 'docker_build':
            tag = parameters.get('tag', 'latest')
            command = f"docker build -t myapp:{tag} ."
            
        elif step_type == 'test':
            command = parameters.get('test_command', 'npm test')
            
        elif step_type == 'build':
            build_tool = parameters.get('build_tool', 'npm')
            if build_tool == 'npm':
                command = "npm ci && npm run build"
            elif build_tool == 'maven':
                command = "mvn clean package"
            else:
                command = f"{build_tool} build"
                
        elif step_type == 'deploy':
            command = parameters.get('deploy_command', 'kubectl apply -f deployment.yaml')
            
        else:
            command = parameters.get('command', f'echo "执行{step_type}步骤"')
        
        stage = f"""        stage('{step_name}') {{
            steps {{
                {_safe_shell_command(command)}
            }}
        }}"""
        stages.append(stage)
    
    jenkinsfile = f"""pipeline {{
    agent any
    
    options {{
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }}
    
    environment {{
        APP_ENV = 'development'
    }}
    
    stages {{
{chr(10).join(stages)}
    }}
    
    post {{
        always {{
            cleanWs()
        }}
        success {{
            echo 'Pipeline 执行成功!'
        }}
        failure {{
            echo 'Pipeline 执行失败!'
        }}
    }}
}}"""
    
    return jenkinsfile

def generate_mock_gitlab_ci_yaml(steps):
    """生成模拟的GitLab CI YAML用于预览"""
    stages = []
    for step in steps:
        step_name = step.get('name', 'unknown').replace(' ', '_')
        step_type = step.get('step_type', 'script')
        parameters = step.get('parameters', {})
        
        if step_type == 'ansible':
            playbook = parameters.get('playbook_path', 'playbook.yml')
            inventory = parameters.get('inventory_path', 'hosts')
            extra_vars = parameters.get('extra_vars', {})
            
            if extra_vars:
                vars_str = ' '.join([f'{k}={v}' for k, v in extra_vars.items()])
                command = f"ansible-playbook -i {inventory} --extra-vars \"{vars_str}\" {playbook}"
            else:
                command = f"ansible-playbook -i {inventory} {playbook}"
                
        elif step_type == 'shell_script':
            command = parameters.get('script', 'echo "Shell脚本执行"')
            
        elif step_type == 'docker_build':
            tag = parameters.get('tag', 'latest')
            command = f"docker build -t myapp:{tag} ."
            
        elif step_type == 'test':
            command = parameters.get('test_command', 'npm test')
            
        elif step_type == 'build':
            build_tool = parameters.get('build_tool', 'npm')
            if build_tool == 'npm':
                command = "npm ci && npm run build"
            elif build_tool == 'maven':
                command = "mvn clean package"
            else:
                command = f"{build_tool} build"
                
        elif step_type == 'deploy':
            command = parameters.get('deploy_command', 'kubectl apply -f deployment.yaml')
            
        else:
            command = parameters.get('command', f'echo "执行{step_type}步骤"')
        
        stage = f"""
{step_name}:
  stage: {step_name}
  script:
    - {command}
"""
        stages.append(stage)
    
    gitlab_ci_yaml = f"""stages:
{chr(10).join(f'  - {step.get("name", "unknown").replace(" ", "_")}' for step in steps)}

{chr(10).join(stages)}
"""
    
    return gitlab_ci_yaml

def generate_mock_github_actions_yaml(steps):
    """生成模拟的GitHub Actions YAML用于预览"""
    jobs = []
    for step in steps:
        step_name = step.get('name', 'unknown').replace(' ', '_')
        step_type = step.get('step_type', 'run')
        parameters = step.get('parameters', {})
        
        if step_type == 'ansible':
            playbook = parameters.get('playbook_path', 'playbook.yml')
            inventory = parameters.get('inventory_path', 'hosts')
            extra_vars = parameters.get('extra_vars', {})
            
            if extra_vars:
                vars_str = ' '.join([f'{k}={v}' for k, v in extra_vars.items()])
                command = f"ansible-playbook -i {inventory} --extra-vars \"{vars_str}\" {playbook}"
            else:
                command = f"ansible-playbook -i {inventory} {playbook}"
                
        elif step_type == 'shell_script':
            command = parameters.get('script', 'echo "Shell脚本执行"')
            
        elif step_type == 'docker_build':
            tag = parameters.get('tag', 'latest')
            command = f"docker build -t myapp:{tag} ."
            
        elif step_type == 'test':
            command = parameters.get('test_command', 'npm test')
            
        elif step_type == 'build':
            build_tool = parameters.get('build_tool', 'npm')
            if build_tool == 'npm':
                command = "npm ci && npm run build"
            elif build_tool == 'maven':
                command = "mvn clean package"
            else:
                command = f"{build_tool} build"
                
        elif step_type == 'deploy':
            command = parameters.get('deploy_command', 'kubectl apply -f deployment.yaml')
            
        else:
            command = parameters.get('command', f'echo "执行{step_type}步骤"')
        
        job = f"""
  {step_name}:
    runs-on: ubuntu-latest
    steps:
      - name: {step_name}
        run: {command}
"""
        jobs.append(job)
    
    github_actions_yaml = f"""name: CI

on: [push, pull_request]

jobs:{chr(10).join(jobs)}
"""
    
    return github_actions_yaml

def _safe_shell_command(command):
    """安全地转义shell命令中的引号"""
    if not command:
        return 'echo "Empty command"'
    
    # 如果命令包含单引号，使用双引号包围，并转义内部的双引号
    if "'" in command:
        # 转义命令中的双引号和反斜杠
        escaped_command = command.replace('\\', '\\\\').replace('"', '\\"')
        return f'sh "{escaped_command}"'
    else:
        # 如果命令不包含单引号，使用单引号包围
        return f"sh '{command}'"
