"""
Main FastAPI application factory
"""
from contextlib import asynccontextmanager
from pathlib import Path
import sys

# 添加项目根路径以便导入统一日志系统
current_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(current_dir))

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

# 导入统一日志系统集成
try:
    from standalone_logging import setup_standalone_logging, get_fastapi_logger
    HAS_STANDALONE_LOGGING = True
except ImportError:
    try:
        from logging_integration import setup_structlog_integration, get_fastapi_logger
        HAS_UNIFIED_LOGGING = True
        HAS_STANDALONE_LOGGING = False
    except ImportError:
        HAS_UNIFIED_LOGGING = False
        HAS_STANDALONE_LOGGING = False
        print("⚠️  统一日志系统集成不可用，使用基本日志配置")


# Configure structured logging with unified system integration
if HAS_STANDALONE_LOGGING:
    # 使用独立日志系统（推荐）
    logger = setup_standalone_logging()
    print("✅ 使用FastAPI独立日志系统")
elif HAS_UNIFIED_LOGGING:
    # 使用原有统一日志系统集成
    log_integration = setup_structlog_integration()
    logger = get_fastapi_logger('main')
    print("✅ 使用原有统一日志系统")
else:
    # 基本structlog配置 - 暂时使用标准logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('fastapi.main')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    # Startup
    logger.info(f"Starting AnsFlow FastAPI service v{settings.api.version}")
    
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
    
    # 添加日志管理路由
    try:
        from .api.log_management import log_router
        app.include_router(log_router, prefix="/api/v1", tags=["日志管理"])
        logger.info("Log management router added successfully")
    except ImportError as e:
        logger.warning(f"Failed to import log management router: {e}")
        pass
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        logger.info("Root endpoint accessed")
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
