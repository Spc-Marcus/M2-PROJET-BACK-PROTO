from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Role
from app.models.classroom import Classroom, ClassroomTeacher
from app.models.module import Module
from app.models.quiz import Quiz
from app.models.question import (
    Question, QuestionType, QuestionOption, MatchingPair,
    ImageZone, TextConfig, Media
)
from app.schemas.question import (
    QuestionCreate, QuestionResponse, QuestionOptionResponse,
    MatchingPairResponse, ImageZoneResponse, TextConfigResponse
)

router = APIRouter(tags=["Questions"])


@router.get("/api/quizzes/{quiz_id}/questions", response_model=List[QuestionResponse])
def list_questions(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all questions in a quiz with answers (teachers only)."""
    quiz = _get_quiz_or_404(quiz_id, db)
    module = db.query(Module).filter(Module.id == quiz.module_id).first()
    classroom = db.query(Classroom).filter(Classroom.id == module.classroom_id).first()
    _check_classroom_teacher(classroom, current_user, db)
    
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    return [_question_to_response(q, db) for q in questions]


@router.post("/api/quizzes/{quiz_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    quiz_id: str,
    request: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new question (teachers only)."""
    quiz = _get_quiz_or_404(quiz_id, db)
    module = db.query(Module).filter(Module.id == quiz.module_id).first()
    classroom = db.query(Classroom).filter(Classroom.id == module.classroom_id).first()
    _check_classroom_teacher(classroom, current_user, db)
    
    # Create question
    question = Question(
        quiz_id=quiz_id,
        type=request.type,
        content_text=request.content_text,
        explanation=request.explanation,
        media_id=request.media_id
    )
    db.add(question)
    db.flush()
    
    # Create type-specific data
    if request.type in [QuestionType.QCM, QuestionType.VRAI_FAUX]:
        if not request.options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Options required for QCM/VRAI_FAUX"
            )
        for opt in request.options:
            option = QuestionOption(
                question_id=question.id,
                text_choice=opt.text_choice,
                is_correct=opt.is_correct,
                display_order=opt.display_order
            )
            db.add(option)
    
    elif request.type == QuestionType.MATCHING:
        if not request.matching_pairs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Matching pairs required for MATCHING"
            )
        for pair in request.matching_pairs:
            mp = MatchingPair(
                question_id=question.id,
                item_left=pair.item_left,
                item_right=pair.item_right
            )
            db.add(mp)
    
    elif request.type == QuestionType.IMAGE:
        if not request.image_zones:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image zones required for IMAGE"
            )
        for zone in request.image_zones:
            iz = ImageZone(
                question_id=question.id,
                label_name=zone.label_name,
                x=zone.x,
                y=zone.y,
                radius=zone.radius
            )
            db.add(iz)
    
    elif request.type == QuestionType.TEXT:
        if not request.text_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text config required for TEXT"
            )
        tc = TextConfig(
            question_id=question.id,
            accepted_answer=request.text_config.accepted_answer,
            is_case_sensitive=request.text_config.is_case_sensitive,
            ignore_spelling_errors=request.text_config.ignore_spelling_errors
        )
        db.add(tc)
    
    db.commit()
    db.refresh(question)
    
    return _question_to_response(question, db)


@router.put("/api/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: str,
    request: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a question (teachers only)."""
    question = _get_question_or_404(question_id, db)
    quiz = db.query(Quiz).filter(Quiz.id == question.quiz_id).first()
    module = db.query(Module).filter(Module.id == quiz.module_id).first()
    classroom = db.query(Classroom).filter(Classroom.id == module.classroom_id).first()
    _check_classroom_teacher(classroom, current_user, db)
    
    # Update basic fields
    question.type = request.type
    question.content_text = request.content_text
    question.explanation = request.explanation
    question.media_id = request.media_id
    
    # Delete old type-specific data
    db.query(QuestionOption).filter(QuestionOption.question_id == question_id).delete()
    db.query(MatchingPair).filter(MatchingPair.question_id == question_id).delete()
    db.query(ImageZone).filter(ImageZone.question_id == question_id).delete()
    db.query(TextConfig).filter(TextConfig.question_id == question_id).delete()
    
    # Create new type-specific data
    if request.type in [QuestionType.QCM, QuestionType.VRAI_FAUX] and request.options:
        for opt in request.options:
            option = QuestionOption(
                question_id=question.id,
                text_choice=opt.text_choice,
                is_correct=opt.is_correct,
                display_order=opt.display_order
            )
            db.add(option)
    
    elif request.type == QuestionType.MATCHING and request.matching_pairs:
        for pair in request.matching_pairs:
            mp = MatchingPair(
                question_id=question.id,
                item_left=pair.item_left,
                item_right=pair.item_right
            )
            db.add(mp)
    
    elif request.type == QuestionType.IMAGE and request.image_zones:
        for zone in request.image_zones:
            iz = ImageZone(
                question_id=question.id,
                label_name=zone.label_name,
                x=zone.x,
                y=zone.y,
                radius=zone.radius
            )
            db.add(iz)
    
    elif request.type == QuestionType.TEXT and request.text_config:
        tc = TextConfig(
            question_id=question.id,
            accepted_answer=request.text_config.accepted_answer,
            is_case_sensitive=request.text_config.is_case_sensitive,
            ignore_spelling_errors=request.text_config.ignore_spelling_errors
        )
        db.add(tc)
    
    db.commit()
    db.refresh(question)
    
    return _question_to_response(question, db)


@router.delete("/api/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a question (teachers only)."""
    question = _get_question_or_404(question_id, db)
    quiz = db.query(Quiz).filter(Quiz.id == question.quiz_id).first()
    module = db.query(Module).filter(Module.id == quiz.module_id).first()
    classroom = db.query(Classroom).filter(Classroom.id == module.classroom_id).first()
    _check_classroom_teacher(classroom, current_user, db)
    
    db.delete(question)
    db.commit()


# Helper functions
def _get_quiz_or_404(quiz_id: str, db: Session) -> Quiz:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    return quiz


def _get_question_or_404(question_id: str, db: Session) -> Question:
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return question


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


def _question_to_response(question: Question, db: Session) -> QuestionResponse:
    media_url = None
    if question.media:
        media_url = question.media.url
    
    options = [
        QuestionOptionResponse(
            id=o.id,
            text_choice=o.text_choice,
            is_correct=o.is_correct,
            display_order=o.display_order
        )
        for o in question.options
    ]
    
    matching_pairs = [
        MatchingPairResponse(id=p.id, item_left=p.item_left, item_right=p.item_right)
        for p in question.matching_pairs
    ]
    
    image_zones = [
        ImageZoneResponse(id=z.id, label_name=z.label_name, x=z.x, y=z.y, radius=z.radius)
        for z in question.image_zones
    ]
    
    text_config = None
    if question.text_config:
        text_config = TextConfigResponse(
            id=question.text_config.id,
            accepted_answer=question.text_config.accepted_answer,
            is_case_sensitive=question.text_config.is_case_sensitive,
            ignore_spelling_errors=question.text_config.ignore_spelling_errors
        )
    
    return QuestionResponse(
        id=question.id,
        quiz_id=question.quiz_id,
        type=question.type,
        content_text=question.content_text,
        explanation=question.explanation,
        media_url=media_url,
        options=options,
        matching_pairs=matching_pairs,
        image_zones=image_zones,
        text_config=text_config
    )
