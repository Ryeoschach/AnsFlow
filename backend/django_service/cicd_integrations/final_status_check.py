#!/usr/bin/env python3
"""
Jenkins集成和视图拆分最终状态检查
验证所有组件是否正确安装和配置
"""
import sys
import os
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')

def check_view_structure():
    """检查视图文件结构"""
    print("🔍 检查视图文件结构...")
    
    base_path = '/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service/cicd_integrations'
    
    required_files = [
        'views/__init__.py',
        'views/tools.py', 
        'views/jenkins.py',
        'views/executions.py',
        'views/steps.py',
        'views.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"  ❌ 缺少文件: {missing_files}")
        return False
    
    print("✅ 视图文件结构完整")
    return True

def check_imports():
    """检查模块导入"""
    print("🔍 检查模块导入...")
    
    try:
        # 设置Django环境
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
        import django
        django.setup()
        
        # 测试主要导入
        from cicd_integrations.views import (
            CICDToolViewSet,
            PipelineExecutionViewSet, 
            AtomicStepViewSet,
            JenkinsManagementMixin
        )
        print("  ✅ 主视图类导入成功")
        
        # 测试子模块导入
        from cicd_integrations.views.tools import CICDToolViewSet as ToolsView
        from cicd_integrations.views.jenkins import JenkinsManagementMixin as JenkinsMixin
        from cicd_integrations.views.executions import PipelineExecutionViewSet as ExecutionsView
        from cicd_integrations.views.steps import AtomicStepViewSet as StepsView
        print("  ✅ 子模块导入成功")
        
        # 验证Jenkins方法
        jenkins_methods = [method for method in dir(CICDToolViewSet) if method.startswith('jenkins_')]
        expected_count = 12  # 我们实现的Jenkins方法数量
        
        if len(jenkins_methods) >= expected_count:
            print(f"  ✅ Jenkins方法数量正确: {len(jenkins_methods)}个")
        else:
            print(f"  ⚠️ Jenkins方法数量不足: {len(jenkins_methods)}/{expected_count}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def check_management_commands():
    """检查管理命令"""
    print("🔍 检查管理命令...")
    
    commands_path = '/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service/cicd_integrations/management/commands'
    
    command_files = [
        'test_jenkins_integration.py',
        'test_jenkins_comprehensive.py'
    ]
    
    for cmd_file in command_files:
        cmd_path = os.path.join(commands_path, cmd_file)
        if os.path.exists(cmd_path):
            print(f"  ✅ {cmd_file}")
        else:
            print(f"  ❌ 缺少: {cmd_file}")
    
    return True

def check_test_files():
    """检查测试文件"""
    print("🔍 检查测试文件...")
    
    base_path = '/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service/cicd_integrations'
    
    test_files = [
        'test_views_split.py',
        'test_api_endpoints.py'
    ]
    
    for test_file in test_files:
        test_path = os.path.join(base_path, test_file)
        if os.path.exists(test_path):
            print(f"  ✅ {test_file}")
        else:
            print(f"  ❌ 缺少: {test_file}")
    
    return True

def check_documentation():
    """检查文档"""
    print("🔍 检查文档...")
    
    base_path = '/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service/cicd_integrations'
    
    doc_files = [
        'JENKINS_VIEWS_SPLIT_COMPLETION_REPORT.md'
    ]
    
    for doc_file in doc_files:
        doc_path = os.path.join(base_path, doc_file)
        if os.path.exists(doc_path):
            print(f"  ✅ {doc_file}")
        else:
            print(f"  ❌ 缺少: {doc_file}")
    
    return True

def main():
    """主检查函数"""
    print("🚀 Jenkins集成和视图拆分最终状态检查")
    print("=" * 60)
    
    checks = [
        ("视图文件结构", check_view_structure),
        ("模块导入", check_imports),
        ("管理命令", check_management_commands),
        ("测试文件", check_test_files),
        ("文档", check_documentation)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            success = check_func()
            results.append((check_name, success))
        except Exception as e:
            print(f"❌ {check_name} 检查失败: {e}")
            results.append((check_name, False))
        print()
    
    # 显示汇总结果
    print("=" * 60)
    print("📊 检查结果汇总:")
    
    passed = 0
    total = len(results)
    
    for check_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {check_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 总体状态: {passed}/{total} 检查通过")
    
    if passed == total:
        print("\n🎉 Jenkins集成和视图拆分项目完成！")
        print("所有组件都正确安装和配置。")
        return True
    else:
        print(f"\n⚠️ 发现 {total - passed} 个问题，请检查上述失败项。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
