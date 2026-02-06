"""Statistics routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_student
from app.models.user import User
from app.services import stats_service

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/student")
async def get_student_stats(
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get student statistics."""
    return await stats_service.get_student_stats(db, current_user)


@router.get("/leaderboard/{cid}")
async def get_leaderboard(
    cid: str,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get classroom leaderboard."""
    return await stats_service.get_leaderboard(db, cid, current_user, page, limit)


@router.get("/dashboard/{cid}")
async def get_professor_dashboard(
    cid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get professor dashboard."""
    return await stats_service.get_professor_dashboard(db, cid, current_user)
