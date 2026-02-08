"""Statistics service."""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.classroom import Classroom, ClassroomStudent
from app.models.session import QuizSession, SessionStatus
from app.models.completion import CompletedQuiz
from app.models.leitner import LeitnerBox, LeitnerSession
from app.models.module import Module
from app.models.quiz import Quiz
from app.services.classroom_service import is_classroom_member, is_classroom_teacher


async def get_student_stats(db: AsyncSession, user: User) -> Dict[str, Any]:
    """Get student statistics."""
    # Count completed quizzes
    result = await db.execute(
        select(func.count(CompletedQuiz.quiz_id))
        .where(CompletedQuiz.student_id == user.id)
    )
    completed_quizzes = result.scalar() or 0
    
    # Calculate average score from completed sessions
    result = await db.execute(
        select(
            func.avg(QuizSession.total_score * 20.0 / QuizSession.max_score)
        )
        .where(
            QuizSession.student_id == user.id,
            QuizSession.status == SessionStatus.COMPLETED,
            QuizSession.max_score > 0
        )
    )
    avg_score = result.scalar() or 0.0
    
    # Count Leitner boxes by level
    result = await db.execute(
        select(LeitnerBox.box_level, func.count(LeitnerBox.id))
        .where(LeitnerBox.student_id == user.id)
        .group_by(LeitnerBox.box_level)
    )
    leitner_distribution = {i: 0 for i in range(1, 6)}
    for box_level, count in result.all():
        leitner_distribution[box_level] = count
    
    # Calculate Leitner mastery (weighted average)
    total_questions = sum(leitner_distribution.values())
    if total_questions > 0:
        mastery_score = sum(box_level * count for box_level, count in leitner_distribution.items()) / total_questions
    else:
        mastery_score = 0.0
    
    return {
        "completed_quizzes": completed_quizzes,
        "average_score": round(avg_score, 2),
        "leitner_distribution": leitner_distribution,
        "leitner_mastery": round(mastery_score, 2)
    }


async def get_leaderboard(
    db: AsyncSession,
    classroom_id: str,
    user: User,
    page: int = 1,
    limit: int = 50
) -> Dict[str, Any]:
    """Get classroom leaderboard."""
    # Check classroom exists first
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    # Then check membership
    if not await is_classroom_member(db, classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Get all students in classroom with their stats
    result = await db.execute(
        select(User.id, User.name, User.email)
        .join(ClassroomStudent)
        .where(ClassroomStudent.classroom_id == classroom_id)
    )
    students = result.all()
    
    leaderboard = []
    for student_id, name, email in students:
        # Count completed quizzes in this classroom
        result = await db.execute(
            select(func.count(CompletedQuiz.quiz_id))
            .join(Quiz)
            .join(Module)
            .where(
                CompletedQuiz.student_id == student_id,
                Module.classroom_id == classroom_id
            )
        )
        completed = result.scalar() or 0
        
        # Calculate average score for this classroom
        result = await db.execute(
            select(
                func.avg(QuizSession.total_score * 20.0 / QuizSession.max_score)
            )
            .where(
                QuizSession.student_id == student_id,
                QuizSession.classroom_id == classroom_id,
                QuizSession.status == SessionStatus.COMPLETED,
                QuizSession.max_score > 0
            )
        )
        avg_score = result.scalar() or 0.0
        
        leaderboard.append({
            "student_id": student_id,
            "name": name,
            "email": email,
            "completed_quizzes": completed,
            "average_score": round(avg_score, 2)
        })
    
    # Sort by completed quizzes desc, then by average score desc
    leaderboard.sort(key=lambda x: (-x["completed_quizzes"], -x["average_score"]))
    
    # Paginate
    offset = (page - 1) * limit
    paginated = leaderboard[offset:offset + limit]
    
    return {
        "data": paginated,
        "total": len(leaderboard),
        "page": page,
        "limit": limit
    }


async def get_professor_dashboard(db: AsyncSession, classroom_id: str, user: User) -> Dict[str, Any]:
    """Get professor dashboard for a classroom."""
    if not await is_classroom_teacher(db, classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Get modules in classroom
    result = await db.execute(
        select(Module).where(Module.classroom_id == classroom_id)
    )
    modules = list(result.scalars().all())
    
    module_stats = []
    for module in modules:
        # Get quizzes in module
        result = await db.execute(
            select(Quiz).where(Quiz.module_id == module.id)
        )
        quizzes = list(result.scalars().all())
        
        # Calculate average difficulty (based on average scores)
        total_avg = 0
        quiz_count = 0
        
        for quiz in quizzes:
            result = await db.execute(
                select(func.avg(QuizSession.total_score * 20.0 / QuizSession.max_score))
                .where(
                    QuizSession.quiz_id == quiz.id,
                    QuizSession.status == SessionStatus.COMPLETED,
                    QuizSession.max_score > 0
                )
            )
            avg = result.scalar()
            if avg is not None:
                total_avg += avg
                quiz_count += 1
        
        avg_score = (total_avg / quiz_count) if quiz_count > 0 else 0
        
        module_stats.append({
            "module_id": module.id,
            "module_name": module.name,
            "quiz_count": len(quizzes),
            "average_score": round(avg_score, 2)
        })
    
    # Get Leitner stats for classroom
    result = await db.execute(
        select(LeitnerBox.box_level, func.count(LeitnerBox.id))
        .where(LeitnerBox.classroom_id == classroom_id)
        .group_by(LeitnerBox.box_level)
    )
    leitner_distribution = {i: 0 for i in range(1, 6)}
    for box_level, count in result.all():
        leitner_distribution[box_level] = count
    
    # Count active students (students who have Leitner sessions)
    result = await db.execute(
        select(func.count(func.distinct(LeitnerSession.student_id)))
        .where(LeitnerSession.classroom_id == classroom_id)
    )
    active_students = result.scalar() or 0
    
    # Calculate average mastery
    total_questions = sum(leitner_distribution.values())
    if total_questions > 0:
        avg_mastery = sum(box_level * count for box_level, count in leitner_distribution.items()) / total_questions
    else:
        avg_mastery = 0.0
    
    return {
        "module_stats": module_stats,
        "leitner_stats": {
            "distribution": leitner_distribution,
            "average_mastery": round(avg_mastery, 2),
            "active_students": active_students
        }
    }
