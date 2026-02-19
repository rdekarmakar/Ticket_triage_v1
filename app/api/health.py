"""
Health check endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.database import get_db_session
from config.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db_session)):
    """
    Detailed health check including dependencies.
    """
    settings = get_settings()
    health = {
        "status": "healthy",
        "version": settings.app_version,
        "components": {}
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"

    # Check Groq API (just verify key is set)
    if settings.groq_api_key:
        health["components"]["groq_api"] = {"status": "configured"}
    else:
        health["components"]["groq_api"] = {"status": "not_configured"}
        health["status"] = "degraded"

    # Check Webex (just verify token is set)
    if settings.webex_access_token:
        health["components"]["webex"] = {"status": "configured"}
    else:
        health["components"]["webex"] = {"status": "not_configured"}

    return health


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db_session)):
    """
    Readiness check for Kubernetes probes.
    Returns 200 only if the service is ready to accept traffic.
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as e:
        return {"ready": False, "error": str(e)}
