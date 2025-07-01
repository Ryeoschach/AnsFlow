# AnsFlow Jenkins流水线集成修复指南

## 问题总结
通过今天的调试发现，Jenkins流水线的"No flow definition"错误的根本原因是：

1. **缺少pipeline-model-definition插件** - 声明式Pipeline语法需要此插件
2. **PipelineViewSet缺失** - pipelines/views.py是空的，缺少run方法
3. **Celery任务导入错误** - 使用了错误的任务路径
4. **Django ORM异步调用问题** - 在异步上下文中需要sync_to_async

## 解决方案

### 1. Jenkins适配器修复（已完成）
文件：`backend/django_service/cicd_integrations/adapters/jenkins.py`

关键修改：
- 改用**脚本式Pipeline语法**而不是声明式语法（兼容性更好）
- 修改`create_pipeline_file`方法生成脚本式Jenkinsfile
- 添加`_convert_atomic_steps_to_scripted_jenkinsfile`方法
- 添加`_generate_scripted_stage_script`方法
- 修复shell命令转义问题（使用双引号）

### 2. PipelineViewSet实现
文件：`backend/django_service/pipelines/views.py`

需要创建完整的ViewSet：

```python
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.utils import timezone
import logging

from .models import Pipeline, PipelineRun
from .serializers import PipelineSerializer, PipelineRunSerializer
from cicd_integrations.models import PipelineExecution, CICDTool
from cicd_integrations.services import execute_pipeline_task

logger = logging.getLogger(__name__)

class PipelineViewSet(viewsets.ModelViewSet):
    """流水线管理ViewSet"""
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Run pipeline",
        description="Trigger pipeline execution",
        request=None,
        responses={201: PipelineRunSerializer}
    )
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """运行流水线"""
        try:
            pipeline = self.get_object()
            logger.info(f"触发流水线执行: ID={pipeline.id}, 名称={pipeline.name}")
            
            # 检查流水线是否激活
            if not pipeline.is_active:
                return Response(
                    {'error': 'Pipeline is not active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 检查是否有CI/CD工具
            if pipeline.execution_mode == 'remote' and not pipeline.execution_tool:
                return Response(
                    {'error': 'No CI/CD tool configured for remote execution'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 创建流水线执行记录
            execution = PipelineExecution.objects.create(
                pipeline=pipeline,
                cicd_tool=pipeline.execution_tool,
                triggered_by=request.user,
                trigger_type='manual',
                trigger_data={
                    'source': 'api',
                    'user_id': request.user.id,
                    'timestamp': str(timezone.now())
                },
                status='pending'
            )
            
            logger.info(f"创建流水线执行记录: ID={execution.id}")
            
            # 使用services.py中的Celery任务
            task_result = execute_pipeline_task.delay(execution.id)
            execution.task_id = task_result.id
            execution.save()
            
            logger.info(f"Celery任务已启动: task_id={task_result.id}")
            
            # 返回执行信息
            from cicd_integrations.serializers import PipelineExecutionSerializer
            serializer = PipelineExecutionSerializer(execution)
            
            return Response({
                'message': f'Pipeline execution started successfully',
                'execution': serializer.data
            }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"流水线执行请求处理失败: {e}")
            return Response(
                {'error': f'Pipeline execution failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PipelineToolMappingViewSet(viewsets.ModelViewSet):
    """流水线工具映射ViewSet - 占位符"""
    queryset = Pipeline.objects.none()  # 暂时为空
    permission_classes = [permissions.IsAuthenticated]

def pipeline_health(request):
    """流水线健康检查"""
    from django.http import JsonResponse
    return JsonResponse({
        'status': 'healthy',
        'service': 'Pipeline Service',
        'pipelines_count': Pipeline.objects.count()
    })
```

### 3. URL路由修复
文件：`backend/django_service/pipelines/urls.py`

