"""Email service for sending notifications via OneSignal."""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


class OneSignalEmailService:
    """Service for sending emails via OneSignal API."""
    
    BASE_URL = "https://onesignal.com/api/v1"
    
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
        alert_name: str
    ) -> Dict[str, Any]:
        """
        Send a job digest email with matched jobs.
        
        Args:
            to_email: Recipient email address
            user_name: User's display name
            jobs: List of job dictionaries with title, company, location, url
            alert_name: Name of the alert that matched
            
        Returns:
            Response from OneSignal API
        """
        subject = f"🎯 {len(jobs)} new job{'s' if len(jobs) > 1 else ''} matching '{alert_name}'"
        
        html_content = self._render_digest_html(user_name, jobs, alert_name)
        text_content = self._render_digest_text(user_name, jobs, alert_name)
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    def _render_digest_html(
        self,
        user_name: str,
        jobs: List[Dict[str, Any]],
        alert_name: str
    ) -> str:
        """Render HTML email template for job digest."""
        jobs_html = ""
        for job in jobs[:20]:  # Limit to 20 jobs per email
            company = job.get('company_name', 'Unknown Company')
            title = job.get('title', 'Unknown Position')
            location = job.get('location', 'Location not specified')
            url = job.get('job_url', '#')
            posted = job.get('posted_date', '')
            
            jobs_html += f"""
            <tr>
                <td style="padding: 16px; border-bottom: 1px solid #e5e7eb;">
                    <a href="{url}" style="color: #2563eb; text-decoration: none; font-weight: 600; font-size: 16px;">
                        {title}
                    </a>
                    <div style="color: #374151; margin-top: 4px;">{company}</div>
                    <div style="color: #6b7280; font-size: 14px; margin-top: 2px;">
                        📍 {location}
                        {f' • 📅 {posted}' if posted else ''}
                    </div>
                </td>
            </tr>
            """
        
        more_jobs_note = ""
        if len(jobs) > 20:
            more_jobs_note = f"""
            <tr>
                <td style="padding: 16px; text-align: center; color: #6b7280;">
                    ... and {len(jobs) - 20} more jobs. 
                    <a href="https://hiddenjobs.me/jobs" style="color: #2563eb;">View all on HiddenJobs</a>
                </td>
            </tr>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); padding: 24px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px;">🎯 HiddenJobs Alert</h1>
                        </td>
                    </tr>
                    
                    <!-- Greeting -->
                    <tr>
                        <td style="padding: 24px 24px 16px;">
                            <p style="margin: 0; color: #374151; font-size: 16px;">
                                Hi {user_name or 'there'},
                            </p>
                            <p style="margin: 12px 0 0; color: #374151; font-size: 16px;">
                                We found <strong>{len(jobs)} new job{'s' if len(jobs) > 1 else ''}</strong> matching your alert "<strong>{alert_name}</strong>":
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Jobs List -->
                    <tr>
                        <td style="padding: 0 24px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                                {jobs_html}
                                {more_jobs_note}
                            </table>
                        </td>
                    </tr>
                    
                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 24px; text-align: center;">
                            <a href="https://hiddenjobs.me/jobs" style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 12px 32px; border-radius: 6px; text-decoration: none; font-weight: 600;">
                                View All Jobs
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 16px 24px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                You're receiving this because you have job alerts enabled on HiddenJobs.
                            </p>
                            <p style="margin: 8px 0 0; color: #6b7280; font-size: 12px;">
                                <a href="https://hiddenjobs.me/settings/alerts" style="color: #2563eb;">Manage alerts</a> • 
                                <a href="https://hiddenjobs.me/settings/notifications" style="color: #2563eb;">Unsubscribe</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
    
    def _render_digest_text(
        self,
        user_name: str,
        jobs: List[Dict[str, Any]],
        alert_name: str
    ) -> str:
        """Render plain text email for job digest."""
        lines = [
            f"Hi {user_name or 'there'},",
            "",
            f"We found {len(jobs)} new job{'s' if len(jobs) > 1 else ''} matching your alert \"{alert_name}\":",
            "",
        ]
        
        for job in jobs[:20]:
            company = job.get('company_name', 'Unknown Company')
            title = job.get('title', 'Unknown Position')
            location = job.get('location', 'Location not specified')
            url = job.get('job_url', '')
            
            lines.append(f"• {title} at {company}")
            lines.append(f"  📍 {location}")
            if url:
                lines.append(f"  🔗 {url}")
            lines.append("")
        
        if len(jobs) > 20:
            lines.append(f"... and {len(jobs) - 20} more jobs.")
            lines.append("")
        
        lines.extend([
            "View all jobs: https://hiddenjobs.me/jobs",
            "",
            "---",
            "Manage alerts: https://hiddenjobs.me/settings/alerts",
            "Unsubscribe: https://hiddenjobs.me/settings/notifications",
        ])
        
        return "\n".join(lines)


# Singleton instance
email_service = OneSignalEmailService()
