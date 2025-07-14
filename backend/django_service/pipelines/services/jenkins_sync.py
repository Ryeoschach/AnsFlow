"""
Jenkins流水线同步服务
负责将AnsFlow流水线转换为Jenkins Pipeline Job，并同步状态
"""
import json
import requests
from typing import Dict, Any, Optional
from django.utils import timezone
from django.conf import settings
import logging

from pipelines.models import Pipeline, PipelineToolMapping
from cicd_integrations.models import CICDTool

logger = logging.getLogger(__name__)


class JenkinsPipelineSyncService:
    """Jenkins流水线同步服务"""
    
    def __init__(self, tool: CICDTool):
        self.tool = tool
        self.base_url = tool.base_url.rstrip('/')
        self.auth = None
        if tool.username and tool.token:
            self.auth = (tool.username, tool.token)
    
    def create_jenkins_job(self, pipeline: Pipeline) -> Optional[Dict[str, Any]]:
        """在Jenkins中创建作业"""
        try:
            # 生成Jenkins Pipeline配置
            job_config = self._generate_jenkins_config(pipeline)
            job_name = self._generate_job_name(pipeline)
            
            # 创建Jenkins作业
            url = f"{self.base_url}/createItem"
            headers = {
                'Content-Type': 'application/xml',
            }
            params = {
                'name': job_name
            }
            
            response = requests.post(
                url,
                data=job_config,
                headers=headers,
                params=params,
                auth=self.auth,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully created Jenkins job: {job_name}")
                
                # 创建或更新映射关系
                mapping, created = PipelineToolMapping.objects.update_or_create(
                    pipeline=pipeline,
                    tool=self.tool,
                    defaults={
                        'external_job_id': job_name,
                        'external_job_name': job_name,
                        'sync_status': 'success',
                        'last_sync_at': timezone.now()
                    }
                )
                
                # 更新流水线的工具关联
                pipeline.execution_tool = self.tool
                pipeline.tool_job_name = job_name
                pipeline.execution_mode = 'remote'
                pipeline.save()
                
                return {
                    'success': True,
                    'job_name': job_name,
                    'job_url': f"{self.base_url}/job/{job_name}/",
                    'mapping_id': mapping.id
                }
            else:
                logger.error(f"Failed to create Jenkins job: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Jenkins API error: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Exception creating Jenkins job: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_jenkins_job(self, pipeline: Pipeline) -> Optional[Dict[str, Any]]:
        """更新Jenkins作业配置"""
        try:
            mapping = PipelineToolMapping.objects.get(pipeline=pipeline, tool=self.tool)
            job_name = mapping.external_job_name
            
            # 生成新的配置
            job_config = self._generate_jenkins_config(pipeline)
            
            # 更新Jenkins作业
            url = f"{self.base_url}/job/{job_name}/config.xml"
            headers = {
                'Content-Type': 'application/xml',
            }
            
            response = requests.post(
                url,
                data=job_config,
                headers=headers,
                auth=self.auth,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully updated Jenkins job: {job_name}")
                mapping.sync_status = 'success'
                mapping.last_sync_at = timezone.now()
                mapping.save()
                
                return {
                    'success': True,
                    'job_name': job_name,
                    'message': 'Job updated successfully'
                }
            else:
                logger.error(f"Failed to update Jenkins job: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Jenkins API error: {response.status_code}"
                }
                
        except PipelineToolMapping.DoesNotExist:
            logger.error(f"No mapping found for pipeline {pipeline.id} and tool {self.tool.id}")
            return {
                'success': False,
                'error': 'No mapping found'
            }
        except Exception as e:
            logger.error(f"Exception updating Jenkins job: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def trigger_jenkins_build(self, pipeline: Pipeline, parameters: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """触发Jenkins构建"""
        try:
            mapping = PipelineToolMapping.objects.get(pipeline=pipeline, tool=self.tool)
            job_name = mapping.external_job_name
            
            # 构建触发URL
            if parameters:
                url = f"{self.base_url}/job/{job_name}/buildWithParameters"
                data = parameters
            else:
                url = f"{self.base_url}/job/{job_name}/build"
                data = {}
            
            response = requests.post(
                url,
                data=data,
                auth=self.auth,
                timeout=30,
                verify=False
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully triggered Jenkins build for job: {job_name}")
                
                # 从Location头获取队列URL
                queue_url = response.headers.get('Location', '')
                
                return {
                    'success': True,
                    'job_name': job_name,
                    'queue_url': queue_url,
                    'message': 'Build triggered successfully'
                }
            else:
                logger.error(f"Failed to trigger Jenkins build: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Jenkins API error: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Exception triggering Jenkins build: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_build_status(self, pipeline: Pipeline) -> Optional[Dict[str, Any]]:
        """同步构建状态"""
        try:
            mapping = PipelineToolMapping.objects.get(pipeline=pipeline, tool=self.tool)
            job_name = mapping.external_job_name
            
            # 获取最新构建信息
            url = f"{self.base_url}/job/{job_name}/lastBuild/api/json"
            
            response = requests.get(
                url,
                auth=self.auth,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                build_info = response.json()
                
                # 映射Jenkins状态到Pipeline状态
                jenkins_result = build_info.get('result', '').lower()
                status_mapping = {
                    'success': 'success',
                    'failure': 'failed',
                    'aborted': 'cancelled',
                    'unstable': 'failed',
                    '': 'running'  # 空表示正在运行
                }
                
                new_status = status_mapping.get(jenkins_result, 'pending')
                
                # 更新流水线状态
                if pipeline.status != new_status:
                    pipeline.status = new_status
                    if jenkins_result and jenkins_result != '':
                        pipeline.completed_at = timezone.now()
                    pipeline.save()
                
                # 更新映射状态
                mapping.sync_status = 'success'
                mapping.last_sync_at = timezone.now()
                mapping.save()
                
                return {
                    'success': True,
                    'jenkins_status': jenkins_result,
                    'pipeline_status': new_status,
                    'build_number': build_info.get('number'),
                    'build_url': build_info.get('url')
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to get build status: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Exception syncing build status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_job_name(self, pipeline: Pipeline) -> str:
        """生成Jenkins作业名称"""
        # 清理名称，确保符合Jenkins命名规范
        project_name = pipeline.project.name.replace(' ', '_').replace('-', '_')
        pipeline_name = pipeline.name.replace(' ', '_').replace('-', '_')
        return f"ansflow_{project_name}_{pipeline_name}_{pipeline.id}"
    
    def _generate_jenkins_config(self, pipeline: Pipeline) -> str:
        """生成Jenkins Pipeline配置XML"""
        
        # 将AnsFlow原子步骤转换为Jenkins Pipeline脚本
        pipeline_script = self._convert_steps_to_jenkins_script(pipeline)
        
        # Jenkins Pipeline Job配置模板
        config_template = """<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions/>
  <description>Auto-generated from AnsFlow Pipeline: {pipeline_name}</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.plugins.jira.JiraProjectProperty plugin="jira@3.1.1"/>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.87">
    <script>{pipeline_script}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>"""
        
        return config_template.format(
            pipeline_name=pipeline.name,
            pipeline_script=pipeline_script
        )
    
    def _convert_steps_to_jenkins_script(self, pipeline: Pipeline) -> str:
        """将AnsFlow步骤转换为Jenkins Pipeline脚本（支持并行组）"""
        
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
        
        # 获取流水线的步骤并分析并行组
        pipeline_steps = pipeline.steps.all().order_by('order')
        pipeline_steps_list = list(pipeline_steps)  # 转换为列表以便调试
        logger.info(f"Jenkins同步: 获取到 {len(pipeline_steps_list)} 个步骤")
        
        # 打印每个步骤的详细信息
        for i, step in enumerate(pipeline_steps_list):
            parallel_group = getattr(step, 'parallel_group', None)
            logger.info(f"步骤 {i+1}: name='{step.name}', order={step.order}, parallel_group='{parallel_group}'")
        
        execution_plan = self._analyze_execution_plan(pipeline_steps_list)
        
        # 根据执行计划生成Jenkins stages
        for stage_info in execution_plan['stages']:
            if stage_info['parallel']:
                # 生成并行stage
                self._add_parallel_stage_to_script(script_lines, stage_info)
            else:
                # 生成顺序stage
                self._add_sequential_stage_to_script(script_lines, stage_info)
        
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
        
        return "\n".join(script_lines)
    
    def _analyze_execution_plan(self, pipeline_steps):
        """分析原子步骤的执行计划，识别并行组"""
        parallel_groups = {}
        sequential_steps = []
        execution_plan = {'stages': []}
        
        # 收集并行组信息
        for step in pipeline_steps:
            parallel_group_id = getattr(step, 'parallel_group', None)
            logger.info(f"步骤 '{step.name}': parallel_group = '{parallel_group_id}'")
            if parallel_group_id and parallel_group_id.strip():
                group_id = parallel_group_id.strip()
                logger.info(f"步骤 '{step.name}' 属于并行组 '{group_id}'")
                if group_id not in parallel_groups:
                    parallel_groups[group_id] = {
                        'id': group_id,
                        'name': f"并行组-{group_id}",
                        'steps': [],
                        'min_order': float('inf'),
                        'max_order': 0
                    }
                
                parallel_groups[group_id]['steps'].append(step)
                parallel_groups[group_id]['min_order'] = min(parallel_groups[group_id]['min_order'], step.order)
                parallel_groups[group_id]['max_order'] = max(parallel_groups[group_id]['max_order'], step.order)
            else:
                sequential_steps.append(step)
        
        logger.info(f"分析完成: {len(parallel_groups)} 个并行组, {len(sequential_steps)} 个顺序步骤")
        
        # 创建执行阶段
        all_items = []
        
        # 添加单独步骤
        for step in sequential_steps:
            all_items.append({
                'type': 'step',
                'order': step.order,
                'item': step,
                'parallel': False
            })
        
        # 添加并行组（使用最小order作为组的order）
        for group_id, group_info in parallel_groups.items():
            all_items.append({
                'type': 'parallel_group',
                'order': group_info['min_order'],
                'item': group_info,
                'parallel': True
            })
        
        # 按order排序
        all_items.sort(key=lambda x: x['order'])
        
        # 构建执行阶段
        for item in all_items:
            stage = {
                'type': item['type'],
                'parallel': item['parallel'],
                'items': []
            }
            
            if item['type'] == 'step':
                stage['items'] = [item['item']]
            else:  # parallel_group
                stage['items'] = item['item']['steps']
                stage['group_info'] = item['item']
            
            execution_plan['stages'].append(stage)
        
        return execution_plan
    
    def _add_parallel_stage_to_script(self, script_lines, stage_info):
        """向脚本添加并行stage"""
        group_info = stage_info.get('group_info', {})
        group_name = group_info.get('name', '并行执行')
        steps = stage_info['items']
        
        script_lines.append(f"        stage('{group_name}') {{")
        script_lines.append("            parallel {")
        
        # 为每个并行步骤生成一个并行分支
        for step in steps:
            step_name = step.name.replace("'", "\\'").replace(" ", "_").replace("-", "_")
            script_lines.append(f"                stage('{step_name}') {{")
            script_lines.append("                    steps {")
            
            # 生成步骤命令
            command = self._generate_step_command(step)
            script_lines.append(f"                        {command}")
            
            script_lines.append("                    }")
            script_lines.append("                }")
        
        script_lines.append("            }")
        script_lines.append("        }")
    
    def _add_sequential_stage_to_script(self, script_lines, stage_info):
        """向脚本添加顺序stage"""
        step = stage_info['items'][0]  # 顺序stage只有一个步骤
        stage_name = step.name.replace("'", "\\'")
        
        script_lines.append(f"        stage('{stage_name}') {{")
        script_lines.append("            steps {")
        
        # 生成步骤命令
        command = self._generate_step_command(step)
        script_lines.append(f"                {command}")
        
        script_lines.append("            }")
        script_lines.append("        }")
    
    def _generate_step_command(self, step):
        """根据步骤类型生成Jenkins命令"""
        # 首先检查step的config字段（新格式）
        if hasattr(step, 'config') and step.config:
            if step.step_type == 'shell' and 'command' in step.config:
                command = step.config['command']
                return self._safe_shell_command(command)
            elif step.step_type == 'python' and 'script' in step.config:
                script = step.config['script']
                return f'sh "python3 -c \\"{script}\\""'
            elif step.step_type == 'docker' and 'command' in step.config:
                image = step.config.get('image', 'ubuntu:latest')
                command = step.config['command']
                return f'sh "docker run --rm {image} {command}"'
        
        # 兼容旧的parameters字段
        if hasattr(step, 'parameters') and step.parameters:
            if step.step_type == 'shell_command':
                command = step.parameters.get('command', 'echo "No command specified"')
                return self._safe_shell_command(command)
            elif step.step_type == 'git_clone':
                repo_url = step.parameters.get('repository_url', '')
                branch = step.parameters.get('branch', 'main')
                return f"git branch: '{branch}', url: '{repo_url}'"
            elif step.step_type == 'docker_build':
                image_name = step.parameters.get('image_name', 'app')
                dockerfile = step.parameters.get('dockerfile', 'Dockerfile')
                return f'sh "docker build -t {image_name} -f {dockerfile} ."'
            elif step.step_type == 'test_execution':
                test_command = step.parameters.get('test_command', 'npm test')
                return self._safe_shell_command(test_command)
            elif step.step_type == 'artifact_upload':
                artifacts = step.parameters.get('artifacts', '**/*')
                return f"archiveArtifacts artifacts: '{artifacts}'"
            elif step.step_type == 'notification':
                message = step.parameters.get('message', 'Step completed')
                return f"echo '{message}'"
        
        # 默认处理
        step_name = step.name.replace("'", "\\'")
        return f"echo 'Executing step: {step_name}'"
    
    def _safe_shell_command(self, command):
        """安全地转义shell命令中的引号"""
        if not command:
            return 'sh "Empty command"'
        
        # 如果命令包含单引号，使用双引号包围，并转义内部的双引号
        if "'" in command:
            # 转义命令中的双引号和反斜杠
            escaped_command = command.replace('\\', '\\\\').replace('"', '\\"')
            return f'sh "{escaped_command}"'
        else:
            # 如果命令不包含单引号，使用单引号包围
            return f"sh '{command}'"
    
    def sync_pipeline_to_jenkins(self, pipeline: Pipeline) -> Dict[str, Any]:
        """将AnsFlow流水线同步到Jenkins"""
        try:
            # 检查是否已经存在映射
            try:
                mapping = PipelineToolMapping.objects.get(pipeline=pipeline, tool=self.tool)
                # 如果已存在，更新作业
                return self.update_jenkins_job(pipeline)
            except PipelineToolMapping.DoesNotExist:
                # 如果不存在，创建新作业
                return self.create_jenkins_job(pipeline)
                
        except Exception as e:
            logger.error(f"Exception syncing pipeline to Jenkins: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def import_jenkins_job_as_pipeline(self, job_name: str) -> Dict[str, Any]:
        """从Jenkins导入作业为AnsFlow流水线"""
        try:
            # 获取Jenkins作业配置
            url = f"{self.base_url}/job/{job_name}/config.xml"
            
            response = requests.get(
                url,
                auth=self.auth,
                timeout=30,
                verify=False
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"Failed to get Jenkins job config: {response.status_code}"
                }
            
            # 解析Jenkins配置并转换为Pipeline
            jenkins_config = response.text
            pipeline_data = self._parse_jenkins_config_to_pipeline(jenkins_config, job_name)
            
            # 创建Pipeline
            from pipelines.models import Pipeline
            pipeline = Pipeline.objects.create(**pipeline_data)
            
            # 创建映射关系
            mapping = PipelineToolMapping.objects.create(
                pipeline=pipeline,
                tool=self.tool,
                external_job_id=job_name,
                external_job_name=job_name,
                sync_status='imported',
                last_sync_at=timezone.now()
            )
            
            return {
                'success': True,
                'pipeline_id': pipeline.id,
                'pipeline_name': pipeline.name,
                'mapping_id': mapping.id,
                'message': 'Jenkins job imported successfully'
            }
            
        except Exception as e:
            logger.error(f"Exception importing Jenkins job: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_jenkins_config_to_pipeline(self, jenkins_config: str, job_name: str) -> Dict[str, Any]:
        """解析Jenkins配置XML并转换为Pipeline数据"""
        import xml.etree.ElementTree as ET
        from pipelines.models import AtomicStep
        
        try:
            # 解析XML配置
            root = ET.fromstring(jenkins_config)
            
            # 提取基本信息
            description_elem = root.find('description')
            description = description_elem.text if description_elem is not None else f"Imported from Jenkins job: {job_name}"
            
            # 提取Pipeline脚本
            script_elem = root.find('.//script')
            script_content = script_elem.text if script_elem is not None else ""
            
            # 生成Pipeline名称
            pipeline_name = job_name.replace('_', ' ').title()
            if pipeline_name.startswith('Ansflow '):
                pipeline_name = pipeline_name[8:]  # 移除 "Ansflow " 前缀
            
            # 基本Pipeline数据
            pipeline_data = {
                'name': pipeline_name,
                'description': description,
                'project': self.tool.project,
                'created_by': None,  # 需要在调用时设置
                'execution_tool': self.tool,
                'tool_job_name': job_name,
                'execution_mode': 'remote',
                'trigger_type': 'manual',
                'status': 'pending'
            }
            
            return pipeline_data
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse Jenkins XML config: {e}")
            # 返回基本的Pipeline数据
            return {
                'name': job_name.replace('_', ' ').title(),
                'description': f"Imported from Jenkins job: {job_name} (parsing failed)",
                'project': self.tool.project,
                'created_by': None,
                'execution_tool': self.tool,
                'tool_job_name': job_name,
                'execution_mode': 'remote',
                'trigger_type': 'manual',
                'status': 'pending'
            }
        except Exception as e:
            logger.error(f"Exception parsing Jenkins config: {e}")
            raise
    
    def _parse_jenkins_script_to_steps(self, script_content: str) -> list:
        """解析Jenkins Pipeline脚本并提取步骤（可选的高级功能）"""
        steps = []
        
        try:
            # 简单的脚本解析 - 查找常见的步骤模式
            lines = script_content.split('\\n') if '\\n' in script_content else script_content.split('\n')
            
            current_stage = None
            step_order = 1
            
            for line in lines:
                line = line.strip()
                
                # 检测stage定义
                if line.startswith("stage("):
                    # 提取stage名称
                    import re
                    match = re.search(r"stage\(['\"](.*?)['\"]\)", line)
                    if match:
                        current_stage = match.group(1)
                
                # 检测各种步骤类型
                elif line.startswith("sh "):
                    # Shell命令步骤
                    command = self._extract_shell_command(line)
                    if command and current_stage:
                        steps.append({
                            'name': current_stage,
                            'step_type': 'shell_command',
                            'description': f'Execute: {command[:50]}...' if len(command) > 50 else f'Execute: {command}',
                            'parameters': {'command': command},
                            'order': step_order
                        })
                        step_order += 1
                
                elif line.startswith("git "):
                    # Git步骤
                    git_params = self._extract_git_params(line)
                    if git_params and current_stage:
                        steps.append({
                            'name': f"{current_stage} - Git Clone",
                            'step_type': 'git_clone',
                            'description': f'Clone repository: {git_params.get("url", "unknown")}',
                            'parameters': git_params,
                            'order': step_order
                        })
                        step_order += 1
                
                elif "archiveArtifacts" in line:
                    # 归档构件步骤
                    artifacts = self._extract_archive_artifacts(line)
                    if artifacts and current_stage:
                        steps.append({
                            'name': f"{current_stage} - Archive Artifacts",
                            'step_type': 'artifact_upload',
                            'description': f'Archive artifacts: {artifacts}',
                            'parameters': {'artifacts': artifacts},
                            'order': step_order
                        })
                        step_order += 1
        
        except Exception as e:
            logger.warning(f"Failed to parse Jenkins script steps: {e}")
        
        return steps
    
    def _extract_shell_command(self, line: str) -> str:
        """从Jenkins脚本行中提取shell命令"""
        import re
        # 匹配 sh 'command' 或 sh "command" 格式
        match = re.search(r"sh\s+['\"](.+?)['\"]", line)
        return match.group(1) if match else ""
    
    def _extract_git_params(self, line: str) -> Dict[str, str]:
        """从Jenkins脚本行中提取git参数"""
        import re
        params = {}
        
        # 提取URL
        url_match = re.search(r"url:\s*['\"](.+?)['\"]", line)
        if url_match:
            params['repository_url'] = url_match.group(1)
        
        # 提取分支
        branch_match = re.search(r"branch:\s*['\"](.+?)['\"]", line)
        if branch_match:
            params['branch'] = branch_match.group(1)
        else:
            params['branch'] = 'main'  # 默认分支
        
        return params
    
    def _extract_archive_artifacts(self, line: str) -> str:
        """从Jenkins脚本行中提取归档构件路径"""
        import re
        # 匹配 archiveArtifacts artifacts: 'pattern' 格式
        match = re.search(r"artifacts:\s*['\"](.+?)['\"]", line)
        return match.group(1) if match else "**/*"
    
    def get_jenkins_jobs_list(self) -> Dict[str, Any]:
        """获取Jenkins中的作业列表"""
        try:
            url = f"{self.base_url}/api/json?tree=jobs[name,url,description,buildable]"
            
            response = requests.get(
                url,
                auth=self.auth,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                
                for job in data.get('jobs', []):
                    jobs.append({
                        'name': job.get('name'),
                        'url': job.get('url'),
                        'description': job.get('description', ''),
                        'buildable': job.get('buildable', False)
                    })
                
                return {
                    'success': True,
                    'jobs': jobs,
                    'total_count': len(jobs)
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to get jobs list: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Exception getting Jenkins jobs list: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_jenkins_job(self, job_name: str) -> Dict[str, Any]:
        """删除Jenkins作业"""
        try:
            url = f"{self.base_url}/job/{job_name}/doDelete"
            
            response = requests.post(
                url,
                auth=self.auth,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully deleted Jenkins job: {job_name}")
                return {
                    'success': True,
                    'message': f'Job {job_name} deleted successfully'
                }
            else:
                logger.error(f"Failed to delete Jenkins job: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Jenkins API error: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Exception deleting Jenkins job: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_job_build_history(self, job_name: str, limit: int = 10) -> Dict[str, Any]:
        """获取Jenkins作业的构建历史"""
        try:
            url = f"{self.base_url}/job/{job_name}/api/json?tree=builds[number,url,result,timestamp,duration,displayName]{{,{limit}}}"
            
            response = requests.get(
                url,
                auth=self.auth,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                builds = []
                
                for build in data.get('builds', []):
                    builds.append({
                        'number': build.get('number'),
                        'url': build.get('url'),
                        'result': build.get('result'),
                        'timestamp': build.get('timestamp'),
                        'duration': build.get('duration'),
                        'display_name': build.get('displayName')
                    })
                
                return {
                    'success': True,
                    'job_name': job_name,
                    'builds': builds,
                    'total_builds': len(builds)
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to get build history: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Exception getting Jenkins build history: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_jenkins_connection(self) -> Dict[str, Any]:
        """测试Jenkins连接"""
        try:
            url = f"{self.base_url}/api/json"
            
            response = requests.get(
                url,
                auth=self.auth,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'message': 'Jenkins connection successful',
                    'jenkins_version': data.get('version', 'unknown'),
                    'node_name': data.get('nodeName', 'unknown'),
                    'num_executors': data.get('numExecutors', 0)
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Authentication failed - invalid username or token'
                }
            elif response.status_code == 403:
                return {
                    'success': False,
                    'error': 'Access forbidden - insufficient permissions'
                }
            else:
                return {
                    'success': False,
                    'error': f"Jenkins API error: {response.status_code}"
                }
                
        except requests.exceptions.ConnectTimeout:
            return {
                'success': False,
                'error': 'Connection timeout - Jenkins server unreachable'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error - Jenkins server unreachable'
            }
        except Exception as e:
            logger.error(f"Exception testing Jenkins connection: {e}")
            return {
                'success': False,
                'error': str(e)
            }