修改router注册：

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pipelines', views.PipelineViewSet)
router.register(r'pipeline-mappings', views.PipelineToolMappingViewSet, basename='pipeline-mapping')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.pipeline_health, name='pipeline-health'),
]
```

### 4. Celery任务修复
**重要：删除错误的tasks.py文件**
文件：`backend/django_service/cicd_integrations/tasks.py`（删除此文件）

使用services.py中已有的正确任务：`cicd_integrations.services.execute_pipeline_task`

### 5. Jenkins脚本式Pipeline语法示例

生成的Jenkinsfile格式：

```groovy
node {
    try {
        timeout(time: 60, unit: 'MINUTES') {
            
            echo "=== AnsFlow 流水线开始执行 ==="
            echo "流水线名称: Integration Test Pipeline"
            echo "超时时间: 60 分钟"
            
            // 设置环境变量
            env.ANSFLOW_EXECUTION_ID = '52'
            env.ANSFLOW_PIPELINE_ID = '12'
            env.ANSFLOW_TRIGGER_TYPE = 'manual'
            
            // 执行流水线步骤            
            stage('Build Step') {
                echo "执行阶段: Build Step"
                echo "执行Shell命令: sleep 10"
                sh "sleep 10"
            }
            
            stage('Test Step') {
                echo "执行阶段: Test Step"
                echo "执行Shell命令: echo 'hello world'"
                sh "echo 'hello world'"
            }
            
            echo "=== AnsFlow 流水线执行完成 ==="
        }
    } catch (Exception e) {
        echo "=== 流水线执行失败 ==="
        echo "错误信息: ${e.getMessage()}"
        currentBuild.result = 'FAILURE'
        throw e
    } finally {
        echo "=== 清理工作空间 ==="
        cleanWs()
    }
}
```

## 测试验证

### 1. 验证脚本式Pipeline
使用jenkins_simple_test.py验证：

```python
import asyncio
import httpx

async def test_simple_scripted_pipeline():
    auth = ("ansflow", "111f1d7d113b3a197723e852d94cfc61ff")
    
    simple_jenkinsfile = """node {
    echo 'Hello from scripted pipeline'
    stage('Test') {
        sh 'echo "Test stage"'
    }
}"""
    
    job_config = f'''<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions/>
  <description>Simple scripted pipeline test</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.92">
    <script>{simple_jenkinsfile}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>'''
    
    async with httpx.AsyncClient(verify=False) as client:
        # 创建作业
        response = await client.post(
            "http://localhost:8080/createItem?name=scripted-test",
            auth=auth,
            headers={'Content-Type': 'application/xml'},
            content=job_config
        )
        print(f"创建作业: {response.status_code}")
        
        # 触发构建
        if response.status_code == 200:
            build_response = await client.post(
                "http://localhost:8080/job/scripted-test/build",
                auth=auth
            )
            print(f"触发构建: {build_response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_simple_scripted_pipeline())
```

### 2. API测试
```bash
# 获取JWT token
curl -X POST "http://localhost:8000/api/v1/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 测试流水线执行
curl -X POST "http://localhost:8000/api/v1/pipelines/pipelines/12/run/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"

# 检查执行状态
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/cicd/executions/<execution_id>/"
```

## 关键要点

1. **脚本式Pipeline兼容性更好** - 不需要额外插件
2. **正确的Celery任务路径** - 使用services.py中的任务
3. **异步Django ORM** - 在async上下文中使用sync_to_async
4. **Shell命令转义** - 使用双引号避免嵌套问题
5. **完整的ViewSet实现** - 包含run方法的PipelineViewSet

## 回滚后操作步骤

1. 检查pipelines/views.py是否为空，如果是则按照指南重新创建
2. 检查cicd_integrations/tasks.py是否存在，如果存在则删除
3. 验证jenkins.py中的脚本式Pipeline方法是否存在
4. 测试简单的脚本式Pipeline是否能在Jenkins中运行
5. 测试完整的API流程

## 成功标志

- Jenkins中脚本式Pipeline能正常运行（无"No flow definition"错误）
- API调用能成功创建执行记录并启动Celery任务
- Celery任务能正确调用UnifiedCICDEngine
- 端到端流水线执行成功完成
