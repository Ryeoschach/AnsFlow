"""
Health check endpoints and monitoring
"""
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx
import redis.asyncio as redis

from ..core.database import get_db
from ..config.settings import settings
from . import update_health_check

health_router = APIRouter()


async def check_database(db: AsyncSession) -> bool:
    """Check database connectivity"""
    try:
        result = await db.execute(text("SELECT 1"))
        return result.scalar() == 1
    except Exception:
        return False


async def check_redis() -> bool:
    """Check Redis connectivity"""
    try:
        r = redis.from_url(settings.redis.url)
        await r.ping()
        await r.aclose()
        return True
    except Exception:
        return False


async def check_django_service() -> bool:
    """Check Django service connectivity"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.django_service_url}/api/health/",
                timeout=5.0
            )
            return response.status_code == 200
    except Exception:
        return False


@health_router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint
    """
    checks = {
        "database": await check_database(db),
        "redis": await check_redis(),
        "django_service": await check_django_service(),
    }
    
    # Update Prometheus health check metrics
    update_health_check("fastapi", "database", checks["database"])
    update_health_check("fastapi", "redis", checks["redis"])
    update_health_check("fastapi", "django_service", checks["django_service"])
    
    overall_healthy = all(checks.values())
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ansflow-fastapi",
        "version": settings.api.version,
        "environment": settings.environment,
        "checks": checks
    }


@health_router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Kubernetes readiness probe endpoint
    """
    db_healthy = await check_database(db)
    
    if not db_healthy:
        raise HTTPException(status_code=503, detail="Database not ready")
    
    return {"status": "ready"}


@health_router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint
    """
    return {"status": "alive"}
