"""
API routes for high-performance endpoints - AnsFlow优化版本
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
import asyncio
import json
from datetime import datetime

from ..core.database import get_session
from ..core.redis import cache_service, async_cache
from ..models.schemas import (
    PipelineSchema,
    PipelineCreateSchema,
    PipelineUpdateSchema,
    PipelineRunSchema,
    PipelineRunCreateSchema,
    PipelineStatus,
    ResponseSchema,
    PaginatedResponseSchema
)
from ..services.pipeline_service import pipeline_service
from ..services.websocket_service import websocket_service

api_router = APIRouter()
logger = structlog.get_logger(__name__)


# 临时用户依赖 - 在没有完整认证系统时使用
async def get_current_active_user():
    """临时用户依赖 - 返回模拟用户"""
    return {"id": 1, "username": "test_user", "is_active": True}


@api_router.get("/pipelines/status", response_model=List[Dict[str, Any]])
@async_cache(ttl=60, key_prefix="pipeline_status_fast")  # 1分钟缓存
async def get_pipelines_status_fast(
    project_id: Optional[str] = Query(None, description="项目ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(50, le=200, description="返回数量限制"),
    session: AsyncSession = Depends(get_session)
):
    """
    高性能Pipeline状态查询 - 1分钟缓存
    专门为Dashboard等高频查询场景优化
    """
    try:
        # 模拟获取Pipeline状态数据（实际应该从数据库获取）
        pipelines_status = [
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
            },
            {
                "id": 2,
                "name": "Frontend Build Pipeline",
                "status": "completed",
                "last_execution_id": 124,
                "last_execution_status": "completed",
                "last_execution_time": "2025-07-10T06:40:00Z",
                "success_rate": 0.92,
                "avg_duration": 180,
                "project_id": "proj_002",
                "project_name": "AnsFlow Frontend",
                "updated_at": "2025-07-10T06:40:30Z"
            }
        ]
        
        # 应用过滤器
        if project_id:
            pipelines_status = [p for p in pipelines_status if p["project_id"] == project_id]
        if status:
            pipelines_status = [p for p in pipelines_status if p["status"] == status]
        
        # 应用限制
        pipelines_status = pipelines_status[:limit]
        
        logger.info("Pipeline status retrieved", count=len(pipelines_status))
        return pipelines_status
        
    except Exception as e:
        logger.error("Error retrieving pipeline status", error=str(e))
        raise HTTPException(status_code=500, detail="获取Pipeline状态失败")


@api_router.get("/system/metrics", response_model=Dict[str, Any])
@async_cache(ttl=30, key_prefix="system_metrics_fast")  # 30秒缓存
async def get_system_metrics_fast(
    session: AsyncSession = Depends(get_session)
):
    """
    高性能系统监控指标 - 30秒缓存
    提供实时系统状态概览
    """
    try:
        # 模拟系统指标数据（实际应该从数据库和监控系统获取）
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "active_executions": 3,
            "total_pipelines": 15,
            "success_rate": 0.87,
            "health_status": "healthy",
            "cache_stats": {
                "api": {
                    "hit_rate": 0.78,
                    "total_hits": 1234,
                    "total_misses": 345
                },
                "pipeline": {
                    "hit_rate": 0.82,
                    "total_hits": 567,
                    "total_misses": 123
                }
            },
            "queue_stats": {
                "high_priority": {"pending": 0, "processing": 1},
                "medium_priority": {"pending": 2, "processing": 0},
                "low_priority": {"pending": 0, "processing": 0}
            },
            "performance": {
                "avg_response_time_ms": 45,
                "cpu_usage_percent": 25.5,
                "memory_usage_percent": 42.3,
                "database_connections": 8
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error("Error retrieving system metrics", error=str(e))
        raise HTTPException(status_code=500, detail="获取系统指标失败")


@api_router.get("/executions/{execution_id}/logs/stream")
async def stream_execution_logs_fast(
    execution_id: int,
    follow: bool = Query(False, description="实时跟踪日志"),
    lines: int = Query(100, le=1000, description="返回行数"),
    session: AsyncSession = Depends(get_session)
):
    """
    流式获取执行日志 - 支持实时跟踪
    高性能日志流式传输
    """
    async def log_generator():
        try:
            # 模拟历史日志
            historical_logs = [
                {"timestamp": "2025-07-10T06:42:00Z", "level": "INFO", "message": "Pipeline execution started"},
                {"timestamp": "2025-07-10T06:42:05Z", "level": "INFO", "message": "Checking out code from repository"},
                {"timestamp": "2025-07-10T06:42:10Z", "level": "INFO", "message": "Installing dependencies"},
                {"timestamp": "2025-07-10T06:42:20Z", "level": "INFO", "message": "Running tests"},
                {"timestamp": "2025-07-10T06:42:35Z", "level": "WARNING", "message": "Some tests have warnings"},
                {"timestamp": "2025-07-10T06:42:40Z", "level": "INFO", "message": "Building application"},
            ]
            
            # 返回历史日志
            for log in historical_logs[-lines:]:
                yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
            
            # 如果需要实时跟踪
            if follow:
                last_timestamp = historical_logs[-1]['timestamp'] if historical_logs else None
                
                # 模拟实时日志生成
                for i in range(5):
                    await asyncio.sleep(2)  # 每2秒生成新日志
                    
                    new_log = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "INFO",
                        "message": f"执行进度更新 {i+1}/5"
                    }
                    
                    yield f"data: {json.dumps(new_log, ensure_ascii=False)}\n\n"
                
                # 完成日志
                final_log = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "INFO",
                    "message": "Pipeline execution completed successfully"
                }
                yield f"data: {json.dumps(final_log, ensure_ascii=False)}\n\n"
                        
        except Exception as e:
            logger.error("Error streaming logs", execution_id=execution_id, error=str(e))
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "ERROR",
                "message": f"日志流错误: {str(e)}"
            }
            yield f"data: {json.dumps(error_log, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
    )


@api_router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats_fast():
    """
    获取缓存统计信息 - 不缓存，实时数据
    监控缓存性能和命中率
    """
    try:
        # 获取Redis缓存统计
        stats = await cache_service.get_cache_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_stats": stats,
            "summary": {
                "total_caches": len(stats),
                "overall_hit_rate": sum(s.get("hit_rate", 0) for s in stats.values() if isinstance(s, dict)) / len(stats)
            }
        }
    except Exception as e:
        logger.error("Error getting cache stats", error=str(e))
        raise HTTPException(status_code=500, detail="获取缓存统计失败")


@api_router.post("/cache/invalidate")
async def invalidate_cache_fast(
    patterns: List[str] = Query(..., description="要清除的缓存模式"),
    cache_type: str = Query("api", description="缓存类型")
):
    """
    清除缓存 - 管理功能
    支持模式匹配的缓存清理
    """
    try:
        total_deleted = 0
        for pattern in patterns:
            deleted = await cache_service.delete_pattern(pattern, cache_type)
            total_deleted += deleted
        
        logger.info("Cache invalidated", patterns=patterns, deleted=total_deleted)
        
        return {
            "success": True,
            "message": f"已清除 {total_deleted} 个缓存项",
            "data": {
                "deleted_count": total_deleted,
                "patterns": patterns,
                "cache_type": cache_type
            }
        }
        
    except Exception as e:
        logger.error("Error invalidating cache", patterns=patterns, error=str(e))
        raise HTTPException(status_code=500, detail="清除缓存失败")


@api_router.get("/health/detailed")
async def detailed_health_check_fast():
    """
    详细健康检查 - 检查所有服务状态
    提供完整的系统健康状态
    """
    health_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "healthy",
        "services": {}
    }
    
    # 检查Redis连接
    try:
        await cache_service.get("health_check", default="test")
        health_data["services"]["redis"] = {"status": "healthy", "response_time_ms": 2.5}
    except Exception as e:
        health_data["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_data["overall_status"] = "unhealthy"
    
    # 模拟检查数据库连接
    health_data["services"]["database"] = {"status": "healthy", "response_time_ms": 15.2}
    
    # 模拟检查RabbitMQ连接
    health_data["services"]["rabbitmq"] = {"status": "healthy", "queues_count": 3}
    
    # 检查Celery workers（模拟）
    health_data["services"]["celery"] = {
        "status": "healthy", 
        "active_workers": 1,
        "pending_tasks": 2
    }
    
    return health_data


@api_router.post("/pipelines", response_model=PipelineSchema)
async def create_pipeline(
    pipeline_data: PipelineCreateSchema,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    Create a new pipeline
    """
    try:
        pipeline = await pipeline_service.create_pipeline(
            pipeline_data, current_user.id, session
        )
        return pipeline
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/pipelines/{pipeline_id}", response_model=PipelineSchema)
async def get_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    Get pipeline by ID
    """
    pipeline = await pipeline_service.get_pipeline(pipeline_id, session)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@api_router.put("/pipelines/{pipeline_id}", response_model=PipelineSchema)
async def update_pipeline(
    pipeline_id: str,
    pipeline_data: PipelineUpdateSchema,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    Update pipeline
    """
    pipeline = await pipeline_service.update_pipeline(
        pipeline_id, pipeline_data, session
    )
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@api_router.delete("/pipelines/{pipeline_id}", response_model=ResponseSchema)
async def delete_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    Delete pipeline
    """
    success = await pipeline_service.delete_pipeline(pipeline_id, session)
    if not success:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return ResponseSchema(message="Pipeline deleted successfully")


@api_router.get("/pipelines/{pipeline_id}/status")
async def get_pipeline_status(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    Get pipeline status with real-time information
    """
    pipeline = await pipeline_service.get_pipeline(pipeline_id, session)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Get latest runs
    runs = await pipeline_service.get_pipeline_runs(
        pipeline_id=pipeline_id,
        limit=5,
        session=session
    )
    
    return {
        "pipeline_id": pipeline_id,
        "status": pipeline.status,
        "latest_runs": runs
    }


