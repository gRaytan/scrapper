"""Pydantic schemas for Interview Question API."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AnswerBase(BaseModel):
    """Base answer schema."""
    text: str = Field(..., min_length=1, max_length=5000)


class AnswerCreate(AnswerBase):
    """Schema for creating an answer."""
    pass


class AnswerResponse(AnswerBase):
    """Schema for answer response."""
    id: str
    user_id: str
    user_name: str
    created_at: datetime
    upvotes: int = 0


class InterviewQuestionBase(BaseModel):
    """Base interview question schema."""
    question_text: str = Field(..., min_length=1, max_length=2000)
    role: str = Field(..., min_length=1, max_length=255)
    difficulty: Optional[str] = Field(None, pattern="^(Easy|Medium|Hard)$")
    interview_stage: Optional[str] = Field(None, max_length=100)


class InterviewQuestionCreate(InterviewQuestionBase):
    """Schema for creating an interview question."""
    pass


class InterviewQuestionResponse(InterviewQuestionBase):
    """Schema for interview question response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    answers: List[AnswerResponse] = []
    upvotes: int = 0
    answer_count: int = 0
    created_at: datetime
    updated_at: datetime


class InterviewQuestionListResponse(BaseModel):
    """Schema for paginated interview questions list."""
    total: int
    page: int
    page_size: int
    questions: List[InterviewQuestionResponse]
    roles: List[str] = []


class RolesListResponse(BaseModel):
    """Schema for roles list response."""
    roles: List[str]
