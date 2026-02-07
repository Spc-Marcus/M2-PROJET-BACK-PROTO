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

router = APIRouter()


@router.get("/api/classrooms/{cid}/leitner/status", response_model=LeitnerBoxesStatusDto)
async def get_leitner_status(
    cid: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get Leitner box distribution."""
    from app.models.classroom import Classroom
    from sqlalchemy import select
    
    distribution = await leitner_service.get_leitner_status(db, cid, current_user)
    
    result = await db.execute(select(Classroom).where(Classroom.id == cid))
    classroom = result.scalar_one()
    
    total = sum(distribution.values())
    boxes = [{
        "level": i,
        "questionCount": distribution[i],
        "percentage": (distribution[i] / total * 100) if total > 0 else 0,
        "selectionWeight": [50, 25, 15, 7, 3][i-1]
    } for i in range(1, 6)]
    
    return LeitnerBoxesStatusDto(
        classroomId=cid,
        classroomName=classroom.name,
        totalQuestions=total,
        boxes=boxes,
        lastReviewedAt=None
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
    
    # Return minimal data since we don't have questions attached to session yet
    return LeitnerSessionStartResponseDto(
        sessionId=session.id,
        classroomId=session.classroom_id,
        questions=[],
        selectionDistribution={
            "box1": 0, "box2": 0, "box3": 0, "box4": 0, "box5": 0
        }
    )


@router.post("/api/leitner/sessions/{sid}/submit-answer", response_model=AnswerResultDto)
async def submit_leitner_answer(
    sid: str,
    data: SubmitAnswerDto,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Submit an answer in Leitner session."""
    answer_data = {
        "selected_option_ids": [data.selected_option_id] if data.selected_option_id else [],
        "text_answer": data.text_response
    }
    
    is_correct = await leitner_service.submit_leitner_answer(
        db, sid, str(data.question_id), answer_data, current_user
    )
    
    return AnswerResultDto(
        questionId=data.question_id,
        isCorrect=is_correct,
        message="Correct!" if is_correct else "Incorrect"
    )


@router.post("/api/leitner/sessions/{sid}/finish", response_model=LeitnerSessionResultDto)
async def finish_leitner_session(
    sid: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Finish a Leitner session."""
    session = await leitner_service.finish_leitner_session(db, sid, current_user)
    
    total = session.correct_answers + session.wrong_answers
    accuracy = (session.correct_answers / total * 100) if total > 0 else 0
    
    return LeitnerSessionResultDto(
        sessionId=session.id,
        classroomId=session.classroom_id,
        totalQuestions=session.question_count,
        correctAnswers=session.correct_answers,
        wrongAnswers=session.wrong_answers,
        accuracyRate=accuracy,
        boxMovements={"promoted": session.promoted, "demoted": session.demoted},
        newBoxDistribution={"box1": 0, "box2": 0, "box3": 0, "box4": 0, "box5": 0}
    )


@router.get("/api/leitner/sessions/{sid}/review", response_model=LeitnerSessionReviewDto)
async def get_leitner_review(
    sid: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get Leitner session review."""
    session = await leitner_service.get_leitner_review(db, sid, current_user)
    
    total = session.correct_answers + session.wrong_answers
    accuracy = (session.correct_answers / total * 100) if total > 0 else 0
    
    return LeitnerSessionReviewDto(
        sessionId=session.id,
        classroomId=session.classroom_id,
        answers=[{
            "questionId": a.question_id,
            "questionText": "",  # Would need to load question
            "isCorrect": a.is_correct,
            "previousBox": a.previous_box,
            "newBox": a.new_box,
            "correctAnswer": {},
            "explanation": ""
        } for a in session.answers],
        summary={
            "totalQuestions": total,
            "correctAnswers": session.correct_answers,
            "accuracyRate": accuracy
        }
    )
