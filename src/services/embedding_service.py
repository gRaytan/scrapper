"""Embedding service for semantic text matching using Sentence Transformers."""
import logging
from typing import List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Lazy load the model to avoid import-time overhead
_model = None
_model_name = 'all-MiniLM-L6-v2'  # 80MB, fast, good quality


def get_model():
    """Lazy load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {_model_name}")
            _model = SentenceTransformer(_model_name)
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            raise
    return _model


class EmbeddingService:
    """Service for generating and comparing text embeddings."""
    
    # Similarity threshold for considering a match
    DEFAULT_THRESHOLD = 0.65
    
    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        """
        Initialize embedding service.
        
        Args:
            threshold: Minimum cosine similarity for a match (0-1)
        """
        self.threshold = threshold
        self._model = None
    
    @property
    def model(self):
        """Lazy load model on first use."""
        if self._model is None:
            self._model = get_model()
        return self._model
    
    def encode(self, text: str) -> np.ndarray:
        """
        Encode text into an embedding vector.
        
        Args:
            text: Text to encode
            
        Returns:
            Numpy array of shape (384,) for MiniLM model
        """
        return self.model.encode(text, convert_to_numpy=True)
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Encode multiple texts into embedding vectors.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            Numpy array of shape (n_texts, 384)
        """
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    
    def cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))
    
    def is_similar(
        self,
        text1: str,
        text2: str,
        threshold: Optional[float] = None
    ) -> Tuple[bool, float]:
        """
        Check if two texts are semantically similar.
        
        Args:
            text1: First text
            text2: Second text
            threshold: Optional custom threshold (uses default if not specified)
            
        Returns:
            Tuple of (is_match, similarity_score)
        """
        threshold = threshold or self.threshold
        
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        
        similarity = self.cosine_similarity(emb1, emb2)
        
        return similarity >= threshold, similarity
    
    def find_best_match(
        self,
        query: str,
        candidates: List[str],
        threshold: Optional[float] = None
    ) -> Tuple[Optional[int], float]:
        """
        Find the best matching candidate for a query.
        
        Args:
            query: Query text
            candidates: List of candidate texts
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (best_match_index, similarity_score)
            Returns (None, 0.0) if no match above threshold
        """
        if not candidates:
            return None, 0.0
        
        threshold = threshold or self.threshold
        
        query_emb = self.encode(query)
        candidate_embs = self.encode_batch(candidates)
        
        # Calculate similarities
        similarities = [
            self.cosine_similarity(query_emb, cand_emb)
            for cand_emb in candidate_embs
        ]
        
        best_idx = int(np.argmax(similarities))
        best_score = similarities[best_idx]
        
        if best_score >= threshold:
            return best_idx, best_score
        
        return None, best_score
    
    def keywords_match_title(
        self,
        keywords: List[str],
        title: str,
        threshold: Optional[float] = None
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Check if any keyword semantically matches a job title.
        
        Args:
            keywords: List of keyword phrases
            title: Job title to match against
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (is_match, best_score, matched_keyword)
        """
        if not keywords:
            return False, 0.0, None
        
        threshold = threshold or self.threshold
        
        title_emb = self.encode(title)
        keyword_embs = self.encode_batch(keywords)
        
        best_score = 0.0
        best_keyword = None
        
        for i, kw_emb in enumerate(keyword_embs):
            score = self.cosine_similarity(title_emb, kw_emb)
            if score > best_score:
                best_score = score
                best_keyword = keywords[i]
        
        return best_score >= threshold, best_score, best_keyword

