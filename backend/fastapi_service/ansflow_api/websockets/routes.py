"""
WebSocket routes for real-time communication
"""
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer
import json
import structlog
from datetime import datetime

from ..auth.dependencies import get_current_user_ws

logger = structlog.get_logger(__name__)

websocket_router = APIRouter()
security = HTTPBearer()


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room: str, user_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Add to room
        if room not in self.active_connections:
            self.active_connections[room] = set()
        self.active_connections[room].add(websocket)
        
        # Add to user connections if authenticated
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        logger.info("WebSocket connected", room=room, user_id=user_id)
    
    def disconnect(self, websocket: WebSocket, room: str, user_id: str = None):
        """Remove a WebSocket connection"""
        # Remove from room
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]
        
        # Remove from user connections
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info("WebSocket disconnected", room=room, user_id=user_id)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error("Failed to send personal message", error=str(e))
    
    async def send_to_room(self, message: str, room: str):
        """Send a message to all connections in a room"""
        if room in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[room]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error("Failed to send message to room", room=room, error=str(e))
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[room].discard(connection)
    
    async def send_to_user(self, message: str, user_id: str):
        """Send a message to all connections of a specific user"""
        if user_id in self.user_connections:
            disconnected = set()
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error("Failed to send message to user", user_id=user_id, error=str(e))
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.user_connections[user_id].discard(connection)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all active connections"""
        for room_connections in self.active_connections.values():
            for connection in room_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error("Failed to broadcast message", error=str(e))


# Global connection manager instance
manager = ConnectionManager()


@websocket_router.websocket("/pipeline/{pipeline_id}")
async def websocket_pipeline_updates(
    websocket: WebSocket,
    pipeline_id: str,
    token: str = None
):
    """
    WebSocket endpoint for real-time pipeline updates
    """
    user = None
    user_id = None
    
    # Try to authenticate user if token is provided
    if token:
        try:
            user = await get_current_user_ws(token)
            user_id = user.id if user else None
        except Exception as e:
            logger.warning("WebSocket authentication failed", error=str(e))
    
    room = f"pipeline_{pipeline_id}"
    await manager.connect(websocket, room, user_id)
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": f"Connected to pipeline {pipeline_id}",
                "timestamp": datetime.utcnow().isoformat(),
                "authenticated": user is not None
            }),
            websocket
        )
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
                elif message_type == "subscribe":
                    # Handle subscription to specific events
                    event_types = message.get("events", [])
                    logger.info("WebSocket subscription", 
                              pipeline_id=pipeline_id, 
                              events=event_types, 
                              user_id=user_id)
                    
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscription_confirmed",
                            "events": event_types,
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
                
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received from WebSocket", data=data)
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    websocket
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room, user_id)
        logger.info("WebSocket disconnected", pipeline_id=pipeline_id, user_id=user_id)


@websocket_router.websocket("/project/{project_id}")
async def websocket_project_updates(
    websocket: WebSocket,
    project_id: str,
    token: str = None
):
    """
    WebSocket endpoint for real-time project updates
    """
    user = None
    user_id = None
    
    # Try to authenticate user if token is provided
    if token:
        try:
            user = await get_current_user_ws(token)
            user_id = user.id if user else None
        except Exception as e:
            logger.warning("WebSocket authentication failed", error=str(e))
    
    room = f"project_{project_id}"
    await manager.connect(websocket, room, user_id)
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": f"Connected to project {project_id}",
                "timestamp": datetime.utcnow().isoformat(),
                "authenticated": user is not None
            }),
            websocket
        )
        
        while True:
            data = await websocket.receive_text()
            # Handle project-specific WebSocket messages
            logger.info("Project WebSocket message received", project_id=project_id, data=data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room, user_id)
        logger.info("WebSocket disconnected", project_id=project_id, user_id=user_id)


@websocket_router.websocket("/system")
async def websocket_system_updates(
    websocket: WebSocket,
    token: str = None
):
    """
    WebSocket endpoint for system-wide updates
    """
    user = None
    user_id = None
    
    # Try to authenticate user if token is provided
    if token:
        try:
            user = await get_current_user_ws(token)
            user_id = user.id if user else None
        except Exception as e:
            logger.warning("WebSocket authentication failed", error=str(e))
    
    room = "system"
    await manager.connect(websocket, room, user_id)
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": "Connected to system updates",
                "timestamp": datetime.utcnow().isoformat(),
                "authenticated": user is not None
            }),
            websocket
        )
        
        while True:
            data = await websocket.receive_text()
            # Handle system-wide WebSocket messages
            logger.info("System WebSocket message received", data=data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room, user_id)
        logger.info("System WebSocket disconnected", user_id=user_id)


# Export the connection manager for use by other services
__all__ = ["websocket_router", "manager"]
