"""Email service for sending notifications via AWS SES with Jinja2 templates."""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config.settings import settings

logger = logging.getLogger(__name__)

# Set up Jinja2 environment
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
            "source": "email_service",
            **(properties or {})
        }
        # Use email as distinct_id since we may not have user_id in email context
        mp.track(user_email, event_name, event_properties)
        logger.debug(f"Tracked Mixpanel event: {event_name} for {user_email}")
    except Exception as e:
        logger.warning(f"Failed to track Mixpanel event: {e}")


class SESEmailService:
    """Service for sending emails via AWS SES with Jinja2 templates."""

    DEFAULT_BASE_URL = "https://hiddenjobs.me"

    def __init__(self):
        """Initialize the SES email service."""
        self.from_email = settings.ses_from_email
        self.from_name = settings.ses_from_name
        self.region = settings.aws_region

        # Initialize SES client
        try:
            self.client = boto3.client('sesv2', region_name=self.region)
            logger.info(f"SES email service initialized for region {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize SES client: {e}")
            self.client = None

    @property
    def is_configured(self) -> bool:
        """Check if SES is properly configured."""
        return self.client is not None

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
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via AWS SES.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            text_content: Plain text body (optional)

        Returns:
            Response dict with success status
        """
        if not self.is_configured:
            logger.error("SES not configured. Cannot send email.")
            return {"success": False, "error": "SES not configured"}

        try:
            # Build email content
            body = {"Html": {"Data": html_content, "Charset": "UTF-8"}}
            if text_content:
                body["Text"] = {"Data": text_content, "Charset": "UTF-8"}

            response = self.client.send_email(
                FromEmailAddress=f"{self.from_name} <{self.from_email}>",
                Destination={"ToAddresses": [to_email]},
                Content={
                    "Simple": {
                        "Subject": {"Data": subject, "Charset": "UTF-8"},
                        "Body": body
                    }
                }
            )

            message_id = response.get("MessageId")
            logger.info(f"Email sent successfully to {to_email}: {message_id}")
            return {"success": True, "id": message_id}

        except ClientError as e:
            error_msg = e.response['Error']['Message']
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            return {"success": False, "error": error_msg}
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
            jobs: List of job dictionaries with title, company_name, location, job_url, posted_date
            alert_name: Name of the alert that matched
            show_tips: Whether to show the tips section
            tip_text: Custom tip text (optional)

        Returns:
            Response dict with success status
        """
        job_count = len(jobs)
        subject = f"🎯 {job_count} new job{'s' if job_count > 1 else ''} matching '{alert_name}'"

        # Prepare template context
        context = {
            "user_name": user_name,
            "jobs": jobs,
            "job_count": job_count,
            "alert_name": alert_name,
            "show_tips": show_tips,
            "tip_text": tip_text,
        }

        # Render templates
        html_content = self.render_template("daily_digest.html", context)
        text_content = self.render_template("daily_digest.txt", context)

        result = self.send_email(to_email, subject, html_content, text_content)

        # Track email sent event in Mixpanel
        if result.get("success"):
            companies = list(set(job.get("company_name", "Unknown") for job in jobs))
            track_email_event(
                event_name="Email Sent",
                user_email=to_email,
                user_name=user_name,
                properties={
                    "email_type": "job_digest",
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
            text_content = self.render_template("welcome.txt", context)
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
            text_content = f"Welcome to HiddenJobs, {user_name or 'there'}! Start by setting up your job alerts."

        result = self.send_email(to_email, subject, html_content, text_content)

        # Track welcome email sent event in Mixpanel
        if result.get("success"):
            track_email_event(
                event_name="Email Sent",
                user_email=to_email,
                user_name=user_name,
                properties={
                    "email_type": "welcome",
                }
            )

        return result


# Singleton instance
email_service = SESEmailService()
