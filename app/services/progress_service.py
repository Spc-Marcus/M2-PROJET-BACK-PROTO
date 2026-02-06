"""Progress service."""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.module import Module
from app.models.quiz import Quiz
from app.models.session import QuizSession, SessionStatus
from app.models.completion import CompletedQuiz, CompletedModule
from app.services.classroom_service import is_classroom_member, is_classroom_teacher


async def get_module_progress(db: AsyncSession, module_id: str, user: User) -> Dict[str, Any]:
    """Get student progress on a module."""
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    
    if not await is_classroom_member(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Check if module is locked
    is_locked = False
    if module.prerequisite_module_id:
        result = await db.execute(
            select(CompletedModule)
            .where(
                CompletedModule.student_id == user.id,
                CompletedModule.module_id == module.prerequisite_module_id
            )
        )
        is_locked = result.scalar_one_or_none() is None
    
    # Get all quizzes in module
    result = await db.execute(
        select(Quiz).where(Quiz.module_id == module_id)
    )
    quizzes = list(result.scalars().all())
    
    # Get progress for each quiz
    quiz_progress = []
    completed_count = 0
    
    for quiz in quizzes:
        # Check if completed
        result = await db.execute(
            select(CompletedQuiz)
            .where(CompletedQuiz.student_id == user.id, CompletedQuiz.quiz_id == quiz.id)
        )
        is_completed = result.scalar_one_or_none() is not None
        
        if is_completed:
            completed_count += 1
        
        # Get best score and attempts
        result = await db.execute(
            select(
                func.max(QuizSession.total_score * 20.0 / QuizSession.max_score),
                func.count(QuizSession.id)
            )
            .where(
                QuizSession.quiz_id == quiz.id,
                QuizSession.student_id == user.id,
                QuizSession.status == SessionStatus.COMPLETED,
                QuizSession.max_score > 0
            )
        )
        best_score, attempts = result.one()
        
        quiz_progress.append({
            "quiz_id": quiz.id,
            "quiz_title": quiz.title,
            "is_completed": is_completed,
            "best_score": round(best_score, 2) if best_score else None,
            "attempts": attempts or 0
        })
    
    # Check if module is completed
    result = await db.execute(
        select(CompletedModule)
        .where(CompletedModule.student_id == user.id, CompletedModule.module_id == module_id)
    )
    is_module_completed = result.scalar_one_or_none() is not None
    
    return {
        "module_id": module.id,
        "module_name": module.name,
        "is_locked": is_locked,
        "is_completed": is_module_completed,
        "total_quizzes": len(quizzes),
        "completed_quizzes": completed_count,
        "quiz_progress": quiz_progress
    }


async def get_quiz_progress(db: AsyncSession, quiz_id: str, user: User) -> Dict[str, Any]:
    """Get student progress on a quiz."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    
    result = await db.execute(select(Module).where(Module.id == quiz.module_id))
    module = result.scalar_one_or_none()
    
    if not module or not await is_classroom_member(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Check if quiz is locked
    is_locked = False
    if quiz.prerequisite_quiz_id:
        result = await db.execute(
            select(CompletedQuiz)
            .where(
                CompletedQuiz.student_id == user.id,
                CompletedQuiz.quiz_id == quiz.prerequisite_quiz_id
            )
        )
        is_locked = result.scalar_one_or_none() is None
    
    # Check if completed
    result = await db.execute(
        select(CompletedQuiz)
        .where(CompletedQuiz.student_id == user.id, CompletedQuiz.quiz_id == quiz_id)
    )
    is_completed = result.scalar_one_or_none() is not None
    
    # Get best score and attempts
    result = await db.execute(
        select(
            func.max(QuizSession.total_score * 20.0 / QuizSession.max_score),
            func.count(QuizSession.id)
        )
        .where(
            QuizSession.quiz_id == quiz_id,
            QuizSession.student_id == user.id,
            QuizSession.status == SessionStatus.COMPLETED,
            QuizSession.max_score > 0
        )
    )
    best_score, attempts = result.one()
    
    return {
        "quiz_id": quiz.id,
        "quiz_title": quiz.title,
        "is_locked": is_locked,
        "is_completed": is_completed,
        "best_score": round(best_score, 2) if best_score else None,
        "attempts": attempts or 0,
        "min_score_to_unlock": quiz.min_score_to_unlock_next
    }


async def get_classroom_progress(db: AsyncSession, classroom_id: str, user: User) -> List[Dict[str, Any]]:
    """Get student progress on all modules in a classroom."""
    if not await is_classroom_member(db, classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Get all modules
    result = await db.execute(
        select(Module)
        .where(Module.classroom_id == classroom_id)
        .order_by(Module.created_at)
    )
    modules = list(result.scalars().all())
    
    progress = []
    for module in modules:
        module_progress = await get_module_progress(db, module.id, user)
        progress.append(module_progress)
    
    return progress


async def get_student_progress_for_teacher(
    db: AsyncSession,
    classroom_id: str,
    student_id: str,
    user: User
) -> List[Dict[str, Any]]:
    """Get a specific student's progress (teacher view)."""
    if not await is_classroom_teacher(db, classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Fetch the student user from database
    result = await db.execute(select(User).where(User.id == student_id))
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    # Get all modules
    result = await db.execute(
        select(Module)
        .where(Module.classroom_id == classroom_id)
        .order_by(Module.created_at)
    )
    modules = list(result.scalars().all())
    
    progress = []
    for module in modules:
        module_progress = await get_module_progress(db, module.id, student)
        progress.append(module_progress)
    
    return progress
