"""Leitner system routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_student
from app.models.user import User
from app.schemas.leitner import (
    LeitnerSessionStartRequestDto,
)
from app.schemas.session import SubmitAnswerDto
from app.services import leitner_service

router = APIRouter()


@router.get("/classrooms/{cid}/leitner/status")
async def get_leitner_status(
    cid: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get Leitner box distribution."""
    from app.models.classroom import Classroom
    
    distribution = await leitner_service.get_leitner_status(db, cid, current_user)
    
    result = await db.execute(select(Classroom).where(Classroom.id == cid))
    classroom = result.scalar_one()
    
    total = sum(distribution.values())
    weights = [50, 25, 15, 7, 3]
    boxes = [{
        "boxLevel": i,
        "level": i,
        "count": distribution[i],
        "questionCount": distribution[i],
        "percentage": round((distribution[i] / total * 100), 2) if total > 0 else 0,
        "selectionWeight": weights[i-1]
    } for i in range(1, 6)]
    
    return {
        "classroomId": cid,
        "classroomName": classroom.name,
        "totalQuestions": total,
        "boxes": boxes,
        "lastReviewedAt": None
    }


@router.post("/classrooms/{cid}/leitner/start")
async def start_leitner_session(
    cid: str,
    data: LeitnerSessionStartRequestDto,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Start a Leitner revision session."""
    session, selected_questions, distribution = await leitner_service.start_leitner_session(
        db, cid, data.question_count, current_user
    )
    
    # Build question list (without correct answers)
    questions = []
    for q in selected_questions:
        qtype = q.type if isinstance(q.type, str) else q.type.value
        question_dto = {
            "id": q.id,
            "type": qtype,
            "contentText": q.content_text,
            "mediaUrl": None,
        }
        questions.append(question_dto)
    
    return {
        "sessionId": session.id,
        "classroomId": session.classroom_id,
        "questions": questions,
        "selectionDistribution": {
            f"box{i}": distribution.get(i, 0) for i in range(1, 6)
        }
    }


@router.post("/leitner/sessions/{sid}/submit-answer")
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
    
    return {
        "questionId": data.question_id,
        "isCorrect": is_correct,
        "message": "Correct!" if is_correct else "Incorrect"
    }


@router.post("/leitner/sessions/{sid}/finish")
async def finish_leitner_session(
    sid: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Finish a Leitner session."""
    session = await leitner_service.finish_leitner_session(db, sid, current_user)
    
    total = session.correct_answers + session.wrong_answers
    accuracy = round((session.correct_answers / total * 100), 2) if total > 0 else 0
    
    return {
        "sessionId": session.id,
        "classroomId": session.classroom_id,
        "totalQuestions": session.question_count,
        "correctAnswers": session.correct_answers,
        "wrongAnswers": session.wrong_answers,
        "accuracyRate": accuracy,
        "boxMovements": {"promoted": session.promoted, "demoted": session.demoted},
        "newBoxDistribution": {"box1": 0, "box2": 0, "box3": 0, "box4": 0, "box5": 0},
        "summary": {
            "totalQuestions": total,
            "correctAnswers": session.correct_answers,
            "accuracyRate": accuracy,
            "promoted": session.promoted,
            "demoted": session.demoted
        },
        "promoted": session.promoted,
        "demoted": session.demoted
    }


@router.get("/leitner/sessions/{sid}/review")
async def get_leitner_review(
    sid: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get Leitner session review."""
    session = await leitner_service.get_leitner_review(db, sid, current_user)
    
    # Eagerly load answers
    from app.models.leitner import LeitnerSessionAnswer
    result = await db.execute(
        select(LeitnerSessionAnswer).where(LeitnerSessionAnswer.session_id == sid)
    )
    answers = list(result.scalars().all())
    
    total = session.correct_answers + session.wrong_answers
    accuracy = round((session.correct_answers / total * 100), 2) if total > 0 else 0
    
    return {
        "sessionId": session.id,
        "classroomId": session.classroom_id,
        "answers": [{
            "questionId": a.question_id,
            "questionText": "",
            "isCorrect": a.is_correct,
            "previousBox": a.previous_box,
            "newBox": a.new_box,
            "correctAnswer": {},
            "explanation": ""
        } for a in answers],
        "summary": {
            "totalQuestions": total,
            "correctCount": session.correct_answers,
            "correctAnswers": session.correct_answers,
            "accuracy": accuracy,
            "accuracyRate": accuracy,
            "promoted": session.promoted,
            "demoted": session.demoted
        }
    }
