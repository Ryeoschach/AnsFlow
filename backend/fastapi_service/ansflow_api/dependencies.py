"""
FastAPI依赖注入模块 - AnsFlow优化版本
提供缓存服务、数据库服务等依赖
"""

from typing import AsyncGenerator
import structlog
from ..core.redis import cache_service

logger = structlog.get_logger(__name__)


async def get_cache_service():
    """获取缓存服务依赖"""
    return cache_service


async def get_database_service():
    """获取数据库服务依赖（模拟）"""
    class MockDatabaseService:
        async def health_check(self):
            return True
        
        async def get_pipelines_status(self, conditions=None, limit=50):
            # 模拟数据库查询
            return [
                {
                    "id": 1,
                    "name": "Backend CI/CD Pipeline",
                    "status": "running",
                    "last_execution_id": 123,
                    "last_execution_status": "running",
                    "last_execution_time": "2025-07-10T06:42:00Z",
                    "success_rate": 0.85,
                    "avg_duration": 300,
                    "project_id": "proj_001",
                    "project_name": "AnsFlow Backend",
                    "updated_at": "2025-07-10T06:42:41Z"
                }
            ]
        
        async def get_pipeline_by_id(self, pipeline_id):
            return {
                "id": pipeline_id,
                "name": f"Pipeline {pipeline_id}",
                "status": "completed",
                "project_id": "proj_001",
                "project_name": "Test Project",
                "updated_at": "2025-07-10T06:42:41Z"
            }
        
        async def get_pipeline_execution_stats(self, pipeline_id):
            return {
                "last_execution_id": 123,
                "last_execution_status": "completed",
                "last_execution_time": "2025-07-10T06:42:00Z",
                "success_rate": 0.85,
                "avg_duration": 300,
                "total_executions": 50
            }
        
        async def get_active_executions_count(self):
            return 3
        
        async def get_pipeline_count(self):
            return 15
        
        async def get_execution_success_rate(self):
            return 0.87
        
        async def get_execution_logs(self, execution_id, since=None):
            return [
                {
                    "timestamp": "2025-07-10T06:42:00Z",
                    "level": "INFO", 
                    "message": "Pipeline execution started"
                },
                {
                    "timestamp": "2025-07-10T06:42:05Z",
                    "level": "INFO",
                    "message": "Checking out code from repository"
                }
            ]
        
        async def get_execution_by_id(self, execution_id):
            return {
                "id": execution_id,
                "status": "running",
                "pipeline_id": 1
            }
        
        async def create_pipeline_execution(self, pipeline_id):
            return {
                "id": 999,
                "pipeline_id": pipeline_id,
                "status": "initiated"
            }
    
    return MockDatabaseService()


def get_current_user():
    """获取当前用户（模拟）"""
    return {"id": 1, "username": "test_user", "is_active": True}


async def get_current_active_user():
    """获取当前活跃用户"""
    user = get_current_user()
    if not user.get("is_active"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return user
