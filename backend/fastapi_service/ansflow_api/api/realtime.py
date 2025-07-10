"""
实时API路由 - AnsFlow FastAPI优化版本
提供高性能的Pipeline状态查询、系统监控等实时API
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime, timedelta
import structlog

from ..core.redis import cache_service, async_cache
from ..dependencies import get_cache_service, get_database_service
from ..models.schemas import (
    PipelineStatusResponse,
    SystemMetricsResponse,
    ExecutionLogResponse,
    ApiResponse
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/pipelines/status", response_model=List[PipelineStatusResponse])
@async_cache(ttl=60, key_prefix="pipeline_status")  # 1分钟缓存
async def get_pipelines_status(
    project_id: Optional[int] = Query(None, description="项目ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(50, le=200, description="返回数量限制"),
    cache_service=Depends(get_cache_service),
    db_service=Depends(get_database_service)
) -> List[PipelineStatusResponse]:
    """
    获取Pipeline状态列表 - 高频访问API，1分钟缓存
    """
    try:
        # 构建查询条件
        query_conditions = {}
        if project_id:
            query_conditions['project_id'] = project_id
        if status:
            query_conditions['status'] = status
        
        # 从数据库获取Pipeline状态
        pipelines = await db_service.get_pipelines_status(
            conditions=query_conditions,
            limit=limit
        )
        
        # 转换为响应模型
        response_data = []
        for pipeline in pipelines:
            response_data.append(PipelineStatusResponse(
                id=pipeline['id'],
                name=pipeline['name'],
                status=pipeline['status'],
                last_execution_id=pipeline.get('last_execution_id'),
                last_execution_status=pipeline.get('last_execution_status'),
                last_execution_time=pipeline.get('last_execution_time'),
                success_rate=pipeline.get('success_rate', 0.0),
                avg_duration=pipeline.get('avg_duration', 0),
                project_id=pipeline['project_id'],
                project_name=pipeline.get('project_name', ''),
                updated_at=pipeline['updated_at']
            ))
        
        logger.info("Pipeline status retrieved", count=len(response_data))
        return response_data
        
    except Exception as e:
        logger.error("Error retrieving pipeline status", error=str(e))
        raise HTTPException(status_code=500, detail="获取Pipeline状态失败")


@router.get("/pipelines/{pipeline_id}/status", response_model=PipelineStatusResponse)
@async_cache(ttl=30, key_prefix="single_pipeline_status")  # 30秒缓存
async def get_pipeline_status(
    pipeline_id: int,
    cache_service=Depends(get_cache_service),
    db_service=Depends(get_database_service)
) -> PipelineStatusResponse:
    """
    获取单个Pipeline详细状态 - 30秒缓存
    """
    try:
        pipeline = await db_service.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline不存在")
        
        # 获取执行统计
        stats = await db_service.get_pipeline_execution_stats(pipeline_id)
        
        return PipelineStatusResponse(
            id=pipeline['id'],
            name=pipeline['name'],
            status=pipeline['status'],
            last_execution_id=stats.get('last_execution_id'),
            last_execution_status=stats.get('last_execution_status'),
            last_execution_time=stats.get('last_execution_time'),
            success_rate=stats.get('success_rate', 0.0),
            avg_duration=stats.get('avg_duration', 0),
            total_executions=stats.get('total_executions', 0),
            project_id=pipeline['project_id'],
            project_name=pipeline.get('project_name', ''),
            updated_at=pipeline['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving single pipeline status", pipeline_id=pipeline_id, error=str(e))
        raise HTTPException(status_code=500, detail="获取Pipeline状态失败")


@router.get("/system/metrics", response_model=SystemMetricsResponse)
@async_cache(ttl=30, key_prefix="system_metrics")  # 30秒缓存
async def get_system_metrics(
    cache_service=Depends(get_cache_service),
    db_service=Depends(get_database_service)
) -> SystemMetricsResponse:
    """
    获取系统监控指标 - 30秒缓存
    """
    try:
        # 获取各类统计数据
        stats = await asyncio.gather(
            db_service.get_active_executions_count(),
            db_service.get_pipeline_count(),
            db_service.get_execution_success_rate(),
            cache_service.get_cache_stats(),
            return_exceptions=True
        )
        
        active_executions = stats[0] if not isinstance(stats[0], Exception) else 0
        total_pipelines = stats[1] if not isinstance(stats[1], Exception) else 0
        success_rate = stats[2] if not isinstance(stats[2], Exception) else 0.0
        cache_stats = stats[3] if not isinstance(stats[3], Exception) else {}
        
        # 系统健康状况
        health_status = "healthy"
        if active_executions > 100:  # 如果活跃执行数过多
            health_status = "warning"
        if success_rate < 0.8:  # 如果成功率过低
            health_status = "critical"
        
        return SystemMetricsResponse(
            timestamp=datetime.utcnow(),
            active_executions=active_executions,
            total_pipelines=total_pipelines,
            success_rate=success_rate,
            health_status=health_status,
            cache_stats=cache_stats
        )
        
    except Exception as e:
        logger.error("Error retrieving system metrics", error=str(e))
        raise HTTPException(status_code=500, detail="获取系统指标失败")


@router.get("/executions/{execution_id}/logs/stream")
async def stream_execution_logs(
    execution_id: int,
    follow: bool = Query(False, description="实时跟踪日志"),
    db_service=Depends(get_database_service)
):
    """
    流式获取执行日志 - 支持实时跟踪
    """
    async def log_generator():
        try:
            # 获取历史日志
            logs = await db_service.get_execution_logs(execution_id)
            for log in logs:
                yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
            
            # 如果需要实时跟踪
            if follow:
                last_timestamp = logs[-1]['timestamp'] if logs else None
                
                while True:
                    # 每2秒检查新日志
                    await asyncio.sleep(2)
                    
                    new_logs = await db_service.get_execution_logs(
                        execution_id, 
                        since=last_timestamp
                    )
                    
                    for log in new_logs:
                        yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
                        last_timestamp = log['timestamp']
                    
                    # 检查执行是否完成
                    execution = await db_service.get_execution_by_id(execution_id)
                    if execution and execution['status'] in ['completed', 'failed', 'cancelled']:
                        break
                        
        except Exception as e:
            logger.error("Error streaming logs", execution_id=execution_id, error=str(e))
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        log_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.post("/cache/invalidate")
async def invalidate_cache(
    patterns: List[str] = Query(..., description="要清除的缓存模式"),
    cache_type: str = Query("api", description="缓存类型"),
    cache_service=Depends(get_cache_service)
) -> ApiResponse:
    """
    清除缓存 - 管理功能
    """
    try:
        total_deleted = 0
        for pattern in patterns:
            deleted = await cache_service.delete_pattern(pattern, cache_type)
            total_deleted += deleted
        
        logger.info("Cache invalidated", patterns=patterns, deleted=total_deleted)
        
        return ApiResponse(
            success=True,
            message=f"已清除 {total_deleted} 个缓存项",
            data={"deleted_count": total_deleted, "patterns": patterns}
        )
        
    except Exception as e:
        logger.error("Error invalidating cache", patterns=patterns, error=str(e))
        raise HTTPException(status_code=500, detail="清除缓存失败")


@router.get("/cache/stats")
async def get_cache_stats(
    cache_service=Depends(get_cache_service)
) -> Dict[str, Any]:
    """
    获取缓存统计信息 - 不缓存，实时数据
    """
    try:
        stats = await cache_service.get_cache_stats()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_stats": stats
        }
    except Exception as e:
        logger.error("Error getting cache stats", error=str(e))
        raise HTTPException(status_code=500, detail="获取缓存统计失败")


@router.post("/pipelines/{pipeline_id}/execute")
async def execute_pipeline(
    pipeline_id: int,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="强制执行，忽略状态检查"),
    cache_service=Depends(get_cache_service),
    db_service=Depends(get_database_service)
) -> ApiResponse:
    """
    执行Pipeline - 清除相关缓存
    """
    try:
        # 检查Pipeline状态
        pipeline = await db_service.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline不存在")
        
        if not force and pipeline['status'] == 'running':
            raise HTTPException(status_code=400, detail="Pipeline正在运行中")
        
        # 创建执行记录
        execution = await db_service.create_pipeline_execution(pipeline_id)
        
        # 后台任务：清除相关缓存
        background_tasks.add_task(
            invalidate_pipeline_cache,
            pipeline_id,
            cache_service
        )
        
        # 触发异步执行（这里应该调用Celery任务）
        # TODO: 集成Celery任务调用
        
        logger.info("Pipeline execution initiated", pipeline_id=pipeline_id, execution_id=execution['id'])
        
        return ApiResponse(
            success=True,
            message="Pipeline执行已启动",
            data={
                "execution_id": execution['id'],
                "pipeline_id": pipeline_id,
                "status": "initiated"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error executing pipeline", pipeline_id=pipeline_id, error=str(e))
        raise HTTPException(status_code=500, detail="执行Pipeline失败")


async def invalidate_pipeline_cache(pipeline_id: int, cache_service):
    """后台任务：清除Pipeline相关缓存"""
    try:
        patterns = [
            f"*pipeline_status*{pipeline_id}*",
            f"*single_pipeline_status*{pipeline_id}*",
            "*system_metrics*"
        ]
        
        for pattern in patterns:
            await cache_service.delete_pattern(pattern, "api")
        
        logger.info("Pipeline cache invalidated", pipeline_id=pipeline_id)
        
    except Exception as e:
        logger.error("Error invalidating pipeline cache", pipeline_id=pipeline_id, error=str(e))


@router.get("/health/detailed")
async def detailed_health_check(
    cache_service=Depends(get_cache_service),
    db_service=Depends(get_database_service)
) -> Dict[str, Any]:
    """
    详细健康检查 - 检查所有服务状态
    """
    health_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "healthy",
        "services": {}
    }
    
    # 检查数据库连接
    try:
        await db_service.health_check()
        health_data["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_data["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_data["overall_status"] = "unhealthy"
    
    # 检查Redis连接
    try:
        await cache_service.get("health_check", default="test")
        health_data["services"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_data["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_data["overall_status"] = "unhealthy"
    
    # TODO: 检查RabbitMQ连接
    # TODO: 检查Celery workers状态
    
    return health_data
