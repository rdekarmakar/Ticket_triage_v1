"""
Ticket management REST API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketListResponse,
    TicketStats,
    CommentCreate,
    CommentResponse,
    TicketStatus,
    AlertType,
    Severity
)
from db.database import get_db_session
from db.repository import TicketRepository
from db.models import TicketStatus as DBTicketStatus, AlertType as DBAlertType, Severity as DBSeverity

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("", response_model=TicketListResponse)
def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session)
):
    """List tickets with optional filtering."""
    repo = TicketRepository(db)

    # Convert string params to enums
    db_status = None
    if status:
        try:
            db_status = DBTicketStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    db_severity = None
    if severity:
        try:
            db_severity = DBSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    db_alert_type = None
    if alert_type:
        try:
            db_alert_type = DBAlertType(alert_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid alert_type: {alert_type}")

    tickets = repo.get_all(
        limit=limit,
        offset=offset,
        status=db_status,
        severity=db_severity,
        alert_type=db_alert_type
    )

    return TicketListResponse(
        tickets=[TicketResponse.model_validate(t) for t in tickets],
        total=len(tickets)
    )


@router.get("/stats", response_model=TicketStats)
def get_stats(db: Session = Depends(get_db_session)):
    """Get ticket statistics."""
    repo = TicketRepository(db)
    return repo.get_stats()


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db_session)):
    """Get a single ticket by ID."""
    repo = TicketRepository(db)
    ticket = repo.get(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return TicketResponse.model_validate(ticket)


@router.post("", response_model=TicketResponse, status_code=201)
def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new ticket manually."""
    repo = TicketRepository(db)

    # Convert Pydantic enums to DB enums
    db_alert_type = DBAlertType(ticket_data.alert_type.value)
    db_severity = DBSeverity(ticket_data.severity.value)

    ticket = repo.create(
        title=ticket_data.title,
        description=ticket_data.description,
        raw_message=ticket_data.raw_message,
        alert_type=db_alert_type,
        severity=db_severity,
        source_system=ticket_data.source_system,
        webex_room_id=ticket_data.webex_room_id,
        webex_message_id=ticket_data.webex_message_id,
        extra_data=ticket_data.extra_data or {}
    )

    return TicketResponse.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    update_data: TicketUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a ticket."""
    repo = TicketRepository(db)
    ticket = repo.get(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Update status if provided
    if update_data.status:
        db_status = DBTicketStatus(update_data.status.value)
        repo.update_status(ticket_id, db_status)

    # Update suggestion if provided
    if update_data.suggestion:
        repo.update_suggestion(
            ticket_id,
            suggestion=update_data.suggestion,
            runbook_sources=update_data.runbook_sources or [],
            confidence_score=update_data.confidence_score
        )

    # Refresh and return
    ticket = repo.get(ticket_id)
    return TicketResponse.model_validate(ticket)


@router.delete("/{ticket_id}", status_code=204)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db_session)):
    """Delete a ticket."""
    repo = TicketRepository(db)

    if not repo.delete(ticket_id):
        raise HTTPException(status_code=404, detail="Ticket not found")


@router.post("/{ticket_id}/comments", response_model=CommentResponse, status_code=201)
def add_comment(
    ticket_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db_session)
):
    """Add a comment to a ticket."""
    repo = TicketRepository(db)

    comment = repo.add_comment(
        ticket_id=ticket_id,
        content=comment_data.content,
        author=comment_data.author,
        source=comment_data.source
    )

    if not comment:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return CommentResponse.model_validate(comment)


@router.post("/{ticket_id}/triage", response_model=TicketResponse)
def retriage_ticket(ticket_id: int, db: Session = Depends(get_db_session)):
    """Re-run triage on an existing ticket."""
    from app.services.triage_service import TriageService

    repo = TicketRepository(db)
    ticket = repo.get(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Re-triage using the raw message
    triage_service = TriageService(db)
    result = triage_service.quick_triage(ticket.raw_message)

    # Update ticket with new suggestion
    repo.update_suggestion(
        ticket_id,
        suggestion=result["suggestion"],
        runbook_sources=[s["file"] for s in result["runbook_sources"]],
        confidence_score=result["confidence"]
    )

    ticket = repo.get(ticket_id)
    return TicketResponse.model_validate(ticket)
