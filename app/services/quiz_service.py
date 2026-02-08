"""Quiz service."""
from typing import List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.quiz import Quiz
from app.models.module import Module
from app.models.user import User
from app.services.classroom_service import is_classroom_teacher


MAX_PREREQUISITE_DEPTH = 50


async def get_quizzes_by_module(db: AsyncSession, module_id: str) -> List[Quiz]:
    """Get all quizzes for a module."""
    result = await db.execute(
        select(Quiz)
        .where(Quiz.module_id == module_id)
        .order_by(Quiz.created_at)
    )
    return list(result.scalars().all())


async def get_quiz_by_id(db: AsyncSession, quiz_id: str) -> Quiz:
    """Get a quiz by ID."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    
    return quiz


async def create_quiz(
    db: AsyncSession,
    module_id: str,
    title: str,
    prerequisite_quiz_id: Optional[str],
    min_score_to_unlock_next: int,
    is_active: bool,
    user: User
) -> Quiz:
    """Create a new quiz (teacher of course)."""
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    
    if not await is_classroom_teacher(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Validate min_score_to_unlock_next
    if min_score_to_unlock_next is not None and min_score_to_unlock_next < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="minScoreToUnlockNext must be >= 0"
        )
    
    # Validate prerequisite
    if prerequisite_quiz_id:
        result = await db.execute(select(Quiz).where(Quiz.id == prerequisite_quiz_id))
        prereq = result.scalar_one_or_none()
        
        if not prereq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prerequisite quiz not found")
    
    quiz = Quiz(
        module_id=module_id,
        title=title,
        prerequisite_quiz_id=prerequisite_quiz_id,
        min_score_to_unlock_next=min_score_to_unlock_next,
        is_active=is_active,
        created_by_id=user.id
    )
    
    db.add(quiz)
    await db.flush()
    
    # Check for circular dependency
    if prerequisite_quiz_id and await has_circular_quiz_prerequisite(db, quiz.id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CIRCULAR_PREREQUISITE"
        )
    
    await db.commit()
    await db.refresh(quiz)
    
    return quiz


async def update_quiz(
    db: AsyncSession,
    quiz_id: str,
    title: Optional[str],
    prerequisite_quiz_id: Optional[str],
    min_score_to_unlock_next: Optional[int],
    is_active: Optional[bool],
    user: User
) -> Quiz:
    """Update a quiz (teacher of course)."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    
    result = await db.execute(select(Module).where(Module.id == quiz.module_id))
    module = result.scalar_one_or_none()
    
    if not module or not await is_classroom_teacher(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Validate prerequisite
    if prerequisite_quiz_id is not None:
        if prerequisite_quiz_id == quiz_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CIRCULAR_PREREQUISITE"
            )
        
        if prerequisite_quiz_id:
            result = await db.execute(select(Quiz).where(Quiz.id == prerequisite_quiz_id))
            prereq = result.scalar_one_or_none()
            
            if not prereq:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prerequisite quiz not found")
    
    if title is not None:
        quiz.title = title
    if prerequisite_quiz_id is not None:
        quiz.prerequisite_quiz_id = prerequisite_quiz_id
    if min_score_to_unlock_next is not None:
        quiz.min_score_to_unlock_next = min_score_to_unlock_next
    if is_active is not None:
        quiz.is_active = is_active
    
    await db.flush()
    
    # Check for circular dependency
    if prerequisite_quiz_id and await has_circular_quiz_prerequisite(db, quiz.id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CIRCULAR_PREREQUISITE"
        )
    
    await db.commit()
    await db.refresh(quiz)
    
    return quiz


async def delete_quiz(db: AsyncSession, quiz_id: str, user: User):
    """Delete a quiz (teacher of course)."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    
    result = await db.execute(select(Module).where(Module.id == quiz.module_id))
    module = result.scalar_one_or_none()
    
    if not module or not await is_classroom_teacher(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    await db.delete(quiz)
    await db.commit()


async def has_circular_quiz_prerequisite(db: AsyncSession, quiz_id: str, visited: Optional[Set[str]] = None, depth: int = 0) -> bool:
    """Check if a quiz has a circular prerequisite dependency."""
    if depth > MAX_PREREQUISITE_DEPTH:
        return True
    
    if visited is None:
        visited = set()
    
    if quiz_id in visited:
        return True
    
    visited.add(quiz_id)
    
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz or not quiz.prerequisite_quiz_id:
        return False
    
    return await has_circular_quiz_prerequisite(db, quiz.prerequisite_quiz_id, visited, depth + 1)
