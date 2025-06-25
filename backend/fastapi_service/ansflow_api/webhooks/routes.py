"""
Webhook receivers for external CI/CD tools
"""
import json
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog

from ..services.webhook_service import webhook_service

webhook_router = APIRouter()
logger = structlog.get_logger(__name__)


async def process_github_webhook_background(
    payload: Dict[str, Any],
    event_type: str,
    delivery_id: str
):
    """Process GitHub webhook in background"""
    try:
        from ..core.database import get_session
        async for session in get_session():
            result = await webhook_service.process_github_webhook(
                payload, event_type, session
            )
            logger.info("GitHub webhook processed", 
                       delivery_id=delivery_id,
                       result=result)
            break
    except Exception as e:
        logger.error("GitHub webhook processing failed", 
                    delivery_id=delivery_id,
                    error=str(e))


async def process_gitlab_webhook_background(
    payload: Dict[str, Any],
    event_type: str,
    delivery_id: str
):
    """Process GitLab webhook in background"""
    try:
        from ..core.database import get_session
        async for session in get_session():
            result = await webhook_service.process_gitlab_webhook(
                payload, event_type, session
            )
            logger.info("GitLab webhook processed", 
                       delivery_id=delivery_id,
                       result=result)
            break
    except Exception as e:
        logger.error("GitLab webhook processing failed", 
                    delivery_id=delivery_id,
                    error=str(e))


async def process_jenkins_webhook_background(
    payload: Dict[str, Any],
    delivery_id: str
):
    """Process Jenkins webhook in background"""
    try:
        from ..core.database import get_session
        async for session in get_session():
            result = await webhook_service.process_jenkins_webhook(
                payload, session
            )
            logger.info("Jenkins webhook processed", 
                       delivery_id=delivery_id,
                       result=result)
            break
    except Exception as e:
        logger.error("Jenkins webhook processing failed", 
                    delivery_id=delivery_id,
                    error=str(e))


@webhook_router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    GitHub webhook receiver
    """
    try:
        # Get headers
        event_type = request.headers.get("X-GitHub-Event")
        signature = request.headers.get("X-Hub-Signature-256")
        delivery_id = request.headers.get("X-GitHub-Delivery")
        
        # Get payload
        payload = await request.json()
        
        logger.info("GitHub webhook received", 
                   event_type=event_type, 
                   delivery_id=delivery_id)
        
        # Verify signature (TODO: implement signature verification)
        # if not verify_github_signature(payload, signature):
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process webhook in background
        background_tasks.add_task(
            process_github_webhook_background,
            payload,
            event_type,
            delivery_id
        )
        
        return JSONResponse(
            content={"status": "accepted", "delivery_id": delivery_id},
            status_code=202
        )
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received from GitHub")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error("GitHub webhook processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@webhook_router.post("/gitlab")
async def gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    GitLab webhook receiver
    """
    try:
        # Get headers
        event_type = request.headers.get("X-Gitlab-Event")
        token = request.headers.get("X-Gitlab-Token")
        delivery_id = request.headers.get("X-Gitlab-Event-UUID", "unknown")
        
        # Get payload
        payload = await request.json()
        
        logger.info("GitLab webhook received", 
                   event_type=event_type, 
                   delivery_id=delivery_id)
        
        # Verify token (TODO: implement token verification)
        # if not verify_gitlab_token(token):
        #     raise HTTPException(status_code=401, detail="Invalid token")
        
        # Process webhook in background
        background_tasks.add_task(
            process_gitlab_webhook_background,
            payload,
            event_type,
            delivery_id
        )
        
        return JSONResponse(
            content={"status": "accepted", "delivery_id": delivery_id},
            status_code=202
        )
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received from GitLab")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error("GitLab webhook processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@webhook_router.post("/jenkins")
async def jenkins_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Jenkins webhook receiver
    """
    try:
        # Get headers
        content_type = request.headers.get("Content-Type", "")
        delivery_id = request.headers.get("X-Jenkins-Event", "unknown")
        
        # Get payload
        if "application/json" in content_type:
            payload = await request.json()
        else:
            # Jenkins might send form data
            form_data = await request.form()
            payload = dict(form_data)
        
        logger.info("Jenkins webhook received", delivery_id=delivery_id)
        
        # Process webhook in background
        background_tasks.add_task(
            process_jenkins_webhook_background,
            payload,
            delivery_id
        )
        
        return JSONResponse(
            content={"status": "accepted", "delivery_id": delivery_id},
            status_code=202
        )
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received from Jenkins")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error("Jenkins webhook processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@webhook_router.post("/generic")
async def generic_webhook(
    request: Request,
    source: str,
    background_tasks: BackgroundTasks
):
    """
    Generic webhook receiver for custom integrations
    """
    try:
        # Get headers
        content_type = request.headers.get("Content-Type", "")
        delivery_id = request.headers.get("X-Delivery-ID", "unknown")
        
        # Get payload
        if "application/json" in content_type:
            payload = await request.json()
        else:
            form_data = await request.form()
            payload = dict(form_data)
        
        logger.info("Generic webhook received", 
                   source=source,
                   delivery_id=delivery_id)
        
        # TODO: Process generic webhook
        # For now, just log the event
        logger.info("Generic webhook payload", 
                   source=source,
                   payload_keys=list(payload.keys()) if isinstance(payload, dict) else "non-dict")
        
        return JSONResponse(
            content={"status": "accepted", "source": source, "delivery_id": delivery_id},
            status_code=202
        )
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received from generic webhook", source=source)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error("Generic webhook processing failed", source=source, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@webhook_router.get("/test")
async def test_webhook():
    """
    Test endpoint for webhook functionality
    """
    return {
        "status": "webhook service is running",
        "endpoints": [
            "/webhooks/github",
            "/webhooks/gitlab", 
            "/webhooks/jenkins",
            "/webhooks/generic?source=<source_name>"
        ]
    }
