"""
API routes for high-performance endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..core.database import get_session
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
from ..auth.dependencies import get_current_active_user

api_router = APIRouter()
logger = structlog.get_logger(__name__)


@api_router.get("/pipelines", response_model=PaginatedResponseSchema)
async def list_pipelines(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),  # Use string instead of enum
    project_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_active_user)
):
    """
    List pipelines with high-performance pagination and filtering
    """
    pipelines = await pipeline_service.get_pipelines(
        project_id=project_id,
        status=status,
        skip=skip,
        limit=limit,
        session=session
    )
    
    # TODO: Implement proper pagination with total count
    return PaginatedResponseSchema(
        items=pipelines,
        total=len(pipelines),
        page=skip // limit + 1,
        per_page=limit,
        pages=(len(pipelines) + limit - 1) // limit
    )


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
