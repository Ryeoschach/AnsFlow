"""
WebSocket routes for real-time communication
"""
import asyncio
import json
from typing import Dict, Set
from datetime import datetime, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer
import structlog

from ..auth.dependencies import get_current_user_ws
from ..monitoring import track_websocket_connection, track_websocket_message
from ..services.django_db import django_db_service

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
        
        # Track WebSocket connection in Prometheus
        track_websocket_connection(room, "connected", 1)
        
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
        
        # Track WebSocket disconnection in Prometheus
        track_websocket_connection(room, "connected", -1)
        
        logger.info("WebSocket disconnected", room=room, user_id=user_id)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            # Check if WebSocket is still connected before sending
            if hasattr(websocket, 'client_state') and hasattr(websocket.client_state, 'name'):
                if websocket.client_state.name != 'CONNECTED':
                    logger.warning("Attempted to send message to disconnected WebSocket", 
                                 state=websocket.client_state.name)
                    return False
            
            await websocket.send_text(message)
            return True
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected during message send")
            self._cleanup_disconnected_websocket(websocket)
            return False
        except RuntimeError as e:
            if "WebSocket is disconnected" in str(e) or "close message has been sent" in str(e):
                logger.info("WebSocket connection closed during message send", error=str(e))
                self._cleanup_disconnected_websocket(websocket)
                return False
            else:
                logger.error("Runtime error sending personal message", error=str(e))
                return False
        except Exception as e:
            logger.error("Failed to send personal message", error=str(e), error_type=type(e).__name__)
            self._cleanup_disconnected_websocket(websocket)
            return False
    
    def _cleanup_disconnected_websocket(self, websocket: WebSocket):
        """Clean up a disconnected WebSocket from all connection sets"""
        # Remove from room connections
        for room in list(self.active_connections.keys()):
            if websocket in self.active_connections[room]:
                self.active_connections[room].discard(websocket)
                if not self.active_connections[room]:
                    del self.active_connections[room]
        
        # Remove from user connections
        for user_id in list(self.user_connections.keys()):
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
    
    async def send_to_room(self, message: str, room: str):
        """Send a message to all connections in a room"""
        if room in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[room].copy():  # Use copy to avoid modification during iteration
                success = await self.send_personal_message(message, connection)
                if not success:
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[room].discard(connection)
                
            # Clean up empty room
            if not self.active_connections[room]:
                del self.active_connections[room]
    
    async def send_to_user(self, message: str, user_id: str):
        """Send a message to all connections of a specific user"""
        if user_id in self.user_connections:
            disconnected = set()
            for connection in self.user_connections[user_id].copy():  # Use copy to avoid modification during iteration
                success = await self.send_personal_message(message, connection)
                if not success:
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.user_connections[user_id].discard(connection)
                
            # Clean up empty user connection set
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
    
    async def broadcast(self, message: str):
        """Broadcast a message to all active connections"""
        disconnected = set()
        for room_connections in self.active_connections.values():
            for connection in room_connections.copy():  # Use copy to avoid modification during iteration
                success = await self.send_personal_message(message, connection)
                if not success:
                    disconnected.add(connection)
        
        # Clean up disconnected connections from all rooms
        for connection in disconnected:
            self._cleanup_disconnected_websocket(connection)


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
        success = await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": f"Connected to pipeline {pipeline_id}",
                "timestamp": datetime.utcnow().isoformat(),
                "authenticated": user is not None
            }),
            websocket
        )
        
        if not success:
            logger.error("Failed to send initial connection message", pipeline_id=pipeline_id)
            return
        
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


