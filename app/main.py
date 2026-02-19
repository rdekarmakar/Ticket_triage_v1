"""
Main FastAPI application entry point.
"""

from typing import Optional
from fastapi import FastAPI, Request, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api import webhooks, tickets, health
from app.core.security import get_current_user
from db.database import get_db_session, init_db
from db.repository import TicketRepository
from config.settings import get_settings

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production Issues Ticket Triage System"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(health.router)
app.include_router(webhooks.router)
app.include_router(tickets.router)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print(f"{settings.app_name} v{settings.app_version} started")


# Root redirect
@app.get("/")
async def root():
    """Redirect root to dashboard."""
    return RedirectResponse(url="/dashboard")


# Dashboard routes (protected by basic auth)
@app.get("/dashboard")
async def dashboard(
    request: Request,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Main dashboard view."""
    repo = TicketRepository(db)
    tickets = repo.get_recent(limit=20)
    stats = repo.get_stats()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "tickets": tickets,
            "stats": stats,
            "username": username,
            "active_page": "dashboard"
        }
    )


@app.get("/dashboard/tickets")
async def tickets_list(
    request: Request,
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """All tickets list view with filtering."""
    from db.models import TicketStatus, Severity, AlertType

    repo = TicketRepository(db)

    # Convert string params to enums
    db_status = None
    if status:
        try:
            db_status = TicketStatus(status)
        except ValueError:
            pass

    db_severity = None
    if severity:
        try:
            db_severity = Severity(severity)
        except ValueError:
            pass

    db_alert_type = None
    if alert_type:
        try:
            db_alert_type = AlertType(alert_type)
        except ValueError:
            pass

    tickets = repo.get_all(
        limit=100,
        status=db_status,
        severity=db_severity,
        alert_type=db_alert_type
    )

    return templates.TemplateResponse(
        "tickets_list.html",
        {
            "request": request,
            "tickets": tickets,
            "username": username,
            "active_page": "tickets",
            "current_status": status,
            "current_severity": severity,
            "current_type": alert_type
        }
    )


@app.get("/dashboard/ticket/{ticket_id}")
async def ticket_detail(
    request: Request,
    ticket_id: int,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Single ticket detail view."""
    repo = TicketRepository(db)
    ticket = repo.get(ticket_id)

    if not ticket:
        return RedirectResponse(url="/dashboard")

    return templates.TemplateResponse(
        "ticket_detail.html",
        {
            "request": request,
            "ticket": ticket,
            "username": username,
            "active_page": "tickets"
        }
    )


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
