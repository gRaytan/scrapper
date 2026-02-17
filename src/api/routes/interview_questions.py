"""Interview Questions API endpoints."""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

from src.storage.database import db
from src.services.interview_question_service import InterviewQuestionService
from src.services.company_service import CompanyService
from src.auth.dependencies import get_current_active_user
from src.models.user import User
from src.api.schemas.interview_question import (
    InterviewQuestionCreate,
    InterviewQuestionResponse,
    InterviewQuestionListResponse,
    AnswerCreate,
    RolesListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session():
    """Dependency to get database session."""
    with db.get_session() as session:
        yield session


def _parse_answer_created_at(created_at) -> datetime:
    """Parse created_at from stored JSON (iso string or datetime) to datetime."""
    if isinstance(created_at, datetime):
        return created_at
    if isinstance(created_at, str):
        return datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return datetime.utcnow()


def _question_to_response(question, session: Session) -> dict:
    """Convert InterviewQuestion model to response dict."""
    user = session.query(User).filter(User.id == question.user_id).first()
    user_name = user.full_name if user and user.full_name else "Anonymous"

    answers = []
    for a in (question.answers or []):
        answers.append({
            "id": a.get("id", ""),
            "text": a.get("text", ""),
            "user_id": a.get("user_id", ""),
            "user_name": a.get("user_name", "Anonymous"),
            "created_at": _parse_answer_created_at(a.get("created_at")),
            "upvotes": a.get("upvotes", 0),
        })

    return {
        "id": question.id,
        "company_id": question.company_id,
        "user_id": question.user_id,
        "user_name": user_name,
        "question_text": question.question_text,
        "role": question.role,
        "difficulty": question.difficulty,
        "interview_stage": question.interview_stage,
        "answers": answers,
        "upvotes": question.upvotes or 0,
        "answer_count": len(question.answers) if question.answers else 0,
        "created_at": question.created_at,
        "updated_at": question.updated_at,
    }


@router.get("/companies/{company_id}/questions", response_model=InterviewQuestionListResponse)
def list_company_questions(
    company_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role"),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """List interview questions for a company."""
    try:
        company_service = CompanyService(session)
        company = company_service.get_company(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company {company_id} not found"
            )

        service = InterviewQuestionService(session)
        result = service.list_questions(
            company_id=company_id,
            page=page,
            page_size=page_size,
            role=role,
        )

        questions_response = [
            _question_to_response(q, session) for q in result["questions"]
        ]

        return InterviewQuestionListResponse(
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            questions=questions_response,
            roles=result["roles"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing questions for company %s: %s", company_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list interview questions"
        )


@router.post("/companies/{company_id}/questions", response_model=InterviewQuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    company_id: UUID,
    question_data: InterviewQuestionCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """Create a new interview question for a company."""
    try:
        company_service = CompanyService(session)
        company = company_service.get_company(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company {company_id} not found"
            )

        service = InterviewQuestionService(session)
        question = service.create_question(
            company_id=company_id,
            user_id=current_user.id,
            question_data=question_data,
        )



@router.post("/questions/{question_id}/answers", response_model=InterviewQuestionResponse)
def add_answer(
    question_id: UUID,
    answer_data: AnswerCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """Add an answer to an interview question."""
    try:
        service = InterviewQuestionService(session)
        question = service.add_answer(
            question_id=question_id,
            user_id=current_user.id,
            answer_data=answer_data,
        )

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {question_id} not found"
            )

        return _question_to_response(question, session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error adding answer to question %s: %s", question_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add answer"
        )


@router.post("/questions/{question_id}/upvote", response_model=InterviewQuestionResponse)
def upvote_question(
    question_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """Upvote an interview question."""
    try:
        service = InterviewQuestionService(session)
        question = service.upvote_question(question_id)

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {question_id} not found"
            )

        return _question_to_response(question, session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error upvoting question %s: %s", question_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upvote question"
        )


@router.get("/companies/{company_id}/questions/roles", response_model=RolesListResponse)
def get_company_question_roles(
    company_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_db_session)
):
    """Get unique roles for a company's interview questions."""
    try:
        service = InterviewQuestionService(session)
        roles = service.get_roles_for_company(company_id)
        return RolesListResponse(roles=roles)
    except Exception as e:
        logger.error("Error getting roles for company %s: %s", company_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get roles"
        )
