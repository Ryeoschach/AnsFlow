#!/usr/bin/env python3
"""
测试流水线中Ansible步骤的日志记录修复
验证修复后的执行器是否能产生详细的日志信息
"""
import os
import django
import sys

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

import logging
from pipelines.models import Pipeline, PipelineStep
from ansible_integration.models import AnsiblePlaybook, AnsibleInventory, AnsibleCredential
from pipelines.services.local_executor import LocalPipelineExecutor
from django.contrib.auth.models import User

# 设置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ansible_pipeline_logs():
    """测试流水线中Ansible步骤的日志记录"""
    print("\n🧪 测试流水线中Ansible步骤的日志记录修复...")
    
    try:
        # 查找现有的Ansible相关资源
        playbook = AnsiblePlaybook.objects.first()
        inventory = AnsibleInventory.objects.first()
        credential = AnsibleCredential.objects.first()
        
        if not playbook or not inventory:
            print("❌ 缺少Ansible测试资源（playbook或inventory）")
            return False
            
        print(f"✅ 找到测试资源:")
        print(f"   - Playbook: {playbook.name} (ID: {playbook.id})")
        print(f"   - Inventory: {inventory.name} (ID: {inventory.id})")
        print(f"   - Credential: {credential.name if credential else 'None'} (ID: {credential.id if credential else 'None'})")
        
        # 查找包含Ansible步骤的流水线
        ansible_pipeline = None
        for pipeline in Pipeline.objects.all():
            ansible_steps = pipeline.steps.filter(step_type='ansible')
            if ansible_steps.exists():
                ansible_pipeline = pipeline
                break
                
        if not ansible_pipeline:
            print("❌ 没有找到包含Ansible步骤的流水线")
            return False
            
        ansible_step = ansible_pipeline.steps.filter(step_type='ansible').first()
        print(f"✅ 找到Ansible步骤: {ansible_step.name} in 流水线 {ansible_pipeline.name}")
        print(f"   - Step ID: {ansible_step.id}")
        print(f"   - Ansible Playbook: {ansible_step.ansible_playbook}")
        print(f"   - Ansible Inventory: {ansible_step.ansible_inventory}")
        print(f"   - Ansible Credential: {ansible_step.ansible_credential}")
        print(f"   - Ansible Parameters: {ansible_step.ansible_parameters}")
        
        # 创建执行器并测试步骤执行
        print(f"\n🚀 开始测试Ansible步骤执行...")
        executor = LocalPipelineExecutor()
        
        # 构建执行上下文
        context = {
            'working_directory': '/tmp',
            'execution_id': 999,  # 测试用的ID
            'pipeline_name': ansible_pipeline.name
        }
        
        print(f"📋 执行上下文: {context}")
        print(f"\n📝 开始执行步骤，请观察日志输出...")
        print("=" * 60)
        
        # 执行步骤
        result = executor._execute_ansible_step(ansible_step, context)
        
        print("=" * 60)
        print(f"✅ 步骤执行完成！")
        print(f"📊 执行结果:")
        print(f"   - Success: {result.get('success', False)}")
        print(f"   - Message: {result.get('message', 'No message')}")
        print(f"   - Output: {result.get('output', 'No output')[:200]}...")
        if result.get('error'):
            print(f"   - Error: {result.get('error', 'No error')}")
        if result.get('data'):
            print(f"   - Data: {result.get('data', {})}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_ansible_pipeline_logs()
    print(f"\n{'✅ 测试通过！' if success else '❌ 测试失败！'}")
    
    print(f"\n📝 修复说明:")
    print(f"   1. 修改了 pipelines/services/local_executor.py 中的 _execute_ansible_step 方法")
    print(f"   2. 现在会创建真正的 AnsibleExecution 记录并调用 execute_ansible_playbook 任务")
    print(f"   3. 使用 ExecutionLogger 记录详细的执行过程")
    print(f"   4. 流水线中的 Ansible 步骤现在应该能看到完整的执行日志")
    
    sys.exit(0 if success else 1)
