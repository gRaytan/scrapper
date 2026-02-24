"""Email service for sending notifications via OneSignal API with Jinja2 templates."""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config.settings import settings

logger = logging.getLogger(__name__)

# Set up Jinja2 environment (same as email_service.py)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)

# Initialize Mixpanel for analytics tracking
_mixpanel_client = None


def get_mixpanel():
    """Get or create Mixpanel client."""
    global _mixpanel_client
    if _mixpanel_client is None and settings.mixpanel_token:
        try:
            from mixpanel import Mixpanel
            _mixpanel_client = Mixpanel(settings.mixpanel_token)
            logger.info("Mixpanel client initialized for email tracking")
        except Exception as e:
            logger.warning(f"Failed to initialize Mixpanel: {e}")
    return _mixpanel_client


def track_email_event(
    event_name: str,
    user_email: str,
    user_name: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None
):
    """Track an email event in Mixpanel."""
    mp = get_mixpanel()
    if not mp:
        return

    try:
        event_properties = {
            "user_email": user_email,
            "user_name": user_name or "Unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "onesignal_email_service",
            **(properties or {})
        }
        mp.track(user_email, event_name, event_properties)
        logger.debug(f"Tracked Mixpanel event: {event_name} for {user_email}")
    except Exception as e:
        logger.warning(f"Failed to track Mixpanel event: {e}")


