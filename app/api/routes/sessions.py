"""Quiz session routes."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_student
from app.models.user import User
from app.models.session import QuizSession, SessionAnswer
from app.schemas.session import (
    GameSessionStartDto, SubmitAnswerDto, AnswerResultDto,
    SessionResultDto, SessionReviewDto
)
from app.services import session_service

router = APIRouter()


class StartSessionRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    quiz_id: str = Field(..., alias="quizId")


@router.post("/start")
async def start_session(
    data: StartSessionRequestDto,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Start a new quiz session."""
    quiz_id = data.quiz_id
    session = await session_service.start_session(db, quiz_id, current_user)
    
    # Get questions for the quiz (without answers)
    from app.models.quiz import Quiz
    from app.models.question import Question, QuestionOption
    result = await db.execute(
        select(Quiz)
        .options(
            selectinload(Quiz.questions).selectinload(Question.options)
        )
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one()
    
    questions = []
    for q in quiz.questions:
        qtype = q.type if isinstance(q.type, str) else q.type.value
        question_dto = {
            "id": q.id,
            "type": qtype,
            "contentText": q.content_text,
            "mediaUrl": None,
            "options": []
        }
        
        if qtype in ["QCM", "VRAI_FAUX"] and q.options:
            question_dto["options"] = [{
                "id": opt.id,
                "textChoice": opt.text_choice
            } for opt in q.options]
        
        questions.append(question_dto)
    
    return {
        "sessionId": session.id,
        "questions": questions
    }


@router.post("/{sessionId}/submit-answer")
async def submit_answer(
    sessionId: str,
    data: SubmitAnswerDto,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Submit an answer to a question."""
    # Build answer_data based on what the student submitted
    answer_data = {}
    
    if data.selected_option_id:
        answer_data["selected_option_ids"] = [data.selected_option_id]
    
    if data.text_response:
        answer_data["text_answer"] = data.text_response
    
    if data.matched_pairs:
        answer_data["pairs"] = {
            pair.left_id: pair.right_id for pair in data.matched_pairs
        }
    
    if data.clicked_coordinates:
        answer_data["clicked_coordinates"] = {
            "x": data.clicked_coordinates.x,
            "y": data.clicked_coordinates.y
        }
    
    is_correct = await session_service.submit_answer(
        db, sessionId, str(data.question_id), answer_data, current_user
    )
    
    return {
        "questionId": data.question_id,
        "isCorrect": is_correct,
        "message": "Correct!" if is_correct else "Incorrect"
    }


@router.post("/{sessionId}/finish")
async def finish_session(
    sessionId: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Finish a quiz session."""
    session = await session_service.finish_session(db, sessionId, current_user)
    
    return {
        "sessionId": session.id,
        "quizId": session.quiz_id,
        "totalScore": session.total_score,
        "maxScore": session.max_score,
        "passed": session.passed,
        "completedAt": session.completed_at.isoformat() if session.completed_at else None
    }


@router.get("/{sessionId}/review")
async def get_session_review(
    sessionId: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get session review with corrections."""
    session = await session_service.get_session_review(db, sessionId, current_user)
    
    # Eagerly load answers
    result = await db.execute(
        select(SessionAnswer).where(SessionAnswer.session_id == sessionId)
    )
    answers = list(result.scalars().all())
    
    return {
        "sessionId": session.id,
        "totalScore": session.total_score,
        "maxScore": session.max_score,
        "passed": session.passed,
        "answers": [{
            "questionId": a.question_id,
            "isCorrect": a.is_correct,
            "answerData": a.answer_data
        } for a in answers]
    }
