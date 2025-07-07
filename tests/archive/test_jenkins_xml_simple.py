#!/usr/bin/env python3
"""
简化的Jenkins XML转义测试
"""
import html
import xml.etree.ElementTree as ET
import asyncio
import httpx


class MockPipelineDefinition:
    """模拟流水线定义"""
    def __init__(self, name, steps, environment=None, timeout=3600):
        self.name = name
        self.steps = steps
        self.environment = environment or {}
        self.timeout = timeout


def escape_shell_command(command: str) -> str:
    """转义shell命令中的单引号"""
    if not command:
        return command
    return command.replace("'", "\\'")


def safe_shell_command(command: str) -> str:
    """生成安全的Jenkins Pipeline sh步骤"""
    if not command:
        return "echo 'No command specified'"
    
    escaped_command = escape_shell_command(command)
    return f"sh '{escaped_command}'"


def safe_stage_name(name: str) -> str:
    """生成安全的stage名称"""
    if not name:
        return "Unnamed_Stage"
    
    # 移除或替换特殊字符
    import re
    safe_name = re.sub(r'[^\w\s\-_]', '', name)
    safe_name = safe_name.replace(' ', '_')
    
    # 如果名称为空或只包含特殊字符，使用默认名称
    if not safe_name.strip():
        safe_name = "Stage"
    
    return safe_name


def generate_stage_script(step_type: str, params: dict) -> str:
    """根据步骤类型生成Jenkins脚本"""
    if step_type == 'ansible':
        # Ansible步骤处理
        playbook_path = params.get('playbook_path', params.get('playbook', ''))
        inventory_path = params.get('inventory_path', params.get('inventory', 'hosts'))
        extra_vars = params.get('extra_vars', {})
        tags = params.get('tags', '')
        verbose = params.get('verbose', False)
        
        # 自定义命令优先
        custom_command = params.get('command', '')
        if custom_command:
            return safe_shell_command(custom_command)
        
        # 构建ansible-playbook命令
        ansible_cmd_parts = ['ansible-playbook']
        
        if inventory_path:
            ansible_cmd_parts.extend(['-i', inventory_path])
        
        if extra_vars:
            if isinstance(extra_vars, dict):
                vars_str = ' '.join([f'{k}={v}' for k, v in extra_vars.items()])
                ansible_cmd_parts.extend(['--extra-vars', f'"{vars_str}"'])
            else:
                ansible_cmd_parts.extend(['--extra-vars', f'"{extra_vars}"'])
        
        if tags:
            ansible_cmd_parts.extend(['--tags', tags])
        if verbose:
            ansible_cmd_parts.append('-v')
        
        if playbook_path:
            ansible_cmd_parts.append(playbook_path)
        else:
            return safe_shell_command("echo 'Error: No Ansible playbook specified' && exit 1")
        
        ansible_command = ' '.join(ansible_cmd_parts)
        
        return f"""
                {safe_shell_command('echo "Starting Ansible playbook execution..."')}
                {safe_shell_command(ansible_command)}
                {safe_shell_command('echo "Ansible playbook execution completed"')}"""
    
    elif step_type == 'fetch_code':
        custom_command = params.get('command', '')
        if custom_command:
            return safe_shell_command(custom_command)
        
        repo_url = params.get('repository', '')
        branch = params.get('branch', 'main')
        if repo_url:
            return f"""
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '{branch}']],
                    userRemoteConfigs: [[url: '{repo_url}']]
                ])"""
        else:
            return "checkout scm"
    
    elif step_type == 'custom':
        command = params.get('command', 'echo "No command specified"')
        return safe_shell_command(command)
    
    else:
        # 默认处理
        command = params.get('command', params.get('script', f'echo "Step type: {step_type}"'))
        return safe_shell_command(command)


def convert_steps_to_jenkinsfile(steps: list) -> str:
    """转换步骤为Jenkinsfile stages"""
    stages = []
    
    for step in steps:
        step_name = step.get('name', f"Step {step.get('id', 'Unknown')}")
        step_type = step.get('type', 'custom')
        params = step.get('parameters', {})
        
        # 生成安全的stage名称
        safe_step_name = safe_stage_name(step_name)
        
        # 生成脚本内容
        stage_script = generate_stage_script(step_type, params)
        
        stage = f"""
        stage('{safe_step_name}') {{
            steps {{
                {stage_script}
            }}
        }}"""
        stages.append(stage)
    
    return ''.join(stages)


def create_jenkinsfile(pipeline_def) -> str:
    """创建Jenkinsfile内容"""
    stages_content = convert_steps_to_jenkinsfile(pipeline_def.steps)
    
    # 构建环境变量部分
    env_vars = []
    for key, value in pipeline_def.environment.items():
        env_vars.append(f"        {key} = '{value}'")
    
    env_section = f"""
    environment {{
{chr(10).join(env_vars)}
    }}""" if env_vars else ""
    
    jenkinsfile = f"""
pipeline {{
    agent any
    
    options {{
        timeout(time: {pipeline_def.timeout // 60}, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }}{env_section}
    
    stages {{{stages_content}
    }}
    
    post {{
        always {{
            cleanWs()
        }}
        success {{
            echo 'Pipeline completed successfully!'
        }}
        failure {{
            echo 'Pipeline failed!'
        }}
    }}
}}"""
    
    return jenkinsfile.strip()


def create_job_xml(jenkinsfile: str) -> str:
    """创建Jenkins Job XML配置"""
    # XML转义Jenkinsfile内容
    escaped_jenkinsfile = html.escape(jenkinsfile)
    
    job_config = f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions/>
  <description>Generated by AnsFlow CI/CD Platform</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers/>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.92">
    <script>{escaped_jenkinsfile}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>"""
    
    return job_config


async def test_jenkins_connection(base_url: str, username: str, token: str):
    """测试Jenkins连接"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            auth = (username, token) if username and token else None
            response = await client.get(f"{base_url}/api/json", auth=auth)
            return response.status_code == 200, response.status_code
    except Exception as e:
        return False, str(e)


