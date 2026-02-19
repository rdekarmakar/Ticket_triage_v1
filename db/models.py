"""
SQLAlchemy ORM models for the ticket triage system.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class AlertType(str, enum.Enum):
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    MONITORING = "monitoring"
    UNKNOWN = "unknown"


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Ticket(Base):
    """Main ticket model for storing production alerts and triage results."""

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core fields
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)
    raw_message = Column(Text, nullable=False)

    # Classification
    alert_type = Column(Enum(AlertType), default=AlertType.UNKNOWN, index=True)
    severity = Column(Enum(Severity), default=Severity.MEDIUM, index=True)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, index=True)

    # Source information
    source_system = Column(String(255), nullable=True)
    webex_room_id = Column(String(255), nullable=True)
    webex_message_id = Column(String(255), nullable=True)

    # Triage information
    suggestion = Column(Text, nullable=True)
    runbook_sources = Column(JSON, default=list)
    confidence_score = Column(String(50), nullable=True)

    # Extra data
    extra_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    comments = relationship(
        "TicketComment", back_populates="ticket", cascade="all, delete-orphan"
    )
    actions = relationship(
        "TicketAction", back_populates="ticket", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Ticket(id={self.id}, title='{self.title[:30]}...', severity={self.severity})>"


class TicketComment(Base):
    """Comments on tickets from users, Webex, or system."""

    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)
    source = Column(String(50), default="manual")  # manual, webex, llm
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="comments")

    def __repr__(self):
        return f"<TicketComment(id={self.id}, ticket_id={self.ticket_id})>"


class TicketAction(Base):
    """Audit log for ticket state changes."""

    __tablename__ = "ticket_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    performed_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="actions")

    def __repr__(self):
        return f"<TicketAction(id={self.id}, type={self.action_type})>"


class KnowledgeBaseIndex(Base):
    """Track indexed runbook files for incremental updates."""

    __tablename__ = "knowledge_base_index"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(500), unique=True, nullable=False)
    file_hash = Column(String(64), nullable=False)
    chunk_count = Column(Integer, default=0)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<KnowledgeBaseIndex(file={self.file_path})>"
