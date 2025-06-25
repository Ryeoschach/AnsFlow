"""
Pipeline service for managing pipeline operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
import structlog
from datetime import datetime

from ..models.database import Pipeline, PipelineRun, Project
from ..models.schemas import (
    PipelineSchema,
    PipelineCreateSchema,
    PipelineUpdateSchema,
    PipelineRunSchema,
    PipelineRunCreateSchema,
    PipelineStatus
)
from ..core.database import get_session
from .websocket_service import websocket_service

logger = structlog.get_logger(__name__)


class PipelineService:
    """Service for managing pipelines"""
    
    async def create_pipeline(
        self,
        pipeline_data: PipelineCreateSchema,
        created_by: str,
        session: AsyncSession
    ) -> PipelineSchema:
        """Create a new pipeline"""
        
        # Verify project exists
        project_query = select(Project).where(Project.id == pipeline_data.project_id)
        project_result = await session.execute(project_query)
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise ValueError(f"Project with ID {pipeline_data.project_id} not found")
        
        # Create pipeline
        pipeline = Pipeline(
            name=pipeline_data.name,
            project_id=pipeline_data.project_id,
            definition=pipeline_data.definition,
            created_by=created_by
        )
        
        session.add(pipeline)
        await session.commit()
        await session.refresh(pipeline)
        
        logger.info("Pipeline created", 
                   pipeline_id=pipeline.id, 
                   name=pipeline.name,
                   project_id=pipeline.project_id)
        
        return PipelineSchema.model_validate(pipeline)
    
    async def get_pipeline(
        self,
        pipeline_id: str,
        session: AsyncSession
    ) -> Optional[PipelineSchema]:
        """Get pipeline by ID"""
        
        query = select(Pipeline).where(Pipeline.id == pipeline_id)
        result = await session.execute(query)
        pipeline = result.scalar_one_or_none()
        
        if pipeline:
            return PipelineSchema.model_validate(pipeline)
        return None
    
    async def get_pipelines(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,  # Use string instead of enum
        skip: int = 0,
        limit: int = 100,
        session: AsyncSession = None
    ) -> List[PipelineSchema]:
        """Get pipelines with optional filtering"""
        
        query = select(Pipeline)
        
        conditions = []
        if project_id:
            conditions.append(Pipeline.project_id == project_id)
        if status:
            conditions.append(Pipeline.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.offset(skip).limit(limit).order_by(Pipeline.created_at.desc())
        
        result = await session.execute(query)
        pipelines = result.scalars().all()
        
        return [PipelineSchema.model_validate(pipeline) for pipeline in pipelines]
    
    async def update_pipeline(
        self,
        pipeline_id: str,
        pipeline_data: PipelineUpdateSchema,
        session: AsyncSession
    ) -> Optional[PipelineSchema]:
        """Update pipeline"""
        
        # Get existing pipeline
        query = select(Pipeline).where(Pipeline.id == pipeline_id)
        result = await session.execute(query)
        pipeline = result.scalar_one_or_none()
        
        if not pipeline:
            return None
        
        # Update fields
        update_data = pipeline_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pipeline, field, value)
        
        await session.commit()
        await session.refresh(pipeline)
        
        logger.info("Pipeline updated", 
                   pipeline_id=pipeline.id, 
                   updates=update_data)
        
        return PipelineSchema.model_validate(pipeline)
    
    async def delete_pipeline(
        self,
        pipeline_id: str,
        session: AsyncSession
    ) -> bool:
        """Delete pipeline"""
        
        query = select(Pipeline).where(Pipeline.id == pipeline_id)
        result = await session.execute(query)
        pipeline = result.scalar_one_or_none()
        
        if not pipeline:
            return False
        
        await session.delete(pipeline)
        await session.commit()
        
        logger.info("Pipeline deleted", pipeline_id=pipeline_id)
        return True
    
    async def create_pipeline_run(
        self,
        run_data: PipelineRunCreateSchema,
        triggered_by: str,
        session: AsyncSession
    ) -> PipelineRunSchema:
        """Create a new pipeline run"""
        
        # Verify pipeline exists
        pipeline_query = select(Pipeline).where(Pipeline.id == run_data.pipeline_id)
        pipeline_result = await session.execute(pipeline_query)
        pipeline = pipeline_result.scalar_one_or_none()
        
        if not pipeline:
            raise ValueError(f"Pipeline with ID {run_data.pipeline_id} not found")
        
        # Create pipeline run
        pipeline_run = PipelineRun(
            pipeline_id=run_data.pipeline_id,
            run_metadata=run_data.run_metadata,  # Updated field name
            triggered_by=triggered_by,
            status="pending"  # Use string instead of enum
        )
        
        session.add(pipeline_run)
        await session.commit()
        await session.refresh(pipeline_run)
        
        logger.info("Pipeline run created", 
                   run_id=pipeline_run.id,
                   pipeline_id=pipeline_run.pipeline_id)
        
        # Send WebSocket notification
        await websocket_service.notify_pipeline_started(
            pipeline_id=pipeline.id,
            pipeline_name=pipeline.name
        )
        
        return PipelineRunSchema.model_validate(pipeline_run)
    
    async def get_pipeline_run(
        self,
        run_id: str,
        session: AsyncSession
    ) -> Optional[PipelineRunSchema]:
        """Get pipeline run by ID"""
        
        query = select(PipelineRun).where(PipelineRun.id == run_id)
        result = await session.execute(query)
        run = result.scalar_one_or_none()
        
        if run:
            return PipelineRunSchema.model_validate(run)
        return None
    
    async def get_pipeline_runs(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,  # Use string instead of enum
        skip: int = 0,
        limit: int = 100,
        session: AsyncSession = None
    ) -> List[PipelineRunSchema]:
        """Get pipeline runs with optional filtering"""
        
        query = select(PipelineRun)
        
        conditions = []
        if pipeline_id:
            conditions.append(PipelineRun.pipeline_id == pipeline_id)
        if status:
            conditions.append(PipelineRun.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.offset(skip).limit(limit).order_by(PipelineRun.created_at.desc())
        
        result = await session.execute(query)
        runs = result.scalars().all()
        
        return [PipelineRunSchema.model_validate(run) for run in runs]
    
    async def update_pipeline_run_status(
        self,
        run_id: str,
        status: str,  # Use string instead of enum
        logs: Optional[List[str]] = None,
        progress: Optional[int] = None,
        session: AsyncSession = None
    ) -> Optional[PipelineRunSchema]:
        """Update pipeline run status"""
        
        # Get existing run with pipeline info
        query = (
            select(PipelineRun)
            .options(selectinload(PipelineRun.pipeline))
            .where(PipelineRun.id == run_id)
        )
        result = await session.execute(query)
        run = result.scalar_one_or_none()
        
        if not run:
            return None
        
        # Update status
        run.status = status
        
        # Update timestamps
        if status == "running" and not run.started_at:
            run.started_at = datetime.utcnow()
        elif status in ["success", "failed", "cancelled"]:
            run.completed_at = datetime.utcnow()
        
        # Update logs
        if logs:
            current_logs = run.logs or []
            run.logs = current_logs + logs
        
        await session.commit()
        await session.refresh(run)
        
        logger.info("Pipeline run status updated", 
                   run_id=run.id,
                   status=status.value)
        
        # Send WebSocket notifications
        if progress is not None:
            await websocket_service.notify_pipeline_progress(
                pipeline_id=run.pipeline_id,
                progress=progress,
                logs=logs
            )
        
        if status in ["success", "failed", "cancelled"]:
            await websocket_service.notify_pipeline_completed(
                pipeline_id=run.pipeline_id,
                pipeline_name=run.pipeline.name,
                status=status,
                logs=logs
            )
        
        return PipelineRunSchema.model_validate(run)
    
    async def add_pipeline_run_logs(
        self,
        run_id: str,
        logs: List[str],
        session: AsyncSession
    ) -> Optional[PipelineRunSchema]:
        """Add logs to pipeline run"""
        
        query = select(PipelineRun).where(PipelineRun.id == run_id)
        result = await session.execute(query)
        run = result.scalar_one_or_none()
        
        if not run:
            return None
        
        # Append new logs
        current_logs = run.logs or []
        run.logs = current_logs + logs
        
        await session.commit()
        await session.refresh(run)
        
        logger.info("Pipeline run logs added", 
                   run_id=run.id,
                   log_count=len(logs))
        
        # Send WebSocket notification with logs
        await websocket_service.send_pipeline_update(
            pipeline_id=run.pipeline_id,
            status=run.status,
            logs=logs
        )
        
        return PipelineRunSchema.model_validate(run)


# Global pipeline service instance
pipeline_service = PipelineService()
