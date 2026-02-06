"""Quiz session routes."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_student
from app.models.user import User
from app.schemas.session import (
    GameSessionStartDto, SubmitAnswerDto, AnswerResultDto,
    SessionResultDto, SessionReviewDto
)
from app.services import session_service

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/start", response_model=GameSessionStartDto)
async def start_session(
    quiz_id: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Start a new quiz session."""
    session = await session_service.start_session(db, quiz_id, current_user)
    
    # Get questions for the quiz (without answers)
    from app.models.quiz import Quiz
    from sqlalchemy import select
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one()
    
    questions = []
    for q in quiz.questions:
        question_dto = {
            "id": q.id,
            "type": q.type,
            "contentText": q.content_text,
            "mediaUrl": q.media.url if q.media else None,
            "options": []
        }
        
        if q.type in ["QCM", "VRAI_FAUX"]:
            question_dto["options"] = [{
                "id": str(i),
                "textChoice": opt.text_choice
            } for i, opt in enumerate(q.options)]
        
        questions.append(question_dto)
    
    return GameSessionStartDto(
        sessionId=session.id,
        questions=questions
    )


@router.post("/{sessionId}/submit-answer", response_model=AnswerResultDto)
async def submit_answer(
    sessionId: str,
    data: SubmitAnswerDto,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Submit an answer to a question."""
    # Extract answer data from SubmitAnswerDto
    answer_data = {
        "selected_option_ids": [data.selected_option_id] if data.selected_option_id else [],
        "text_answer": data.text_response
    }
    
    is_correct = await session_service.submit_answer(
        db, sessionId, str(data.question_id), answer_data, current_user
    )
    
    return AnswerResultDto(
        questionId=data.question_id,
        isCorrect=is_correct,
        message="Correct!" if is_correct else "Incorrect"
    )


@router.post("/{sessionId}/finish", response_model=SessionResultDto)
async def finish_session(
    sessionId: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Finish a quiz session."""
    session = await session_service.finish_session(db, sessionId, current_user)
    
    return SessionResultDto(
        sessionId=session.id,
        quizId=session.quiz_id,
        totalScore=session.total_score,
        maxScore=session.max_score,
        passed=session.passed,
        completedAt=session.completed_at
    )


@router.get("/{sessionId}/review", response_model=SessionReviewDto)
async def get_session_review(
    sessionId: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get session review with corrections."""
    session = await session_service.get_session_review(db, sessionId, current_user)
    
    return SessionReviewDto(
        sessionId=session.id,
        totalScore=session.total_score,
        maxScore=session.max_score,
        passed=session.passed,
        answers=[{
            "questionId": a.question_id,
            "isCorrect": a.is_correct,
            "answerData": a.answer_data
        } for a in session.answers]
    )
