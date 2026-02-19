"""
Pydantic models for tickets.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class AlertType(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    MONITORING = "monitoring"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TicketCreate(BaseModel):
    """Schema for creating a ticket."""
    title: str = Field(..., max_length=500)
    description: str
    raw_message: str
    alert_type: AlertType = AlertType.UNKNOWN
    severity: Severity = Severity.MEDIUM
    source_system: Optional[str] = None
    webex_room_id: Optional[str] = None
    webex_message_id: Optional[str] = None
    extra_data: Optional[dict] = None


class TicketUpdate(BaseModel):
    """Schema for updating a ticket."""
    status: Optional[TicketStatus] = None
    severity: Optional[Severity] = None
    suggestion: Optional[str] = None
    runbook_sources: Optional[List[str]] = None
    confidence_score: Optional[str] = None


class TicketResponse(BaseModel):
    """Schema for ticket response."""
    id: int
    title: str
    description: str
    raw_message: str
    alert_type: AlertType
    severity: Severity
    status: TicketStatus
    source_system: Optional[str]
    webex_room_id: Optional[str]
    webex_message_id: Optional[str]
    suggestion: Optional[str]
    runbook_sources: List[str]
    confidence_score: Optional[str]
    extra_data: dict
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    """Schema for list of tickets."""
    tickets: List[TicketResponse]
    total: int


class TicketStats(BaseModel):
    """Schema for ticket statistics."""
    total: int
    open_count: int
    critical_count: int
    high_count: int
    by_status: dict
    by_severity: dict


class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    content: str
    author: Optional[str] = None
    source: str = "manual"


class CommentResponse(BaseModel):
    """Schema for comment response."""
    id: int
    ticket_id: int
    content: str
    author: Optional[str]
    source: str
    created_at: datetime

    class Config:
        from_attributes = True
