import json
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Role
from app.models.classroom import Classroom, ClassroomStudent
from app.models.module import Module
from app.models.quiz import Quiz
from app.models.question import Question, QuestionType, QuestionOption, MatchingPair, ImageZone, TextConfig
from app.models.session import QuizSession, SessionAnswer, SessionStatus, CompletedQuiz, CompletedModule
from app.models.leitner import LeitnerBox
from app.schemas.session import (
    StartSessionRequest, GameSessionStart, SubmitAnswerRequest,
    AnswerResult, SessionResult, SessionReview, SessionReviewAnswer
)
from app.schemas.question import QuestionForGameplay

router = APIRouter(prefix="/api/sessions", tags=["Game Sessions"])


@router.post("/start", response_model=GameSessionStart)
def start_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new quiz session (students only)."""
    if current_user.role != Role.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students only")
    
    quiz = db.query(Quiz).filter(Quiz.id == request.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    
    if not quiz.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz is not active")
    
    # Check if quiz is locked
    if quiz.prerequisite_quiz_id:
        completed = db.query(CompletedQuiz).filter(
            CompletedQuiz.student_id == current_user.id,
            CompletedQuiz.quiz_id == quiz.prerequisite_quiz_id
        ).first()
        if not completed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "QUIZ_LOCKED", "message": "Complete prerequisite quiz first"}
            )
    
    # Get classroom
    module = db.query(Module).filter(Module.id == quiz.module_id).first()
    
    # Check enrollment
    enrollment = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == module.classroom_id,
        ClassroomStudent.student_id == current_user.id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this classroom")
    
    # Get questions
    questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
    if not questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz has no questions")
    
    # Create session
    session = QuizSession(
        quiz_id=quiz.id,
        student_id=current_user.id,
        classroom_id=module.classroom_id,
        max_score=len(questions)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Prepare questions for gameplay (without correct answers)
    gameplay_questions = []
    for q in questions:
        gq = _question_for_gameplay(q, db)
        gameplay_questions.append(gq)
    
    return GameSessionStart(
        session_id=session.id,
        questions=gameplay_questions
    )


@router.post("/{session_id}/submit-answer", response_model=AnswerResult)
def submit_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an answer for a question in the session."""
    session = _get_session_or_404(session_id, current_user, db)
    
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "SESSION_ALREADY_FINISHED", "message": "Session already finished"}
        )
    
    # Check if already answered
    existing = db.query(SessionAnswer).filter(
        SessionAnswer.session_id == session_id,
        SessionAnswer.question_id == request.question_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already answered")
    
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question or question.quiz_id != session.quiz_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    
    # Check answer
    is_correct = _check_answer(question, request, db)
    
    # Save answer
    answer = SessionAnswer(
        session_id=session_id,
        question_id=request.question_id,
        is_correct=is_correct,
        answer_data=json.dumps({
            "selected_option_id": request.selected_option_id,
            "clicked_coordinates": request.clicked_coordinates,
            "text_response": request.text_response,
            "matched_pairs": request.matched_pairs
        })
    )
    db.add(answer)
    db.commit()
    
    return AnswerResult(
        question_id=request.question_id,
        is_correct=is_correct,
        message="Réponse enregistrée."
    )


@router.post("/{session_id}/finish", response_model=SessionResult)
def finish_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Finish a quiz session and calculate score."""
    session = _get_session_or_404(session_id, current_user, db)
    
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "SESSION_ALREADY_FINISHED", "message": "Session already finished"}
        )
    
    # Calculate score
    correct_count = db.query(SessionAnswer).filter(
        SessionAnswer.session_id == session_id,
        SessionAnswer.is_correct == True
    ).count()
    
    quiz = db.query(Quiz).filter(Quiz.id == session.quiz_id).first()
    passed = correct_count >= quiz.min_score_to_unlock_next if quiz.min_score_to_unlock_next > 0 else True
    
    session.total_score = correct_count
    session.passed = passed
    session.status = SessionStatus.COMPLETED
    session.completed_at = datetime.utcnow()
    
    # If passed, create CompletedQuiz and add questions to Leitner
    if passed:
        existing_complete = db.query(CompletedQuiz).filter(
            CompletedQuiz.student_id == current_user.id,
            CompletedQuiz.quiz_id == quiz.id
        ).first()
        
        if not existing_complete:
            completed = CompletedQuiz(
                student_id=current_user.id,
                quiz_id=quiz.id
            )
            db.add(completed)
            
            # Add questions to Leitner box 1
            questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
            for q in questions:
                existing_box = db.query(LeitnerBox).filter(
                    LeitnerBox.student_id == current_user.id,
                    LeitnerBox.classroom_id == session.classroom_id,
                    LeitnerBox.question_id == q.id
                ).first()
                if not existing_box:
                    lb = LeitnerBox(
                        classroom_id=session.classroom_id,
                        student_id=current_user.id,
                        question_id=q.id,
                        box_level=1
                    )
                    db.add(lb)
        
        # Check if module is now completed
        _check_module_completion(quiz.module_id, current_user.id, db)
    
    db.commit()
    db.refresh(session)
    
    return SessionResult(
        session_id=session.id,
        quiz_id=session.quiz_id,
        total_score=session.total_score,
        max_score=session.max_score,
        passed=session.passed,
        completed_at=session.completed_at
    )


@router.get("/{session_id}/review", response_model=SessionReview)
def review_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed review of a completed session."""
    session = _get_session_or_404(session_id, current_user, db)
    
    if session.status != SessionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session not finished yet"
        )
    
    answers = db.query(SessionAnswer).filter(SessionAnswer.session_id == session_id).all()
    
    review_answers = []
    for answer in answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        correct_answer = _get_correct_answer(question, db)
        
        answer_data = json.loads(answer.answer_data) if answer.answer_data else {}
        your_answer = _format_your_answer(question.type, answer_data, db)
        
        review_answers.append(SessionReviewAnswer(
            question_id=answer.question_id,
            question_text=question.content_text,
            is_correct=answer.is_correct,
            correct_answer=correct_answer,
            your_answer=your_answer,
            explanation=question.explanation
        ))
    
    return SessionReview(
        session_id=session.id,
        quiz_id=session.quiz_id,
        total_score=session.total_score,
        max_score=session.max_score,
        passed=session.passed,
        answers=review_answers
    )


