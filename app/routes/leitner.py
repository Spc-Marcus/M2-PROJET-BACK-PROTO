import json
import random
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User, Role
from app.models.classroom import Classroom, ClassroomStudent
from app.models.question import Question, QuestionType
from app.models.leitner import LeitnerBox, LeitnerSession, LeitnerSessionAnswer
from app.schemas.leitner import (
    LeitnerBoxesStatus, LeitnerBoxInfo, LeitnerSessionStartRequest,
    LeitnerSessionStartResponse, LeitnerQuestionForSession,
    LeitnerSessionResult, BoxMovements, LeitnerSessionReview, LeitnerReviewAnswer
)
from app.schemas.session import SubmitAnswerRequest, AnswerResult

router = APIRouter(tags=["Leitner System"])


@router.get("/api/classrooms/{classroom_id}/leitner/status", response_model=LeitnerBoxesStatus)
def get_leitner_status(
    classroom_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Leitner boxes status for a classroom."""
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students only")
    
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_enrollment(classroom_id, current_user.id, db)
    
    # Get box counts
    boxes = []
    total = 0
    weights = settings.LEITNER_BOX_WEIGHTS
    
    for level in range(1, 6):
        count = db.query(LeitnerBox).filter(
            LeitnerBox.classroom_id == classroom_id,
            LeitnerBox.student_id == current_user.id,
            LeitnerBox.box_level == level
        ).count()
        total += count
        boxes.append(LeitnerBoxInfo(
            level=level,
            question_count=count,
            percentage=0,  # Will calculate after
            selection_weight=weights[level - 1]
        ))
    
    # Calculate percentages
    for box in boxes:
        box.percentage = (box.question_count / total * 100) if total > 0 else 0
    
    # Get last review date
    last_session = db.query(LeitnerSession).filter(
        LeitnerSession.classroom_id == classroom_id,
        LeitnerSession.student_id == current_user.id
    ).order_by(LeitnerSession.completed_at.desc()).first()
    
    return LeitnerBoxesStatus(
        classroom_id=classroom_id,
        classroom_name=classroom.name,
        total_questions=total,
        boxes=boxes,
        last_reviewed_at=last_session.completed_at if last_session else None
    )


@router.post("/api/classrooms/{classroom_id}/leitner/start", response_model=LeitnerSessionStartResponse)
def start_leitner_session(
    classroom_id: str,
    request: LeitnerSessionStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a Leitner review session."""
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students only")
    
    if request.question_count not in settings.LEITNER_VALID_QUESTION_COUNTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_QUESTION_COUNT", "message": "Must be 5, 10, 15, or 20"}
        )
    
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_enrollment(classroom_id, current_user.id, db)
    
    # Select questions based on box weights
    selected_questions = _select_leitner_questions(
        classroom_id, current_user.id, request.question_count, db
    )
    
    if not selected_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "LEITNER_NO_QUESTIONS", "message": "No questions available"}
        )
    
    # Create session
    session = LeitnerSession(
        classroom_id=classroom_id,
        student_id=current_user.id,
        question_count=len(selected_questions)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Prepare questions for response
    questions = []
    distribution = {"box1": 0, "box2": 0, "box3": 0, "box4": 0, "box5": 0}
    
    for lb in selected_questions:
        question = db.query(Question).filter(Question.id == lb.question_id).first()
        if question:
            distribution[f"box{lb.box_level}"] += 1
            questions.append(_leitner_question_for_session(question, lb.box_level, db))
    
    return LeitnerSessionStartResponse(
        session_id=session.id,
        classroom_id=classroom_id,
        questions=questions,
        selection_distribution=distribution
    )


@router.post("/api/leitner/sessions/{session_id}/submit-answer", response_model=AnswerResult)
def submit_leitner_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an answer during Leitner review."""
    session = _get_leitner_session_or_404(session_id, current_user, db)
    
    if session.completed_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already finished")
    
    # Check if already answered
    existing = db.query(LeitnerSessionAnswer).filter(
        LeitnerSessionAnswer.session_id == session_id,
        LeitnerSessionAnswer.question_id == request.question_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already answered")
    
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    
    # Get current box
    lb = db.query(LeitnerBox).filter(
        LeitnerBox.classroom_id == session.classroom_id,
        LeitnerBox.student_id == current_user.id,
        LeitnerBox.question_id == request.question_id
    ).first()
    
    if not lb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not in Leitner boxes")
    
    # Check answer
    from app.routes.session import _check_answer
    is_correct = _check_answer(question, request, db)
    
    # Calculate new box
    previous_box = lb.box_level
    if is_correct:
        new_box = min(lb.box_level + 1, 5)  # Max box 5
    else:
        new_box = 1  # Back to box 1
    
    # Save answer
    answer = LeitnerSessionAnswer(
        session_id=session_id,
        question_id=request.question_id,
        is_correct=is_correct,
        previous_box=previous_box,
        new_box=new_box,
        answer_data=json.dumps({
            "selected_option_id": request.selected_option_id,
            "clicked_coordinates": request.clicked_coordinates,
            "text_response": request.text_response,
            "matched_pairs": request.matched_pairs
        })
    )
    db.add(answer)
    
    # Update box level
    lb.box_level = new_box
    lb.last_reviewed_at = datetime.utcnow()
    
    db.commit()
    
    return AnswerResult(
        question_id=request.question_id,
        is_correct=is_correct,
        message="Réponse enregistrée."
    )


@router.post("/api/leitner/sessions/{session_id}/finish", response_model=LeitnerSessionResult)
def finish_leitner_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Finish a Leitner review session."""
    session = _get_leitner_session_or_404(session_id, current_user, db)
    
    if session.completed_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already finished")
    
    # Calculate stats
    answers = db.query(LeitnerSessionAnswer).filter(
        LeitnerSessionAnswer.session_id == session_id
    ).all()
    
    correct = sum(1 for a in answers if a.is_correct)
    wrong = len(answers) - correct
    promoted = sum(1 for a in answers if a.new_box > a.previous_box)
    demoted = sum(1 for a in answers if a.new_box < a.previous_box)
    
    session.correct_answers = correct
    session.wrong_answers = wrong
    session.promoted = promoted
    session.demoted = demoted
    session.completed_at = datetime.utcnow()
    
    db.commit()
    
    # Get new distribution
    distribution = {}
    for level in range(1, 6):
        count = db.query(LeitnerBox).filter(
            LeitnerBox.classroom_id == session.classroom_id,
            LeitnerBox.student_id == current_user.id,
            LeitnerBox.box_level == level
        ).count()
        distribution[f"box{level}"] = count
    
    accuracy = correct / len(answers) if answers else 0
    
    return LeitnerSessionResult(
        session_id=session.id,
        classroom_id=session.classroom_id,
        total_questions=session.question_count,
        correct_answers=correct,
        wrong_answers=wrong,
        accuracy_rate=accuracy,
        box_movements=BoxMovements(promoted=promoted, demoted=demoted),
        new_box_distribution=distribution
    )


@router.get("/api/leitner/sessions/{session_id}/review", response_model=LeitnerSessionReview)
def review_leitner_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed review of a completed Leitner session."""
    session = _get_leitner_session_or_404(session_id, current_user, db)
    
    if not session.completed_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session not finished yet")
    
    answers = db.query(LeitnerSessionAnswer).filter(
        LeitnerSessionAnswer.session_id == session_id
    ).all()
    
    review_answers = []
    for answer in answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        from app.routes.session import _get_correct_answer
        correct_answer = _get_correct_answer(question, db)
        
        review_answers.append(LeitnerReviewAnswer(
            question_id=answer.question_id,
            question_text=question.content_text,
            is_correct=answer.is_correct,
            previous_box=answer.previous_box,
            new_box=answer.new_box,
            correct_answer=correct_answer,
            explanation=question.explanation
        ))
    
    return LeitnerSessionReview(
        session_id=session.id,
        classroom_id=session.classroom_id,
        answers=review_answers,
        summary={
            "total_questions": session.question_count,
            "correct_answers": session.correct_answers,
            "accuracy_rate": session.correct_answers / session.question_count if session.question_count > 0 else 0
        }
    )


# Helper functions
def _get_classroom_or_404(classroom_id: str, db: Session) -> Classroom:
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    return classroom


def _check_enrollment(classroom_id: str, student_id: str, db: Session):
    enrollment = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id,
        ClassroomStudent.student_id == student_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled")


def _get_leitner_session_or_404(session_id: str, user: User, db: Session) -> LeitnerSession:
    session = db.query(LeitnerSession).filter(
        LeitnerSession.id == session_id,
        LeitnerSession.student_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


def _select_leitner_questions(classroom_id: str, student_id: str, count: int, db: Session) -> List[LeitnerBox]:
    """Select questions based on Leitner box weights."""
    weights = settings.LEITNER_BOX_WEIGHTS  # [50, 25, 15, 7, 3]
    
    # Get all questions by box
    boxes = {}
    for level in range(1, 6):
        boxes[level] = db.query(LeitnerBox).filter(
            LeitnerBox.classroom_id == classroom_id,
            LeitnerBox.student_id == student_id,
            LeitnerBox.box_level == level
        ).all()
    
    # Redistribute weights for empty boxes
    active_weights = []
    active_levels = []
    for level in range(1, 6):
        if boxes[level]:
            active_weights.append(weights[level - 1])
            active_levels.append(level)
    
    if not active_levels:
        return []
    
    # Normalize weights
    total_weight = sum(active_weights)
    normalized = [w / total_weight for w in active_weights]
    
    # Select questions
    selected = []
    for _ in range(count):
        if not any(boxes[l] for l in active_levels):
            break
        
        # Choose box based on weights
        r = random.random()
        cumulative = 0
        chosen_level = active_levels[0]
        for i, level in enumerate(active_levels):
            cumulative += normalized[i]
            if r <= cumulative and boxes[level]:
                chosen_level = level
                break
        
        if boxes[chosen_level]:
            question = random.choice(boxes[chosen_level])
            boxes[chosen_level].remove(question)
            selected.append(question)
    
    return selected


def _leitner_question_for_session(question: Question, current_box: int, db: Session) -> LeitnerQuestionForSession:
    """Format question for Leitner session."""
    options = None
    matching_left = None
    matching_right = None
    
    if question.type in [QuestionType.QCM, QuestionType.VRAI_FAUX]:
        options = [
            {"id": o.id, "text_choice": o.text_choice}
            for o in sorted(question.options, key=lambda x: x.display_order)
        ]
    elif question.type == QuestionType.MATCHING:
        matching_left = [{"id": p.id, "item": p.item_left} for p in question.matching_pairs]
        matching_right = [{"id": p.id, "item": p.item_right} for p in question.matching_pairs]
        random.shuffle(matching_right)
    
    media_url = question.media.url if question.media else None
    
    return LeitnerQuestionForSession(
        id=question.id,
        type=question.type.value,
        content_text=question.content_text,
        media_url=media_url,
        current_box=current_box,
        options=options,
        matching_items_left=matching_left,
        matching_items_right=matching_right
    )
