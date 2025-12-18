"""Alert data model."""
import logging
import re
from datetime import datetime
from typing import Optional, List, Set, Tuple
from uuid import UUID

from sqlalchemy import Boolean, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


logger = logging.getLogger(__name__)

# Common words to ignore when matching (articles, prepositions, etc.)
STOP_WORDS = {'a', 'an', 'the', 'of', 'and', 'or', 'in', 'at', 'to', 'for', 'with', 'on', 'by', 'is', 'are'}

# Semantic matching settings
SEMANTIC_MATCHING_ENABLED = True
SEMANTIC_SIMILARITY_THRESHOLD = 0.65


def tokenize(text: str) -> Set[str]:
    """
    Tokenize text into a set of lowercase words, removing punctuation.

    Args:
        text: Text to tokenize

    Returns:
        Set of lowercase words
    """
    # Replace punctuation with spaces and split
    words = re.sub(r'[^\w\s]', ' ', text.lower()).split()
    return set(words)


def keyword_matches(keyword: str, title: str) -> bool:
    """
    Check if a keyword matches a title using flexible word-based matching.

    All significant words in the keyword must appear in the title.
    Stop words (of, and, the, etc.) are ignored.

    Examples:
        - "engineering manager" matches "Senior Engineering Manager"
        - "vp engineering" matches "VP, Engineering & GM"
        - "vice president engineering" matches "Vice President of Engineering"

    Args:
        keyword: The keyword phrase to match
        title: The job title to match against

    Returns:
        True if all significant words in keyword appear in title
    """
    keyword_words = tokenize(keyword) - STOP_WORDS
    title_words = tokenize(title)

    # All keyword words (except stop words) must be in the title
    return keyword_words.issubset(title_words)


def semantic_keyword_matches(keywords: List[str], title: str) -> Tuple[bool, float, Optional[str]]:
    """
    Check if any keyword semantically matches a title using embeddings.

    This is a fallback when exact keyword matching fails.

    Args:
        keywords: List of keyword phrases
        title: Job title to match against

    Returns:
        Tuple of (is_match, similarity_score, matched_keyword)
    """
    if not SEMANTIC_MATCHING_ENABLED:
        return False, 0.0, None

    try:
        from src.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService(threshold=SEMANTIC_SIMILARITY_THRESHOLD)
        return embedding_service.keywords_match_title(keywords, title)
    except ImportError:
        logger.debug("Semantic matching unavailable - sentence-transformers not installed")
        return False, 0.0, None
    except Exception as e:
        logger.warning(f"Semantic matching failed: {e}")
        return False, 0.0, None


class Alert(Base, UUIDMixin, TimestampMixin):
    """Alert model for storing user alert configurations."""
    
    __tablename__ = "alerts"
    
    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Alert configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Matching criteria - Company filter
    company_ids: Mapped[Optional[List[UUID]]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)),
        default=list
    )
    
    # Matching criteria - Keywords
    keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    excluded_keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    
    # Matching criteria - Location and department
    locations: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    departments: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    
    # Matching criteria - Employment details
    employment_types: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    remote_types: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)  # remote, hybrid, onsite
    seniority_levels: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    
    # Notification settings
    notification_method: Mapped[str] = mapped_column(String(50), default='email', nullable=False)
    notification_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Tracking
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trigger_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    notifications = relationship("AlertNotification", back_populates="alert", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    def matches_position(self, position, use_semantic: bool = True) -> bool:
        """
        Check if a job position matches this alert's criteria.
        All specified criteria must match (AND logic).

        Keyword matching uses flexible word-based matching first, then
        falls back to semantic matching using sentence embeddings.

        Word-based matching:
        - All significant words in the keyword must appear in the title
        - Stop words (of, and, the, etc.) are ignored
        - Punctuation is ignored

        Semantic matching (fallback):
        - Uses sentence-transformers to compute similarity
        - Matches if cosine similarity >= threshold (default 0.65)

        Examples:
            - "engineering manager" matches "Senior Engineering Manager" (word-based)
            - "vp engineering" matches "VP, Engineering & GM" (word-based)
            - "Software Engineer" matches "Backend Developer" (semantic)
        """
        # Company filter
        if self.company_ids and position.company_id not in self.company_ids:
            return False

        # Keywords filter (at least one keyword must match)
        if self.keywords:
            # First try word-based matching
            word_match = any(keyword_matches(kw, position.title) for kw in self.keywords)

            if not word_match and use_semantic:
                # Fall back to semantic matching
                semantic_match, score, matched_kw = semantic_keyword_matches(
                    self.keywords, position.title
                )
                if semantic_match:
                    logger.debug(
                        f"Semantic match: '{matched_kw}' ~ '{position.title}' (score: {score:.2f})"
                    )
                    word_match = True

            if not word_match:
                return False

        # Excluded keywords filter (none should match using flexible matching)
        # Note: We only use word-based matching for exclusions (more precise)
        if self.excluded_keywords:
            if any(keyword_matches(excluded, position.title) for excluded in self.excluded_keywords):
                return False
        
        # Location filter
        if self.locations and position.location:
            location_lower = position.location.lower()
            if not any(loc.lower() in location_lower for loc in self.locations):
                return False
        
        # Department filter
        if self.departments and position.department:
            department_lower = position.department.lower()
            if not any(dept.lower() in department_lower for dept in self.departments):
                return False
        
        # Employment type filter
        if self.employment_types and position.employment_type:
            if position.employment_type not in self.employment_types:
                return False
        
        # Remote type filter
        if self.remote_types and position.remote_type:
            if position.remote_type not in self.remote_types:
                return False
        
        # Seniority level filter
        if self.seniority_levels and position.seniority_level:
            if position.seniority_level not in self.seniority_levels:
                return False
        
        return True
    
    @property
    def immediate_notification(self) -> bool:
        """Check if alert should send immediate notifications."""
        return self.notification_config.get("immediate", True)
    
    @property
    def digest_enabled(self) -> bool:
        """Check if daily digest is enabled."""
        return self.notification_config.get("digest_enabled", False)

