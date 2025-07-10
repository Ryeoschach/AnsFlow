"""
WebSocket实时推送服务 - AnsFlow优化版本
提供Pipeline执行状态、系统监控数据的实时推送
"""

import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Depends
import structlog

from ..core.redis import cache_service
from ..dependencies import get_cache_service, get_database_service

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 按类型管理连接
        self.pipeline_connections: Dict[int, Set[WebSocket]] = {}  # pipeline_id -> websockets
        self.system_connections: Set[WebSocket] = set()  # 系统监控连接
        self.execution_connections: Dict[int, Set[WebSocket]] = {}  # execution_id -> websockets
        self.user_connections: Dict[int, Set[WebSocket]] = {}  # user_id -> websockets
        
        # 所有活跃连接
        self.active_connections: Set[WebSocket] = set()
        
    async def connect(self, websocket: WebSocket, connection_type: str, resource_id: Optional[int] = None, user_id: Optional[int] = None):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # 根据连接类型进行分类管理
        if connection_type == "pipeline" and resource_id:
            if resource_id not in self.pipeline_connections:
                self.pipeline_connections[resource_id] = set()
            self.pipeline_connections[resource_id].add(websocket)
            
        elif connection_type == "execution" and resource_id:
            if resource_id not in self.execution_connections:
                self.execution_connections[resource_id] = set()
            self.execution_connections[resource_id].add(websocket)
            
        elif connection_type == "system":
            self.system_connections.add(websocket)
        
        # 用户连接管理
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        logger.info("WebSocket connected", type=connection_type, resource_id=resource_id, user_id=user_id)
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # 从各类连接集合中移除
        self._remove_from_pipeline_connections(websocket)
        self._remove_from_execution_connections(websocket)
        self._remove_from_system_connections(websocket)
        self._remove_from_user_connections(websocket)
        
        logger.info("WebSocket disconnected")
    
    def _remove_from_pipeline_connections(self, websocket: WebSocket):
        """从Pipeline连接中移除"""
        for pipeline_id in list(self.pipeline_connections.keys()):
            if websocket in self.pipeline_connections[pipeline_id]:
                self.pipeline_connections[pipeline_id].remove(websocket)
                if not self.pipeline_connections[pipeline_id]:
                    del self.pipeline_connections[pipeline_id]
    
    def _remove_from_execution_connections(self, websocket: WebSocket):
        """从执行连接中移除"""
        for execution_id in list(self.execution_connections.keys()):
            if websocket in self.execution_connections[execution_id]:
                self.execution_connections[execution_id].remove(websocket)
                if not self.execution_connections[execution_id]:
                    del self.execution_connections[execution_id]
    
    def _remove_from_system_connections(self, websocket: WebSocket):
        """从系统连接中移除"""
        if websocket in self.system_connections:
            self.system_connections.remove(websocket)
    
    def _remove_from_user_connections(self, websocket: WebSocket):
        """从用户连接中移除"""
        for user_id in list(self.user_connections.keys()):
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error("Error sending personal message", error=str(e))
            self.disconnect(websocket)
    
    async def broadcast_to_pipeline(self, message: Dict[str, Any], pipeline_id: int):
        """向特定Pipeline的所有连接广播消息"""
        if pipeline_id in self.pipeline_connections:
            await self._broadcast_to_connections(
                message, 
                self.pipeline_connections[pipeline_id]
            )
    
    async def broadcast_to_execution(self, message: Dict[str, Any], execution_id: int):
        """向特定执行的所有连接广播消息"""
        if execution_id in self.execution_connections:
            await self._broadcast_to_connections(
                message, 
                self.execution_connections[execution_id]
            )
    
    async def broadcast_to_system(self, message: Dict[str, Any]):
        """向系统监控连接广播消息"""
        await self._broadcast_to_connections(message, self.system_connections)
    
    async def broadcast_to_user(self, message: Dict[str, Any], user_id: int):
        """向特定用户的所有连接广播消息"""
        if user_id in self.user_connections:
            await self._broadcast_to_connections(
                message, 
                self.user_connections[user_id]
            )
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """向所有连接广播消息"""
        await self._broadcast_to_connections(message, self.active_connections)
    
    async def _broadcast_to_connections(self, message: Dict[str, Any], connections: Set[WebSocket]):
        """向连接集合广播消息"""
        if not connections:
            return
        
        message_str = json.dumps(message, ensure_ascii=False, default=str)
        dead_connections = set()
        
        for connection in connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error("Error broadcasting message", error=str(e))
                dead_connections.add(connection)
        
        # 清理失效连接
        for dead_connection in dead_connections:
            self.disconnect(dead_connection)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            "total_connections": len(self.active_connections),
            "pipeline_connections": len(self.pipeline_connections),
            "execution_connections": len(self.execution_connections),
            "system_connections": len(self.system_connections),
            "user_connections": len(self.user_connections),
            "pipeline_details": {
                pipeline_id: len(connections) 
                for pipeline_id, connections in self.pipeline_connections.items()
            },
            "execution_details": {
                execution_id: len(connections) 
                for execution_id, connections in self.execution_connections.items()
            }
        }


