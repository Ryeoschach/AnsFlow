"""
Prometheus monitoring middleware
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Prometheus metrics
REQUEST_COUNT = Counter(
    'fastapi_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'fastapi_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'fastapi_active_connections',
    'Number of active connections'
)

WEBSOCKET_CONNECTIONS = Gauge(
    'fastapi_websocket_connections',
    'Number of active WebSocket connections'
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics collection for metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Increment active connections
        ACTIVE_CONNECTIONS.inc()
        
        # Record request start time
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            method = request.method
            endpoint = request.url.path
            status_code = response.status_code
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(time.time() - start_time)
            
            return response
            
        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()


def get_metrics() -> str:
    """
    Get Prometheus metrics in text format
    """
    return generate_latest()