# Pipeline run endpoints
@api_router.post("/pipelines/{pipeline_id}/runs", response_model=PipelineRunSchema)
async def create_pipeline_run(
    pipeline_id: str,
    run_data: PipelineRunCreateSchema,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    Create and start a new pipeline run
    """
    try:
        # Ensure pipeline_id matches
        run_data.pipeline_id = pipeline_id
        
        pipeline_run = await pipeline_service.create_pipeline_run(
            run_data, current_user.id, session
        )
        
        # Start pipeline execution in background
        background_tasks.add_task(
            execute_pipeline_run,
            pipeline_run.id
        )
        
        return pipeline_run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/pipeline-runs/{run_id}", response_model=PipelineRunSchema)
async def get_pipeline_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    Get pipeline run by ID
    """
    run = await pipeline_service.get_pipeline_run(run_id, session)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return run


@api_router.get("/pipeline-runs", response_model=PaginatedResponseSchema)
async def list_pipeline_runs(
    pipeline_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),  # Use string instead of enum
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    List pipeline runs with filtering
    """
    runs = await pipeline_service.get_pipeline_runs(
        pipeline_id=pipeline_id,
        status=status,
        skip=skip,
        limit=limit,
        session=session
    )
    
    # TODO: Implement proper pagination with total count
    return PaginatedResponseSchema(
        items=runs,
        total=len(runs),
        page=skip // limit + 1,
        per_page=limit,
        pages=(len(runs) + limit - 1) // limit
    )


@api_router.post("/pipeline-runs/{run_id}/status", response_model=PipelineRunSchema)
async def update_pipeline_run_status(
    run_id: str,
    status: str,  # Use string instead of enum
    logs: Optional[List[str]] = None,
    progress: Optional[int] = Query(None, ge=0, le=100),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    Update pipeline run status (for external integrations)
    """
    # Validate status
    valid_statuses = ["pending", "running", "success", "failed", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    run = await pipeline_service.update_pipeline_run_status(
        run_id, status, logs, progress, session
    )
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return run


@api_router.post("/pipeline-runs/{run_id}/logs", response_model=PipelineRunSchema)
async def add_pipeline_run_logs(
    run_id: str,
    logs: List[str],
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    Add logs to pipeline run
    """
    run = await pipeline_service.add_pipeline_run_logs(run_id, logs, session)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return run


# System endpoints
@api_router.post("/system/notify")
async def send_system_notification(
    title: str,
    message: str,
    level: str = "info",
    user_id: Optional[str] = None,
    current_user = Depends(get_current_active_user)
):
    """
    Send system notification via WebSocket
    """
    valid_levels = ["info", "warning", "error", "success"]
    if level not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Invalid level. Must be one of: {valid_levels}")
    
    await websocket_service.send_system_notification(
        title=title,
        message=message,
        level=level,
        user_id=user_id
    )
    
    return {"status": "notification sent"}


# Health and monitoring endpoints
@api_router.get("/status")
async def api_status():
    """
    Get API status
    """
    return {
        "status": "healthy",
        "service": "AnsFlow FastAPI Service",
        "version": "1.0.0"
    }


# Background task functions
async def execute_pipeline_run(run_id: str):
    """Execute pipeline run in background"""
    try:
        from ..core.database import get_session
        
        async for session in get_session():
            # Simulate pipeline execution
            import asyncio
            
            # Update to running
            await pipeline_service.update_pipeline_run_status(
                run_id, "running", session=session
            )
            
            # Simulate some work with progress updates
            for i in range(0, 101, 20):
                await asyncio.sleep(2)  # Simulate work
                await pipeline_service.update_pipeline_run_status(
                    run_id, 
                    "running", 
                    logs=[f"Step {i//20 + 1}: Progress {i}%"],
                    progress=i,
                    session=session
                )
            
            # Complete
            await pipeline_service.update_pipeline_run_status(
                run_id, 
                "success",
                logs=["Pipeline execution completed successfully"],
                progress=100,
                session=session
            )
            break
            
    except Exception as e:
        logger.error("Pipeline execution failed", run_id=run_id, error=str(e))
        
        # Mark as failed
        async for session in get_session():
            await pipeline_service.update_pipeline_run_status(
                run_id,
                "failed",
                logs=[f"Pipeline execution failed: {str(e)}"],
                session=session
            )
            break
