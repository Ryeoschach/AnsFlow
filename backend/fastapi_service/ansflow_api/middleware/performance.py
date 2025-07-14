"""
性能优化中间件集合
包含缓存、压缩、限流等优化功能
"""

import time
import gzip
import asyncio
import hashlib
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import logging

from ..config.performance import performance_settings

logger = logging.getLogger(__name__)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """响应缓存中间件"""
    
    def __init__(self, app, cache_ttl: int = 300):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {"hits": 0, "misses": 0}
    
    def _get_cache_key(self, request: Request) -> str:
        """生成缓存键"""
        # 使用请求方法、路径和查询参数生成缓存键
        key_data = f"{request.method}:{request.url.path}:{request.url.query}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cacheable(self, request: Request, response: Response) -> bool:
        """判断响应是否可缓存"""
        # 只缓存 GET 请求和 200 状态码的响应
        return (
            request.method == "GET" and
            response.status_code == 200 and
            not request.url.path.startswith("/metrics") and
            not request.url.path.startswith("/health")
        )
    
    async def dispatch(self, request: Request, call_next):
        # 跳过不需要缓存的请求
        if not performance_settings.enable_response_cache or request.method != "GET":
            return await call_next(request)
        
        cache_key = self._get_cache_key(request)
        
        # 检查缓存
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                self.cache_stats["hits"] += 1
                response_data = cached_item["response"]
                return JSONResponse(
                    content=response_data["content"],
                    status_code=response_data["status_code"],
                    headers={**response_data["headers"], "X-Cache": "HIT"}
                )
            else:
                # 缓存过期，删除
                del self.cache[cache_key]
        
        # 执行请求
        response = await call_next(request)
        
        # 缓存响应
        if self._is_cacheable(request, response):
            # 读取响应内容
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            try:
                # 假设响应是 JSON
                import json
                content = json.loads(body.decode())
                
                # 缓存响应数据
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "response": {
                        "content": content,
                        "status_code": response.status_code,
                        "headers": dict(response.headers)
                    }
                }
                
                # 限制缓存大小
                if len(self.cache) > performance_settings.cache_max_size:
                    # 删除最旧的缓存项
                    oldest_key = min(self.cache.keys(), 
                                   key=lambda k: self.cache[k]["timestamp"])
                    del self.cache[oldest_key]
                
                self.cache_stats["misses"] += 1
                
                # 返回新的响应，添加缓存头
                return JSONResponse(
                    content=content,
                    status_code=response.status_code,
                    headers={**dict(response.headers), "X-Cache": "MISS"}
                )
                
            except Exception as e:
                logger.warning(f"Failed to cache response: {e}")
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """响应压缩中间件"""
    
    def __init__(self, app, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 检查是否需要压缩
        if (
            "gzip" in request.headers.get("accept-encoding", "") and
            hasattr(response, "body") and
            len(getattr(response, "body", b"")) > self.minimum_size
        ):
            try:
                # 压缩响应体
                compressed_body = gzip.compress(response.body)
                
                # 更新响应
                response.body = compressed_body
                response.headers["content-encoding"] = "gzip"
                response.headers["content-length"] = str(len(compressed_body))
                
            except Exception as e:
                logger.warning(f"Failed to compress response: {e}")
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """请求限流中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests: Dict[str, list] = {}
        self.max_requests = performance_settings.rate_limit_requests
        self.window = performance_settings.rate_limit_window
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端ID"""
        # 使用 IP 地址作为客户端标识
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_id: str):
        """清理过期的请求记录"""
        if client_id not in self.requests:
            return
        
        current_time = time.time()
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if current_time - req_time < self.window
        ]
    
    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # 清理过期请求
        self._cleanup_old_requests(client_id)
        
        # 检查请求频率
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        if len(self.requests[client_id]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window} seconds"
            )
        
        # 记录请求时间
        self.requests[client_id].append(current_time)
        
        return await call_next(request)


class PerformanceMetricsMiddleware(BaseHTTPMiddleware):
    """性能指标收集中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_times: list = []
        self.slow_requests: list = []
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # 计算请求处理时间
            process_time = time.time() - start_time
            self.request_times.append(process_time)
            
            # 记录慢请求
            if process_time > 1.0:  # 超过1秒的请求
                self.slow_requests.append({
                    "path": request.url.path,
                    "method": request.method,
                    "duration": process_time,
                    "timestamp": time.time()
                })
                logger.warning(f"Slow request detected: {request.method} {request.url.path} took {process_time:.2f}s")
            
            # 限制内存中的数据量
            if len(self.request_times) > 1000:
                self.request_times = self.request_times[-500:]
            
            if len(self.slow_requests) > 100:
                self.slow_requests = self.slow_requests[-50:]
            
            # 添加性能头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed after {process_time:.2f}s: {e}")
            raise
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self.request_times:
            return {"error": "No request data available"}
        
        avg_time = sum(self.request_times) / len(self.request_times)
        max_time = max(self.request_times)
        min_time = min(self.request_times)
        
        return {
            "total_requests": len(self.request_times),
            "avg_response_time": round(avg_time, 4),
            "max_response_time": round(max_time, 4),
            "min_response_time": round(min_time, 4),
            "slow_requests_count": len(self.slow_requests),
            "recent_slow_requests": self.slow_requests[-5:] if self.slow_requests else []
        }


class AsyncConnectionPoolMiddleware(BaseHTTPMiddleware):
    """异步连接池优化中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.active_connections = 0
        self.max_connections = performance_settings.max_connections
        
    async def dispatch(self, request: Request, call_next):
        # 检查连接数限制
        if self.active_connections >= self.max_connections:
            raise HTTPException(
                status_code=503,
                detail="Server is busy. Too many active connections."
            )
        
        self.active_connections += 1
        
        try:
            response = await call_next(request)
            return response
        finally:
            self.active_connections -= 1


# 全局中间件实例
response_cache_middleware = None
compression_middleware = None
rate_limit_middleware = None
performance_metrics_middleware = None
connection_pool_middleware = None


def get_performance_middlewares():
    """获取所有性能中间件"""
    global response_cache_middleware, compression_middleware, rate_limit_middleware
    global performance_metrics_middleware, connection_pool_middleware
    
    if response_cache_middleware is None:
        response_cache_middleware = ResponseCacheMiddleware
        compression_middleware = CompressionMiddleware
        rate_limit_middleware = RateLimitMiddleware
        performance_metrics_middleware = PerformanceMetricsMiddleware
        connection_pool_middleware = AsyncConnectionPoolMiddleware
    
    return [
        connection_pool_middleware,
        rate_limit_middleware,
        performance_metrics_middleware,
        response_cache_middleware,
        compression_middleware,
    ]
