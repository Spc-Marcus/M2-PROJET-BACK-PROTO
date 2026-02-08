"""Statistics routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_student
from app.models.user import User
from app.services import stats_service

router = APIRouter()


@router.get("/student")
async def get_student_stats(
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get student statistics."""
    result = await stats_service.get_student_stats(db, current_user)
    # Convert to camelCase format expected by tests
    return {
        "totalCompletedQuizzes": result.get("completed_quizzes", 0),
        "averageScore": result.get("average_score", 0.0),
        "leitnerMastery": result.get("leitner_mastery", 0.0),
        "leitnerDistribution": result.get("leitner_distribution", {}),
        "classroomsProgress": []
    }


@router.get("/leaderboard/{cid}")
async def get_leaderboard(
    cid: str,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get classroom leaderboard."""
    result = await stats_service.get_leaderboard(db, cid, current_user, page, limit)
    
    # Add rank and camelCase fields to each entry
    entries = []
    for i, entry in enumerate(result.get("data", []), start=1):
        entries.append({
            "rank": (result.get("page", 1) - 1) * result.get("limit", 50) + i,
            "studentId": entry.get("student_id"),
            "studentName": entry.get("name"),
            "completedQuizzes": entry.get("completed_quizzes", 0),
            "averageScore": entry.get("average_score", 0.0),
            "leitnerMastery": 0.0
        })
    
    return {
        "data": entries,
        "total": result.get("total", 0),
        "page": result.get("page", page),
        "limit": result.get("limit", limit)
    }


@router.get("/dashboard/{cid}")
async def get_professor_dashboard(
    cid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get professor dashboard."""
    result = await stats_service.get_professor_dashboard(db, cid, current_user)
    
    # Convert to camelCase format
    modules_stats = []
    for ms in result.get("module_stats", []):
        modules_stats.append({
            "moduleName": ms.get("module_name", ""),
            "averageScore": ms.get("average_score", 0.0),
            "completionRate": 0.0,
            "alertStudents": [],
            "hardestQuestions": []
        })
    
    leitner_stats_raw = result.get("leitner_stats", {})
    
    return {
        "classroomId": cid,
        "modulesStats": modules_stats,
        "leitnerStats": {
            "totalActiveStudents": leitner_stats_raw.get("active_students", 0),
            "averageMastery": leitner_stats_raw.get("average_mastery", 0.0),
            "studentsInBox5": 0,
            "distribution": leitner_stats_raw.get("distribution", {})
        },
        "hardestQuestions": [],
        "alertStudents": []
    }