class OneSignalEmailService:
    """Service for sending emails via OneSignal API with Jinja2 templates."""

    DEFAULT_BASE_URL = "https://hiddenjobs.me"
    ONESIGNAL_API_URL = "https://api.onesignal.com/notifications"
    ONESIGNAL_USERS_API_URL = "https://api.onesignal.com/apps/{app_id}/users"

    def __init__(self):
        """Initialize the OneSignal email service."""
        self.app_id = settings.onesignal_app_id
        self.api_key = settings.onesignal_api_key
        self.from_email = settings.onesignal_from_email
        self.from_name = settings.onesignal_from_name
        # Cache for subscription IDs to avoid repeated API calls
        self._subscription_cache: Dict[str, str] = {}

        if self.is_configured:
            logger.info("OneSignal email service initialized")
        else:
            logger.warning("OneSignal email service not configured (missing app_id or api_key)")

    @property
    def is_configured(self) -> bool:
        """Check if OneSignal is properly configured."""
        return bool(self.app_id and self.api_key)

    def _ensure_email_subscription(self, email: str, user_id: Optional[str] = None) -> Optional[str]:
        """
        Ensure an email is registered as a OneSignal subscription.
        Creates a new user/subscription if it doesn't exist.

        Args:
            email: The email address to register
            user_id: Optional external user ID (defaults to email)

        Returns:
            The subscription_id if successful, None otherwise
        """
        # Check cache firstdas
        if email in self._subscription_cache:
            return self._subscription_cache[email]

        if not self.is_configured:
            return None

        external_id = user_id or email

        try:
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json",
            }

            # Create user with email subscription
            payload = {
                "identity": {
                    "external_id": external_id
                },
                "subscriptions": [
                    {
                        "type": "Email",
                        "token": email,
                        "enabled": True
                    }
                ]
            }

            url = self.ONESIGNAL_USERS_API_URL.format(app_id=self.app_id)

            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)

            # 200 = success, 201 = created new user, 202 = user exists (subscription may be added/updated)
            if response.status_code in (200, 201, 202):
                data = response.json()
                # Get subscription ID from response
                subscriptions = data.get("subscriptions", [])
                for sub in subscriptions:
                    if sub.get("type") == "Email" and sub.get("token") == email:
                        subscription_id = sub.get("id")
                        if subscription_id:
                            self._subscription_cache[email] = subscription_id
                            logger.info(f"Email subscription registered: {email} -> {subscription_id}")
                            return subscription_id

                # If we got here, try to get onesignal_id as fallback
                onesignal_id = data.get("identity", {}).get("onesignal_id")
                if onesignal_id:
                    self._subscription_cache[email] = onesignal_id
                    logger.info(f"User registered with onesignal_id: {email} -> {onesignal_id}")
                    return onesignal_id

                logger.warning(f"User created but no subscription ID found for {email}")
                return None
            else:
                logger.error(f"Failed to create subscription for {email}: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.exception(f"Error creating email subscription for {email}: {e}")
            return None

    def _get_base_context(self) -> Dict[str, Any]:
        """Get base context variables for all templates."""
        return {
            "base_url": self.DEFAULT_BASE_URL,
            "current_year": datetime.utcnow().year,
        }

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render a Jinja2 template with the given context.

        Args:
            template_name: Name of the template file (e.g., 'daily_digest.html')
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template string
        """
        template = jinja_env.get_template(template_name)
        full_context = {**self._get_base_context(), **context}
        return template.render(**full_context)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via OneSignal API.

        Automatically registers the email as a subscription if not already registered.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            text_content: Plain text body (optional, not used by OneSignal)
            user_id: Optional external user ID for subscription registration

        Returns:
            Response dict with success status
        """
        if not self.is_configured:
            logger.error("OneSignal not configured. Cannot send email.")
            return {"success": False, "error": "OneSignal not configured"}

        # First, ensure the email is registered as a subscription
        subscription_id = self._ensure_email_subscription(to_email, user_id)
        if not subscription_id:
            logger.error(f"Failed to register email subscription for {to_email}")
            return {"success": False, "error": "Failed to register email subscription"}

        try:
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json",
            }

            # Use include_subscription_ids instead of email_to
            # This targets the specific subscription we just created/verified
            payload = {
                "app_id": self.app_id,
                "target_channel": "email",
                "include_subscription_ids": [subscription_id],
                "email_subject": subject,
                "email_body": html_content,
                "email_from_name": self.from_name,
                "email_from_address": self.from_email,
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.ONESIGNAL_API_URL,
                    headers=headers,
                    json=payload
                )

            if response.status_code == 200:
                data = response.json()
                notification_id = data.get("id")
                logger.info(f"Email sent successfully to {to_email} via OneSignal: {notification_id}")
                return {
                    "success": True,
                    "id": notification_id,
                    "notification_id": notification_id,  # Alias for clarity
                    "external_id": data.get("external_id"),
                    "recipients": data.get("recipients", 0)
                }
            else:
                error_msg = response.text
                logger.error(f"OneSignal API error ({response.status_code}): {error_msg}")
                return {"success": False, "error": error_msg}

        except httpx.TimeoutException:
            logger.error(f"Timeout sending email to {to_email} via OneSignal")
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            logger.exception(f"Error sending email to {to_email}: {e}")
            return {"success": False, "error": str(e)}

    def send_job_digest_email(
        self,
        to_email: str,
        user_name: str,
        jobs: List[Dict[str, Any]],
        alert_name: str,
        show_tips: bool = False,
        tip_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a job digest email with matched jobs using Jinja2 templates.

        Args:
            to_email: Recipient email address
            user_name: User's display name
            jobs: List of job dicts with title, company_name, location, job_url, posted_date
            alert_name: Name of the alert that matched
            show_tips: Whether to show the tips section
            tip_text: Custom tip text (optional)

        Returns:
            Response dict with success status
        """
        job_count = len(jobs)
        subject = f"🎯 {job_count} new job{'s' if job_count > 1 else ''} matching '{alert_name}'"

        context = {
            "user_name": user_name,
            "jobs": jobs,
            "job_count": job_count,
            "alert_name": alert_name,
            "show_tips": show_tips,
            "tip_text": tip_text,
        }

        html_content = self.render_template("daily_digest.html", context)

        result = self.send_email(to_email, subject, html_content)

        # Track email sent event in Mixpanel
        if result.get("success"):
            companies = list(set(job.get("company_name", "Unknown") for job in jobs))
            track_email_event(
                event_name="Email Sent",
                user_email=to_email,
                user_name=user_name,
                properties={
                    "email_type": "job_digest",
                    "email_provider": "onesignal",
                    "alert_name": alert_name,
                    "job_count": job_count,
                    "companies": companies,
                    "company_count": len(companies),
                }
            )

        return result

    def send_welcome_email(
        self,
        to_email: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Send a welcome email to new users.

        Args:
            to_email: Recipient email address
            user_name: User's display name

        Returns:
            Response dict with success status
        """
        subject = "🎉 Welcome to HiddenJobs!"

        context = {
            "user_name": user_name,
        }

        # Check if welcome template exists, otherwise use a simple message
        try:
            html_content = self.render_template("welcome.html", context)
        except Exception:
            # Fallback if welcome template doesn't exist yet
            html_content = f"""
            <html>
            <body style="font-family: sans-serif; padding: 20px;">
                <h1>Welcome to HiddenJobs, {user_name or 'there'}!</h1>
                <p>We're excited to have you on board.</p>
                <p>Start by setting up your job alerts to get notified about new opportunities.</p>
                <a href="{self.DEFAULT_BASE_URL}/alerts">Set up alerts</a>
            </body>
            </html>
            """

        result = self.send_email(to_email, subject, html_content)

        # Track welcome email sent event in Mixpanel
        if result.get("success"):
            track_email_event(
                event_name="Email Sent",
                user_email=to_email,
                user_name=user_name,
                properties={
                    "email_type": "welcome",
                    "email_provider": "onesignal",
                }
            )

        return result


# Singleton instance
onesignal_email_service = OneSignalEmailService()
