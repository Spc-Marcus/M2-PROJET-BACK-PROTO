"""Progress routes."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import progress_service

router = APIRouter()


def _to_camel_progress(data: dict) -> dict:
    """Convert progress dict keys to camelCase."""
    result = {}
    for key, value in data.items():
        # Convert snake_case to camelCase
        parts = key.split('_')
        camel = parts[0] + ''.join(p.capitalize() for p in parts[1:])
        if isinstance(value, dict):
            result[camel] = _to_camel_progress(value)
        elif isinstance(value, list):
            result[camel] = [_to_camel_progress(item) if isinstance(item, dict) else item for item in value]
        else:
            result[camel] = value
    return result


@router.get("/modules/{moduleId}")
async def get_module_progress(
    moduleId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get progress on a module."""
    result = await progress_service.get_module_progress(db, moduleId, current_user)
    return _to_camel_progress(result)


@router.get("/quizzes/{quizId}")
async def get_quiz_progress(
    quizId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get progress on a quiz."""
    result = await progress_service.get_quiz_progress(db, quizId, current_user)
    return _to_camel_progress(result)


@router.get("/classroom/{cid}")
async def get_classroom_progress(
    cid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get progress on all modules in a classroom."""
    result = await progress_service.get_classroom_progress(db, cid, current_user)
    return [_to_camel_progress(item) for item in result]


@router.get("/classroom/{cid}/student/{sid}")
async def get_student_progress(
    cid: str,
    sid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a student's progress (teacher view or self-view)."""
    # Support "me" keyword for students viewing their own progress
    if sid == "me":
        sid = current_user.id
    
    # Students can only view their own progress
    from app.models.user import Role
    if current_user.role == Role.STUDENT:
        if sid != current_user.id:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
        result = await progress_service.get_classroom_progress(db, cid, current_user)
        return [_to_camel_progress(item) for item in result]
    
    result = await progress_service.get_student_progress_for_teacher(db, cid, sid, current_user)
    return [_to_camel_progress(item) for item in result]
