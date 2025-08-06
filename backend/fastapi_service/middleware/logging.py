"""
FastAPI日志中间件
记录所有HTTP请求和响应信息
"""
import time
import uuid
import json
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware

# 创建日志器
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """FastAPI HTTP请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求和响应"""
        # 生成请求ID和开始时间
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = self.get_client_ip(request)
        
        # 获取用户信息（如果有认证）
        user_info = await self.get_user_info(request)
        
        # 请求体大小
        request_size = 0
        if hasattr(request, 'body'):
            try:
                body = await request.body()
                request_size = len(body) if body else 0
            except:
                pass
        
        # 记录请求开始日志
        self.log_with_context(
            logger, 'INFO',
            f"Request started: {request.method} {request.url.path}",
            extra_data={
                'trace_id': f"req_{request_id}",
                'user_id': user_info.get('user_id'),
                'user_name': user_info.get('user_name'),
                'ip': client_ip,
                'method': request.method,
                'path': str(request.url.path),
                'query_params': dict(request.query_params),
                'request_size': request_size,
                'content_type': request.headers.get('content-type', ''),
                'user_agent': request.headers.get('user-agent', ''),
            },
            labels=['fastapi', 'http', 'request', 'start']
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 确定日志级别
            if response.status_code >= 500:
                level = 'ERROR'
            elif response.status_code >= 400:
                level = 'WARNING'
            else:
                level = 'INFO'
            
            # 记录响应日志
            self.log_with_context(
                logger, level,
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra_data={
                    'trace_id': f"req_{request_id}",
                    'user_id': user_info.get('user_id'),
                    'user_name': user_info.get('user_name'),
                    'ip': client_ip,
                    'method': request.method,
                    'path': str(request.url.path),
                    'status_code': response.status_code,
                    'response_time_ms': response_time_ms,
                },
                labels=['fastapi', 'http', 'response', 'complete']
            )
            
            return response
            
        except Exception as e:
            # 计算响应时间
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 记录异常日志
            self.log_with_context(
                logger, 'ERROR',
                f"Request exception: {request.method} {request.url.path} - {str(e)}",
                extra_data={
                    'trace_id': f"req_{request_id}",
                    'user_id': user_info.get('user_id'),
                    'user_name': user_info.get('user_name'),
                    'ip': client_ip,
                    'method': request.method,
                    'path': str(request.url.path),
                    'response_time_ms': response_time_ms,
                    'exception_type': e.__class__.__name__,
                    'exception_message': str(e),
                },
                labels=['fastapi', 'http', 'exception', 'error']
            )
            
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 尝试从X-Forwarded-For获取
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # 尝试从X-Real-IP获取
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # 从客户端地址获取
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return 'unknown'
    
    async def get_user_info(self, request: Request) -> dict:
        """获取用户信息"""
        user_info = {'user_id': None, 'user_name': None}
        
        try:
            # 尝试从请求中获取用户信息
            # 这里需要根据实际的认证机制进行调整
            if hasattr(request.state, 'user'):
                user = request.state.user
                user_info['user_id'] = getattr(user, 'id', None)
                user_info['user_name'] = getattr(user, 'username', None)
        except:
            pass
            
        return user_info
    
    def log_with_context(self, logger_instance: logging.Logger, level: str, 
                        message: str, extra_data: dict = None, labels: list = None):
        """带上下文信息的日志记录"""
        # 构建日志记录
        log_data = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime()),
            'level': level,
            'service': 'fastapi',
            'module': __name__,
            'message': message,
        }
        
        # 添加额外数据
        if extra_data:
            log_data.update(extra_data)
        
        # 添加标签
        if labels:
            log_data['labels'] = labels
        
        # 过滤敏感信息
        filtered_data = self.filter_sensitive_data(log_data)
        
        # 创建LogRecord
        record = logger_instance.makeRecord(
            name=logger_instance.name,
            level=getattr(logging, level),
            fn='',
            lno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        
        # 添加自定义属性
        for key, value in filtered_data.items():
            setattr(record, key, value)
        
        # 发送日志
        logger_instance.handle(record)
    
    def filter_sensitive_data(self, data: dict) -> dict:
        """过滤敏感信息"""
        sensitive_fields = {
            'password', 'passwd', 'pwd', 'token', 'key', 'secret',
            'authorization', 'cookie', 'session', 'csrf'
        }
        
        filtered_data = {}
        for key, value in data.items():
            if isinstance(key, str) and any(sensitive in key.lower() for sensitive in sensitive_fields):
                if isinstance(value, str) and len(value) > 8:
                    filtered_data[key] = value[:3] + '*' * (len(value) - 3)
                else:
                    filtered_data[key] = '******'
            elif isinstance(value, dict):
                filtered_data[key] = self.filter_sensitive_data(value)
            else:
                filtered_data[key] = value
        
        return filtered_data
