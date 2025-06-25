"""
Main FastAPI application factory
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from .config.settings import settings
from .core.database import create_tables
from .api.routes import api_router
from .webhooks.routes import webhook_router
from .websockets.routes import websocket_router
from .monitoring.middleware import PrometheusMiddleware
from .monitoring.health import health_router


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
    
    # Create database tables
    await create_tables()
    logger.info("Database tables created")
    
    # Initialize message queue connections
    # TODO: Initialize RabbitMQ connection
    
    yield
    
    # Shutdown
    logger.info("Shutting down AnsFlow FastAPI service")


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
    
    # Include routers
    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(api_router, prefix="/api/v1", tags=["API"])
    app.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])
    app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
    
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
