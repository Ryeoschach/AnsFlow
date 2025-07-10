"""
简化的高性能API路由 - AnsFlow优化版本
专为测试和演示优化效果而设计
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import time

router = APIRouter()
logger = logging.getLogger(__name__)

# 模拟缓存存储
_cache = {}

def simple_cache(key: str, ttl: int = 60):
    """简单的内存缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{key}:{hash(str(args) + str(kwargs))}"
            now = time.time()
            
            # 检查缓存
            if cache_key in _cache:
                cached_data, timestamp = _cache[cache_key]
                if now - timestamp < ttl:
                    logger.info(f"Cache hit for {cache_key}")
                    return {"cached": True, **cached_data}
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            _cache[cache_key] = (result, now)
            logger.info(f"Cache set for {cache_key}")
            
            return {"cached": False, **result}
        return wrapper
    return decorator


@router.get("/pipelines/status")
@simple_cache("pipeline_status", ttl=60)  # 1分钟缓存
async def get_pipelines_status(
    project_id: Optional[int] = Query(None, description="项目ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(50, le=200, description="返回数量限制")
):
    """
    获取Pipeline状态列表 - 高性能API，1分钟缓存
    """
    try:
        # 模拟数据库查询延迟
        await asyncio.sleep(0.1)  # 模拟100ms数据库查询
        
        # 模拟Pipeline状态数据
        mock_pipelines = [
            {
                "id": 1,
                "name": "主分支构建流水线",
                "status": "running",
                "last_execution_id": 123,
                "last_execution_status": "running",
                "last_execution_time": "2025-07-10T06:45:00Z",
                "success_rate": 0.95,
                "avg_duration": 180,
                "project_id": 1,
                "project_name": "AnsFlow",
                "updated_at": datetime.utcnow().isoformat()
            },
            {
                "id": 2,
                "name": "测试环境部署",
                "status": "completed",
                "last_execution_id": 122,
                "last_execution_status": "completed",
                "last_execution_time": "2025-07-10T06:30:00Z",
                "success_rate": 0.88,
                "avg_duration": 240,
                "project_id": 1,
                "project_name": "AnsFlow",
                "updated_at": datetime.utcnow().isoformat()
            },
            {
                "id": 3,
                "name": "生产环境发布",
                "status": "pending",
                "last_execution_id": 121,
                "last_execution_status": "completed",
                "last_execution_time": "2025-07-10T05:00:00Z",
                "success_rate": 0.92,
                "avg_duration": 600,
                "project_id": 2,
                "project_name": "Backend API",
                "updated_at": datetime.utcnow().isoformat()
            }
        ]
        
        # 应用过滤
        filtered_pipelines = mock_pipelines
        
        if project_id:
            filtered_pipelines = [p for p in filtered_pipelines if p["project_id"] == project_id]
        
        if status:
            filtered_pipelines = [p for p in filtered_pipelines if p["status"] == status]
        
        # 应用限制
        limited_pipelines = filtered_pipelines[:limit]
        
        logger.info(f"Pipeline status retrieved: {len(limited_pipelines)} items")
        
        return {
            "success": True,
            "data": limited_pipelines,
            "total": len(limited_pipelines),
            "query_time_ms": 100,  # 模拟查询时间
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving pipeline status: {e}")
        raise HTTPException(status_code=500, detail="获取Pipeline状态失败")


@router.get("/system/metrics")
@simple_cache("system_metrics", ttl=30)  # 30秒缓存
async def get_system_metrics():
    """
    获取系统监控指标 - 高性能API，30秒缓存
    """
    try:
        # 模拟系统指标收集延迟
        await asyncio.sleep(0.05)  # 模拟50ms指标收集
        
        import random
        
        # 模拟系统指标
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "active_executions": random.randint(5, 25),
            "total_pipelines": random.randint(15, 30),
            "success_rate": round(random.uniform(0.85, 0.98), 3),
            "avg_response_time_ms": random.randint(50, 200),
            "cpu_usage_percent": round(random.uniform(20, 80), 1),
            "memory_usage_percent": round(random.uniform(30, 70), 1),
            "queue_size": random.randint(0, 10),
            "cache_hit_rate": round(random.uniform(0.75, 0.95), 3),
            "health_status": "healthy"
        }
        
        # 健康状况判断
        if metrics["success_rate"] < 0.9:
            metrics["health_status"] = "warning"
        if metrics["cpu_usage_percent"] > 90 or metrics["memory_usage_percent"] > 90:
            metrics["health_status"] = "critical"
        
        logger.info("System metrics retrieved")
        
        return {
            "success": True,
            "data": metrics,
            "collection_time_ms": 50
        }
        
    except Exception as e:
        logger.error(f"Error retrieving system metrics: {e}")
        raise HTTPException(status_code=500, detail="获取系统指标失败")


@router.get("/pipelines/{pipeline_id}/status")
@simple_cache("single_pipeline", ttl=30)  # 30秒缓存
async def get_pipeline_status(pipeline_id: int):
    """
    获取单个Pipeline详细状态 - 30秒缓存
    """
    try:
        # 模拟数据库查询
        await asyncio.sleep(0.08)  # 模拟80ms查询
        
        if pipeline_id > 10:  # 模拟不存在的Pipeline
            raise HTTPException(status_code=404, detail="Pipeline不存在")
        
        import random
        
        # 模拟Pipeline详细数据
        pipeline_detail = {
            "id": pipeline_id,
            "name": f"Pipeline {pipeline_id}",
            "status": random.choice(["running", "completed", "failed", "pending"]),
            "description": f"这是Pipeline {pipeline_id}的详细描述",
            "created_at": "2025-07-01T00:00:00Z",
            "updated_at": datetime.utcnow().isoformat(),
            "last_execution": {
                "id": random.randint(100, 999),
                "status": random.choice(["running", "completed", "failed"]),
                "started_at": datetime.utcnow().isoformat(),
                "duration_seconds": random.randint(60, 600)
            },
            "statistics": {
                "total_executions": random.randint(50, 500),
                "success_rate": round(random.uniform(0.8, 0.98), 3),
                "avg_duration_seconds": random.randint(120, 400),
                "last_24h_executions": random.randint(5, 50)
            },
            "project": {
                "id": 1,
                "name": "AnsFlow项目"
            }
        }
        
        logger.info(f"Pipeline {pipeline_id} status retrieved")
        
        return {
            "success": True,
            "data": pipeline_detail,
            "query_time_ms": 80
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pipeline {pipeline_id} status: {e}")
        raise HTTPException(status_code=500, detail="获取Pipeline状态失败")


@router.get("/cache/stats")
async def get_cache_stats():
    """
    获取缓存统计信息 - 实时数据，不缓存
    """
    try:
        cache_stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_keys": len(_cache),
            "keys": list(_cache.keys()),
            "memory_usage_estimate": sum(len(str(data)) for data, _ in _cache.values()),
            "hit_rate": 0.85,  # 模拟命中率
            "redis_status": "connected"
        }
        
        return {
            "success": True,
            "data": cache_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="获取缓存统计失败")


@router.post("/cache/clear")
async def clear_cache():
    """
    清除所有缓存 - 管理功能
    """
    try:
        cache_count = len(_cache)
        _cache.clear()
        
        logger.info(f"Cleared {cache_count} cache entries")
        
        return {
            "success": True,
            "message": f"已清除 {cache_count} 个缓存项",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="清除缓存失败")


# 导入asyncio（如果未导入）
import asyncio
