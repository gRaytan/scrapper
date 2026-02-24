"""
Email Provider Abstraction Layer.

This module provides a unified interface for email sending, allowing easy switching
between different email providers (OneSignal, AWS SES, etc.).

Usage:
    from src.services.email_provider import get_email_service
    
    email_service = get_email_service()
    email_service.send_job_digest_email(...)
"""
import logging
from typing import Protocol, List, Dict, Any, Optional, runtime_checkable

from config.settings import settings

logger = logging.getLogger(__name__)


@runtime_checkable
class EmailProvider(Protocol):
    """Protocol defining the interface for email providers."""
    
    @property
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        ...
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a raw email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            text_content: Plain text body (optional)
        
        Returns:
            Dict with 'success' bool and optional 'id' or 'error'
        """
        ...
    
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
        Send a job digest email.
        
        Args:
            to_email: Recipient email address
            user_name: User's display name
            jobs: List of job dicts
            alert_name: Name of the alert that matched
            show_tips: Whether to show tips section
            tip_text: Custom tip text
        
        Returns:
            Dict with 'success' bool and optional 'id' or 'error'
        """
        ...
    
    def send_welcome_email(
        self,
        to_email: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Send a welcome email.
        
        Args:
            to_email: Recipient email address
            user_name: User's display name
        
        Returns:
            Dict with 'success' bool and optional 'id' or 'error'
        """
        ...


# Cached provider instance
_email_provider: Optional[EmailProvider] = None


def get_email_service() -> EmailProvider:
    """
    Get the configured email service provider.
    
    Returns OneSignal if enabled and configured, otherwise falls back to SES.
    
    Returns:
        EmailProvider instance (OneSignal or SES)
    """
    global _email_provider
    
    if _email_provider is not None:
        return _email_provider
    
    # Check if OneSignal is enabled
    onesignal_enabled = getattr(settings, 'onesignal_enabled', True)
    
    if onesignal_enabled:
        try:
            from src.services.onesignal_email_service import onesignal_email_service
            if onesignal_email_service.is_configured:
                logger.info("Using OneSignal as email provider")
                _email_provider = onesignal_email_service
                return _email_provider
            else:
                logger.warning("OneSignal enabled but not configured, falling back to SES")
        except ImportError as e:
            logger.error(f"Failed to import OneSignal service: {e}")
    
    # Fallback to SES
    try:
        from src.services.email_service import email_service
        if email_service.is_configured:
            logger.info("Using AWS SES as email provider")
            _email_provider = email_service
            return _email_provider
        else:
            logger.error("SES not configured either!")
    except ImportError as e:
        logger.error(f"Failed to import SES service: {e}")
    
    # Return a dummy provider that always fails
    logger.error("No email provider available!")
    return _DummyEmailProvider()


class _DummyEmailProvider:
    """Dummy provider that returns failures when no real provider is available."""
    
    @property
    def is_configured(self) -> bool:
        return False
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: Optional[str] = None) -> Dict[str, Any]:
        return {"success": False, "error": "No email provider configured"}
    
    def send_job_digest_email(self, to_email: str, user_name: str, 
                              jobs: List[Dict[str, Any]], alert_name: str,
                              show_tips: bool = False, 
                              tip_text: Optional[str] = None) -> Dict[str, Any]:
        return {"success": False, "error": "No email provider configured"}
    
    def send_welcome_email(self, to_email: str, user_name: str) -> Dict[str, Any]:
        return {"success": False, "error": "No email provider configured"}


def reset_email_provider():
    """Reset the cached provider (useful for testing)."""
    global _email_provider
    _email_provider = None
    logger.info("Email provider cache reset")
