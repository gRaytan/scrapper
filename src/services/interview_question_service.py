"""Interview Question service for business logic."""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.models.interview_question import InterviewQuestion
from src.models.user import User
from src.api.schemas.interview_question import InterviewQuestionCreate, AnswerCreate

logger = logging.getLogger(__name__)


class InterviewQuestionService:
    """Service for interview question-related business logic."""

    def __init__(self, session: Session):
        """Initialize service with database session."""
        self.session = session

    def create_question(
        self,
        company_id: UUID,
        user_id: UUID,
        question_data: InterviewQuestionCreate
    ) -> InterviewQuestion:
        """
        Create a new interview question.

        Args:
            company_id: Company UUID
            user_id: User UUID who is creating the question
            question_data: Question creation data

        Returns:
            Created interview question
        """
        question = InterviewQuestion(
            company_id=company_id,
            user_id=user_id,
            question_text=question_data.question_text,
            role=question_data.role,
            difficulty=question_data.difficulty,
            interview_stage=question_data.interview_stage,
            answers=[],
            upvotes=0,
        )

        self.session.add(question)
        self.session.commit()
        self.session.refresh(question)

        return question

    def get_question(self, question_id: UUID) -> Optional[InterviewQuestion]:
        """Get question by ID."""
        return self.session.query(InterviewQuestion).filter(
            InterviewQuestion.id == question_id
        ).first()

    def list_questions(
        self,
        company_id: UUID,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List interview questions for a company with pagination.

        Args:
            company_id: Company UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            role: Filter by role

        Returns:
            Dictionary with questions and pagination info
        """
        query = self.session.query(InterviewQuestion).filter(
            InterviewQuestion.company_id == company_id
        )

        if role:
            query = query.filter(InterviewQuestion.role == role)

        total = query.count()

        roles_query = self.session.query(InterviewQuestion.role).filter(
            InterviewQuestion.company_id == company_id
        ).distinct()
        roles = [r[0] for r in roles_query.all()]

        offset = (page - 1) * page_size
        questions = query.order_by(
            InterviewQuestion.upvotes.desc(),
            InterviewQuestion.created_at.desc()
        ).offset(offset).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "questions": questions,
            "roles": sorted(roles),
        }

    def add_answer(
        self,
        question_id: UUID,
        user_id: UUID,
        answer_data: AnswerCreate
    ) -> Optional[InterviewQuestion]:
        """
        Add an answer to a question.

        Args:
            question_id: Question UUID
            user_id: User UUID who is adding the answer
            answer_data: Answer data

        Returns:
            Updated question or None if not found
        """
        question = self.get_question(question_id)
        if not question:
            return None

        user = self.session.query(User).filter(User.id == user_id).first()
        user_name = user.full_name if user and user.full_name else "Anonymous"

        answer = {
            "id": str(uuid4()),
            "text": answer_data.text,
            "user_id": str(user_id),
            "user_name": user_name,
            "created_at": datetime.utcnow().isoformat(),
            "upvotes": 0,
        }

        answers = list(question.answers) if question.answers else []
        answers.append(answer)
        question.answers = answers

        self.session.commit()
        self.session.refresh(question)

        return question

    def upvote_question(self, question_id: UUID) -> Optional[InterviewQuestion]:
        """Upvote a question."""
        question = self.get_question(question_id)
        if not question:
            return None

        question.upvotes = (question.upvotes or 0) + 1
        self.session.commit()
        self.session.refresh(question)

        return question

    def get_roles_for_company(self, company_id: UUID) -> List[str]:
        """Get unique roles for a company's interview questions."""
        roles_query = self.session.query(InterviewQuestion.role).filter(
            InterviewQuestion.company_id == company_id
        ).distinct()
        return sorted([r[0] for r in roles_query.all()])
