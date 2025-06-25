"""
CI/CD 集成 API 视图

该文件现在作为拆分后的视图模块的聚合导入点。
原来的大型views.py文件已被拆分为以下模块以提高可维护性：

- views/tools.py: CI/CD工具管理视图
- views/jenkins.py: Jenkins特定功能视图  
- views/executions.py: 流水线执行管理视图
- views/steps.py: 原子步骤管理视图

这种拆分方式具有以下优势：
1. 代码更易维护和理解
2. 功能模块更清晰
3. 减少了单个文件的复杂度
4. 便于团队协作开发
5. 更好的代码复用性
"""

# 从拆分后的模块导入所有视图类
from .views.tools import CICDToolViewSet
from .views.executions import PipelineExecutionViewSet  
from .views.steps import AtomicStepViewSet
from .views.jenkins import JenkinsManagementMixin

# 导出所有视图类供URL配置使用
__all__ = [
    'CICDToolViewSet',
    'PipelineExecutionViewSet', 
    'AtomicStepViewSet',
    'JenkinsManagementMixin',
]
