#!/usr/bin/env python3
"""
测试拆分后的视图模块导入是否正确
"""
import sys
import os
sys.path.append('/Users/creed/workspace/sourceCode/AnsFlow/backend/django_service')

def test_imports():
    """测试视图模块导入"""
    try:
        print("🔍 测试视图模块拆分导入...")
        
        # 设置Django环境
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansflow.settings.development')
        import django
        django.setup()
        
        # 测试导入主views模块
        print("✅ 导入主views模块...")
        from cicd_integrations.views import (
            CICDToolViewSet, 
            PipelineExecutionViewSet, 
            AtomicStepViewSet,
            JenkinsManagementMixin
        )
        
        # 测试导入各子模块
        print("✅ 导入tools模块...")
        from cicd_integrations.views.tools import CICDToolViewSet as ToolsViewSet
        
        print("✅ 导入jenkins模块...")
        from cicd_integrations.views.jenkins import JenkinsManagementMixin as JenkinsMixin
        
        print("✅ 导入executions模块...")
        from cicd_integrations.views.executions import PipelineExecutionViewSet as ExecutionsViewSet
        
        print("✅ 导入steps模块...")
        from cicd_integrations.views.steps import AtomicStepViewSet as StepsViewSet
        
        # 验证类的继承关系
        print("🔍 验证类的继承关系...")
        print(f"CICDToolViewSet MRO: {[cls.__name__ for cls in CICDToolViewSet.__mro__]}")
        print(f"PipelineExecutionViewSet MRO: {[cls.__name__ for cls in PipelineExecutionViewSet.__mro__]}")
        print(f"AtomicStepViewSet MRO: {[cls.__name__ for cls in AtomicStepViewSet.__mro__]}")
        
        # 验证Jenkins方法存在
        print("🔍 验证Jenkins方法...")
        jenkins_methods = [method for method in dir(CICDToolViewSet) if method.startswith('jenkins_')]
        print(f"Jenkins methods: {jenkins_methods}")
        
        print("🎉 所有视图模块导入测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
