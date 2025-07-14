"""
Main FastAPI application factory
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response
import structlog

from .config.settings import settings
from .core.database import create_tables
from .api.routes import api_router
from .webhooks.routes import webhook_router
from .websockets.routes import websocket_router
from .monitoring.middleware import PrometheusMiddleware
from .monitoring.health import health_router
from .monitoring import init_monitoring
from .services.django_db import django_db_service


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    # Startup
    logger.info("Starting AnsFlow FastAPI service", version=settings.api.version)
    
    # Initialize Django database connection pool
    await django_db_service.init_connection_pool()
    logger.info("Django database connection pool initialized")
    
    # Create database tables
    await create_tables()
    logger.info("Database tables created")
    
    # Initialize message queue connections
    # TODO: Initialize RabbitMQ connection
    
    yield
    
    # Shutdown
    logger.info("Shutting down AnsFlow FastAPI service")
    
    # Close Django database connection pool
    await django_db_service.close_connection_pool()
    logger.info("Django database connection pool closed")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application
    """
    app = FastAPI(
        title=settings.api.title,
        description=settings.api.description,
        version=settings.api.version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", settings.host]
        )
    
    # Add Prometheus monitoring middleware
    app.add_middleware(PrometheusMiddleware)
    
    # Initialize Prometheus monitoring
    monitoring = init_monitoring(app)
    logger.info("Prometheus monitoring initialized")
    
    # Add a simple test endpoint to verify metrics
    @app.get("/test-metrics")
    async def test_metrics():
        """Test endpoint to verify metrics collection"""
        from prometheus_client import generate_latest
        metrics_data = generate_latest()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    
    # Add main metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        from prometheus_client import generate_latest
        metrics_data = generate_latest()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    
    # Include routers
    app.include_router(health_router, prefix="/health", tags=["Health"])
    
    # 添加测试路由
    try:
        from .api.test_routes import router as test_router
        app.include_router(test_router, prefix="/api/v1", tags=["Test API"])
    except ImportError:
        pass
    
    try:
        app.include_router(api_router, prefix="/api/v1", tags=["API"])
    except:
        pass
        
    try:
        app.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])
    except:
        pass
        
    try:
        app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
    except:
        pass
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "AnsFlow FastAPI Service",
            "version": settings.api.version,
            "status": "running",
            "environment": settings.environment
        }
    
    return app


# Create application instance
app = create_application()


"""
Performance optimization settings
"""

# 性能优化配置
PERFORMANCE_CONFIG = {
    "enable_compression": True,
    "enable_caching": True,
    "cache_ttl": 300,
    "max_request_size": 16 * 1024 * 1024,  # 16MB
    "connection_timeout": 5,
    "keep_alive_timeout": 5,
}

# 安全配置
SECURITY_CONFIG = {
    "enable_cors": True,
    "cors_origins": ["http://localhost:3000", "http://localhost:3001"],
    "enable_security_headers": True,
    "enable_audit_log": True,
    "jwt_secret_key": "your-secret-key-change-in-production",
}
