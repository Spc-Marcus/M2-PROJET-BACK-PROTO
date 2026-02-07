"""Progress routes."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.progress import ModuleProgressDto, QuizProgressDto
from app.services import progress_service

router = APIRouter()


@router.get("/modules/{moduleId}", response_model=ModuleProgressDto)
async def get_module_progress(
    moduleId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get progress on a module."""
    return await progress_service.get_module_progress(db, moduleId, current_user)


@router.get("/quizzes/{quizId}", response_model=QuizProgressDto)
async def get_quiz_progress(
    quizId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get progress on a quiz."""
    return await progress_service.get_quiz_progress(db, quizId, current_user)


@router.get("/classroom/{cid}", response_model=List[ModuleProgressDto])
async def get_classroom_progress(
    cid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get progress on all modules in a classroom."""
    return await progress_service.get_classroom_progress(db, cid, current_user)


@router.get("/classroom/{cid}/student/{sid}", response_model=List[ModuleProgressDto])
async def get_student_progress(
    cid: str,
    sid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a student's progress (teacher view)."""
    return await progress_service.get_student_progress_for_teacher(db, cid, sid, current_user)
