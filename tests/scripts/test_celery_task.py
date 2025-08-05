#!/usr/bin/env python
"""
测试Celery异步任务执行
"""
import os
import django
import time

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from cicd_integrations.tasks import execute_pipeline_task
from pipelines.models import Pipeline
from cicd_integrations.models import PipelineExecution
from django.contrib.auth.models import User


def test_celery_task():
    """测试Celery任务执行"""
    print("=== 测试Celery异步任务执行 ===")
    
    try:
        # 获取测试数据
        pipeline = Pipeline.objects.get(id=4)
        user = User.objects.first()
        print(f"使用流水线: {pipeline.name}")
        print(f"触发用户: {user.username}")
        
        # 创建流水线执行记录
        execution = PipelineExecution.objects.create(
            pipeline=pipeline,
            trigger_type='manual',
            triggered_by=user,
            parameters={'test': True, 'celery_test': True}
        )
        
        print(f"创建了流水线执行记录，ID: {execution.id}")
        
        # 调用Celery任务
        result = execute_pipeline_task.delay(
            execution_id=execution.id,
            pipeline_id=pipeline.id,
            trigger_type='manual',
            triggered_by_id=user.id,
            parameters={'test': True, 'celery_test': True}
        )
        
        print(f"Celery任务已提交，task_id: {result.task_id}")
        print("等待任务完成...")
        
        # 等待任务完成
        try:
            task_result = result.get(timeout=60)  # 增加超时时间
            print(f"任务完成: {task_result}")
            
            # 检查执行结果
            execution.refresh_from_db()
            print(f"执行状态: {execution.status}")
            print(f"开始时间: {execution.started_at}")
            print(f"完成时间: {execution.completed_at}")
            
            return True
            
        except Exception as e:
            print(f"任务执行出错: {e}")
            return False
            
    except Exception as e:
        print(f"测试失败: {e}")
        return False


if __name__ == "__main__":
    success = test_celery_task()
    if success:
        print("\n✅ Celery异步任务测试成功!")
    else:
        print("\n❌ Celery异步任务测试失败!")
