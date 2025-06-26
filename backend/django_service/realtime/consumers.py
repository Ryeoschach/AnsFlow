"""
WebSocket consumers for real-time pipeline monitoring.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from cicd_integrations.models import PipelineExecution, StepExecution

logger = logging.getLogger(__name__)


class PipelineMonitorConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time pipeline execution monitoring.
    
    Handles:
    - Pipeline execution status updates
    - Step execution progress
    - Real-time logs
    - Execution control commands
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.execution_id = self.scope['url_route']['kwargs']['execution_id']
        self.execution_group_name = f'execution_{self.execution_id}'
        
        # Join execution group
        await self.channel_layer.group_add(
            self.execution_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"WebSocket connected for execution {self.execution_id}")
        
        # Send initial execution status
        await self.send_execution_status()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave execution group
        await self.channel_layer.group_discard(
            self.execution_group_name,
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnected for execution {self.execution_id}")

    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_status':
                await self.send_execution_status()
            elif message_type == 'get_logs':
                await self.send_execution_logs()
            elif message_type == 'control':
                await self.handle_control_command(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send_error("Internal server error")

    async def send_execution_status(self):
        """Send current execution status to client."""
        try:
            execution = await self.get_execution()
            if not execution:
                await self.send_error("Execution not found")
                return
            
            # Get step executions
            steps = await self.get_step_executions()
            
            # Calculate progress
            total_steps = len(steps)
            completed_steps = sum(1 for step in steps if step['status'] in ['success', 'failed', 'skipped'])
            progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0
            
            status_data = {
                'type': 'execution_status',
                'execution': {
                    'id': execution['id'],
                    'status': execution['status'],
                    'started_at': execution['started_at'],
                    'completed_at': execution['completed_at'],
                    'pipeline_name': execution['pipeline_name'],
                    'trigger_type': execution['trigger_type'],
                    'progress': round(progress, 1)
                },
                'steps': steps,
                'total_steps': total_steps,
                'completed_steps': completed_steps
            }
            
            await self.send(text_data=json.dumps(status_data))
            
        except Exception as e:
            logger.error(f"Error sending execution status: {e}")
            await self.send_error("Failed to get execution status")

    async def send_execution_logs(self):
        """Send execution logs to client."""
        try:
            execution = await self.get_execution()
            if not execution:
                return
            
            logs_data = {
                'type': 'execution_logs',
                'execution_id': self.execution_id,
                'logs': execution.get('logs', ''),
                'timestamp': execution.get('updated_at')
            }
            
            await self.send(text_data=json.dumps(logs_data))
            
        except Exception as e:
            logger.error(f"Error sending execution logs: {e}")
            await self.send_error("Failed to get execution logs")

    async def handle_control_command(self, data):
        """Handle pipeline control commands."""
        command = data.get('command')
        
        if command == 'stop':
            await self.stop_execution()
        elif command == 'restart':
            await self.restart_execution()
        else:
            await self.send_error(f"Unknown control command: {command}")

    async def stop_execution(self):
        """Stop the current execution."""
        try:
            # TODO: Implement execution stopping logic
            await self.send_status_update("Stopping execution...")
            
            # For now, just update status to cancelled
            await self.update_execution_status('cancelled')
            
        except Exception as e:
            logger.error(f"Error stopping execution: {e}")
            await self.send_error("Failed to stop execution")

    async def restart_execution(self):
        """Restart the current execution."""
        try:
            # TODO: Implement execution restart logic
            await self.send_status_update("Restarting execution...")
            
        except Exception as e:
            logger.error(f"Error restarting execution: {e}")
            await self.send_error("Failed to restart execution")

    async def send_error(self, message):
        """Send error message to client."""
        error_data = {
            'type': 'error',
            'message': message,
            'execution_id': self.execution_id
        }
        
        await self.send(text_data=json.dumps(error_data))

    async def send_status_update(self, message):
        """Send status update to client."""
        update_data = {
            'type': 'status_update',
            'message': message,
            'execution_id': self.execution_id,
            'timestamp': None  # TODO: Add timestamp
        }
        
        await self.send(text_data=json.dumps(update_data))

    # Group message handlers
    async def execution_update(self, event):
        """Handle execution update from group."""
        await self.send(text_data=json.dumps(event['data']))

    async def step_update(self, event):
        """Handle step update from group."""
        await self.send(text_data=json.dumps(event['data']))

    async def log_update(self, event):
        """Handle log update from group."""
        await self.send(text_data=json.dumps(event['data']))

    # Database operations
    @database_sync_to_async
    def get_execution(self):
        """Get execution details from database."""
        try:
            execution = PipelineExecution.objects.select_related('pipeline').get(
                id=self.execution_id
            )
            
            return {
                'id': execution.id,
                'status': execution.status,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'updated_at': execution.updated_at.isoformat() if execution.updated_at else None,
                'pipeline_name': execution.pipeline.name,
                'trigger_type': execution.trigger_type,
                'logs': execution.logs or '',
                'parameters': execution.parameters or {}
            }
        except PipelineExecution.DoesNotExist:
            return None

    @database_sync_to_async
    def get_step_executions(self):
        """Get step executions for the pipeline."""
        try:
            # Get atomic steps for this execution's pipeline
            from cicd_integrations.models import AtomicStep
            
            execution = PipelineExecution.objects.get(id=self.execution_id)
            atomic_steps = AtomicStep.objects.filter(
                pipeline=execution.pipeline
            ).order_by('order')
            
            steps = []
            for step in atomic_steps:
                # Try to get step execution
                try:
                    step_execution = StepExecution.objects.get(
                        pipeline_execution=execution,
                        atomic_step=step
                    )
                    status = step_execution.status
                    started_at = step_execution.started_at.isoformat() if step_execution.started_at else None
                    completed_at = step_execution.completed_at.isoformat() if step_execution.completed_at else None
                    logs = step_execution.logs or ''
                except StepExecution.DoesNotExist:
                    status = 'pending'
                    started_at = None
                    completed_at = None
                    logs = ''
                
                steps.append({
                    'id': step.id,
                    'name': step.name,
                    'step_type': step.step_type,
                    'order': step.order,
                    'status': status,
                    'started_at': started_at,
                    'completed_at': completed_at,
                    'logs': logs,
                    'config': step.config or {}
                })
            
            return steps
            
        except Exception as e:
            logger.error(f"Error getting step executions: {e}")
            return []

    @database_sync_to_async
    def update_execution_status(self, status):
        """Update execution status in database."""
        try:
            execution = PipelineExecution.objects.get(id=self.execution_id)
            execution.status = status
            execution.save(update_fields=['status'])
            return True
        except PipelineExecution.DoesNotExist:
            return False


class GlobalMonitorConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for global pipeline monitoring.
    
    Handles:
    - All executions overview
    - System status
    - General notifications
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.group_name = 'global_monitor'
        
        # Join global monitor group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info("WebSocket connected for global monitoring")
        
        # Send initial system status
        await self.send_system_status()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave global monitor group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        
        logger.info("WebSocket disconnected from global monitoring")

    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_system_status':
                await self.send_system_status()
            elif message_type == 'get_recent_executions':
                await self.send_recent_executions()
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def send_system_status(self):
        """Send system status to client."""
        try:
            # Get system statistics
            stats = await self.get_system_stats()
            
            status_data = {
                'type': 'system_status',
                'stats': stats,
                'timestamp': None  # TODO: Add timestamp
            }
            
            await self.send(text_data=json.dumps(status_data))
            
        except Exception as e:
            logger.error(f"Error sending system status: {e}")

    async def send_recent_executions(self):
        """Send recent executions to client."""
        try:
            executions = await self.get_recent_executions()
            
            executions_data = {
                'type': 'recent_executions',
                'executions': executions
            }
            
            await self.send(text_data=json.dumps(executions_data))
            
        except Exception as e:
            logger.error(f"Error sending recent executions: {e}")

    # Group message handlers
    async def system_update(self, event):
        """Handle system update from group."""
        await self.send(text_data=json.dumps(event['data']))

    async def execution_notification(self, event):
        """Handle execution notification from group."""
        await self.send(text_data=json.dumps(event['data']))

    # Database operations
    @database_sync_to_async
    def get_system_stats(self):
        """Get system statistics."""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            now = timezone.now()
            today = now.date()
            
            # Total executions
            total_executions = PipelineExecution.objects.count()
            
            # Today's executions
            today_executions = PipelineExecution.objects.filter(
                created_at__date=today
            ).count()
            
            # Running executions
            running_executions = PipelineExecution.objects.filter(
                status='running'
            ).count()
            
            # Success rate (last 24 hours)
            yesterday = now - timedelta(days=1)
            recent_executions = PipelineExecution.objects.filter(
                created_at__gte=yesterday
            )
            total_recent = recent_executions.count()
            successful_recent = recent_executions.filter(status='success').count()
            success_rate = (successful_recent / total_recent * 100) if total_recent > 0 else 0
            
            return {
                'total_executions': total_executions,
                'today_executions': today_executions,
                'running_executions': running_executions,
                'success_rate': round(success_rate, 1),
                'last_updated': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}

    @database_sync_to_async
    def get_recent_executions(self, limit=10):
        """Get recent executions."""
        try:
            executions = PipelineExecution.objects.select_related('pipeline').order_by(
                '-created_at'
            )[:limit]
            
            result = []
            for execution in executions:
                result.append({
                    'id': execution.id,
                    'status': execution.status,
                    'pipeline_name': execution.pipeline.name,
                    'trigger_type': execution.trigger_type,
                    'created_at': execution.created_at.isoformat(),
                    'started_at': execution.started_at.isoformat() if execution.started_at else None,
                    'completed_at': execution.completed_at.isoformat() if execution.completed_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting recent executions: {e}")
            return []
