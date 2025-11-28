"""
Database connection and session management.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings
from src.models.base import Base
from src.utils.logger import logger


class Database:
    """Database connection manager."""
    
    def __init__(self):
        """Initialize database connection."""
        self.engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            echo=settings.db_echo,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        logger.info(f"Database engine created: {settings.database_url.split('@')[-1]}")
    
    def create_tables(self):
        """Create all tables in the database."""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.success("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all tables in the database."""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.success("Database tables dropped successfully")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session.
        
        Usage:
            with db.get_session() as session:
                # Use session here
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_db(self) -> Generator[Session, None, None]:
        """
        Get a database session for dependency injection.
        
        Usage with FastAPI:
            @app.get("/items")
            def get_items(db: Session = Depends(get_db)):
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


# Global database instance
db = Database()


def get_db_session() -> Generator[Session, None, None]:
    """Get database session for dependency injection."""
    return db.get_db()

