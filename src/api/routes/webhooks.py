"""Webhook API endpoints for external service callbacks."""
import logging
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Header, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.storage.database import db
from src.models.alert_notification import AlertNotification
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class OneSignalWebhookEvent(BaseModel):
    """Schema for OneSignal webhook event."""
    event: str  # e.g., "email.delivered", "email.opened", "email.clicked", "email.bounced"
    notification_id: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    timestamp: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# Mapping of OneSignal event types to our delivery status
EVENT_TO_STATUS = {
    "email.sent": "sent",
    "email.delivered": "delivered",
    "email.opened": "delivered",  # Keep as delivered, but track engagement
    "email.clicked": "delivered",  # Keep as delivered, but track engagement
    "email.bounced": "bounced",
    "email.dropped": "failed",
    "email.spam_report": "failed",
    "email.unsubscribed": "delivered",  # Still delivered, user opted out after
}


def get_db_session():
    """Dependency to get database session."""
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()


def track_webhook_event(event_type: str, email: str, notification_id: str, properties: Dict[str, Any] = None):
    """Track webhook event in Mixpanel."""
    try:
        from src.services.onesignal_email_service import track_email_event
        track_email_event(
            event_name=f"Email {event_type.replace('email.', '').title()}",
            user_email=email,
            properties={
                "notification_id": notification_id,
                "event_type": event_type,
                "source": "onesignal_webhook",
                **(properties or {})
            }
        )
    except Exception as e:
        logger.warning(f"Failed to track webhook event in Mixpanel: {e}")


@router.post("/onesignal", status_code=status.HTTP_200_OK)
async def handle_onesignal_webhook(
    request: Request,
    x_onesignal_signature: Optional[str] = Header(None, alias="X-OneSignal-Signature")
):
    """
    Handle OneSignal webhook events for email delivery tracking.
    
    OneSignal can send events for:
    - email.delivered - Email was delivered to recipient's mail server
    - email.opened - Recipient opened the email
    - email.clicked - Recipient clicked a link in the email
    - email.bounced - Email bounced
    - email.dropped - Email was dropped
    - email.spam_report - Email was reported as spam
    - email.unsubscribed - Recipient unsubscribed
    
    Configure webhook in OneSignal dashboard: Settings > Email > Webhooks
    """
    try:
        body = await request.body()
        payload = await request.json()
        
        logger.info(f"Received OneSignal webhook: {payload.get('event', 'unknown')}")
        
        # Validate signature if webhook secret is configured
        # OneSignal uses HMAC SHA-256 for webhook signatures
        webhook_secret = getattr(settings, 'onesignal_webhook_secret', None)
        if webhook_secret and x_onesignal_signature:
            expected_signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(expected_signature, x_onesignal_signature):
                logger.warning("Invalid OneSignal webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        event_type = payload.get("event", "")
        notification_id = payload.get("notification_id") or payload.get("id")
        email = payload.get("email") or payload.get("recipient")
        
        if not notification_id:
            logger.debug("Webhook received without notification_id, acknowledging")
            return {"status": "ok", "message": "No notification_id provided"}
        
        # Map event to delivery status
        new_status = EVENT_TO_STATUS.get(event_type)
        
        if not new_status:
            logger.debug(f"Unknown event type: {event_type}, acknowledging")
            return {"status": "ok", "message": f"Unknown event type: {event_type}"}
        
        # Update AlertNotification if we have one for this notification_id
        session = db.SessionLocal()
        try:
            notification = session.query(AlertNotification).filter(
                AlertNotification.external_notification_id == notification_id
            ).first()
            
            if notification:
                # Only update status if it's a "progression" (don't downgrade delivered -> sent)
                status_order = ["pending", "sent", "delivered", "bounced", "failed"]
                current_idx = status_order.index(notification.delivery_status) if notification.delivery_status in status_order else 0
                new_idx = status_order.index(new_status) if new_status in status_order else 0
                
                if new_idx > current_idx or new_status in ["bounced", "failed"]:
                    notification.delivery_status = new_status
                    session.commit()
                    logger.info(f"Updated notification {notification.id} status to {new_status}")
            else:
                logger.debug(f"No AlertNotification found for external_id: {notification_id}")
            
            # Track engagement events in Mixpanel
            if email and event_type in ["email.opened", "email.clicked"]:
                track_webhook_event(event_type, email, notification_id, payload.get("data"))
                
        finally:
            session.close()
        
        return {"status": "ok", "event": event_type, "processed": True}
        
    except Exception as e:
        logger.exception(f"Error processing OneSignal webhook: {e}")
        # Return 200 to prevent retries for malformed payloads
        return {"status": "error", "message": str(e)}

