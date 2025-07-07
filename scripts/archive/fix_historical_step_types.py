#!/usr/bin/env python3
"""
修复历史数据中的步骤类型
将一些明显的步骤名称映射到正确的步骤类型
"""

import os
import sys
import django
import re

# 设置Django环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings')
django.setup()

from pipelines.models import PipelineStep

def fix_historical_step_types():
    print("🔧 开始修复历史数据中的步骤类型...")
    
    # 获取所有类型为command的步骤
    command_steps = PipelineStep.objects.filter(step_type='command')
    print(f"   发现 {command_steps.count()} 个类型为command的步骤")
    
    # 定义步骤名称到类型的映射规则
    name_to_type_mapping = {
        # 代码拉取相关
        r'.*(?:代码|code|checkout|pull|fetch|clone).*': 'fetch_code',
        # 构建相关  
        r'.*(?:构建|build|compile|package|打包).*': 'build',
        # 测试相关
        r'.*(?:测试|test|unit|integration).*': 'test',
        # 安全扫描相关
        r'.*(?:安全|security|scan|扫描|漏洞).*': 'security_scan',
        # 部署相关
        r'.*(?:部署|deploy|发布|release).*': 'deploy',
        # 通知相关
        r'.*(?:通知|notify|notification|报告|report).*': 'notify',
        # 依赖安装
        r'.*(?:依赖|dependencies|install|安装).*': 'build',
    }
    
    updated_count = 0
    
    for step in command_steps:
        original_type = step.step_type
        new_type = None
        
        # 尝试从步骤名称推断类型
        step_name_lower = step.name.lower()
        for pattern, step_type in name_to_type_mapping.items():
            if re.search(pattern, step_name_lower, re.IGNORECASE):
                new_type = step_type
                break
        
        # 尝试从描述推断类型
        if not new_type and step.description:
            desc_lower = step.description.lower()
            for pattern, step_type in name_to_type_mapping.items():
                if re.search(pattern, desc_lower, re.IGNORECASE):
                    new_type = step_type
                    break
        
        # 如果找到了更合适的类型，则更新
        if new_type and new_type != original_type:
            step.step_type = new_type
            step.save()
            updated_count += 1
            print(f"   ✓ 更新步骤 '{step.name}': {original_type} -> {new_type}")
    
    print(f"\n✅ 修复完成: 更新了 {updated_count} 个步骤的类型")
    
    # 显示更新后的统计信息
    print("\n📊 当前步骤类型统计:")
    from django.db.models import Count
    type_stats = PipelineStep.objects.values('step_type').annotate(count=Count('id')).order_by('-count')
    for stat in type_stats:
        print(f"   - {stat['step_type']}: {stat['count']} 个")
    
    return updated_count

if __name__ == '__main__':
    updated_count = fix_historical_step_types()
    print(f"\n{'='*50}")
    if updated_count > 0:
        print(f"✅ 成功修复了 {updated_count} 个历史步骤的类型")
    else:
        print("ℹ️  没有需要修复的历史步骤")
