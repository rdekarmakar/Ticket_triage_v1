"""
Webex API service for sending and receiving messages.
"""

from typing import Optional
import httpx

from config.settings import get_settings


class WebexService:
    """Service for Webex API interactions."""

    BASE_URL = "https://webexapis.com/v1"

    def __init__(
        self,
        access_token: Optional[str] = None,
        bot_token: Optional[str] = None
    ):
        """
        Initialize the Webex service.

        Args:
            access_token: Webex access token for reading messages
            bot_token: Webex bot token for sending messages
        """
        settings = get_settings()
        self.access_token = access_token or settings.webex_access_token
        self.bot_token = bot_token or settings.webex_bot_token

    def _get_headers(self, use_bot: bool = False) -> dict:
        """Get authorization headers."""
        token = self.bot_token if use_bot and self.bot_token else self.access_token
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def get_message(self, message_id: str) -> dict:
        """
        Get a message by ID.

        Args:
            message_id: Webex message ID

        Returns:
            Message data
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/messages/{message_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def send_message(
        self,
        room_id: str,
        text: str,
        markdown: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> dict:
        """
        Send a message to a Webex room.

        Args:
            room_id: Room to send to
            text: Plain text message
            markdown: Optional markdown formatted message
            parent_id: Optional parent message ID for threading

        Returns:
            Sent message data
        """
        payload = {
            "roomId": room_id,
            "text": text
        }

        if markdown:
            payload["markdown"] = markdown

        if parent_id:
            payload["parentId"] = parent_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/messages",
                headers=self._get_headers(use_bot=True),
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def send_triage_response(
        self,
        room_id: str,
        ticket_id: int,
        title: str,
        severity: str,
        suggestion: str,
        runbook_sources: list,
        parent_id: Optional[str] = None
    ) -> dict:
        """
        Send a formatted triage response to Webex.

        Args:
            room_id: Room to send to
            ticket_id: Created ticket ID
            title: Alert title
            severity: Severity level
            suggestion: Triage suggestion
            runbook_sources: List of runbook files used
            parent_id: Optional parent message for threading

        Returns:
            Sent message data
        """
        # Format markdown response
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵"
        }
        emoji = severity_emoji.get(severity.lower(), "⚪")

        sources_text = ""
        if runbook_sources:
            sources_text = "\n**Runbook References:**\n" + "\n".join(
                f"- {src}" for src in runbook_sources[:3]
            )

        markdown = f"""
{emoji} **Triage Response** | Ticket #{ticket_id}

**Alert:** {title}
**Severity:** {severity.upper()}

---

{suggestion}

{sources_text}

---
*View full details in the dashboard*
"""

        plain_text = f"Triage Response for: {title} (Ticket #{ticket_id})"

        return await self.send_message(
            room_id=room_id,
            text=plain_text,
            markdown=markdown.strip(),
            parent_id=parent_id
        )

    def get_message_sync(self, message_id: str) -> dict:
        """
        Synchronous version of get_message.

        Args:
            message_id: Webex message ID

        Returns:
            Message data
        """
        with httpx.Client() as client:
            response = client.get(
                f"{self.BASE_URL}/messages/{message_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    def send_message_sync(
        self,
        room_id: str,
        text: str,
        markdown: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> dict:
        """
        Synchronous version of send_message.

        Args:
            room_id: Room to send to
            text: Plain text message
            markdown: Optional markdown formatted message
            parent_id: Optional parent message ID for threading

        Returns:
            Sent message data
        """
        payload = {
            "roomId": room_id,
            "text": text
        }

        if markdown:
            payload["markdown"] = markdown

        if parent_id:
            payload["parentId"] = parent_id

        with httpx.Client() as client:
            response = client.post(
                f"{self.BASE_URL}/messages",
                headers=self._get_headers(use_bot=True),
                json=payload
            )
            response.raise_for_status()
            return response.json()
