"""
Django日志中间件
记录所有HTTP请求和响应信息
"""
import time
import uuid
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse
from .logging_config import get_logger, log_with_context

logger = get_logger(__name__)


class LoggingMiddleware(MiddlewareMixin):
    """HTTP请求日志中间件"""
    
    def process_request(self, request: HttpRequest):
        """处理请求开始"""
        # 生成请求ID
        request.id = str(uuid.uuid4())[:8]
        request.start_time = time.time()
        
        # 记录请求开始日志
        log_with_context(
            logger, 'INFO',
            f"Request started: {request.method} {request.path}",
            request=request,
            extra={
                'request_size': len(request.body) if hasattr(request, 'body') else 0,
                'content_type': request.content_type,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            },
            labels=['http', 'request', 'start']
        )
        
    def process_response(self, request: HttpRequest, response: HttpResponse):
        """处理响应"""
        # 计算响应时间
        response_time_ms = int((time.time() - request.start_time) * 1000)
        
        # 设置响应时间到记录中
        if hasattr(request, 'id'):
            setattr(request, 'response_time_ms', response_time_ms)
            setattr(request, 'status_code', response.status_code)
        
        # 确定日志级别
        if response.status_code >= 500:
            level = 'ERROR'
        elif response.status_code >= 400:
            level = 'WARNING'
        else:
            level = 'INFO'
        
        # 记录响应日志
        log_with_context(
            logger, level,
            f"Request completed: {request.method} {request.path} - {response.status_code}",
            request=request,
            extra={
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
                'response_type': response.get('Content-Type', ''),
            },
            labels=['http', 'response', 'complete']
        )
        
        return response
        
    def process_exception(self, request: HttpRequest, exception: Exception):
        """处理异常"""
        log_with_context(
            logger, 'ERROR',
            f"Request exception: {request.method} {request.path} - {str(exception)}",
            request=request,
            extra={
                'exception_type': exception.__class__.__name__,
                'exception_message': str(exception),
            },
            labels=['http', 'exception', 'error']
        )
        
        return None
