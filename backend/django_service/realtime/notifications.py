"""
WebSocket notification utilities for real-time pipeline monitoring.
"""

import json
import logging
from typing import Dict, Any, Optional
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

logger = logging.getLogger(__name__)


class WebSocketNotifier:
    """
    WebSocket notification utility for sending real-time updates
    to connected clients during pipeline execution.
    """
    
    def __init__(self, execution_id: int):
        self.execution_id = execution_id
        self.channel_layer = get_channel_layer()
        self.group_name = f'execution_{execution_id}'
        self.global_group_name = 'global_monitor'
    
    def send_execution_update(self, status: str, data: Optional[Dict[str, Any]] = None):
        """Send execution status update."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping WebSocket notification")
            return
        
        update_data = {
            'type': 'execution_update',
            'data': {
                'type': 'execution_status',
                'execution_id': self.execution_id,
                'status': status,
                'timestamp': timezone.now().isoformat(),
                **(data or {})
            }
        }
        
        try:
            # Send to execution-specific group
            async_to_sync(self.channel_layer.group_send)(
                self.group_name, update_data
            )
            
            # Send to global monitoring group
            async_to_sync(self.channel_layer.group_send)(
                self.global_group_name, update_data
            )
            
            logger.debug(f"Sent execution update: {status} for execution {self.execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to send execution update: {e}")
    
    def send_step_update(self, step_name: str, step_status: str, data: Optional[Dict[str, Any]] = None):
        """Send step execution update."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping WebSocket notification")
            return
        
        update_data = {
            'type': 'step_update',
            'data': {
                'type': 'step_progress',
                'execution_id': self.execution_id,
                'step_name': step_name,
                'status': step_status,
                'timestamp': timezone.now().isoformat(),
                **(data or {})
            }
        }
        
        try:
            # Send to execution-specific group
            async_to_sync(self.channel_layer.group_send)(
                self.group_name, update_data
            )
            
            # Send to global monitoring group
            async_to_sync(self.channel_layer.group_send)(
                self.global_group_name, update_data
            )
            
            logger.debug(f"Sent step update: {step_name} - {step_status} for execution {self.execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to send step update: {e}")
    
    def send_log_update(self, log_message: str, level: str = 'info', step_name: Optional[str] = None):
        """Send log update."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping WebSocket notification")
            return
        
        update_data = {
            'type': 'log_update',
            'data': {
                'type': 'log_message',
                'execution_id': self.execution_id,
                'message': log_message,
                'level': level,
                'step_name': step_name,
                'timestamp': timezone.now().isoformat()
            }
        }
        
        try:
            # Send to execution-specific group
            async_to_sync(self.channel_layer.group_send)(
                self.group_name, update_data
            )
            
            logger.debug(f"Sent log update for execution {self.execution_id}: {log_message}")
            
        except Exception as e:
            logger.error(f"Failed to send log update: {e}")
    
    def send_progress_update(self, progress_percentage: float, current_step: Optional[str] = None):
        """Send progress update."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping WebSocket notification")
            return
        
        update_data = {
            'type': 'execution_update',
            'data': {
                'type': 'progress_update',
                'execution_id': self.execution_id,
                'progress': round(progress_percentage, 1),
                'current_step': current_step,
                'timestamp': timezone.now().isoformat()
            }
        }
        
        try:
            # Send to execution-specific group
            async_to_sync(self.channel_layer.group_send)(
                self.group_name, update_data
            )
            
            # Send to global monitoring group
            async_to_sync(self.channel_layer.group_send)(
                self.global_group_name, update_data
            )
            
            logger.debug(f"Sent progress update: {progress_percentage}% for execution {self.execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")

    def send_error_update(self, error_message: str, step_name: Optional[str] = None):
        """Send error update."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping WebSocket notification")
            return
        
        update_data = {
            'type': 'execution_update',
            'data': {
                'type': 'error',
                'execution_id': self.execution_id,
                'error_message': error_message,
                'step_name': step_name,
                'timestamp': timezone.now().isoformat()
            }
        }
        
        try:
            # Send to execution-specific group
            async_to_sync(self.channel_layer.group_send)(
                self.group_name, update_data
            )
            
            # Send to global monitoring group
            async_to_sync(self.channel_layer.group_send)(
                self.global_group_name, update_data
            )
            
            logger.debug(f"Sent error update for execution {self.execution_id}: {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to send error update: {e}")


# Async version for use in async contexts
class AsyncWebSocketNotifier:
    """
    Async WebSocket notification utility for sending real-time updates
    from async contexts.
    """
    
    def __init__(self, execution_id: int):
        self.execution_id = execution_id
        self.channel_layer = get_channel_layer()
        self.group_name = f'execution_{execution_id}'
        self.global_group_name = 'global_monitor'
    
    async def send_execution_update(self, status: str, data: Optional[Dict[str, Any]] = None):
        """Send execution status update."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping WebSocket notification")
            return
        
        update_data = {
            'type': 'execution_update',
            'data': {
                'type': 'execution_status',
                'execution_id': self.execution_id,
                'status': status,
                'timestamp': timezone.now().isoformat(),
                **(data or {})
            }
        }
        
        try:
            # Send to execution-specific group
            await self.channel_layer.group_send(self.group_name, update_data)
            
            # Send to global monitoring group
            await self.channel_layer.group_send(self.global_group_name, update_data)
            
            logger.debug(f"Sent execution update: {status} for execution {self.execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to send execution update: {e}")
    
    async def send_step_update(self, step_name: str, step_status: str, data: Optional[Dict[str, Any]] = None):
        """Send step execution update."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping WebSocket notification")
            return
        
        update_data = {
            'type': 'step_update',
            'data': {
                'type': 'step_progress',
                'execution_id': self.execution_id,
                'step_name': step_name,
                'status': step_status,
                'timestamp': timezone.now().isoformat(),
                **(data or {})
            }
        }
        
        try:
            # Send to execution-specific group
            await self.channel_layer.group_send(self.group_name, update_data)
            
            # Send to global monitoring group
            await self.channel_layer.group_send(self.global_group_name, update_data)
            
            logger.debug(f"Sent step update: {step_name} - {step_status} for execution {self.execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to send step update: {e}")
    
    async def send_log_update(self, log_message: str, level: str = 'info', step_name: Optional[str] = None):
        """Send log update."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping WebSocket notification")
            return
        
        update_data = {
            'type': 'log_update',
            'data': {
                'type': 'log_message',
                'execution_id': self.execution_id,
                'message': log_message,
                'level': level,
                'step_name': step_name,
                'timestamp': timezone.now().isoformat()
            }
        }
        
        try:
            # Send to execution-specific group
            await self.channel_layer.group_send(self.group_name, update_data)
            
            logger.debug(f"Sent log update for execution {self.execution_id}: {log_message}")
            
        except Exception as e:
            logger.error(f"Failed to send log update: {e}")
    
    async def send_progress_update(self, progress_percentage: float, current_step: Optional[str] = None):
        """Send progress update."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping WebSocket notification")
            return
        
        update_data = {
            'type': 'execution_update',
            'data': {
                'type': 'progress_update',
                'execution_id': self.execution_id,
                'progress': round(progress_percentage, 1),
                'current_step': current_step,
                'timestamp': timezone.now().isoformat()
            }
        }
        
        try:
            # Send to execution-specific group
            await self.channel_layer.group_send(self.group_name, update_data)
            
            # Send to global monitoring group
            await self.channel_layer.group_send(self.global_group_name, update_data)
            
            logger.debug(f"Sent progress update: {progress_percentage}% for execution {self.execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")

    async def send_error_update(self, error_message: str, step_name: Optional[str] = None):
        """Send error update."""
        if not self.channel_layer:
            logger.warning("Channel layer not configured, skipping WebSocket notification")
            return
        
        update_data = {
            'type': 'execution_update',
            'data': {
                'type': 'error',
                'execution_id': self.execution_id,
                'error_message': error_message,
                'step_name': step_name,
                'timestamp': timezone.now().isoformat()
            }
        }
        
        try:
            # Send to execution-specific group
            await self.channel_layer.group_send(self.group_name, update_data)
            
            # Send to global monitoring group
            await self.channel_layer.group_send(self.global_group_name, update_data)
            
            logger.debug(f"Sent error update for execution {self.execution_id}: {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to send error update: {e}")
