from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Role
from app.models.classroom import Classroom, ClassroomTeacher
from app.models.module import Module
from app.models.quiz import Quiz
from app.models.session import CompletedQuiz
from app.schemas.quiz import QuizCreate, QuizUpdate, QuizResponse
from app.schemas.user import UserSummary

router = APIRouter(tags=["Quizzes"])


@router.get("/api/modules/{module_id}/quizzes", response_model=List[QuizResponse])
def list_quizzes(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all quizzes in a module."""
    module = _get_module_or_404(module_id, db)
    
    quizzes = db.query(Quiz).filter(Quiz.module_id == module_id).all()
    return [_quiz_to_response(q, current_user, db) for q in quizzes]


@router.post("/api/modules/{module_id}/quizzes", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(
    module_id: str,
    request: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new quiz (classroom teachers)."""
    module = _get_module_or_404(module_id, db)
    classroom = db.query(Classroom).filter(Classroom.id == module.classroom_id).first()
    _check_classroom_teacher(classroom, current_user, db)
    
    # Check for circular prerequisites
    if request.prerequisite_quiz_id:
        _check_circular_prerequisite_quiz(request.prerequisite_quiz_id, None, db)
    
    quiz = Quiz(
        module_id=module_id,
        title=request.title,
        prerequisite_quiz_id=request.prerequisite_quiz_id,
        min_score_to_unlock_next=request.min_score_to_unlock_next,
        is_active=request.is_active,
        created_by_id=current_user.id
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    return _quiz_to_response(quiz, current_user, db)


@router.put("/api/quizzes/{quiz_id}", response_model=QuizResponse)
def update_quiz(
    quiz_id: str,
    request: QuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a quiz (classroom teachers)."""
    quiz = _get_quiz_or_404(quiz_id, db)
    module = db.query(Module).filter(Module.id == quiz.module_id).first()
    classroom = db.query(Classroom).filter(Classroom.id == module.classroom_id).first()
    _check_classroom_teacher(classroom, current_user, db)
    
    if request.prerequisite_quiz_id:
        _check_circular_prerequisite_quiz(request.prerequisite_quiz_id, quiz_id, db)
    
    if request.title:
        quiz.title = request.title
    if request.prerequisite_quiz_id is not None:
        quiz.prerequisite_quiz_id = request.prerequisite_quiz_id if request.prerequisite_quiz_id else None
    if request.min_score_to_unlock_next is not None:
        quiz.min_score_to_unlock_next = request.min_score_to_unlock_next
    if request.is_active is not None:
        quiz.is_active = request.is_active
    
    db.commit()
    db.refresh(quiz)
    
    return _quiz_to_response(quiz, current_user, db)


@router.delete("/api/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a quiz (classroom teachers)."""
    quiz = _get_quiz_or_404(quiz_id, db)
    module = db.query(Module).filter(Module.id == quiz.module_id).first()
    classroom = db.query(Classroom).filter(Classroom.id == module.classroom_id).first()
    _check_classroom_teacher(classroom, current_user, db)
    
    db.delete(quiz)
    db.commit()


@router.post("/api/quizzes/import", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def import_quiz(
    file: UploadFile = File(...),
    module_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import a quiz from PowerPoint or Excel file (classroom teachers).
    
    This is a placeholder endpoint. In production, implement parsing logic for:
    - PowerPoint (.pptx): Parse slides to extract questions
    - Excel (.xlsx): Parse rows to extract questions
    """
    if current_user.role not in [Role.TEACHER, Role.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers only"
        )
    
    # Validate file type
    allowed_types = {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-powerpoint",  # .ppt
        "application/vnd.ms-excel",  # .xls
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: PowerPoint (.pptx, .ppt) or Excel (.xlsx, .xls)"
        )
    
    if not module_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="module_id is required"
        )
    
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    
    classroom = db.query(Classroom).filter(Classroom.id == module.classroom_id).first()
    _check_classroom_teacher(classroom, current_user, db)
    
    # Read file content (placeholder - in production, parse the file)
    content = await file.read()
    
    # Create a placeholder quiz
    # In production, parse the file and create questions
    quiz = Quiz(
        module_id=module_id,
        title=f"Imported: {file.filename}",
        min_score_to_unlock_next=15,
        is_active=False,  # Inactive until reviewed
        created_by_id=current_user.id
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    # TODO: Parse file and create questions
    # For PowerPoint: Use python-pptx
    # For Excel: Use openpyxl or pandas
    
    return _quiz_to_response(quiz, current_user, db)


# Helper functions
def _get_module_or_404(module_id: str, db: Session) -> Module:
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return module


def _get_quiz_or_404(quiz_id: str, db: Session) -> Quiz:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    return quiz


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


def _check_circular_prerequisite_quiz(prereq_id: str, current_id: str, db: Session, depth: int = 0):
    if depth > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "CIRCULAR_PREREQUISITE", "message": "Maximum prerequisite depth exceeded"}
        )
    
    if prereq_id == current_id and current_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "CIRCULAR_PREREQUISITE", "message": "Circular dependency detected"}
        )
    
    prereq = db.query(Quiz).filter(Quiz.id == prereq_id).first()
    if prereq and prereq.prerequisite_quiz_id:
        _check_circular_prerequisite_quiz(prereq.prerequisite_quiz_id, current_id, db, depth + 1)


def _quiz_to_response(quiz: Quiz, user: User, db: Session) -> QuizResponse:
    from app.models.question import Question
    
    # Count questions
    question_count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
    
    # Calculate is_locked for students
    is_locked = False
    if user.role == Role.STUDENT and quiz.prerequisite_quiz_id:
        completed = db.query(CompletedQuiz).filter(
            CompletedQuiz.student_id == user.id,
            CompletedQuiz.quiz_id == quiz.prerequisite_quiz_id
        ).first()
        is_locked = completed is None
    
    # Get creator info
    created_by = None
    if quiz.created_by:
        created_by = UserSummary(
            id=quiz.created_by.id,
            email=quiz.created_by.email,
            name=quiz.created_by.name,
            role=quiz.created_by.role
        )
    
    return QuizResponse(
        id=quiz.id,
        module_id=quiz.module_id,
        title=quiz.title,
        prerequisite_quiz_id=quiz.prerequisite_quiz_id,
        min_score_to_unlock_next=quiz.min_score_to_unlock_next,
        question_count=question_count,
        is_active=quiz.is_active,
        is_locked=is_locked,
        created_by=created_by,
        created_at=quiz.created_at
    )