class WebSocketService:
    """WebSocket推送服务"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
    
    async def start_monitoring(self, cache_service):
        """启动系统监控推送"""
        if self._is_monitoring:
            return
        
        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(
            self._monitor_system_metrics(cache_service)
        )
        logger.info("WebSocket monitoring started")
    
    async def stop_monitoring(self):
        """停止系统监控推送"""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket monitoring stopped")
    
    async def _monitor_system_metrics(self, cache_service):
        """监控系统指标并推送"""
        while self._is_monitoring:
            try:
                # 每30秒推送系统指标
                await asyncio.sleep(30)
                
                if not self.manager.system_connections:
                    continue
                
                # 获取系统指标（可能来自缓存）
                metrics = await self._get_system_metrics(cache_service)
                
                # 推送给系统监控连接
                await self.manager.broadcast_to_system({
                    "type": "system_metrics",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": metrics
                })
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in system monitoring", error=str(e))
                await asyncio.sleep(5)  # 错误时等待5秒再重试
    
    async def _get_system_metrics(self, cache_service) -> Dict[str, Any]:
        """获取系统指标数据"""
        # 尝试从缓存获取
        cached_metrics = await cache_service.get("system_metrics", cache_type="api")
        if cached_metrics:
            return cached_metrics
        
        # 构造基本指标
        metrics = {
            "active_connections": len(self.manager.active_connections),
            "pipeline_connections": len(self.manager.pipeline_connections),
            "execution_connections": len(self.execution_connections),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 缓存指标（短时间缓存）
        await cache_service.set("system_metrics", metrics, ttl=60, cache_type="api")
        
        return metrics
    
    async def notify_pipeline_status_change(self, pipeline_id: int, status_data: Dict[str, Any]):
        """通知Pipeline状态变化"""
        message = {
            "type": "pipeline_status_update",
            "pipeline_id": pipeline_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": status_data
        }
        
        await self.manager.broadcast_to_pipeline(message, pipeline_id)
        logger.info("Pipeline status update sent", pipeline_id=pipeline_id, status=status_data.get('status'))
    
    async def notify_execution_update(self, execution_id: int, execution_data: Dict[str, Any]):
        """通知执行状态更新"""
        message = {
            "type": "execution_update",
            "execution_id": execution_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": execution_data
        }
        
        # 发送给执行监控连接
        await self.manager.broadcast_to_execution(message, execution_id)
        
        # 如果有pipeline_id，也发送给pipeline监控连接
        if "pipeline_id" in execution_data:
            await self.manager.broadcast_to_pipeline(message, execution_data["pipeline_id"])
        
        logger.info("Execution update sent", execution_id=execution_id, status=execution_data.get('status'))
    
    async def notify_execution_log(self, execution_id: int, log_data: Dict[str, Any]):
        """通知执行日志更新"""
        message = {
            "type": "execution_log",
            "execution_id": execution_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": log_data
        }
        
        await self.manager.broadcast_to_execution(message, execution_id)
    
    async def notify_user_notification(self, user_id: int, notification: Dict[str, Any]):
        """发送用户通知"""
        message = {
            "type": "user_notification",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": notification
        }
        
        await self.manager.broadcast_to_user(message, user_id)
        logger.info("User notification sent", user_id=user_id, type=notification.get('type'))
    
    async def broadcast_system_alert(self, alert_data: Dict[str, Any]):
        """广播系统警报"""
        message = {
            "type": "system_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": alert_data
        }
        
        await self.manager.broadcast_to_all(message)
        logger.warning("System alert broadcasted", alert=alert_data.get('message'))


# 全局连接管理器和WebSocket服务
manager = ConnectionManager()
websocket_service = WebSocketService(manager)
