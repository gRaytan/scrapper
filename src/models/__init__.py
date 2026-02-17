"""Database models."""
from .base import Base, TimestampMixin, UUIDMixin
from .company import Company
from .job_position import JobPosition
from .scraping_session import ScrapingSession
from .user import User
from .alert import Alert
from .user_job_application import UserJobApplication, ApplicationInterview
from .alert_notification import AlertNotification
from .user_job_interaction import UserJobInteraction
from .job_embedding import JobEmbedding
from .saved_filter import SavedFilter

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "Company",
    "JobPosition",
    "ScrapingSession",
    "User",
    "Alert",
    "UserJobApplication",
    "ApplicationInterview",
    "AlertNotification",
    "UserJobInteraction",
    "JobEmbedding",
    "SavedFilter",
]
