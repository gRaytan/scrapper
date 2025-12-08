"""Tests for JobMatchingService."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.job_matching_service import JobMatchingService
from src.models.alert import Alert
from src.models.alert_notification import AlertNotification
from src.models.job_position import JobPosition
from src.models.company import Company
from src.models.user import User


class TestJobMatchingService:
    """Test cases for JobMatchingService."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = MagicMock()
        session.query.return_value.filter.return_value.all.return_value = []
        session.query.return_value.filter.return_value.options.return_value.all.return_value = []
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create a JobMatchingService instance."""
        return JobMatchingService(mock_session)

    @pytest.fixture
    def sample_company(self):
        """Create a sample company."""
        company = MagicMock(spec=Company)
        company.id = uuid4()
        company.name = "Test Company"
        return company

    @pytest.fixture
    def sample_user(self):
        """Create a sample user."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def sample_job(self, sample_company):
        """Create a sample job position."""
        job = MagicMock(spec=JobPosition)
        job.id = uuid4()
        job.title = "Senior Software Engineer"
        job.company_id = sample_company.id
        job.company = sample_company
        job.location = "Tel Aviv, Israel"
        job.department = "Engineering"
        job.employment_type = "full-time"
        job.remote_type = "hybrid"
        job.seniority_level = "senior"
        job.is_active = True
        job.created_at = datetime.utcnow()
        return job

    @pytest.fixture
    def sample_alert(self, sample_user):
        """Create a sample alert."""
        alert = MagicMock(spec=Alert)
        alert.id = uuid4()
        alert.user_id = sample_user.id
        alert.user = sample_user
        alert.name = "Software Engineer Alert"
        alert.is_active = True
        alert.keywords = ["software", "engineer"]
        alert.excluded_keywords = []
        alert.company_ids = []
        alert.locations = []
        alert.departments = []
        alert.employment_types = []
        alert.remote_types = []
        alert.seniority_levels = []
        alert.notification_method = "email"
        alert.trigger_count = 0
        alert.last_triggered_at = None
        return alert

    # Test _create_notification helper
    def test_create_notification(self, service, sample_alert, sample_job, sample_user):
        """Test creating a notification with multiple jobs."""
        job2 = MagicMock(spec=JobPosition)
        job2.id = uuid4()

        notification = service._create_notification(
            sample_alert, [sample_job, job2], sample_user.id
        )

        service.session.add.assert_called_once()
        assert notification.alert_id == sample_alert.id
        assert notification.user_id == sample_user.id
        assert notification.job_count == 2
        assert str(sample_job.id) in notification.job_position_ids
        assert str(job2.id) in notification.job_position_ids
        assert notification.delivery_status == 'pending'

    # Test _update_alert_triggered helper
    def test_update_alert_triggered(self, service, sample_alert):
        """Test updating alert tracking."""
        sample_alert.trigger_count = 5
        sample_alert.last_triggered_at = None

        service._update_alert_triggered(sample_alert)

        assert sample_alert.trigger_count == 6
        assert sample_alert.last_triggered_at is not None

    # Test _get_notified_pairs
    def test_get_notified_pairs_empty(self, service):
        """Test getting notified pairs with empty inputs."""
        result = service._get_notified_pairs([], [])
        assert result == set()

    def test_get_notified_pairs_with_data(self, service, mock_session):
        """Test getting notified pairs with data."""
        alert_id = uuid4()
        job_id = uuid4()

        # New model: job_position_ids is a list of string UUIDs
        mock_notification = MagicMock()
        mock_notification.alert_id = alert_id
        mock_notification.job_position_ids = [str(job_id)]

        mock_session.query.return_value.filter.return_value.all.return_value = [mock_notification]

        result = service._get_notified_pairs([alert_id], [job_id])

        # Now returns (alert_id, job_id_str) pairs
        assert (alert_id, str(job_id)) in result

    # Test match_jobs_to_alerts
    def test_match_jobs_to_alerts_empty_jobs(self, service):
        """Test matching with empty jobs list."""
        result = service.match_jobs_to_alerts([])
        assert result == {}

    def test_match_jobs_to_alerts_no_alerts(self, service, sample_job, mock_session):
        """Test matching when no active alerts exist."""
        mock_session.query.return_value.filter.return_value.options.return_value.all.return_value = []

        result = service.match_jobs_to_alerts([sample_job])
        assert result == {}

    def test_match_jobs_to_alerts_with_match(self, service, sample_job, sample_alert, mock_session):
        """Test matching when job matches alert."""
        # Setup: alert matches the job
        sample_alert.matches_position = MagicMock(return_value=True)

        # No existing notifications
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = service.match_jobs_to_alerts([sample_job], alerts=[sample_alert])

        assert sample_alert.user_id in result
        assert len(result[sample_alert.user_id]) == 1
        assert result[sample_alert.user_id][0]['alert'] == sample_alert
        assert sample_job in result[sample_alert.user_id][0]['jobs']

    def test_match_jobs_to_alerts_skips_already_notified(self, service, sample_job, sample_alert, mock_session):
        """Test that already notified jobs are skipped."""
        sample_alert.matches_position = MagicMock(return_value=True)

        # Setup: job was already notified for this alert (new model with job_position_ids list)
        mock_notification = MagicMock()
        mock_notification.alert_id = sample_alert.id
        mock_notification.job_position_ids = [str(sample_job.id)]

        mock_session.query.return_value.filter.return_value.all.return_value = [mock_notification]

        result = service.match_jobs_to_alerts([sample_job], alerts=[sample_alert])

        # Should be empty because job was already notified
        assert result == {}

    def test_match_jobs_to_alerts_no_match(self, service, sample_job, sample_alert, mock_session):
        """Test matching when job doesn't match alert."""
        sample_alert.matches_position = MagicMock(return_value=False)

        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = service.match_jobs_to_alerts([sample_job], alerts=[sample_alert])

        assert result == {}

    # Test create_notifications
    def test_create_notifications_empty(self, service):
        """Test creating notifications with empty matches."""
        result = service.create_notifications({})

        assert result['notifications_created'] == 0
        assert result['total_jobs_matched'] == 0
        assert result['alerts_triggered'] == 0
        assert result['users_notified'] == 0

    def test_create_notifications_with_matches(self, service, sample_job, sample_alert, sample_user):
        """Test creating notifications with matches."""
        job2 = MagicMock(spec=JobPosition)
        job2.id = uuid4()

        user_matches = {
            sample_user.id: [{
                'alert': sample_alert,
                'jobs': [sample_job, job2]  # Two jobs in one notification
            }]
        }

        result = service.create_notifications(user_matches)

        # One notification per alert, but contains 2 jobs
        assert result['notifications_created'] == 1
        assert result['total_jobs_matched'] == 2
        assert result['alerts_triggered'] == 1
        assert result['users_notified'] == 1
        service.session.commit.assert_called_once()

    # Test process_new_jobs
    def test_process_new_jobs_empty(self, service):
        """Test processing empty jobs list."""
        result = service.process_new_jobs([])

        assert result['status'] == 'success'
        assert 'message' in result

    def test_process_new_jobs_no_matches(self, service, sample_job, mock_session):
        """Test processing jobs with no matching alerts."""
        mock_session.query.return_value.filter.return_value.options.return_value.all.return_value = []

        result = service.process_new_jobs([sample_job])

        assert result['status'] == 'success'
        assert result['jobs_processed'] == 1
        assert result['matches_found'] == 0

    # Test process_alert_against_existing_jobs
    def test_process_alert_against_existing_jobs_no_jobs(self, service, sample_alert, mock_session):
        """Test processing alert when no existing jobs."""
        mock_session.query.return_value.filter.return_value.options.return_value.all.return_value = []

        result = service.process_alert_against_existing_jobs(sample_alert)

        assert result['status'] == 'success'
        assert result['jobs_checked'] == 0
        assert result['matches_found'] == 0

    def test_process_alert_against_existing_jobs_with_matches(
        self, service, sample_alert, sample_job, mock_session
    ):
        """Test processing alert with matching existing jobs."""
        sample_alert.matches_position = MagicMock(return_value=True)
        sample_alert.trigger_count = 0

        # Return existing jobs
        mock_session.query.return_value.filter.return_value.options.return_value.all.return_value = [sample_job]
        # No existing notifications
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = service.process_alert_against_existing_jobs(sample_alert)

        assert result['status'] == 'success'
        assert result['jobs_checked'] == 1
        assert result['matches_found'] == 1
        assert result['notifications_created'] == 1
        service.session.commit.assert_called_once()


class TestJobMatchingServiceIntegration:
    """Integration tests that require a real database session."""

    @pytest.fixture
    def db_session(self):
        """Get a real database session for integration tests."""
        from src.storage.database import db
        with db.get_session() as session:
            yield session
            session.rollback()  # Rollback any changes after test

    @pytest.mark.integration
    def test_full_matching_flow(self, db_session):
        """Test the full matching flow with real database."""
        # This test requires a running database
        # Skip if database is not available
        try:
            from sqlalchemy import text
            db_session.execute(text("SELECT 1"))
        except Exception:
            pytest.skip("Database not available")

        service = JobMatchingService(db_session)

        # Test with empty jobs
        result = service.process_new_jobs([])
        assert result['status'] == 'success'

