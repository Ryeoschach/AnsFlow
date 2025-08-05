#!/usr/bin/env python
"""
完整的并行执行测试
"""
import os
import django
from django.conf import settings

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import Pipeline
from cicd_integrations.services import UnifiedCICDEngine
from cicd_integrations.models import PipelineExecution
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_parallel_execution():
    """测试完整的并行执行流程"""
    
    # 获取流水线
    pipeline = Pipeline.objects.filter(name='前端并行组测试流水线').first()
    if not pipeline:
        print('❌ 未找到流水线')
        return
    
    print(f'✅ 找到流水线: {pipeline.name}')
    
    # 创建执行记录
    execution = PipelineExecution.objects.create(
        pipeline=pipeline,
        status='pending',
        parameters={}
    )
    
    print(f'🚀 创建执行记录: {execution.id}')
    
    # 创建UnifiedCICDEngine实例并执行
    engine = UnifiedCICDEngine()
    
    print('\n=== 开始并行执行 ===')
    try:
        # 执行流水线
        result = engine._perform_execution(execution.id)
        
        print(f'🎯 执行结果: {result}')
        
        # 刷新执行记录
        execution.refresh_from_db()
        print(f'📊 执行状态: {execution.status}')
        print(f'📝 执行日志: {execution.logs}')
        
        # 检查步骤执行记录
        step_executions = execution.step_executions.all().order_by('order')
        print(f'\n📋 步骤执行详情:')
        for step_exec in step_executions:
            step_name = step_exec.step_name
            duration = step_exec.duration
            duration_str = f"{duration.total_seconds():.2f}s" if duration else "N/A"
            print(f'  {step_exec.order}. {step_name}: {step_exec.status} (耗时: {duration_str})')
            if step_exec.started_at and step_exec.completed_at:
                print(f'     开始: {step_exec.started_at.strftime("%H:%M:%S.%f")[:-3]}')
                print(f'     结束: {step_exec.completed_at.strftime("%H:%M:%S.%f")[:-3]}')
        
        # 验证并行执行
        print(f'\n🔍 并行执行验证:')
        step2_exec = step_executions.filter(atomic_step__name='Step2-构建前端').first()
        step4_exec = step_executions.filter(atomic_step__name='Step4-单元测试').first()
        
        if step2_exec and step4_exec:
            if step2_exec.started_at and step4_exec.started_at:
                time_diff = abs((step2_exec.started_at - step4_exec.started_at).total_seconds())
                if time_diff < 5:  # 5秒内启动认为是并行
                    print(f'✅ Step2 和 Step4 并行执行成功 (启动时间差: {time_diff:.2f}s)')
                else:
                    print(f'⚠️ Step2 和 Step4 可能不是并行执行 (启动时间差: {time_diff:.2f}s)')
        
        return result
        
    except Exception as e:
        print(f'❌ 执行过程中出错: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = test_full_parallel_execution()
    if result:
        print(f'\n🎉 测试完成！')
    else:
        print(f'\n❌ 测试失败！')
