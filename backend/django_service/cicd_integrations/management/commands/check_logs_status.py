#!/usr/bin/env python3
"""
检查执行记录的日志状态 - Django管理命令版本
"""
from django.core.management.base import BaseCommand
from cicd_integrations.models import PipelineExecution, StepExecution

class Command(BaseCommand):
    help = '检查执行记录的日志状态'

    def handle(self, *args, **options):
        self.stdout.write("检查最近的执行记录的日志状态...")
        
        # 获取最近10条执行记录
        executions = PipelineExecution.objects.select_related('cicd_tool').order_by('-id')[:10]
        
        for execution in executions:
            self.stdout.write(f"\n=== 执行记录 {execution.id} ===")
            self.stdout.write(f"状态: {execution.status}")
            self.stdout.write(f"工具: {execution.cicd_tool.name if execution.cicd_tool else 'None'}")
            self.stdout.write(f"外部ID: {execution.external_id}")
            self.stdout.write(f"主执行日志长度: {len(execution.logs) if execution.logs else 0}")
            if execution.logs:
                self.stdout.write(f"主执行日志预览: {execution.logs[:100]}...")
            
            # 检查步骤日志
            steps = execution.step_executions.all().order_by('order')
            self.stdout.write(f"步骤数量: {steps.count()}")
            
            for step in steps:
                self.stdout.write(f"  步骤 {step.order}: {step.status}")
                self.stdout.write(f"    原子步骤: {step.atomic_step.name if step.atomic_step else 'None'}")
                self.stdout.write(f"    日志长度: {len(step.logs) if step.logs else 0}")
                if step.logs:
                    self.stdout.write(f"    日志预览: {step.logs[:50]}...")
