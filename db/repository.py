"""
Data access layer with CRUD operations for tickets.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from db.models import Ticket, TicketComment, TicketAction, TicketStatus, AlertType, Severity


class TicketRepository:
    """Repository for ticket CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        title: str,
        description: str,
        raw_message: str,
        alert_type: AlertType = AlertType.UNKNOWN,
        severity: Severity = Severity.MEDIUM,
        source_system: Optional[str] = None,
        webex_room_id: Optional[str] = None,
        webex_message_id: Optional[str] = None,
        suggestion: Optional[str] = None,
        runbook_sources: Optional[List[str]] = None,
        confidence_score: Optional[str] = None,
        extra_data: Optional[dict] = None
    ) -> Ticket:
        """Create a new ticket."""
        ticket = Ticket(
            title=title,
            description=description,
            raw_message=raw_message,
            alert_type=alert_type,
            severity=severity,
            source_system=source_system,
            webex_room_id=webex_room_id,
            webex_message_id=webex_message_id,
            suggestion=suggestion,
            runbook_sources=runbook_sources or [],
            confidence_score=confidence_score,
            extra_data=extra_data or {}
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        # Log creation action
        self._log_action(ticket.id, "created", None, "open", "system")

        return ticket

    def get(self, ticket_id: int) -> Optional[Ticket]:
        """Get a ticket by ID."""
        return self.db.query(Ticket).filter(Ticket.id == ticket_id).first()

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[TicketStatus] = None,
        severity: Optional[Severity] = None,
        alert_type: Optional[AlertType] = None
    ) -> List[Ticket]:
        """Get tickets with optional filtering."""
        query = self.db.query(Ticket)

        if status:
            query = query.filter(Ticket.status == status)
        if severity:
            query = query.filter(Ticket.severity == severity)
        if alert_type:
            query = query.filter(Ticket.alert_type == alert_type)

        return query.order_by(desc(Ticket.created_at)).offset(offset).limit(limit).all()

    def get_recent(self, limit: int = 50) -> List[Ticket]:
        """Get most recent tickets."""
        return (
            self.db.query(Ticket)
            .order_by(desc(Ticket.created_at))
            .limit(limit)
            .all()
        )

    def get_open_tickets(self) -> List[Ticket]:
        """Get all open tickets ordered by severity."""
        severity_order = {
            Severity.CRITICAL: 1,
            Severity.HIGH: 2,
            Severity.MEDIUM: 3,
            Severity.LOW: 4,
            Severity.INFO: 5
        }
        tickets = (
            self.db.query(Ticket)
            .filter(Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS]))
            .all()
        )
        return sorted(tickets, key=lambda t: severity_order.get(t.severity, 99))

    def update(
        self,
        ticket_id: int,
        status: Optional[TicketStatus] = None,
        severity: Optional[Severity] = None,
        performed_by: str = "system"
    ) -> Optional[Ticket]:
        """Update ticket fields."""
        ticket = self.get(ticket_id)
        if not ticket:
            return None

        if status is not None:
            old_status = ticket.status
            ticket.status = status
            self._log_action(
                ticket_id, "status_changed",
                old_status.value, status.value, performed_by
            )
            if status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.utcnow()

        if severity is not None:
            old_severity = ticket.severity
            ticket.severity = severity
            self._log_action(
                ticket_id, "severity_changed",
                old_severity.value, severity.value, performed_by
            )

        ticket.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def update_status(
        self,
        ticket_id: int,
        new_status: TicketStatus,
        performed_by: str = "system"
    ) -> Optional[Ticket]:
        """Update ticket status."""
        return self.update(ticket_id, status=new_status, performed_by=performed_by)

    def update_suggestion(
        self,
        ticket_id: int,
        suggestion: str,
        runbook_sources: List[str],
        confidence_score: Optional[str] = None
    ) -> Optional[Ticket]:
        """Update ticket with triage suggestion."""
        ticket = self.get(ticket_id)
        if not ticket:
            return None

        ticket.suggestion = suggestion
        ticket.runbook_sources = runbook_sources
        ticket.confidence_score = confidence_score
        ticket.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def delete(self, ticket_id: int) -> bool:
        """Delete a ticket."""
        ticket = self.get(ticket_id)
        if not ticket:
            return False

        self.db.delete(ticket)
        self.db.commit()
        return True

    def add_comment(
        self,
        ticket_id: int,
        content: str,
        author: Optional[str] = None,
        source: str = "manual"
    ) -> Optional[TicketComment]:
        """Add a comment to a ticket."""
        ticket = self.get(ticket_id)
        if not ticket:
            return None

        comment = TicketComment(
            ticket_id=ticket_id,
            content=content,
            author=author,
            source=source
        )
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def get_stats(self) -> dict:
        """Get ticket statistics for dashboard."""
        total = self.db.query(Ticket).count()

        status_counts = {}
        for status in TicketStatus:
            count = self.db.query(Ticket).filter(Ticket.status == status).count()
            status_counts[status.value] = count

        severity_counts = {}
        for severity in Severity:
            count = self.db.query(Ticket).filter(Ticket.severity == severity).count()
            severity_counts[severity.value] = count

        open_count = status_counts.get("open", 0) + status_counts.get("in_progress", 0)

        return {
            "total": total,
            "open_count": open_count,
            "critical_count": severity_counts.get("critical", 0),
            "high_count": severity_counts.get("high", 0),
            "by_status": status_counts,
            "by_severity": severity_counts
        }

    def _log_action(
        self,
        ticket_id: int,
        action_type: str,
        old_value: Optional[str],
        new_value: Optional[str],
        performed_by: str
    ):
        """Log an action on a ticket."""
        action = TicketAction(
            ticket_id=ticket_id,
            action_type=action_type,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by
        )
        self.db.add(action)