@websocket_router.websocket("/monitor")
async def websocket_global_monitor(
    websocket: WebSocket,
    token: str = None
):
    """
    WebSocket endpoint for global system monitoring
    替代 Django Channels 的全局监控 WebSocket
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
    
    room = "global_monitor"
    await manager.connect(websocket, room, user_id)
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": "Connected to global monitoring",
                "timestamp": datetime.utcnow().isoformat(),
                "authenticated": user is not None,
                "service": "FastAPI WebSocket Service"
            }),
            websocket
        )
        
        # Send initial system status
        await manager.send_personal_message(
            json.dumps({
                "type": "system_status",
                "data": {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_connections": len(manager.active_connections.get(room, set())),
                    "service": "ansflow-fastapi"
                }
            }),
            websocket
        )
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                logger.info("Received WebSocket message", message=message, user_id=user_id)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific events
                    events = message.get("events", [])
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "events": events,
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
                
            except json.JSONDecodeError:
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
        logger.info("WebSocket disconnected", room=room, user_id=user_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), room=room, user_id=user_id)
        manager.disconnect(websocket, room, user_id)


@websocket_router.websocket("/execution/{execution_id}")
async def websocket_execution_updates(
    websocket: WebSocket,
    execution_id: str,
    token: str = None
):
    """
    WebSocket endpoint for real-time execution updates
    替代 Django Channels 的 execution WebSocket
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
    
    room = f"execution_{execution_id}"
    await manager.connect(websocket, room, user_id)
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": f"Connected to execution {execution_id}",
                "timestamp": datetime.utcnow().isoformat(),
                "authenticated": user is not None,
                "service": "FastAPI WebSocket Service",
                "execution_id": execution_id
            }),
            websocket
        )
        
        # Send initial execution status with steps
        execution_data = await get_execution_with_steps(int(execution_id))
        if execution_data:
            await manager.send_personal_message(
                json.dumps({
                    "type": "execution_status",
                    "data": {
                        "execution_id": int(execution_id),
                        "status": execution_data.get("status", "pending"),
                        "pipeline_name": execution_data.get("pipeline_name"),
                        "steps": execution_data.get("steps", []),
                        "total_steps": len(execution_data.get("steps", [])),
                        "completed_steps": sum(1 for s in execution_data.get("steps", []) if s.get("status") in ["success", "failed"]),
                        "current_step": next((s for s in execution_data.get("steps", []) if s.get("status") == "running"), None),
                        "timestamp": datetime.utcnow().isoformat(),
                        "service": "ansflow-fastapi"
                    }
                }),
                websocket
            )
        
        # Start real-time monitoring loop
        last_log_count = 0  # 跟踪已推送的日志数量
        
        async def monitoring_loop():
            nonlocal last_log_count
            
            while True:
                try:
                    # 获取最新执行状态
                    current_execution = await get_execution_with_steps(int(execution_id))
                    if current_execution:
                        # 推送执行状态更新
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "execution_update",
                                "execution_id": int(execution_id),
                                "status": current_execution.get("status"),
                                "pipeline_name": current_execution.get("pipeline_name"),
                                "steps": current_execution.get("steps", []),
                                "total_steps": len(current_execution.get("steps", [])),
                                "completed_steps": sum(1 for s in current_execution.get("steps", []) if s.get("status") in ["success", "failed"]),
                                "execution_time": current_execution.get("execution_time", 0),
                                "timestamp": datetime.utcnow().isoformat()
                            }),
                            websocket
                        )
                        
                        # 推送每个步骤的状态更新
                        for step in current_execution.get("steps", []):
                            await manager.send_personal_message(
                                json.dumps({
                                    "type": "step_progress",
                                    "execution_id": int(execution_id),
                                    "step_id": step.get("id"),
                                    "step_name": step.get("name"),
                                    "status": step.get("status"),
                                    "execution_time": step.get("execution_time"),
                                    "output": step.get("output"),
                                    "error_message": step.get("error_message"),
                                    "timestamp": datetime.utcnow().isoformat()
                                }),
                                websocket
                            )
                        
                        # 获取新增的日志（从last_log_count开始）
                        new_logs = await get_execution_logs(int(execution_id), last_log_count)
                        
                        for log in new_logs:
                            await manager.send_personal_message(
                                json.dumps({
                                    "type": "log_entry",
                                    "execution_id": int(execution_id),
                                    "timestamp": log.get("timestamp", datetime.utcnow().isoformat()),
                                    "level": log.get("level", "info"),
                                    "message": log.get("message", ""),
                                    "step_name": log.get("step_name"),
                                    "source": log.get("source", "system")
                                }),
                                websocket
                            )
                        
                        # 更新已推送的日志数量
                        last_log_count += len(new_logs)
                        
                        # 如果执行完成，停止监控
                        if current_execution.get("status") in ["success", "failed", "cancelled"]:
                            break
                    
                    # 每500ms检查一次，保证实时性
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error("Error in monitoring loop", error=str(e))
                    break
        
        # 启动监控任务
        monitoring_task = asyncio.create_task(monitoring_loop())
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                logger.info("Received execution WebSocket message", 
                          execution_id=execution_id, 
                          message=message, 
                          user_id=user_id)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific events
                    events = message.get("events", [])
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "events": events,
                            "execution_id": execution_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
                elif message.get("type") == "get_status":
                    # 立即发送当前状态
                    current_execution = await get_execution_with_steps(int(execution_id))
                    if current_execution:
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "execution_status",
                                "data": current_execution,
                                "timestamp": datetime.utcnow().isoformat()
                            }),
                            websocket
                        )
                
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        # 取消监控任务
        if 'monitoring_task' in locals():
            monitoring_task.cancel()
        manager.disconnect(websocket, room, user_id)
        logger.info("Execution WebSocket disconnected", execution_id=execution_id, user_id=user_id)
    except Exception as e:
        # 取消监控任务
        if 'monitoring_task' in locals():
            monitoring_task.cancel()
        logger.error("Execution WebSocket error", error=str(e), execution_id=execution_id, user_id=user_id)
        manager.disconnect(websocket, room, user_id)


async def get_execution_with_steps(execution_id: int):
    """获取执行记录及其步骤信息"""
    return await django_db_service.get_execution_with_steps(execution_id)


async def get_execution_logs(execution_id: int, last_count: int = 0):
    """获取执行日志"""
    return await django_db_service.get_execution_logs(execution_id, last_count)


# Export the connection manager for use by other services
__all__ = ["websocket_router", "manager"]
