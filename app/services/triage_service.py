"""
Core triage service that orchestrates alert processing.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.webhook import ParsedAlert, AlertType, AlertSeverity
from db.models import Ticket, AlertType as DBAlertType, Severity as DBSeverity
from db.repository import TicketRepository
from knowledge_base.indexer import KnowledgeBaseIndexer
from knowledge_base.vector_store import SearchResult
from llm.groq_client import GroqClient
from config.settings import get_settings


class TriageService:
    """
    Service that orchestrates the triage pipeline:
    1. Parse and classify alerts
    2. Search knowledge base for relevant runbooks
    3. Generate triage suggestions via LLM
    4. Store tickets with suggestions
    """

    def __init__(
        self,
        db: Session,
        groq_client: Optional[GroqClient] = None,
        indexer: Optional[KnowledgeBaseIndexer] = None
    ):
        """
        Initialize the triage service.

        Args:
            db: Database session
            groq_client: Groq LLM client (optional, will create default)
            indexer: Knowledge base indexer (optional, will create default)
        """
        self.db = db
        self.ticket_repo = TicketRepository(db)
        self.groq = groq_client or GroqClient()
        self.indexer = indexer or KnowledgeBaseIndexer()
        self.settings = get_settings()

    def process_alert(
        self,
        raw_message: str,
        webex_room_id: Optional[str] = None,
        webex_message_id: Optional[str] = None
    ) -> Ticket:
        """
        Full triage pipeline for an alert.

        Args:
            raw_message: Raw alert text
            webex_room_id: Optional Webex room ID
            webex_message_id: Optional Webex message ID

        Returns:
            Created ticket with triage suggestion
        """
        # Step 1: Classify the alert
        parsed_alert = self.classify_alert(raw_message)
        parsed_alert.webex_room_id = webex_room_id
        parsed_alert.webex_message_id = webex_message_id

        # Step 2: Search knowledge base
        search_results = self.search_runbooks(parsed_alert)

        # Step 3: Generate triage suggestion
        suggestion, confidence = self.generate_suggestion(
            parsed_alert, search_results
        )

        # Step 4: Create ticket
        ticket = self.create_ticket(
            parsed_alert=parsed_alert,
            suggestion=suggestion,
            runbook_sources=[r.source_file for r in search_results],
            confidence_score=confidence
        )

        return ticket

    def classify_alert(self, raw_message: str) -> ParsedAlert:
        """
        Classify an alert using LLM.

        Args:
            raw_message: Raw alert text

        Returns:
            ParsedAlert with classification
        """
        classification = self.groq.classify_alert(raw_message)

        # Map string values to enums
        alert_type = AlertType.UNKNOWN
        try:
            alert_type = AlertType(classification.get("alert_type", "unknown"))
        except ValueError:
            pass

        severity = AlertSeverity.MEDIUM
        try:
            severity = AlertSeverity(classification.get("severity", "medium"))
        except ValueError:
            pass

        return ParsedAlert(
            raw_message=raw_message,
            alert_type=alert_type,
            severity=severity,
            title=classification.get("title", raw_message[:100]),
            description=raw_message,
            source_system=classification.get("source_system"),
            affected_component=classification.get("affected_component"),
            timestamp=datetime.utcnow()
        )

    def search_runbooks(
        self,
        alert: ParsedAlert,
        n_results: int = None
    ) -> List[SearchResult]:
        """
        Search knowledge base for relevant runbooks.

        Args:
            alert: Parsed alert
            n_results: Number of results to return

        Returns:
            List of search results
        """
        n_results = n_results or self.settings.search_results_limit

        # Build search query from alert
        search_query = f"{alert.title} {alert.description}"

        # Filter by alert type if available
        filter_type = None
        if alert.alert_type != AlertType.UNKNOWN:
            filter_type = alert.alert_type.value

        return self.indexer.search(
            query=search_query,
            n_results=n_results,
            filter_type=filter_type,
            min_score=self.settings.min_similarity_score
        )

    def generate_suggestion(
        self,
        alert: ParsedAlert,
        search_results: List[SearchResult]
    ) -> tuple[str, str]:
        """
        Generate triage suggestion using LLM.

        Args:
            alert: Parsed alert
            search_results: Relevant runbook sections

        Returns:
            Tuple of (suggestion text, confidence level)
        """
        # Format runbook context
        runbook_context = self._format_runbook_context(search_results)

        # Generate suggestion
        suggestion = self.groq.generate_triage(
            alert_title=alert.title,
            alert_type=alert.alert_type.value,
            severity=alert.severity.value,
            description=alert.description,
            source_system=alert.source_system or "Unknown",
            timestamp=alert.timestamp.isoformat(),
            runbook_context=runbook_context
        )

        # Extract confidence from suggestion (if present)
        confidence = "Medium"
        if "High" in suggestion and "Confidence" in suggestion:
            confidence = "High"
        elif "Low" in suggestion and "Confidence" in suggestion:
            confidence = "Low"

        return suggestion, confidence

    def create_ticket(
        self,
        parsed_alert: ParsedAlert,
        suggestion: str,
        runbook_sources: List[str],
        confidence_score: Optional[str] = None
    ) -> Ticket:
        """
        Create a ticket from a parsed alert.

        Args:
            parsed_alert: Parsed and classified alert
            suggestion: LLM-generated suggestion
            runbook_sources: List of runbook files used
            confidence_score: Confidence level

        Returns:
            Created ticket
        """
        # Map alert types to DB enums
        db_alert_type = DBAlertType.UNKNOWN
        try:
            db_alert_type = DBAlertType(parsed_alert.alert_type.value)
        except ValueError:
            pass

        db_severity = DBSeverity.MEDIUM
        try:
            db_severity = DBSeverity(parsed_alert.severity.value)
        except ValueError:
            pass

        return self.ticket_repo.create(
            title=parsed_alert.title,
            description=parsed_alert.description,
            raw_message=parsed_alert.raw_message,
            alert_type=db_alert_type,
            severity=db_severity,
            source_system=parsed_alert.source_system,
            webex_room_id=parsed_alert.webex_room_id,
            webex_message_id=parsed_alert.webex_message_id,
            suggestion=suggestion,
            runbook_sources=runbook_sources,
            confidence_score=confidence_score,
            extra_data={
                "affected_component": parsed_alert.affected_component,
                "timestamp": parsed_alert.timestamp.isoformat()
            }
        )

    def quick_triage(self, alert_text: str) -> dict:
        """
        Quick triage without creating a ticket.
        Useful for CLI queries.

        Args:
            alert_text: Alert text to triage

        Returns:
            Dictionary with triage information
        """
        # Classify
        parsed = self.classify_alert(alert_text)

        # Search
        results = self.search_runbooks(parsed)

        # Generate suggestion
        suggestion, confidence = self.generate_suggestion(parsed, results)

        return {
            "classification": {
                "alert_type": parsed.alert_type.value,
                "severity": parsed.severity.value,
                "title": parsed.title,
                "source_system": parsed.source_system,
                "affected_component": parsed.affected_component
            },
            "runbook_sources": [
                {"file": r.source_file, "section": r.section, "score": r.score}
                for r in results
            ],
            "suggestion": suggestion,
            "confidence": confidence
        }

    def _format_runbook_context(self, results: List[SearchResult]) -> str:
        """Format search results as context for LLM."""
        if not results:
            return "No relevant runbook sections found. Please use general troubleshooting practices."

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"### Source {i}: {result.source_file} (Relevance: {result.score:.0%})\n"
                f"{result.content}\n"
            )

        return "\n".join(context_parts)
