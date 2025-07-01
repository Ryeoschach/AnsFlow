# 🔗 流水线与CI/CD工具集成设计方案

## 📋 当前问题分析

### ❌ 现有架构缺陷
1. **流水线与CI/CD工具分离**：Pipeline模型与CICDTool无关联
2. **原子步骤抽象化**：无法映射到具体工具的执行步骤
3. **执行机制不明确**：不知道流水线在哪个工具上运行
4. **Jenkins作业孤立**：Jenkins Job与流水线系统无关联

## 🎯 设计目标

1. **双向关联**：流水线能够选择CI/CD工具，工具能够反映流水线状态
2. **执行映射**：原子步骤能够转换为具体工具的步骤
3. **状态同步**：工具执行状态与流水线状态实时同步
4. **模板化**：支持从现有工具作业创建流水线模板

## 🏗️ 新架构设计

### 1. 数据模型改进

#### Pipeline模型增强
```python
class Pipeline(models.Model):
    # ...existing fields...
    
    # 新增：CI/CD工具关联
    execution_tool = models.ForeignKey(
        'cicd_integrations.CICDTool', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pipelines',
        help_text="执行此流水线的CI/CD工具"
    )
    
    # 新增：工具特定配置
    tool_job_name = models.CharField(
        max_length=255, 
        blank=True,
        help_text="在CI/CD工具中对应的作业名称"
    )
    
    tool_job_config = models.JSONField(
        default=dict,
        help_text="工具特定的作业配置"
    )
    
    # 新增：执行模式
    EXECUTION_MODES = [
        ('local', 'Local Execution'),      # 本地Celery执行
        ('remote', 'Remote Tool'),         # 远程CI/CD工具执行
        ('hybrid', 'Hybrid'),              # 混合模式
    ]
    execution_mode = models.CharField(
        max_length=20, 
        choices=EXECUTION_MODES, 
        default='local'
    )
```

#### 新增：PipelineToolMapping模型
```python
class PipelineToolMapping(models.Model):
    """流水线与工具作业的映射关系"""
    
    pipeline = models.OneToOneField(
        Pipeline, 
        on_delete=models.CASCADE,
        related_name='tool_mapping'
    )
    
    tool = models.ForeignKey(
        'cicd_integrations.CICDTool',
        on_delete=models.CASCADE
    )
    
    # 工具特定标识
    external_job_id = models.CharField(
        max_length=255,
        help_text="在外部工具中的作业ID"
    )
    external_job_name = models.CharField(
        max_length=255,
        help_text="在外部工具中的作业名称"
    )
    
    # 同步配置
    auto_sync = models.BooleanField(
        default=True,
        help_text="是否自动同步状态"
    )
    
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=50, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### AtomicStep模型增强
```python
class AtomicStep(models.Model):
    # ...existing fields...
    
    # 新增：工具步骤映射
    tool_step_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="对应的工具步骤类型，如jenkins:shell, gitlab:script"
    )
    
    tool_step_config = models.JSONField(
        default=dict,
        help_text="工具特定的步骤配置"
    )
    
    # 新增：执行环境要求
    execution_environment = models.JSONField(
        default=dict,
        help_text="执行环境要求和配置"
    )
```

### 2. 服务层设计

#### PipelineToolIntegrationService
```python
class PipelineToolIntegrationService:
    """流水线与CI/CD工具集成服务"""
    
    def create_remote_job(self, pipeline: Pipeline) -> dict:
        """在远程CI/CD工具中创建作业"""
        
    def sync_pipeline_to_tool(self, pipeline: Pipeline) -> bool:
        """将流水线同步到CI/CD工具"""
        
    def import_job_as_pipeline(self, tool: CICDTool, job_name: str) -> Pipeline:
        """从CI/CD工具导入作业作为流水线"""
        
    def execute_pipeline_on_tool(self, pipeline: Pipeline, params: dict) -> str:
        """在指定工具上执行流水线"""
        
    def sync_execution_status(self, pipeline: Pipeline) -> dict:
        """同步执行状态"""
```

### 3. API接口设计

#### 流水线工具关联API
```python
# pipelines/views.py
@action(detail=True, methods=['post'])
def link_to_tool(self, request, pk=None):
    """将流水线关联到CI/CD工具"""
    
@action(detail=True, methods=['post']) 
def sync_to_tool(self, request, pk=None):
    """同步流水线到CI/CD工具"""
    
@action(detail=True, methods=['post'])
def execute_on_tool(self, request, pk=None):
    """在关联的工具上执行流水线"""
```

#### 工具作业导入API
```python
# cicd_integrations/views.py
@action(detail=True, methods=['post'])
def import_job_as_pipeline(self, request, pk=None):
    """导入工具作业为流水线"""
    
@action(detail=True, methods=['get'])
def get_importable_jobs(self, request, pk=None):
    """获取可导入的作业列表"""
```

### 4. 前端界面改进

#### 流水线编辑器增强
- 添加"执行工具"选择器
- 显示工具兼容性提示
- 支持工具特定配置

#### 工具管理页面增强
- 添加"导入作业"功能
- 显示关联的流水线数量
- 提供同步状态监控

## 🔄 实施步骤

### Phase 1: 数据模型改进 (2-3天)
1. 创建数据库迁移
2. 更新序列化器
3. 调整前端类型定义

### Phase 2: 服务层开发 (3-4天)
1. 实现PipelineToolIntegrationService
2. 创建Jenkins适配器
3. 添加状态同步机制

### Phase 3: API接口开发 (2-3天)
1. 实现流水线工具关联API
2. 实现作业导入API
3. 添加执行控制API

### Phase 4: 前端界面改进 (3-4天)
1. 更新流水线编辑器
2. 增强工具管理界面
3. 添加导入向导

### Phase 5: 测试与优化 (2-3天)
1. 端到端测试
2. 性能优化
3. 文档完善

## 💡 关键特性

1. **灵活执行模式**：
   - Local: 在AnsFlow内部执行
   - Remote: 委托给外部工具
   - Hybrid: 混合执行

2. **双向同步**：
   - AnsFlow → Tool: 推送流水线配置
   - Tool → AnsFlow: 拉取执行状态

3. **模板导入**：
   - 从Jenkins导入Jenkinsfile
   - 从GitLab CI导入.gitlab-ci.yml
   - 转换为AnsFlow原子步骤

4. **智能映射**：
   - 原子步骤 → 工具步骤类型
   - 参数转换和验证
   - 环境变量映射

## 🎯 预期效果

完成后，用户将能够：
1. ✅ 创建流水线并选择执行工具
2. ✅ 从现有Jenkins Job导入流水线
3. ✅ 实时查看工具执行状态
4. ✅ 在多个工具间切换执行
5. ✅ 享受统一的管理界面

这样，AnsFlow将真正成为一个**统一的CI/CD编排平台**，而不仅仅是原子步骤的组合工具。
