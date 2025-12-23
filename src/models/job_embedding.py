"""Job embedding model for storing pre-computed title embeddings."""
from uuid import UUID

import numpy as np
from sqlalchemy import ForeignKey, LargeBinary
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class JobEmbedding(Base, UUIDMixin, TimestampMixin):
    """Model for storing pre-computed job title embeddings."""

    __tablename__ = "job_embeddings"

    # Foreign key
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("job_positions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Embedding stored as binary (numpy array serialized)
    # MiniLM model produces 384-dimensional vectors
    # 384 floats × 4 bytes = 1,536 bytes per embedding
    title_embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Relationship
    job = relationship("JobPosition", back_populates="embedding")

    def __repr__(self) -> str:
        return f"<JobEmbedding(job_id={self.job_id})>"

    def set_embedding(self, embedding: np.ndarray) -> None:
        """
        Serialize and store a numpy embedding array.
        
        Args:
            embedding: Numpy array of shape (384,) with float32 values
        """
        self.title_embedding = embedding.astype(np.float32).tobytes()

    def get_embedding(self) -> np.ndarray:
        """
        Deserialize and return the embedding as a numpy array.
        
        Returns:
            Numpy array of shape (384,) with float32 values
        """
        return np.frombuffer(self.title_embedding, dtype=np.float32)

