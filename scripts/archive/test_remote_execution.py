#!/usr/bin/env python3
"""
测试远程流水线执行功能
验证流水线是否能在Jenkins等外部CI/CD工具上正确执行
"""

import os
import sys
import django
import asyncio
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
sys.path.append('/Users/creed/Workspace/OpenSource/ansflow/backend/django_service')

django.setup()

from cicd_integrations.models import CICDTool, PipelineExecution
from pipelines.models import Pipeline
from cicd_integrations.services import UnifiedCICDEngine
from django.contrib.auth.models import User

def test_remote_execution():
    """测试远程执行功能"""
    print("=" * 60)
    print("🚀 测试远程流水线执行功能")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. 获取工具和流水线
        print("1. 📋 获取测试数据")
        tool = CICDTool.objects.get(id=3)  # Jenkins工具
        pipeline = Pipeline.objects.get(id=1)  # 测试流水线
        user = User.objects.get(username='admin')
        
        print(f"   ✅ CI/CD工具: {tool.name} ({tool.tool_type})")
        print(f"   ✅ 流水线: {pipeline.name}")
        print(f"   ✅ 执行模式: {pipeline.execution_mode}")
        print(f"   ✅ 执行工具: {pipeline.execution_tool}")
        print()
        
        # 2. 检查执行模式
        print("2. 🔧 检查执行模式")
        if pipeline.execution_mode != 'remote':
            print(f"   ⚠️  当前执行模式: {pipeline.execution_mode}")
            print("   🔄 更新为远程执行模式...")
            pipeline.execution_mode = 'remote'
            pipeline.execution_tool = tool
            pipeline.save()
            print("   ✅ 已更新为远程执行模式")
        else:
            print("   ✅ 已设置为远程执行模式")
        print()
        
        # 3. 创建执行记录
        print("3. 🚀 创建流水线执行")
        execution = PipelineExecution.objects.create(
            pipeline=pipeline,
            cicd_tool=tool,
            status='pending',
            trigger_type='manual',
            triggered_by=user,
            definition=pipeline.config or {},
            parameters={'branch': 'main', 'test_mode': 'remote'},
            trigger_data={
                'timestamp': datetime.now().isoformat(),
                'user': user.username,
                'test': 'remote_execution'
            }
        )
        
        print(f"   ✅ 执行记录ID: {execution.id}")
        print(f"   ✅ 状态: {execution.status}")
        print(f"   ✅ 关联工具: {execution.cicd_tool.name}")
        print()
        
        # 4. 测试执行逻辑
        print("4. ⚙️  测试执行逻辑")
        engine = UnifiedCICDEngine()
        
        print("   🔄 调用_perform_execution方法...")
        result = engine._perform_execution(execution.id)
        
        print(f"   📊 执行结果类型: {type(result)}")
        print(f"   📊 执行结果: {result}")
        print()
        
        # 5. 检查执行记录状态
        print("5. 📋 检查执行记录状态")
        execution.refresh_from_db()
        print(f"   📌 执行状态: {execution.status}")
        print(f"   📌 外部ID: {execution.external_id}")
        print(f"   📌 开始时间: {execution.started_at}")
        print(f"   📌 完成时间: {execution.completed_at}")
        if execution.logs:
            print(f"   📌 日志: {execution.logs[:200]}...")
        print()
        
        # 6. 验证结果
        print("6. ✅ 验证结果")
        if execution.status == 'running' and execution.external_id:
            print("   🎉 远程执行启动成功!")
            print(f"   🔗 Jenkins作业ID: {execution.external_id}")
            print("   📝 监控任务应该已经启动，会自动更新执行状态")
        elif execution.status == 'failed':
            print("   ❌ 远程执行失败")
            print(f"   💬 错误信息: {execution.logs}")
        else:
            print(f"   ⚠️  未预期的状态: {execution.status}")
        
        print()
        print("=" * 60)
        return execution
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_sync():
    """同步测试入口"""
    return test_remote_execution()

if __name__ == "__main__":
    execution = test_sync()
    
    if execution:
        print("\n🔍 建议检查:")
        print("1. 登录Jenkins查看是否创建了新的作业")
        print("2. 检查作业是否正在运行")
        print("3. 查看数据库中执行记录的状态变化")
        print(f"4. 执行ID: {execution.id}")
        
        print("\n📝 命令行检查:")
        print("# 检查执行状态")
        print(f"# python manage.py shell -c \"from cicd_integrations.models import PipelineExecution; e=PipelineExecution.objects.get(id={execution.id}); print(f'状态: {{e.status}}, 外部ID: {{e.external_id}}')\"")
    
    print("\n✨ 测试完成!")
