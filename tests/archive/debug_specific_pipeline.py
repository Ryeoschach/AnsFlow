#!/usr/bin/env python3
"""
Debug specific pipeline - 测试Integration Test Pipeline的具体问题
"""

import os
import sys
import django
import asyncio
import logging

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from cicd_integrations.models import CICDTool, AtomicStep
from cicd_integrations.adapters.jenkins import JenkinsAdapter
from cicd_integrations.adapters import PipelineDefinition
from pipelines.models import Pipeline

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_specific_pipeline():
    """测试具体的Integration Test Pipeline"""
    
    # 1. 获取Jenkins工具
    try:
        from asgiref.sync import sync_to_async
        
        jenkins_tool = await sync_to_async(CICDTool.objects.filter(
            tool_type='jenkins', 
            status__in=['active', 'authenticated']
        ).first)()
        
        if not jenkins_tool:
            logger.error("No active Jenkins tool found")
            return False
            
        logger.info(f"Using Jenkins tool: {jenkins_tool.name}")
        
        # 创建适配器
        adapter = JenkinsAdapter(
            base_url=jenkins_tool.base_url,
            username=jenkins_tool.username,
            token=jenkins_tool.token,
            **jenkins_tool.config
        )
        
    except Exception as e:
        logger.error(f"Failed to setup Jenkins adapter: {e}")
        return False
    
    # 2. 获取Integration Test Pipeline
    try:
        pipeline = await sync_to_async(Pipeline.objects.filter(
            name='Integration Test Pipeline'
        ).first)()
        
        if not pipeline:
            logger.error("Integration Test Pipeline not found")
            return False
            
        logger.info(f"Found pipeline: {pipeline.name}")
        
        # 获取原子步骤
        atomic_steps = await sync_to_async(list)(
            AtomicStep.objects.filter(
                pipeline=pipeline
            ).select_related('ansible_playbook', 'ansible_inventory', 'ansible_credential')
            .order_by('order')
        )
        
        logger.info(f"Found {len(atomic_steps)} atomic steps:")
        for step in atomic_steps:
            logger.info(f"  - {step.name} ({step.step_type})")
            logger.info(f"    Parameters: {step.parameters}")
            if step.step_type == 'ansible':
                logger.info(f"    Ansible playbook: {step.ansible_playbook}")
                logger.info(f"    Ansible inventory: {step.ansible_inventory}")
                logger.info(f"    Ansible credential: {step.ansible_credential}")
        
    except Exception as e:
        logger.error(f"Failed to get pipeline: {e}")
        return False
    
    # 3. 构建流水线定义
    try:
        steps = []
        for atomic_step in atomic_steps:
            step = {
                'name': atomic_step.name,
                'type': atomic_step.step_type,
                'parameters': atomic_step.parameters.copy(),
                'description': atomic_step.description
            }
            
            # 对于ansible步骤，添加特殊的参数处理
            if atomic_step.step_type == 'ansible':
                ansible_params = {}
                
                # 添加Ansible特有的参数
                if atomic_step.ansible_playbook:
                    ansible_params['playbook_path'] = atomic_step.ansible_playbook.name
                    ansible_params['playbook'] = atomic_step.ansible_playbook.name
                
                if atomic_step.ansible_inventory:
                    ansible_params['inventory_path'] = 'hosts'
                    ansible_params['inventory'] = 'hosts'
                
                if atomic_step.ansible_credential:
                    ansible_params['ansible_user'] = atomic_step.ansible_credential.username
                
                # 合并ansible特有参数到step参数中
                step['parameters'].update(ansible_params)
                
                logger.info(f"Processed Ansible step parameters: {step['parameters']}")
            
            steps.append(step)
        
        pipeline_def = PipelineDefinition(
            name="fixed-pipeline-test",  # 使用简单的英文名称
            steps=steps,
            triggers={},
            environment={},
            artifacts=[],
            timeout=3600
        )
        
        logger.info("Built pipeline definition successfully")
        
    except Exception as e:
        logger.error(f"Failed to build pipeline definition: {e}")
        return False
    
    # 4. 生成Jenkinsfile
    try:
        jenkinsfile = await adapter.create_pipeline_file(pipeline_def)
        logger.info("Generated Jenkinsfile:")
        print("=" * 80)
        print(jenkinsfile)
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Failed to generate Jenkinsfile: {e}")
        logger.error(f"Error details: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 生成Job配置XML
    try:
        import re
        job_name = pipeline_def.name.replace(' ', '-').lower()
        job_name = re.sub(r'[^a-z0-9\-_]', '', job_name)
        
        # 转义Jenkinsfile中的特殊字符用于XML
        escaped_jenkinsfile = jenkinsfile.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
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
        
        logger.info(f"Generated job name: {job_name}")
        logger.info("Generated Job XML (first 500 chars):")
        print(job_config[:500] + "...")
        
        # 验证XML格式
        import xml.etree.ElementTree as ET
        try:
            ET.fromstring(job_config)
            logger.info("XML format is valid")
        except ET.ParseError as e:
            logger.error(f"XML format is invalid: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to generate job config XML: {e}")
        return False
    
    # 6. 尝试实际创建Job
    try:
        logger.info("Attempting to create the job in Jenkins...")
        result = await adapter.create_pipeline(pipeline_def)
        logger.info(f"Job creation result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Job creation failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    logger.info("Starting specific pipeline debug test...")
    
    try:
        success = await test_specific_pipeline()
        
        if success:
            logger.info("✅ Pipeline test completed successfully")
        else:
            logger.error("❌ Pipeline test failed")
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