# Helper functions
def _get_session_or_404(session_id: str, user: User, db: Session) -> QuizSession:
    session = db.query(QuizSession).filter(
        QuizSession.id == session_id,
        QuizSession.student_id == user.id
    ).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "SESSION_NOT_FOUND", "message": "Session not found"}
        )
    return session


def _question_for_gameplay(question: Question, db: Session) -> QuestionForGameplay:
    """Convert question to gameplay format (no correct answers)."""
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
        import random
        matching_right = [{"id": p.id, "item": p.item_right} for p in question.matching_pairs]
        random.shuffle(matching_right)
    
    media_url = question.media.url if question.media else None
    
    return QuestionForGameplay(
        id=question.id,
        type=question.type,
        content_text=question.content_text,
        media_url=media_url,
        options=options,
        matching_items_left=matching_left,
        matching_items_right=matching_right,
        image_zones_count=len(question.image_zones) if question.type == QuestionType.IMAGE else None
    )


def _check_answer(question: Question, request: SubmitAnswerRequest, db: Session) -> bool:
    """Check if the submitted answer is correct."""
    if question.type in [QuestionType.QCM, QuestionType.VRAI_FAUX]:
        if not request.selected_option_id:
            return False
        option = db.query(QuestionOption).filter(
            QuestionOption.id == request.selected_option_id,
            QuestionOption.question_id == question.id
        ).first()
        return option.is_correct if option else False
    
    elif question.type == QuestionType.TEXT:
        if not request.text_response or not question.text_config:
            return False
        
        accepted = question.text_config.accepted_answer
        response = request.text_response
        
        if not question.text_config.is_case_sensitive:
            accepted = accepted.lower()
            response = response.lower()
        
        if question.text_config.ignore_spelling_errors:
            # Simple Levenshtein tolerance (allow up to 2 character difference)
            return _levenshtein_distance(accepted, response) <= 2
        
        return accepted == response
    
    elif question.type == QuestionType.MATCHING:
        if not request.matched_pairs:
            return False
        
        pairs = {p.id: p.item_right for p in question.matching_pairs}
        correct = 0
        for mp in request.matched_pairs:
            left_id = mp.get("left_id")
            right_id = mp.get("right_id")
            if left_id == right_id:  # IDs should match for correct pair
                correct += 1
        
        return correct == len(pairs)
    
    elif question.type == QuestionType.IMAGE:
        if not request.clicked_coordinates:
            return False
        
        x = request.clicked_coordinates.get("x", 0)
        y = request.clicked_coordinates.get("y", 0)
        
        for zone in question.image_zones:
            distance = ((x - zone.x) ** 2 + (y - zone.y) ** 2) ** 0.5
            if distance <= zone.radius:
                return True
        
        return False
    
    return False


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def _get_correct_answer(question: Question, db: Session):
    """Get the correct answer for a question."""
    if question.type in [QuestionType.QCM, QuestionType.VRAI_FAUX]:
        correct_opts = [o.text_choice for o in question.options if o.is_correct]
        return correct_opts
    elif question.type == QuestionType.TEXT:
        return question.text_config.accepted_answer if question.text_config else None
    elif question.type == QuestionType.MATCHING:
        return [{"left": p.item_left, "right": p.item_right} for p in question.matching_pairs]
    elif question.type == QuestionType.IMAGE:
        return [{"label": z.label_name, "x": z.x, "y": z.y} for z in question.image_zones]
    return None


def _format_your_answer(qtype: QuestionType, answer_data: dict, db: Session):
    """Format the user's answer for review."""
    if qtype in [QuestionType.QCM, QuestionType.VRAI_FAUX]:
        opt_id = answer_data.get("selected_option_id")
        if opt_id:
            opt = db.query(QuestionOption).filter(QuestionOption.id == opt_id).first()
            return opt.text_choice if opt else None
    elif qtype == QuestionType.TEXT:
        return answer_data.get("text_response")
    elif qtype == QuestionType.MATCHING:
        return answer_data.get("matched_pairs")
    elif qtype == QuestionType.IMAGE:
        return answer_data.get("clicked_coordinates")
    return None


def _check_module_completion(module_id: str, student_id: str, db: Session):
    """Check if all required quizzes in module are completed."""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        return
    
    # Get all required quizzes (min_score_to_unlock_next > 0)
    required_quizzes = db.query(Quiz).filter(
        Quiz.module_id == module_id,
        Quiz.min_score_to_unlock_next > 0
    ).all()
    
    if not required_quizzes:
        return
    
    # Check if all are completed
    for quiz in required_quizzes:
        completed = db.query(CompletedQuiz).filter(
            CompletedQuiz.student_id == student_id,
            CompletedQuiz.quiz_id == quiz.id
        ).first()
        if not completed:
            return  # Not all completed
    
    # All completed, mark module as completed
    existing = db.query(CompletedModule).filter(
        CompletedModule.student_id == student_id,
        CompletedModule.module_id == module_id
    ).first()
    
    if not existing:
        cm = CompletedModule(
            student_id=student_id,
            module_id=module_id
        )
        db.add(cm)
