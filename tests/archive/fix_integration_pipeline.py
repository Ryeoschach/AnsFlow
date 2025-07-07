#!/usr/bin/env python3
"""
修复Integration Test Pipeline缺失的ansible步骤
"""

import os
import sys
import django
from django.conf import settings

# 设置 Django 环境
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
django.setup()

from pipelines.models import Pipeline
from cicd_integrations.models import AtomicStep
from django.db import models

def fix_integration_test_pipeline():
    """修复Integration Test Pipeline的ansible步骤"""
    print("🔧 修复Integration Test Pipeline")
    print("=" * 50)
    
    try:
        # 查找流水线
        pipeline = Pipeline.objects.filter(name="Integration Test Pipeline").first()
        if not pipeline:
            print("❌ 未找到Integration Test Pipeline")
            return False
        
        print(f"✅ 找到流水线: {pipeline.name} (ID: {pipeline.id})")
        
        # 显示当前步骤
        current_steps = pipeline.atomic_steps.all().order_by('order')
        print(f"📋 当前步骤 ({current_steps.count()}个):")
        for step in current_steps:
            print(f"   {step.order}. {step.name} ({step.step_type})")
        
        # 检查是否已有ansible步骤
        ansible_steps = pipeline.atomic_steps.filter(step_type='ansible')
        if ansible_steps.exists():
            print(f"✅ 已有 {ansible_steps.count()} 个ansible步骤，无需添加")
            return True
        
        # 获取admin用户
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            print("❌ 未找到admin用户，无法创建步骤")
            return False
        
        # 获取最大order值
        max_order = pipeline.atomic_steps.aggregate(models.Max('order'))['order__max'] or 0
        
        # 添加ansible步骤
        ansible_step = AtomicStep.objects.create(
            pipeline=pipeline,
            name="Ansible自动化部署",
            step_type="ansible",
            description="使用Ansible进行自动化部署和配置管理",
            parameters={
                "playbook_path": "deploy.yml",
                "inventory_path": "production.ini",
                "extra_vars": {
                    "app_version": "2.1.0",
                    "environment": "production",
                    "deploy_user": "deploy"
                },
                "vault_password_file": "/etc/ansible/vault_pass",
                "check_mode": False,
                "become": True
            },
            order=max_order + 1,
            is_active=True,
            created_by=admin_user  # 添加必需的创建者字段
        )
        
        print(f"✅ 成功添加ansible步骤:")
        print(f"   名称: {ansible_step.name}")
        print(f"   类型: {ansible_step.step_type}")
        print(f"   顺序: {ansible_step.order}")
        print(f"   参数: {ansible_step.parameters}")
        
        # 验证结果
        updated_steps = pipeline.atomic_steps.all().order_by('order')
        print(f"\n📊 更新后的步骤列表 ({updated_steps.count()}个):")
        for step in updated_steps:
            print(f"   {step.order}. {step.name} ({step.step_type})")
            if step.step_type == 'ansible':
                print(f"      📝 Ansible配置: {step.parameters}")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_more_comprehensive_steps():
    """添加更完整的测试步骤"""
    print("\n🚀 添加更完整的集成测试步骤")
    print("=" * 50)
    
    try:
        pipeline = Pipeline.objects.filter(name="Integration Test Pipeline").first()
        if not pipeline:
            return False
        
        # 获取admin用户
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            print("❌ 未找到admin用户，无法创建步骤")
            return False
        
        # 获取当前最大order
        max_order = pipeline.atomic_steps.aggregate(models.Max('order'))['order__max'] or 0
        
        # 添加更多步骤
        additional_steps = [
            {
                "name": "单元测试",
                "step_type": "test",
                "description": "运行单元测试和代码覆盖率检查",
                "parameters": {
                    "test_command": "pytest --cov=. --cov-report=xml",
                    "coverage_threshold": 80,
                    "test_results_path": "test-results.xml"
                },
                "order": max_order + 1
            },
            {
                "name": "安全扫描",
                "step_type": "security_scan",
                "description": "执行安全漏洞扫描",
                "parameters": {
                    "scanner": "bandit",
                    "scan_command": "bandit -r . -f json -o security-report.json",
                    "fail_on_high": True,
                    "report_path": "security-report.json"
                },
                "order": max_order + 2
            },
            {
                "name": "Docker镜像构建",
                "step_type": "docker_build",
                "description": "构建应用Docker镜像",
                "parameters": {
                    "dockerfile": "Dockerfile",
                    "context": ".",
                    "tag": "integration-test:latest",
                    "build_args": {
                        "APP_ENV": "testing",
                        "BUILD_DATE": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
                    }
                },
                "order": max_order + 3
            }
        ]
        
        created_steps = []
        for step_data in additional_steps:
            step = AtomicStep.objects.create(
                pipeline=pipeline,
                name=step_data["name"],
                step_type=step_data["step_type"],
                description=step_data["description"],
                parameters=step_data["parameters"],
                order=step_data["order"],
                is_active=True,
                created_by=admin_user  # 添加必需的创建者字段
            )
            created_steps.append(step)
            print(f"✅ 添加步骤: {step.name} ({step.step_type})")
        
        print(f"\n📊 总共添加了 {len(created_steps)} 个步骤")
        
        # 显示最终的完整流水线
        final_steps = pipeline.atomic_steps.all().order_by('order')
        print(f"\n🎯 完整的Integration Test Pipeline ({final_steps.count()}个步骤):")
        for step in final_steps:
            icon = {
                'fetch_code': '📥',
                'build': '🔨',
                'ansible': '🤖',
                'test': '🧪',
                'security_scan': '🛡️',
                'docker_build': '🐳'
            }.get(step.step_type, '📋')
            print(f"   {step.order}. {icon} {step.name} ({step.step_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ 添加步骤失败: {e}")
        return False

def main():
    """主函数"""
    print("🛠️ Integration Test Pipeline 修复工具")
    print("=" * 60)
    print("目标: 为流水线添加缺失的ansible步骤，确保预览与实际内容一致")
    print("=" * 60)
    
    # 修复ansible步骤
    success1 = fix_integration_test_pipeline()
    
    if success1:
        print(f"\n🤔 是否要添加更多完整的集成测试步骤? (y/n): ", end="")
        try:
            user_input = input().strip().lower()
            if user_input in ['y', 'yes']:
                success2 = add_more_comprehensive_steps()
            else:
                success2 = True
        except KeyboardInterrupt:
            print(f"\n👋 修复完成")
            success2 = True
        
        if success1 and success2:
            print(f"\n🎉 修复完成！")
            print(f"📝 现在Integration Test Pipeline包含:")
            print(f"   ✅ 代码拉取步骤")
            print(f"   ✅ 构建步骤")
            print(f"   ✅ Ansible部署步骤")
            print(f"   ✅ 其他集成测试步骤")
            print(f"\n💡 建议:")
            print(f"1. 在前端预览页面测试两种模式，确保内容一致")
            print(f"2. 验证ansible步骤在实际模式下正确显示")
            print(f"3. 测试流水线的完整执行流程")
    else:
        print(f"\n❌ 修复失败，请检查日志")

if __name__ == "__main__":
    main()
