"""
Webex webhook endpoints for receiving alerts.
"""

import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from app.models.webhook import WebexWebhookPayload, TriageResponse
from app.services.triage_service import TriageService
from app.services.webex_service import WebexService
from db.database import get_db_session
from config.settings import get_settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """
    Verify Webex webhook signature.

    Args:
        body: Request body bytes
        signature: X-Spark-Signature header value
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    if not secret:
        return True  # Skip verification if no secret configured

    expected = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha1
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@router.post("/webex", response_model=TriageResponse)
async def handle_webex_webhook(
    request: Request,
    x_spark_signature: str = Header(None, alias="X-Spark-Signature"),
    db: Session = Depends(get_db_session)
):
    """
    Receive and process Webex webhook events.

    This endpoint:
    1. Validates the webhook signature
    2. Fetches the full message content
    3. Processes the alert through the triage pipeline
    4. Sends a response back to Webex
    """
    settings = get_settings()
    body = await request.body()

    # Verify webhook signature
    if settings.webex_webhook_secret:
        if not x_spark_signature:
            raise HTTPException(status_code=401, detail="Missing signature")

        if not verify_webhook_signature(body, x_spark_signature, settings.webex_webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse webhook payload
    try:
        payload = WebexWebhookPayload.model_validate_json(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")

    # Get full message content (webhook only contains metadata)
    webex_service = WebexService()

    try:
        message = await webex_service.get_message(payload.data.id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch message: {str(e)}")

    message_text = message.get("text", "")
    if not message_text:
        raise HTTPException(status_code=400, detail="Empty message")

    # Process through triage pipeline
    triage_service = TriageService(db)

    try:
        ticket = triage_service.process_alert(
            raw_message=message_text,
            webex_room_id=payload.data.roomId,
            webex_message_id=payload.data.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage failed: {str(e)}")

    # Send response back to Webex
    try:
        await webex_service.send_triage_response(
            room_id=payload.data.roomId,
            ticket_id=ticket.id,
            title=ticket.title,
            severity=ticket.severity.value,
            suggestion=ticket.suggestion or "No suggestion available",
            runbook_sources=ticket.runbook_sources or [],
            parent_id=payload.data.id
        )
    except Exception as e:
        # Log but don't fail - ticket was created successfully
        print(f"Warning: Failed to send Webex response: {e}")

    return TriageResponse(
        ticket_id=ticket.id,
        status="processed",
        summary=f"Created ticket #{ticket.id} for: {ticket.title}",
        suggestion=ticket.suggestion,
        runbook_sources=ticket.runbook_sources or [],
        confidence=ticket.confidence_score
    )


@router.post("/webex/test")
async def test_webhook(request: Request):
    """
    Test endpoint to verify webhook connectivity.
    Returns the received payload without processing.
    """
    body = await request.body()
    return {
        "status": "received",
        "body_length": len(body),
        "content_type": request.headers.get("content-type")
    }
