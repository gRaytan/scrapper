"""Test database connectivity and basic CRUD operations."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import text

from src.storage.database import db
from src.models.user import User
from src.models.company import Company
from src.models.job_position import JobPosition
from src.models.alert import Alert
from src.utils.logger import logger


def test_database_connection():
    """Test basic database connection."""
    logger.info("Testing database connection...")
    try:
        with db.get_session() as session:
            # Test simple query
            result = session.execute(text("SELECT 1"))
            logger.success("✓ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def test_create_user():
    """Test creating a user."""
    logger.info("Testing user creation...")
    try:
        with db.get_session() as session:
            user = User(
                email="test@example.com",
                full_name="Test User",
                is_active=True,
                preferences={
                    "email_notifications": True,
                    "notification_frequency": "daily"
                }
            )
            session.add(user)
            session.commit()
            logger.success(f"✓ User created: {user.id}")
            return user.id
    except Exception as e:
        logger.error(f"✗ User creation failed: {e}")
        return None


def test_create_company():
    """Test creating a company."""
    logger.info("Testing company creation...")
    try:
        with db.get_session() as session:
            company = Company(
                name="Test Company",
                website="https://testcompany.com",
                careers_url="https://testcompany.com/careers",
                industry="Technology",
                size="100-500",
                location="Tel Aviv, Israel",
                scraping_config={
                    "scraper_type": "playwright",
                    "pagination_type": "click_next",
                    "location_filter": ["Israel"]
                },
                is_active=True
            )
            session.add(company)
            session.commit()
            logger.success(f"✓ Company created: {company.id}")
            return company.id
    except Exception as e:
        logger.error(f"✗ Company creation failed: {e}")
        return None


def test_create_job_position(company_id):
    """Test creating a job position."""
    logger.info("Testing job position creation...")
    try:
        with db.get_session() as session:
            job = JobPosition(
                company_id=company_id,
                title="Senior Software Engineer",
                description="We are looking for a talented software engineer...",
                location="Tel Aviv, Israel",
                remote_type="hybrid",
                employment_type="full-time",
                department="Engineering",
                seniority_level="senior",
                job_url="https://testcompany.com/careers/senior-engineer",
                scraped_at=datetime.now(),
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
                status="active",
                is_active=True
            )
            session.add(job)
            session.commit()
            logger.success(f"✓ Job position created: {job.id}")
            return job.id
    except Exception as e:
        logger.error(f"✗ Job position creation failed: {e}")
        return None


def test_create_alert(user_id, company_id):
    """Test creating an alert."""
    logger.info("Testing alert creation...")
    try:
        with db.get_session() as session:
            alert = Alert(
                user_id=user_id,
                name="Senior Engineering Roles",
                is_active=True,
                company_ids=[company_id],
                keywords=["senior", "engineer", "python"],
                excluded_keywords=["junior", "intern"],
                locations=["Tel Aviv", "Israel"],
                departments=["Engineering"],
                employment_types=["full-time"],
                remote_types=["remote", "hybrid"],
                seniority_levels=["senior"],
                notification_method="email",
                notification_config={
                    "email": "test@example.com",
                    "frequency": "immediate"
                }
            )
            session.add(alert)
            session.commit()
            logger.success(f"✓ Alert created: {alert.id}")
            return alert.id
    except Exception as e:
        logger.error(f"✗ Alert creation failed: {e}")
        return None


def test_read_operations(user_id, company_id):
    """Test reading data from database."""
    logger.info("Testing read operations...")
    try:
        with db.get_session() as session:
            # Read user
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                logger.success(f"✓ User read: {user.email}")
            else:
                logger.error("✗ User not found")
                return False
            
            # Read company
            company = session.query(Company).filter(Company.id == company_id).first()
            if company:
                logger.success(f"✓ Company read: {company.name}")
            else:
                logger.error("✗ Company not found")
                return False
            
            # Read job positions for company
            jobs = session.query(JobPosition).filter(
                JobPosition.company_id == company_id
            ).all()
            logger.success(f"✓ Found {len(jobs)} job position(s) for company")
            
            # Read alerts for user
            alerts = session.query(Alert).filter(Alert.user_id == user_id).all()
            logger.success(f"✓ Found {len(alerts)} alert(s) for user")
            
            return True
    except Exception as e:
        logger.error(f"✗ Read operations failed: {e}")
        return False


def test_update_operations(user_id):
    """Test updating data in database."""
    logger.info("Testing update operations...")
    try:
        with db.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.full_name = "Updated Test User"
                user.preferences["email_notifications"] = False
                session.commit()
                logger.success("✓ User updated successfully")
                return True
            else:
                logger.error("✗ User not found for update")
                return False
    except Exception as e:
        logger.error(f"✗ Update operations failed: {e}")
        return False


def test_delete_operations(user_id, company_id):
    """Test deleting data from database."""
    logger.info("Testing delete operations (cascade)...")
    try:
        with db.get_session() as session:
            # Delete company (should cascade to job_positions)
            company = session.query(Company).filter(Company.id == company_id).first()
            if company:
                session.delete(company)
                session.commit()
                logger.success("✓ Company deleted (cascade to job positions)")
            
            # Delete user (should cascade to alerts)
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                session.delete(user)
                session.commit()
                logger.success("✓ User deleted (cascade to alerts)")
            
            return True
    except Exception as e:
        logger.error(f"✗ Delete operations failed: {e}")
        return False


def main():
    """Run all database tests."""
    logger.info("=" * 80)
    logger.info("Database Connectivity and CRUD Tests")
    logger.info("=" * 80)
    
    # Test connection
    if not test_database_connection():
        logger.error("Database connection failed. Exiting.")
        return 1
    
    # Test CREATE operations
    user_id = test_create_user()
    if not user_id:
        logger.error("User creation failed. Exiting.")
        return 1
    
    company_id = test_create_company()
    if not company_id:
        logger.error("Company creation failed. Exiting.")
        return 1
    
    job_id = test_create_job_position(company_id)
    if not job_id:
        logger.error("Job position creation failed. Exiting.")
        return 1
    
    alert_id = test_create_alert(user_id, company_id)
    if not alert_id:
        logger.error("Alert creation failed. Exiting.")
        return 1
    
    # Test READ operations
    if not test_read_operations(user_id, company_id):
        logger.error("Read operations failed. Exiting.")
        return 1
    
    # Test UPDATE operations
    if not test_update_operations(user_id):
        logger.error("Update operations failed. Exiting.")
        return 1
    
    # Test DELETE operations
    if not test_delete_operations(user_id, company_id):
        logger.error("Delete operations failed. Exiting.")
        return 1
    
    logger.info("=" * 80)
    logger.success("All database tests passed! ✓")
    logger.info("=" * 80)
    
    return 0


if __name__ == "__main__":
    exit(main())

