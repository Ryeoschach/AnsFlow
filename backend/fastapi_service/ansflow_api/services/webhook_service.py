"""
Webhook service for processing webhook events
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
import json

from ..models.database import WebhookEvent, Project, Pipeline
from ..models.schemas import (
    WebhookEventSchema,
    WebhookCreateSchema,
    WebhookEventType,
    GitHubPushEventSchema,
    GitHubPullRequestEventSchema,
    GitLabPushEventSchema,
    GitLabMergeRequestEventSchema,
    JenkinsEventSchema,
    PipelineRunCreateSchema
)
from .pipeline_service import pipeline_service
from .websocket_service import websocket_service

logger = structlog.get_logger(__name__)


class WebhookService:
    """Service for processing webhook events"""
    
    async def create_webhook_event(
        self,
        webhook_data: WebhookCreateSchema,
        session: AsyncSession
    ) -> WebhookEventSchema:
        """Create a new webhook event"""
        
        webhook_event = WebhookEvent(
            event_type=webhook_data.event_type.value,
            source=webhook_data.source,
            payload=webhook_data.payload,
            project_id=webhook_data.project_id
        )
        
        session.add(webhook_event)
        await session.commit()
        await session.refresh(webhook_event)
        
        logger.info("Webhook event created", 
                   event_id=webhook_event.id,
                   event_type=webhook_event.event_type,
                   source=webhook_event.source)
        
        return WebhookEventSchema.model_validate(webhook_event)
    
    async def process_github_webhook(
        self,
        payload: Dict[str, Any],
        event_type: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Process GitHub webhook"""
        
        logger.info("Processing GitHub webhook", event_type=event_type)
        
        try:
            if event_type == "push":
                return await self._process_github_push(payload, session)
            elif event_type == "pull_request":
                return await self._process_github_pull_request(payload, session)
            else:
                logger.warning("Unsupported GitHub event type", event_type=event_type)
                return {"status": "ignored", "reason": f"Unsupported event type: {event_type}"}
        
        except Exception as e:
            logger.error("GitHub webhook processing failed", error=str(e), event_type=event_type)
            return {"status": "error", "error": str(e)}
    
    async def _process_github_push(
        self,
        payload: Dict[str, Any],
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Process GitHub push event"""
        
        try:
            push_event = GitHubPushEventSchema(**payload)
        except Exception as e:
            logger.error("Invalid GitHub push payload", error=str(e))
            return {"status": "error", "error": "Invalid payload format"}
        
        # Find project by repository URL
        repo_url = push_event.repository.get("clone_url") or push_event.repository.get("html_url")
        project = await self._find_project_by_repo_url(repo_url, session)
        
        if not project:
            logger.warning("No project found for repository", repo_url=repo_url)
            return {"status": "ignored", "reason": "No matching project found"}
        
        # Create webhook event record
        webhook_data = WebhookCreateSchema(
            event_type=WebhookEventType.PUSH,
            source="github",
            payload=payload,
            project_id=project.id
        )
        webhook_event = await self.create_webhook_event(webhook_data, session)
        
        # Trigger pipeline if configured
        triggered_pipelines = await self._trigger_pipelines_for_push(
            project, push_event, session
        )
        
        # Send WebSocket notification
        await websocket_service.send_project_update(
            project_id=project.id,
            event="push_received",
            data={
                "ref": push_event.ref,
                "commits": len(push_event.commits),
                "pusher": push_event.pusher.get("name"),
                "triggered_pipelines": [p["id"] for p in triggered_pipelines]
            }
        )
        
        return {
            "status": "processed",
            "webhook_event_id": webhook_event.id,
            "project_id": project.id,
            "triggered_pipelines": triggered_pipelines
        }
    
    async def _process_github_pull_request(
        self,
        payload: Dict[str, Any],
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Process GitHub pull request event"""
        
        try:
            pr_event = GitHubPullRequestEventSchema(**payload)
        except Exception as e:
            logger.error("Invalid GitHub PR payload", error=str(e))
            return {"status": "error", "error": "Invalid payload format"}
        
        # Find project by repository URL
        repo_url = pr_event.repository.get("clone_url") or pr_event.repository.get("html_url")
        project = await self._find_project_by_repo_url(repo_url, session)
        
        if not project:
            logger.warning("No project found for repository", repo_url=repo_url)
            return {"status": "ignored", "reason": "No matching project found"}
        
        # Create webhook event record
        webhook_data = WebhookCreateSchema(
            event_type=WebhookEventType.PULL_REQUEST,
            source="github",
            payload=payload,
            project_id=project.id
        )
        webhook_event = await self.create_webhook_event(webhook_data, session)
        
        # Trigger pipeline for PR events if configured
        triggered_pipelines = await self._trigger_pipelines_for_pr(
            project, pr_event, session
        )
        
        # Send WebSocket notification
        await websocket_service.send_project_update(
            project_id=project.id,
            event="pull_request_received",
            data={
                "action": pr_event.action,
                "number": pr_event.number,
                "triggered_pipelines": [p["id"] for p in triggered_pipelines]
            }
        )
        
        return {
            "status": "processed",
            "webhook_event_id": webhook_event.id,
            "project_id": project.id,
            "triggered_pipelines": triggered_pipelines
        }
    
    async def process_gitlab_webhook(
        self,
        payload: Dict[str, Any],
        event_type: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Process GitLab webhook"""
        
        logger.info("Processing GitLab webhook", event_type=event_type)
        
        try:
            if event_type == "Push Hook":
                return await self._process_gitlab_push(payload, session)
            elif event_type == "Merge Request Hook":
                return await self._process_gitlab_merge_request(payload, session)
            else:
                logger.warning("Unsupported GitLab event type", event_type=event_type)
                return {"status": "ignored", "reason": f"Unsupported event type: {event_type}"}
        
        except Exception as e:
            logger.error("GitLab webhook processing failed", error=str(e), event_type=event_type)
            return {"status": "error", "error": str(e)}
    
    async def _process_gitlab_push(
        self,
        payload: Dict[str, Any],
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Process GitLab push event"""
        
        try:
            push_event = GitLabPushEventSchema(**payload)
        except Exception as e:
            logger.error("Invalid GitLab push payload", error=str(e))
            return {"status": "error", "error": "Invalid payload format"}
        
        # Find project by repository URL
        repo_url = push_event.repository.get("git_http_url") or push_event.repository.get("homepage")
        project = await self._find_project_by_repo_url(repo_url, session)
        
        if not project:
            logger.warning("No project found for repository", repo_url=repo_url)
            return {"status": "ignored", "reason": "No matching project found"}
        
        # Create webhook event record
        webhook_data = WebhookCreateSchema(
            event_type=WebhookEventType.PUSH,
            source="gitlab",
            payload=payload,
            project_id=project.id
        )
        webhook_event = await self.create_webhook_event(webhook_data, session)
        
        return {
            "status": "processed",
            "webhook_event_id": webhook_event.id,
            "project_id": project.id
        }
    
    async def process_jenkins_webhook(
        self,
        payload: Dict[str, Any],
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Process Jenkins webhook"""
        
        logger.info("Processing Jenkins webhook")
        
        try:
            jenkins_event = JenkinsEventSchema(**payload)
        except Exception as e:
            logger.error("Invalid Jenkins payload", error=str(e))
            return {"status": "error", "error": "Invalid payload format"}
        
        # Create webhook event record
        webhook_data = WebhookCreateSchema(
            event_type=WebhookEventType.BUILD_COMPLETE,
            source="jenkins",
            payload=payload
        )
        webhook_event = await self.create_webhook_event(webhook_data, session)
        
        # Send system notification
        build_status = jenkins_event.build.get("phase", "unknown")
        await websocket_service.send_system_notification(
            title="Jenkins Build Update",
            message=f"Jenkins job '{jenkins_event.name}' status: {build_status}"
        )
        
        return {
            "status": "processed",
            "webhook_event_id": webhook_event.id
        }
    
    async def _find_project_by_repo_url(
        self,
        repo_url: str,
        session: AsyncSession
    ) -> Optional[Project]:
        """Find project by repository URL"""
        
        if not repo_url:
            return None
        
        # Normalize URL for comparison
        normalized_url = repo_url.rstrip("/").lower()
        
        query = select(Project).where(
            Project.repository_url.ilike(f"%{normalized_url}%")
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _trigger_pipelines_for_push(
        self,
        project: Project,
        push_event: GitHubPushEventSchema,
        session: AsyncSession
    ) -> list:
        """Trigger pipelines for push event"""
        
        triggered_pipelines = []
        
        # Get pipelines that should be triggered on push
        query = select(Pipeline).where(
            Pipeline.project_id == project.id,
            Pipeline.status == "active"
        )
        result = await session.execute(query)
        pipelines = result.scalars().all()
        
        for pipeline in pipelines:
            # Check if pipeline should be triggered for this branch
            definition = pipeline.definition or {}
            trigger_config = definition.get("triggers", {})
            push_config = trigger_config.get("push", {})
            
            if push_config.get("enabled", False):
                # Check branch filters
                branches = push_config.get("branches", ["*"])
                ref = push_event.ref.replace("refs/heads/", "")
                
                if "*" in branches or ref in branches:
                    # Create pipeline run
                    run_data = PipelineRunCreateSchema(
                        pipeline_id=pipeline.id,
                        run_metadata={  # Updated field name
                            "trigger": "push",
                            "ref": push_event.ref,
                            "before": push_event.before,
                            "after": push_event.after,
                            "commits": push_event.commits,
                            "pusher": push_event.pusher
                        }
                    )
                    
                    # Use system user for triggered runs
                    pipeline_run = await pipeline_service.create_pipeline_run(
                        run_data, "system", session
                    )
                    
                    triggered_pipelines.append({
                        "id": pipeline_run.id,
                        "pipeline_id": pipeline.id,
                        "pipeline_name": pipeline.name
                    })
        
        return triggered_pipelines
    
    async def _trigger_pipelines_for_pr(
        self,
        project: Project,
        pr_event: GitHubPullRequestEventSchema,
        session: AsyncSession
    ) -> list:
        """Trigger pipelines for pull request event"""
        
        triggered_pipelines = []
        
        # Only trigger on specific PR actions
        if pr_event.action not in ["opened", "synchronize", "reopened"]:
            return triggered_pipelines
        
        # Get pipelines that should be triggered on PR
        query = select(Pipeline).where(
            Pipeline.project_id == project.id,
            Pipeline.status == "active"
        )
        result = await session.execute(query)
        pipelines = result.scalars().all()
        
        for pipeline in pipelines:
            # Check if pipeline should be triggered for PRs
            definition = pipeline.definition or {}
            trigger_config = definition.get("triggers", {})
            pr_config = trigger_config.get("pull_request", {})
            
            if pr_config.get("enabled", False):
                # Create pipeline run
                run_data = PipelineRunCreateSchema(
                    pipeline_id=pipeline.id,
                    run_metadata={  # Updated field name
                        "trigger": "pull_request",
                        "action": pr_event.action,
                        "number": pr_event.number,
                        "pull_request": pr_event.pull_request
                    }
                )
                
                # Use system user for triggered runs
                pipeline_run = await pipeline_service.create_pipeline_run(
                    run_data, "system", session
                )
                
                triggered_pipelines.append({
                    "id": pipeline_run.id,
                    "pipeline_id": pipeline.id,
                    "pipeline_name": pipeline.name
                })
        
        return triggered_pipelines


# Global webhook service instance
webhook_service = WebhookService()