async def test_job_creation(base_url: str, username: str, token: str, job_name: str, job_config: str):
    """测试Jenkins Job创建"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            auth = (username, token) if username and token else None
            
            # 先尝试更新
            update_url = f"{base_url}/job/{job_name}/config.xml"
            response = await client.post(
                update_url,
                content=job_config,
                headers={'Content-Type': 'application/xml'},
                auth=auth
            )
            
            if response.status_code == 200:
                return True, f"Updated existing job: {response.status_code}"
            elif response.status_code == 404:
                # Job不存在，创建新的
                create_url = f"{base_url}/createItem?name={job_name}"
                response = await client.post(
                    create_url,
                    content=job_config,
                    headers={'Content-Type': 'application/xml'},
                    auth=auth
                )
                
                if response.status_code in [200, 201]:
                    return True, f"Created new job: {response.status_code}"
                else:
                    return False, f"Create failed: {response.status_code} - {response.text[:200]}"
            else:
                return False, f"Update failed: {response.status_code} - {response.text[:200]}"
                
    except Exception as e:
        return False, str(e)


async def main():
    """主测试函数"""
    print("Jenkins XML转义修复测试")
    print("=" * 50)
    
    # 测试流水线定义
    pipeline_def = MockPipelineDefinition(
        name="Test Special Characters Pipeline",
        steps=[
            {
                'id': 'step-1',
                'name': 'Code & Build',
                'type': 'fetch_code',
                'parameters': {
                    'repository': 'https://github.com/test/repo.git',
                    'branch': 'main',
                    'command': 'git clone "repo" && echo "Success!" && echo \'Single quotes test\''
                }
            },
            {
                'id': 'step-2',
                'name': 'Ansible Deploy',
                'type': 'ansible',
                'parameters': {
                    'playbook_path': 'deploy.yml',
                    'inventory_path': 'hosts',
                    'extra_vars': {
                        'env': 'prod',
                        'db_url': 'postgresql://user:pass@host:5432/db'
                    },
                    'tags': 'deploy,config',
                    'verbose': True
                }
            },
            {
                'id': 'step-3',
                'name': 'Custom Script',
                'type': 'custom',
                'parameters': {
                    'command': 'echo "Test <>&\'" && curl -X POST -d \'{"key": "value"}\' http://api.test.com'
                }
            }
        ],
        environment={
            'NODE_ENV': 'production',
            'API_URL': 'https://api.example.com/v1',
            'DB_URL': 'postgresql://user:pass@host:5432/db'
        }
    )
    
    print(f"测试流水线: {pipeline_def.name}")
    print(f"步骤数量: {len(pipeline_def.steps)}")
    print()
    
    # 1. 生成Jenkinsfile
    print("1. 生成Jenkinsfile...")
    jenkinsfile = create_jenkinsfile(pipeline_def)
    print("✅ Jenkinsfile生成成功")
    print()
    
    # 2. 生成Job XML配置
    print("2. 生成Job XML配置...")
    job_config = create_job_xml(jenkinsfile)
    print("✅ Job XML配置生成成功")
    print()
    
    # 3. 验证XML格式
    print("3. 验证XML格式...")
    try:
        ET.fromstring(job_config)
        print("✅ XML格式验证通过")
    except ET.ParseError as e:
        print(f"❌ XML格式验证失败: {e}")
        return
    
    # 4. 保存文件
    print("4. 保存生成的文件...")
    with open('test_fixed_jenkinsfile.groovy', 'w', encoding='utf-8') as f:
        f.write(jenkinsfile)
    print("✅ Jenkinsfile已保存到 test_fixed_jenkinsfile.groovy")
    
    with open('test_fixed_job_config.xml', 'w', encoding='utf-8') as f:
        f.write(job_config)
    print("✅ Job配置已保存到 test_fixed_job_config.xml")
    print()
    
    # 5. 测试Jenkins连接和Job创建
    jenkins_base_url = 'http://localhost:8080'
    jenkins_username = 'admin'
    jenkins_token = 'admin'
    
    print("5. 测试Jenkins连接...")
    connected, status = await test_jenkins_connection(jenkins_base_url, jenkins_username, jenkins_token)
    
    if connected:
        print("✅ Jenkins连接成功")
        
        print("6. 测试Job创建...")
        import re
        job_name = pipeline_def.name.replace(' ', '-').lower()
        job_name = re.sub(r'[^a-z0-9\-_]', '', job_name)
        
        created, result = await test_job_creation(
            jenkins_base_url, jenkins_username, jenkins_token, job_name, job_config
        )
        
        if created:
            print(f"✅ Jenkins Job操作成功: {result}")
            print(f"Job URL: {jenkins_base_url}/job/{job_name}/")
        else:
            print(f"❌ Jenkins Job操作失败: {result}")
    else:
        print(f"⚠️  Jenkins连接失败: {status}")
        print("XML转义修复已完成，但无法测试Jenkins集成")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("\n📄 生成的文件:")
    print("- test_fixed_jenkinsfile.groovy: 修复后的Jenkinsfile")
    print("- test_fixed_job_config.xml: 修复后的Job XML配置")
    print("\n🔧 修复内容:")
    print("1. 添加了HTML/XML转义处理")
    print("2. 改进了特殊字符处理")
    print("3. 增强了Ansible步骤参数处理")
    print("4. 优化了stage名称生成")


if __name__ == "__main__":
    asyncio.run(main())
