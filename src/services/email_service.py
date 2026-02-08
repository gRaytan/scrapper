"""Email service for sending notifications via OneSignal with Jinja2 templates."""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import httpx
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


class OneSignalEmailService:
    """Service for sending emails via OneSignal API with Jinja2 templates."""
    
    BASE_URL = "https://onesignal.com/api/v1"
    DEFAULT_BASE_URL = "https://hiddenjobs.me"
    
    def __init__(self):
        """Initialize the OneSignal email service."""
        self.app_id = settings.onesignal_app_id
        self.api_key = settings.onesignal_api_key
        self.from_email = settings.onesignal_from_email
        self.from_name = settings.onesignal_from_name
        
        if not self.app_id or not self.api_key:
            logger.warning("OneSignal credentials not configured. Email sending will be disabled.")
    
    @property
    def is_configured(self) -> bool:
        """Check if OneSignal is properly configured."""
        return bool(self.app_id and self.api_key)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for OneSignal API requests."""
        return {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
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
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via OneSignal.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            text_content: Plain text body (optional)
            
        Returns:
            Response from OneSignal API
        """
        if not self.is_configured:
            logger.error("OneSignal not configured. Cannot send email.")
            return {"success": False, "error": "OneSignal not configured"}
        
        payload = {
            "app_id": self.app_id,
            "include_email_tokens": [to_email],
            "email_subject": subject,
            "email_body": html_content,
            "email_from_address": self.from_email,
            "email_from_name": self.from_name,
        }
        
        if text_content:
            payload["email_preheader_text"] = text_content[:100]  # Preview text
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/notifications",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Email sent successfully to {to_email}: {result.get('id')}")
                    return {"success": True, "id": result.get("id"), "recipients": result.get("recipients")}
                else:
                    error_msg = response.text
                    logger.error(f"Failed to send email to {to_email}: {response.status_code} - {error_msg}")
                    return {"success": False, "error": error_msg, "status_code": response.status_code}
                    
        except Exception as e:
            logger.exception(f"Error sending email to {to_email}: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_job_digest_email(
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
            Response from OneSignal API
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
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_welcome_email(
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
            Response from OneSignal API
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
        
        return await self.send_email(to_email, subject, html_content, text_content)


# Singleton instance
email_service = OneSignalEmailService()
