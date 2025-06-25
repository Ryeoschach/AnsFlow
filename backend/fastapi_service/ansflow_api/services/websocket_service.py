"""
WebSocket service for managing real-time communications
"""
from typing import Dict, Any, Optional
import json
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)

# Import manager lazily to avoid circular imports
_manager = None

def get_manager():
    """Get the connection manager instance"""
    global _manager
    if _manager is None:
        from ..websockets.routes import manager
        _manager = manager
    return _manager


class WebSocketService:
    """Service for managing WebSocket communications"""
    
    def __init__(self):
        self._manager = None
    
    @property
    def connection_manager(self):
        """Get connection manager instance"""
        if self._manager is None:
            self._manager = get_manager()
        return self._manager
    
    async def send_pipeline_update(
        self,
        pipeline_id: str,
        status: str,
        progress: Optional[int] = None,
        logs: Optional[list] = None
    ):
        """Send pipeline update to all subscribers"""
        message = {
            "type": "pipeline_update",
            "pipeline_id": pipeline_id,
            "status": status,
            "progress": progress,
            "logs": logs or [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        room = f"pipeline_{pipeline_id}"
        await self.connection_manager.send_to_room(
            json.dumps(message),
            room
        )
        
        logger.info("Pipeline update sent", 
                   pipeline_id=pipeline_id, 
                   status=status, 
                   room=room)
    
    async def send_project_update(
        self,
        project_id: str,
        event: str,
        data: Dict[str, Any] = None
    ):
        """Send project update to all subscribers"""
        message = {
            "type": "project_update",
            "project_id": project_id,
            "event": event,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        room = f"project_{project_id}"
        await self.connection_manager.send_to_room(
            json.dumps(message),
            room
        )
        
        logger.info("Project update sent", 
                   project_id=project_id, 
                   event=event, 
                   room=room)
    
    async def send_system_notification(
        self,
        title: str,
        message: str,
        level: str = "info",
        user_id: Optional[str] = None
    ):
        """Send system notification"""
        notification = {
            "type": "system_notification",
            "level": level,
            "title": title,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id:
            # Send to specific user
            await self.connection_manager.send_to_user(
                json.dumps(notification),
                user_id
            )
            logger.info("System notification sent to user", 
                       user_id=user_id, 
                       title=title)
        else:
            # Broadcast to all users
            await self.connection_manager.broadcast(
                json.dumps(notification)
            )
            logger.info("System notification broadcast", title=title)
    
    async def send_custom_message(
        self,
        room: str,
        message_type: str,
        data: Dict[str, Any]
    ):
        """Send custom message to a room"""
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_to_room(
            json.dumps(message),
            room
        )
        
        logger.info("Custom message sent", 
                   room=room, 
                   message_type=message_type)
    
    async def notify_pipeline_started(self, pipeline_id: str, pipeline_name: str):
        """Notify that a pipeline has started"""
        await self.send_pipeline_update(
            pipeline_id=pipeline_id,
            status="running",
            progress=0
        )
        
        await self.send_system_notification(
            title="Pipeline Started",
            message=f"Pipeline '{pipeline_name}' has started execution",
            level="info"
        )
    
    async def notify_pipeline_completed(
        self, 
        pipeline_id: str, 
        pipeline_name: str, 
        status: str,
        logs: Optional[list] = None
    ):
        """Notify that a pipeline has completed"""
        await self.send_pipeline_update(
            pipeline_id=pipeline_id,
            status=status,
            progress=100 if status == "success" else None,
            logs=logs
        )
        
        level = "success" if status == "success" else "error"
        message = f"Pipeline '{pipeline_name}' completed with status: {status}"
        
        await self.send_system_notification(
            title="Pipeline Completed",
            message=message,
            level=level
        )
    
    async def notify_pipeline_progress(
        self, 
        pipeline_id: str, 
        progress: int, 
        logs: Optional[list] = None
    ):
        """Notify pipeline progress update"""
        await self.send_pipeline_update(
            pipeline_id=pipeline_id,
            status="running",
            progress=progress,
            logs=logs
        )
    
    async def notify_project_created(self, project_id: str, project_name: str):
        """Notify that a project has been created"""
        await self.send_project_update(
            project_id=project_id,
            event="created",
            data={"name": project_name}
        )
        
        await self.send_system_notification(
            title="Project Created",
            message=f"New project '{project_name}' has been created",
            level="info"
        )
    
    async def notify_project_updated(self, project_id: str, project_name: str, changes: Dict[str, Any]):
        """Notify that a project has been updated"""
        await self.send_project_update(
            project_id=project_id,
            event="updated",
            data={"name": project_name, "changes": changes}
        )
    
    async def notify_project_deleted(self, project_id: str, project_name: str):
        """Notify that a project has been deleted"""
        await self.send_project_update(
            project_id=project_id,
            event="deleted",
            data={"name": project_name}
        )
        
        await self.send_system_notification(
            title="Project Deleted",
            message=f"Project '{project_name}' has been deleted",
            level="warning"
        )


# Global WebSocket service instance
websocket_service = WebSocketService()
