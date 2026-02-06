"""Question routes."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.question import QuestionCreateDto
from app.services import question_service

router = APIRouter(tags=["questions"])


@router.get("/api/quizzes/{quizId}/questions", response_model=List[QuestionCreateDto])
async def get_questions(
    quizId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all questions for a quiz (teacher only)."""
    return await question_service.get_questions_by_quiz(db, quizId, current_user)


@router.post("/api/quizzes/{quizId}/questions", response_model=QuestionCreateDto, status_code=status.HTTP_201_CREATED)
async def create_question(
    quizId: str,
    data: QuestionCreateDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new question."""
    question_data = data.dict(by_alias=False)
    return await question_service.create_question(db, quizId, question_data, current_user)


@router.put("/api/questions/{questionId}", response_model=QuestionCreateDto)
async def update_question(
    questionId: str,
    data: QuestionCreateDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a question."""
    question_data = data.dict(by_alias=False)
    return await question_service.update_question(db, questionId, question_data, current_user)


@router.delete("/api/questions/{questionId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    questionId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a question."""
    await question_service.delete_question(db, questionId, current_user)
