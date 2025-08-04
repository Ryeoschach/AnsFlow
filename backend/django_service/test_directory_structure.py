#!/usr/bin/env python
"""
测试工作目录打印功能和目录结构建议
"""
import os
import sys

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')

import django
django.setup()

from pipelines.services.local_executor import LocalPipelineExecutor
from cicd_integrations.executors.execution_context import ExecutionContext

class MockPipelineStep:
    """模拟PipelineStep对象"""
    def __init__(self, step_type, name, command="", parameters=None, timeout_seconds=300):
        self.id = 999
        self.step_type = step_type
        self.name = name
        self.command = command
        self.parameters = parameters or {}
        self.timeout_seconds = timeout_seconds
        
        # 添加必要的属性
        self.ansible_parameters = {}
        self.ansible_playbook = None
        self.ansible_inventory = None
        self.ansible_credential = None
        self.docker_image = parameters.get('image', '') if parameters else ''
        self.docker_tag = parameters.get('tag', '') if parameters else ''
        self.docker_registry = None
        self.docker_config = {}
        self.k8s_cluster = None
        self.k8s_namespace = ""
        self.k8s_resource_name = ""
        self.k8s_config = {}
        self.environment_vars = {}
        self.order = 1
        self.status = 'pending'

def test_directory_structure_scenarios():
    """测试不同的目录结构场景"""
    print("🧪 测试工作目录和代码目录结构方案")
    print("=" * 80)
    
    # 创建执行上下文
    context = ExecutionContext(
        execution_id=100,
        pipeline_name="目录结构测试",
        trigger_type='manual'
    )
    
    working_directory = context.get_workspace_path()
    execution_context = {
        'working_directory': working_directory,
        'execution_id': 100,
        'pipeline_name': "目录结构测试"
    }
    
    executor = LocalPipelineExecutor()
    
    print(f"✅ 工作目录: {working_directory}")
    
    # 场景1: 拉取代码到工作目录下的子目录
    print(f"\n📋 场景1: 标准Git克隆 - 拉取到子目录")
    print("-" * 60)
    
    # 模拟git clone命令 (创建代码目录)
    step1 = MockPipelineStep(
        step_type='fetch_code',
        name='拉取代码',
        command=f'mkdir -p myproject && echo "# My Project" > myproject/README.md && echo "FROM python:3.9" > myproject/Dockerfile'
    )
    
    print(f"🚀 执行fetch_code步骤...")
    result1 = executor.execute_step(step1, execution_context)
    print(f"   结果: {'✅ 成功' if result1.get('success') else '❌ 失败'}")
    
    # 场景2: 在代码目录中执行构建
    if result1.get('success'):
        print(f"\n📋 场景2: 在代码目录中构建")
        print("-" * 60)
        
        # 创建Docker构建步骤 - 需要进入代码目录
        step2 = MockPipelineStep(
            step_type='docker_build',
            name='构建镜像',
            parameters={
                'image': 'myproject',
                'tag': 'latest',
                'dockerfile': 'Dockerfile',  # 相对于代码目录的路径
                'context': '.'  # 构建上下文为代码目录
            }
        )
        
        # 修改上下文，指向代码目录
        code_context = execution_context.copy()
        code_directory = os.path.join(working_directory, 'myproject')
        code_context['working_directory'] = code_directory
        
        print(f"🚀 执行docker_build步骤...")
        print(f"   切换到代码目录: {code_directory}")
        result2 = executor.execute_step(step2, code_context)
        print(f"   结果: {'✅ 成功' if result2.get('success') else '❌ 失败'}")
        if not result2.get('success'):
            print(f"   错误: {result2.get('error', 'Unknown error')}")

def print_directory_recommendations():
    """打印目录结构建议"""
    print(f"\n" + "=" * 80)
    print("💡 关于工作目录结构的建议")
    print("=" * 80)
    
    print("""
🎯 推荐的目录结构方案：

┌─ 方案A: 保持在工作目录根 (推荐)
│
├── /tmp/pipeline_name_execution_id/          # 工作目录根
│   ├── project_name/                         # git clone创建的代码目录  
│   │   ├── Dockerfile
│   │   ├── src/
│   │   └── README.md
│   ├── artifacts/                            # 构建产物目录
│   ├── logs/                                 # 执行日志目录
│   └── temp/                                 # 临时文件目录

┌─ 方案B: 直接进入代码目录 (不推荐)
│
├── /tmp/pipeline_name_execution_id/project_name/  # 直接在代码目录工作
│   ├── Dockerfile  
│   ├── src/
│   └── README.md

""")
    
    print("🔍 各方案优缺点分析:")
    print()
    print("✅ 方案A优点:")
    print("   • 工作目录结构清晰，便于管理多个项目")
    print("   • 可以存储构建产物、日志等元数据")  
    print("   • 后续步骤可以灵活切换目录")
    print("   • 便于目录隔离和清理")
    print()
    print("❌ 方案B缺点:")
    print("   • 工作目录混乱，代码和构建产物混杂")
    print("   • 难以管理多个代码仓库")
    print("   • 清理困难")
    print()
    
    print("🎯 具体实施建议:")
    print()
    print("1. fetch_code步骤:")
    print("   • 始终在工作目录根执行git clone")
    print("   • git clone会自动创建项目目录")
    print("   • 保存代码目录路径到上下文")
    print()
    print("2. docker_build步骤:")
    print("   • 从上下文获取代码目录路径")
    print("   • 切换到代码目录执行docker build")
    print("   • 构建完成后可以回到工作目录根")
    print()
    print("3. 其他步骤:")
    print("   • 根据需要在工作目录根或代码目录执行")
    print("   • 通过上下文传递目录信息")
    print("   • 使用相对路径提高可移植性")

def main():
    """主函数"""
    print("🚀 AnsFlow工作目录管理测试")
    print("=" * 80)
    
    test_directory_structure_scenarios()
    print_directory_recommendations()
    
    print(f"\n" + "=" * 80)
    print("📋 实施建议总结:")
    print("1. ✅ 已添加工作目录打印功能 - 每个步骤都会显示当前目录")
    print("2. ✅ 推荐使用方案A - 保持在工作目录根，按需切换")
    print("3. 🔄 下一步 - 实现智能目录切换逻辑")
    print("4. 🔄 下一步 - 在上下文中传递代码目录路径")

if __name__ == "__main__":
    main()
