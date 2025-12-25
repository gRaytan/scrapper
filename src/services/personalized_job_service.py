"""Service for personalized job feed, star/archive functionality."""
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

import numpy as np
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from src.models import JobPosition, User, JobEmbedding, UserJobInteraction
from src.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class PersonalizedJobService:
    """Service for personalized job feed and user-job interactions."""

    DEFAULT_SIMILARITY_THRESHOLD = 0.70
    DEFAULT_DAYS_BACK = 30

    def __init__(self, session: Session, threshold: float = DEFAULT_SIMILARITY_THRESHOLD):
        """
        Initialize the service.

        Args:
            session: SQLAlchemy database session
            threshold: Minimum similarity score for matching (0.0 - 1.0)
        """
        self.session = session
        self.threshold = threshold
        self._embedding_service: Optional[EmbeddingService] = None

    @property
    def embedding_service(self) -> EmbeddingService:
        """Lazy load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService(threshold=self.threshold)
        return self._embedding_service

    # ============ Star/Archive Operations ============

    def _get_or_create_interaction(self, user_id: UUID, job_id: UUID) -> UserJobInteraction:
        """Get existing interaction or create a new one."""
        interaction = self.session.query(UserJobInteraction).filter(
            UserJobInteraction.user_id == user_id,
            UserJobInteraction.job_id == job_id
        ).first()

        if not interaction:
            interaction = UserJobInteraction(user_id=user_id, job_id=job_id)
            self.session.add(interaction)

        return interaction

    def star_job(self, user_id: UUID, job_id: UUID) -> UserJobInteraction:
        """Star a job for a user."""
        interaction = self._get_or_create_interaction(user_id, job_id)
        interaction.is_starred = True
        interaction.starred_at = datetime.utcnow()
        self.session.commit()
        logger.info(f"User {user_id} starred job {job_id}")
        return interaction

    def unstar_job(self, user_id: UUID, job_id: UUID) -> UserJobInteraction:
        """Unstar a job for a user."""
        interaction = self._get_or_create_interaction(user_id, job_id)
        interaction.is_starred = False
        interaction.starred_at = None
        self.session.commit()
        logger.info(f"User {user_id} unstarred job {job_id}")
        return interaction

    def archive_job(self, user_id: UUID, job_id: UUID) -> UserJobInteraction:
        """Archive a job for a user."""
        interaction = self._get_or_create_interaction(user_id, job_id)
        interaction.is_archived = True
        interaction.archived_at = datetime.utcnow()
        self.session.commit()
        logger.info(f"User {user_id} archived job {job_id}")
        return interaction

    def unarchive_job(self, user_id: UUID, job_id: UUID) -> UserJobInteraction:
        """Unarchive a job for a user."""
        interaction = self._get_or_create_interaction(user_id, job_id)
        interaction.is_archived = False
        interaction.archived_at = None
        self.session.commit()
        logger.info(f"User {user_id} unarchived job {job_id}")
        return interaction

    def get_interaction(self, user_id: UUID, job_id: UUID) -> Optional[UserJobInteraction]:
        """Get user's interaction with a job."""
        return self.session.query(UserJobInteraction).filter(
            UserJobInteraction.user_id == user_id,
            UserJobInteraction.job_id == job_id
        ).first()

    # ============ Starred/Archived Lists ============

    def get_starred_jobs(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[JobPosition], int]:
        """Get user's starred jobs with pagination."""
        query = self.session.query(JobPosition).join(
            UserJobInteraction,
            and_(
                UserJobInteraction.job_id == JobPosition.id,
                UserJobInteraction.user_id == user_id,
                UserJobInteraction.is_starred == True
            )
        ).options(joinedload(JobPosition.company))

        total = query.count()
        jobs = query.order_by(UserJobInteraction.starred_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return jobs, total

    def get_archived_jobs(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[JobPosition], int]:
        """Get user's archived jobs with pagination."""
        query = self.session.query(JobPosition).join(
            UserJobInteraction,
            and_(
                UserJobInteraction.job_id == JobPosition.id,
                UserJobInteraction.user_id == user_id,
                UserJobInteraction.is_archived == True
            )
        ).options(joinedload(JobPosition.company))

        total = query.count()
        jobs = query.order_by(UserJobInteraction.archived_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return jobs, total

    # ============ User Interactions Map ============

    def get_user_interactions_map(self, user_id: UUID, job_ids: List[UUID]) -> Dict[UUID, Dict[str, bool]]:
        """Get star/archive status for multiple jobs."""
        if not job_ids:
            return {}

        interactions = self.session.query(UserJobInteraction).filter(
            UserJobInteraction.user_id == user_id,
            UserJobInteraction.job_id.in_(job_ids)
        ).all()

        return {
            i.job_id: {"is_starred": i.is_starred, "is_archived": i.is_archived}
            for i in interactions
        }

    # ============ Embedding Operations ============

    def compute_and_store_job_embedding(self, job: JobPosition) -> JobEmbedding:
        """Compute and store embedding for a job's title."""
        embedding_vector = self.embedding_service.encode(job.title)

        # Check if embedding already exists
        existing = self.session.query(JobEmbedding).filter(
            JobEmbedding.job_id == job.id
        ).first()

        if existing:
            existing.set_embedding(embedding_vector)
            existing.updated_at = datetime.utcnow()
            job_embedding = existing
        else:
            job_embedding = JobEmbedding(job_id=job.id)
            job_embedding.set_embedding(embedding_vector)
            self.session.add(job_embedding)

        self.session.commit()
        return job_embedding

    def compute_embeddings_for_jobs(self, jobs: List[JobPosition]) -> int:
        """Compute and store embeddings for multiple jobs. Returns count of processed jobs."""
        if not jobs:
            return 0

        # Get existing embeddings
        job_ids = [j.id for j in jobs]
        existing = self.session.query(JobEmbedding.job_id).filter(
            JobEmbedding.job_id.in_(job_ids)
        ).all()
        existing_ids = {e.job_id for e in existing}

        # Filter to jobs without embeddings
        jobs_to_process = [j for j in jobs if j.id not in existing_ids]

        if not jobs_to_process:
            return 0

        # Batch encode titles
        titles = [j.title for j in jobs_to_process]
        embeddings = self.embedding_service.encode_batch(titles)

        # Store embeddings
        for job, embedding in zip(jobs_to_process, embeddings):
            job_embedding = JobEmbedding(job_id=job.id)
            job_embedding.set_embedding(embedding)
            self.session.add(job_embedding)

        self.session.commit()
        logger.info(f"Computed embeddings for {len(jobs_to_process)} jobs")
        return len(jobs_to_process)

    def compute_user_query_embedding(self, user: User) -> Optional[np.ndarray]:
        """Compute embedding for user's job preferences (title only).

        Keywords are used for filtering, not for embedding computation.
        This ensures the semantic search focuses on the job title match.
        """
        job_title = user.preferences.get("job_title", "")

        if not job_title:
            return None

        # Use only job_title for embedding - keywords are used for filtering
        return self.embedding_service.encode(job_title)

    def update_user_job_preferences(
        self,
        user: User,
        job_title: Optional[str] = None,
        job_keywords: Optional[List[str]] = None
    ) -> User:
        """Update user's job preferences and recompute query embedding."""
        preferences = user.preferences.copy() if user.preferences else {}

        if job_title is not None:
            preferences["job_title"] = job_title
        if job_keywords is not None:
            preferences["job_keywords"] = job_keywords

        # Compute and store query embedding
        user.preferences = preferences
        query_embedding = self.compute_user_query_embedding(user)

        if query_embedding is not None:
            # Store as base64 for JSON compatibility
            preferences["query_embedding"] = base64.b64encode(
                query_embedding.astype(np.float32).tobytes()
            ).decode("utf-8")
            user.preferences = preferences

        self.session.commit()
        logger.info(f"Updated job preferences for user {user.id}")
        return user

    def get_user_query_embedding(self, user: User) -> Optional[np.ndarray]:
        """Get user's pre-computed query embedding from preferences."""
        embedding_b64 = user.preferences.get("query_embedding")
        if not embedding_b64:
            return None

        try:
            embedding_bytes = base64.b64decode(embedding_b64)
            return np.frombuffer(embedding_bytes, dtype=np.float32)
        except Exception as e:
            logger.warning(f"Failed to decode user query embedding: {e}")
            return None


    # ============ Personalized Feed ============

    def get_personalized_feed(
        self,
        user: User,
        location: Optional[str] = None,
        days_back: int = DEFAULT_DAYS_BACK,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get personalized job feed for a user based on their preferences.

        Args:
            user: User object
            location: Optional location filter
            days_back: How many days back to look for jobs
            page: Page number (1-indexed)
            page_size: Number of jobs per page

        Returns:
            Dictionary with jobs, pagination info, and user preferences
        """
        # Get user's query embedding
        query_embedding = self.get_user_query_embedding(user)

        if query_embedding is None:
            # Try to compute it on the fly
            query_embedding = self.compute_user_query_embedding(user)

        if query_embedding is None:
            # No preferences set, return empty feed
            return {
                "jobs": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "user_preferences": {
                    "job_title": user.preferences.get("job_title"),
                    "job_keywords": user.preferences.get("job_keywords", [])
                }
            }

        # Get active jobs from the last N days
        cutoff = datetime.utcnow() - timedelta(days=days_back)

        query = self.session.query(JobPosition).filter(
            JobPosition.is_active == True,
            JobPosition.created_at >= cutoff
        ).options(joinedload(JobPosition.company))

        # Apply location filter if provided
        if location:
            query = query.filter(JobPosition.location.ilike(f"%{location}%"))

        # Get all matching jobs
        jobs = query.all()

        if not jobs:
            return {
                "jobs": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "user_preferences": {
                    "job_title": user.preferences.get("job_title"),
                    "job_keywords": user.preferences.get("job_keywords", [])
                }
            }

        # Get archived job IDs for this user (to exclude)
        archived_interactions = self.session.query(UserJobInteraction.job_id).filter(
            UserJobInteraction.user_id == user.id,
            UserJobInteraction.is_archived == True
        ).all()
        archived_job_ids = {i.job_id for i in archived_interactions}

        # Filter out archived jobs
        jobs = [j for j in jobs if j.id not in archived_job_ids]

        if not jobs:
            return {
                "jobs": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "user_preferences": {
                    "job_title": user.preferences.get("job_title"),
                    "job_keywords": user.preferences.get("job_keywords", [])
                }
            }

        # Get job embeddings
        job_ids = [j.id for j in jobs]
        embeddings = self.session.query(JobEmbedding).filter(
            JobEmbedding.job_id.in_(job_ids)
        ).all()
        embedding_map = {e.job_id: e.get_embedding() for e in embeddings}

        # Get user's keywords for filtering (optional)
        job_keywords = user.preferences.get("job_keywords", [])
        keywords_lower = [kw.lower() for kw in job_keywords] if job_keywords else []

        def job_matches_keywords(job_title: str) -> bool:
            """Check if job title contains at least one keyword."""
            if not keywords_lower:
                return True  # No keywords = no filtering
            title_lower = job_title.lower()
            return any(kw in title_lower for kw in keywords_lower)

        # Compute similarity scores
        scored_jobs = []
        for job in jobs:
            job_embedding = embedding_map.get(job.id)
            if job_embedding is not None:
                # Apply keyword filter if keywords are set
                if not job_matches_keywords(job.title or ""):
                    continue
                score = self.embedding_service.cosine_similarity(query_embedding, job_embedding)
                if score >= self.threshold:
                    scored_jobs.append((job, score))

        # Sort by similarity score (descending), then by posted_date (descending)
        scored_jobs.sort(key=lambda x: (-x[1], -(x[0].posted_date or x[0].created_at).timestamp()))

        total = len(scored_jobs)
        total_pages = (total + page_size - 1) // page_size

        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_jobs = scored_jobs[start_idx:end_idx]

        # Get interaction status for page jobs
        page_job_ids = [j.id for j, _ in page_jobs]
        interactions_map = self.get_user_interactions_map(user.id, page_job_ids)

        # Build response
        result_jobs = []
        for job, score in page_jobs:
            interaction = interactions_map.get(job.id, {"is_starred": False, "is_archived": False})
            result_jobs.append({
                "job": job,
                "similarity_score": round(score, 4),
                "is_starred": interaction["is_starred"],
                "is_archived": interaction["is_archived"]
            })

        return {
            "jobs": result_jobs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "user_preferences": {
                "job_title": user.preferences.get("job_title"),
                "job_keywords": user.preferences.get("job_keywords", [])
            }
        }

