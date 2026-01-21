from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Role
from app.models.classroom import Classroom, ClassroomStudent, ClassroomTeacher
from app.models.module import Module
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.session import QuizSession, SessionAnswer, CompletedQuiz, CompletedModule, SessionStatus
from app.models.leitner import LeitnerBox, LeitnerSession
from app.schemas.leitner import (
    QuizProgress, ModuleProgress, StudentStats, ClassroomProgress,
    LeaderboardEntry, ProfessorDashboard, ModuleStats, LeitnerGlobalStats, HardQuestion
)
from app.schemas.common import PaginatedResponse, create_pagination

router = APIRouter(tags=["Stats & Progress"])


# ============== Student Progress ==============

@router.get("/api/progress/modules/{module_id}", response_model=ModuleProgress)
def get_module_progress(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get student's progress on a module."""
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students only")
    
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    
    return _calculate_module_progress(module, current_user.id, db)


@router.get("/api/progress/quizzes/{quiz_id}", response_model=QuizProgress)
def get_quiz_progress(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get student's progress on a quiz."""
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students only")
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    
    return _calculate_quiz_progress(quiz, current_user.id, db)


@router.get("/api/progress/classroom/{classroom_id}", response_model=List[ModuleProgress])
def get_classroom_progress(
    classroom_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get student's progress on all modules in a classroom."""
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students only")
    
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    modules = db.query(Module).filter(Module.classroom_id == classroom_id).all()
    return [_calculate_module_progress(m, current_user.id, db) for m in modules]


@router.get("/api/progress/classroom/{classroom_id}/student/{student_id}", response_model=List[ModuleProgress])
def get_student_progress_in_classroom(
    classroom_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a student's progress in a classroom (teachers only)."""
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    _check_classroom_teacher(classroom, current_user, db)
    
    modules = db.query(Module).filter(Module.classroom_id == classroom_id).all()
    return [_calculate_module_progress(m, student_id, db) for m in modules]


# ============== Statistics ==============

@router.get("/api/stats/student", response_model=StudentStats)
def get_student_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get student's global statistics."""
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students only")
    
    # Total completed quizzes
    total_completed = db.query(CompletedQuiz).filter(
        CompletedQuiz.student_id == current_user.id
    ).count()
    
    # Average score
    avg_score = db.query(func.avg(QuizSession.total_score)).filter(
        QuizSession.student_id == current_user.id,
        QuizSession.status == SessionStatus.COMPLETED
    ).scalar() or 0
    
    # Leitner mastery (% in boxes 4-5)
    total_leitner = db.query(LeitnerBox).filter(
        LeitnerBox.student_id == current_user.id
    ).count()
    
    mastered = db.query(LeitnerBox).filter(
        LeitnerBox.student_id == current_user.id,
        LeitnerBox.box_level >= 4
    ).count()
    
    leitner_mastery = mastered / total_leitner if total_leitner > 0 else 0
    
    # Progress per classroom
    enrollments = db.query(ClassroomStudent).filter(
        ClassroomStudent.student_id == current_user.id
    ).all()
    
    classrooms_progress = []
    for enrollment in enrollments:
        classroom = db.query(Classroom).filter(Classroom.id == enrollment.classroom_id).first()
        if classroom:
            classrooms_progress.append(_calculate_classroom_progress(classroom, current_user.id, db))
    
    return StudentStats(
        student_id=current_user.id,
        total_completed_quizzes=total_completed,
        average_score=float(avg_score),
        leitner_mastery=leitner_mastery,
        classrooms_progress=classrooms_progress
    )


@router.get("/api/stats/leaderboard/{classroom_id}", response_model=List[LeaderboardEntry])
def get_leaderboard(
    classroom_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get classroom leaderboard."""
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    # Get all students
    enrollments = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id
    ).all()
    
    entries = []
    for enrollment in enrollments:
        student = db.query(User).filter(User.id == enrollment.student_id).first()
        if not student:
            continue
        
        # Count completed quizzes
        completed = db.query(CompletedQuiz).join(Quiz).join(Module).filter(
            CompletedQuiz.student_id == student.id,
            Module.classroom_id == classroom_id
        ).count()
        
        # Average score
        avg = db.query(func.avg(QuizSession.total_score)).filter(
            QuizSession.student_id == student.id,
            QuizSession.classroom_id == classroom_id,
            QuizSession.status == SessionStatus.COMPLETED
        ).scalar() or 0
        
        # Leitner mastery
        total = db.query(LeitnerBox).filter(
            LeitnerBox.student_id == student.id,
            LeitnerBox.classroom_id == classroom_id
        ).count()
        mastered = db.query(LeitnerBox).filter(
            LeitnerBox.student_id == student.id,
            LeitnerBox.classroom_id == classroom_id,
            LeitnerBox.box_level >= 4
        ).count()
        mastery = mastered / total if total > 0 else 0
        
        entries.append({
            "student_id": student.id,
            "student_name": student.name,
            "completed_quizzes": completed,
            "average_score": float(avg),
            "leitner_mastery": mastery
        })
    
    # Sort by completed quizzes, then average score
    entries.sort(key=lambda x: (-x["completed_quizzes"], -x["average_score"]))
    
    # Add ranks and paginate
    result = []
    for i, entry in enumerate(entries):
        result.append(LeaderboardEntry(
            rank=i + 1,
            **entry
        ))
    
    # Paginate
    start = (page - 1) * limit
    end = start + limit
    return result[start:end]


@router.get("/api/stats/dashboard/{classroom_id}", response_model=ProfessorDashboard)
def get_professor_dashboard(
    classroom_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get professor dashboard for a classroom."""
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    _check_classroom_teacher(classroom, current_user, db)
    
    modules = db.query(Module).filter(Module.classroom_id == classroom_id).all()
    
    modules_stats = []
    for module in modules:
        # Average score for module
        avg = db.query(func.avg(QuizSession.total_score)).join(Quiz).filter(
            Quiz.module_id == module.id,
            QuizSession.status == SessionStatus.COMPLETED
        ).scalar() or 0
        
        # Completion rate
        total_students = db.query(ClassroomStudent).filter(
            ClassroomStudent.classroom_id == classroom_id
        ).count()
        
        completed_students = db.query(CompletedModule).filter(
            CompletedModule.module_id == module.id
        ).count()
        
        completion_rate = completed_students / total_students if total_students > 0 else 0
        
        # Find struggling students (below 50% average)
        alert_students = []
        enrollments = db.query(ClassroomStudent).filter(
            ClassroomStudent.classroom_id == classroom_id
        ).all()
        
        for enrollment in enrollments:
            student_avg = db.query(func.avg(QuizSession.total_score)).join(Quiz).filter(
                Quiz.module_id == module.id,
                QuizSession.student_id == enrollment.student_id,
                QuizSession.status == SessionStatus.COMPLETED
            ).scalar()
            if student_avg is not None and student_avg < 10:  # Below 50%
                student = db.query(User).filter(User.id == enrollment.student_id).first()
                if student:
                    alert_students.append(student.name)
        
        # Hardest questions
        quizzes = db.query(Quiz).filter(Quiz.module_id == module.id).all()
        quiz_ids = [q.id for q in quizzes]
        
        hard_questions = []
        questions = db.query(Question).filter(Question.quiz_id.in_(quiz_ids)).all()
        for question in questions:
            total_attempts = db.query(SessionAnswer).filter(
                SessionAnswer.question_id == question.id
            ).count()
            wrong = db.query(SessionAnswer).filter(
                SessionAnswer.question_id == question.id,
                SessionAnswer.is_correct == False
            ).count()
            if total_attempts > 5:  # Only consider if enough attempts
                failure_rate = wrong / total_attempts
                if failure_rate > 0.5:
                    hard_questions.append(HardQuestion(
                        question_text=question.content_text[:50] + "...",
                        failure_rate=failure_rate
                    ))
        
        hard_questions.sort(key=lambda x: -x.failure_rate)
        
        modules_stats.append(ModuleStats(
            module_name=module.name,
            average_score=float(avg),
            completion_rate=completion_rate,
            alert_students=alert_students[:5],  # Top 5
            hardest_questions=hard_questions[:5]  # Top 5
        ))
    
    # Leitner global stats
    total_students = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id
    ).count()
    
    active_students = db.query(LeitnerSession.student_id).filter(
        LeitnerSession.classroom_id == classroom_id
    ).distinct().count()
    
    # Average mastery
    all_boxes = db.query(LeitnerBox).filter(
        LeitnerBox.classroom_id == classroom_id
    ).count()
    mastered_boxes = db.query(LeitnerBox).filter(
        LeitnerBox.classroom_id == classroom_id,
        LeitnerBox.box_level >= 4
    ).count()
    avg_mastery = mastered_boxes / all_boxes if all_boxes > 0 else 0
    
    # Students with questions in box 5
    box5_students = db.query(LeitnerBox.student_id).filter(
        LeitnerBox.classroom_id == classroom_id,
        LeitnerBox.box_level == 5
    ).distinct().count()
    
    return ProfessorDashboard(
        classroom_id=classroom_id,
        modules_stats=modules_stats,
        leitner_stats=LeitnerGlobalStats(
            total_active_students=active_students,
            average_mastery=avg_mastery,
            students_in_box5=box5_students
        )
    )


# Helper functions
def _check_classroom_teacher(classroom: Classroom, user: User, db: Session):
    if user.role == Role.ADMIN:
        return
    if classroom.responsible_professor_id == user.id:
        return
    
    teacher_link = db.query(ClassroomTeacher).filter(
        ClassroomTeacher.classroom_id == classroom.id,
        ClassroomTeacher.teacher_id == user.id
    ).first()
    if not teacher_link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Classroom teacher access required"
        )


def _calculate_quiz_progress(quiz: Quiz, student_id: str, db: Session) -> QuizProgress:
    # Check if completed
    completed = db.query(CompletedQuiz).filter(
        CompletedQuiz.student_id == student_id,
        CompletedQuiz.quiz_id == quiz.id
    ).first()
    
    # Get sessions
    sessions = db.query(QuizSession).filter(
        QuizSession.student_id == student_id,
        QuizSession.quiz_id == quiz.id,
        QuizSession.status == SessionStatus.COMPLETED
    ).all()
    
    best_score = max([s.total_score for s in sessions]) if sessions else None
    first_attempt = min([s.completed_at for s in sessions]) if sessions else None
    last_attempt = max([s.completed_at for s in sessions]) if sessions else None
    
    return QuizProgress(
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        is_completed=completed is not None,
        best_score=best_score,
        attempts_count=len(sessions),
        first_attempt_at=first_attempt,
        last_attempt_at=last_attempt,
        completed_at=completed.completed_at if completed else None
    )


def _calculate_module_progress(module: Module, student_id: str, db: Session) -> ModuleProgress:
    # Check if completed
    completed = db.query(CompletedModule).filter(
        CompletedModule.student_id == student_id,
        CompletedModule.module_id == module.id
    ).first()
    
    # Count quizzes
    total_quizzes = db.query(Quiz).filter(Quiz.module_id == module.id).count()
    
    completed_quizzes = db.query(CompletedQuiz).join(Quiz).filter(
        CompletedQuiz.student_id == student_id,
        Quiz.module_id == module.id
    ).count()
    
    completion_rate = completed_quizzes / total_quizzes if total_quizzes > 0 else 0
    
    return ModuleProgress(
        module_id=module.id,
        module_name=module.name,
        is_completed=completed is not None,
        completed_at=completed.completed_at if completed else None,
        completed_quizzes_count=completed_quizzes,
        total_quizzes_count=total_quizzes,
        completion_rate=completion_rate
    )


def _calculate_classroom_progress(classroom: Classroom, student_id: str, db: Session) -> ClassroomProgress:
    # Count quizzes
    modules = db.query(Module).filter(Module.classroom_id == classroom.id).all()
    module_ids = [m.id for m in modules]
    
    total_quizzes = db.query(Quiz).filter(Quiz.module_id.in_(module_ids)).count()
    
    completed_quizzes = db.query(CompletedQuiz).join(Quiz).filter(
        CompletedQuiz.student_id == student_id,
        Quiz.module_id.in_(module_ids)
    ).count()
    
    # Average score
    avg = db.query(func.avg(QuizSession.total_score)).filter(
        QuizSession.student_id == student_id,
        QuizSession.classroom_id == classroom.id,
        QuizSession.status == SessionStatus.COMPLETED
    ).scalar() or 0
    
    # Leitner mastery
    total = db.query(LeitnerBox).filter(
        LeitnerBox.student_id == student_id,
        LeitnerBox.classroom_id == classroom.id
    ).count()
    mastered = db.query(LeitnerBox).filter(
        LeitnerBox.student_id == student_id,
        LeitnerBox.classroom_id == classroom.id,
        LeitnerBox.box_level >= 4
    ).count()
    mastery = mastered / total if total > 0 else 0
    
    return ClassroomProgress(
        classroom_id=classroom.id,
        classroom_name=classroom.name,
        completed_quizzes=completed_quizzes,
        total_quizzes=total_quizzes,
        average_score=float(avg),
        leitner_mastery=mastery
    )
