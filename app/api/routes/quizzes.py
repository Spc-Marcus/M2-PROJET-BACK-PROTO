"""Quiz routes."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.quiz import QuizDto, CreateQuizDto, UpdateQuizDto
from app.services import quiz_service

router = APIRouter()


@router.get("/modules/{mid}/quizzes", response_model=List[QuizDto])
async def get_quizzes(
    mid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all quizzes for a module."""
    quizzes = await quiz_service.get_quizzes_by_module(db, mid)
    return [QuizDto.model_validate(q) for q in quizzes]


@router.post("/modules/{mid}/quizzes", response_model=QuizDto, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    mid: str,
    data: CreateQuizDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new quiz."""
    quiz = await quiz_service.create_quiz(
        db, mid, data.title, data.prerequisite_quiz_id,
        data.min_score_to_unlock_next, data.is_active, current_user
    )
    return QuizDto.model_validate(quiz)


@router.get("/quizzes/{id}", response_model=QuizDto)
async def get_quiz(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get quiz by ID."""
    quiz = await quiz_service.get_quiz_by_id(db, id)
    return QuizDto.model_validate(quiz)


@router.patch("/quizzes/{id}", response_model=QuizDto)
async def update_quiz(
    id: str,
    data: UpdateQuizDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a quiz."""
    quiz = await quiz_service.update_quiz(
        db, id, data.title, data.prerequisite_quiz_id,
        data.min_score_to_unlock_next, data.is_active, current_user
    )
    return QuizDto.model_validate(quiz)


@router.delete("/quizzes/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a quiz."""
    await quiz_service.delete_quiz(db, id, current_user)
