"""
Pydantic models for Webex webhook payloads.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class AlertType(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    MONITORING = "monitoring"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class WebexMessageData(BaseModel):
    """Data from Webex message webhook."""
    id: str
    roomId: str
    roomType: Optional[str] = None
    personId: Optional[str] = None
    personEmail: Optional[str] = None
    created: Optional[datetime] = None


class WebexWebhookPayload(BaseModel):
    """Webex webhook payload structure."""
    id: str
    name: str
    targetUrl: str
    resource: str
    event: str
    orgId: Optional[str] = None
    createdBy: Optional[str] = None
    appId: Optional[str] = None
    ownedBy: Optional[str] = None
    status: Optional[str] = None
    created: Optional[datetime] = None
    actorId: Optional[str] = None
    data: WebexMessageData


class ParsedAlert(BaseModel):
    """Parsed and classified alert from Webex message."""
    raw_message: str
    alert_type: AlertType = AlertType.UNKNOWN
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str
    description: str
    source_system: Optional[str] = None
    affected_component: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    # Webex context
    webex_room_id: Optional[str] = None
    webex_message_id: Optional[str] = None


class TriageResponse(BaseModel):
    """Response after triaging an alert."""
    ticket_id: int
    status: str
    summary: str
    suggestion: Optional[str] = None
    runbook_sources: list = Field(default_factory=list)
    confidence: Optional[str] = None
