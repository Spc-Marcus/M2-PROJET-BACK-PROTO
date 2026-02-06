"""Leitner system routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_student
from app.models.user import User
from app.schemas.leitner import (
    LeitnerBoxesStatusDto, LeitnerSessionStartRequestDto,
    LeitnerSessionStartResponseDto, LeitnerSessionResultDto,
    LeitnerSessionReviewDto
)
from app.schemas.session import SubmitAnswerDto, AnswerResultDto
from app.services import leitner_service

router = APIRouter(tags=["leitner"])


@router.get("/api/classrooms/{cid}/leitner/status", response_model=LeitnerBoxesStatusDto)
async def get_leitner_status(
    cid: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get Leitner box distribution."""
    distribution = await leitner_service.get_leitner_status(db, cid, current_user)
    
    return LeitnerBoxesStatusDto(
        classroomId=cid,
        box1=distribution[1],
        box2=distribution[2],
        box3=distribution[3],
        box4=distribution[4],
        box5=distribution[5]
    )


@router.post("/api/classrooms/{cid}/leitner/start", response_model=LeitnerSessionStartResponseDto)
async def start_leitner_session(
    cid: str,
    data: LeitnerSessionStartRequestDto,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Start a Leitner revision session."""
    session = await leitner_service.start_leitner_session(
        db, cid, data.question_count, current_user
    )
    
    return LeitnerSessionStartResponseDto(
        sessionId=session.id,
        questionCount=session.question_count,
        startedAt=session.started_at
    )


@router.post("/api/leitner/sessions/{sid}/submit-answer", response_model=AnswerResultDto)
async def submit_leitner_answer(
    sid: str,
    data: SubmitAnswerDto,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Submit an answer in Leitner session."""
    is_correct = await leitner_service.submit_leitner_answer(
        db, sid, data.question_id, data.answer_data, current_user
    )
    
    return AnswerResultDto(isCorrect=is_correct)


@router.post("/api/leitner/sessions/{sid}/finish", response_model=LeitnerSessionResultDto)
async def finish_leitner_session(
    sid: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Finish a Leitner session."""
    session = await leitner_service.finish_leitner_session(db, sid, current_user)
    
    return LeitnerSessionResultDto(
        sessionId=session.id,
        correctAnswers=session.correct_answers,
        wrongAnswers=session.wrong_answers,
        promoted=session.promoted,
        demoted=session.demoted,
        completedAt=session.completed_at
    )


@router.get("/api/leitner/sessions/{sid}/review", response_model=LeitnerSessionReviewDto)
async def get_leitner_review(
    sid: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get Leitner session review."""
    session = await leitner_service.get_leitner_review(db, sid, current_user)
    
    return LeitnerSessionReviewDto(
        sessionId=session.id,
        correctAnswers=session.correct_answers,
        wrongAnswers=session.wrong_answers,
        answers=[{
            "questionId": a.question_id,
            "isCorrect": a.is_correct,
            "previousBox": a.previous_box,
            "newBox": a.new_box
        } for a in session.answers]
    )
