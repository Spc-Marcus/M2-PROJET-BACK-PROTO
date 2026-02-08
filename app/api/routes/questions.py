"""Question routes."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.question import QuestionCreateDto, QuestionResponseDto
from app.services import question_service

router = APIRouter()


def _question_to_response(question) -> dict:
    """Convert a Question model to response dict."""
    resp = {
        "id": question.id,
        "type": question.type if isinstance(question.type, str) else question.type.value,
        "contentText": question.content_text,
        "explanation": question.explanation,
        "mediaId": question.media_id,
    }
    
    if hasattr(question, 'options') and question.options:
        resp["options"] = [{
            "textChoice": o.text_choice,
            "isCorrect": o.is_correct,
            "displayOrder": o.display_order
        } for o in question.options]
    
    if hasattr(question, 'matching_pairs') and question.matching_pairs:
        resp["matchingPairs"] = [{
            "itemLeft": p.item_left,
            "itemRight": p.item_right
        } for p in question.matching_pairs]
    
    if hasattr(question, 'image_zones') and question.image_zones:
        resp["imageZones"] = [{
            "labelName": z.label_name,
            "x": z.x,
            "y": z.y,
            "radius": z.radius
        } for z in question.image_zones]
    
    if hasattr(question, 'text_config') and question.text_config:
        resp["textConfig"] = {
            "acceptedAnswer": question.text_config.accepted_answer,
            "isCaseSensitive": question.text_config.is_case_sensitive,
            "ignoreSpellingErrors": question.text_config.ignore_spelling_errors
        }
    
    return resp


@router.get("/quizzes/{quizId}/questions")
async def get_questions(
    quizId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all questions for a quiz (teacher only)."""
    questions = await question_service.get_questions_by_quiz(db, quizId, current_user)
    return [_question_to_response(q) for q in questions]


@router.post("/quizzes/{quizId}/questions", status_code=status.HTTP_201_CREATED)
async def create_question(
    quizId: str,
    data: QuestionCreateDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new question."""
    question_data = data.model_dump(by_alias=False)
    question = await question_service.create_question(db, quizId, question_data, current_user)
    return _question_to_response(question)


@router.get("/questions/{questionId}")
async def get_question(
    questionId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get question by ID."""
    question = await question_service.get_question_by_id(db, questionId, current_user)
    return _question_to_response(question)


@router.patch("/questions/{questionId}")
async def update_question(
    questionId: str,
    data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a question."""
    # Convert camelCase keys to snake_case
    question_data = {}
    key_map = {
        "contentText": "content_text",
        "explanation": "explanation",
        "mediaId": "media_id",
        "options": "options",
        "matchingPairs": "matching_pairs",
        "imageZones": "image_zones",
        "textConfig": "text_config",
        "type": "type",
    }
    for camel, snake in key_map.items():
        if camel in data:
            val = data[camel]
            if camel == "options" and val is not None:
                val = [{"text_choice": o.get("textChoice", o.get("text_choice")),
                        "is_correct": o.get("isCorrect", o.get("is_correct")),
                        "display_order": o.get("displayOrder", o.get("display_order"))} for o in val]
            elif camel == "matchingPairs" and val is not None:
                val = [{"item_left": p.get("itemLeft", p.get("item_left")),
                        "item_right": p.get("itemRight", p.get("item_right"))} for p in val]
            elif camel == "imageZones" and val is not None:
                val = [{"label_name": z.get("labelName", z.get("label_name")),
                        "x": z["x"], "y": z["y"], "radius": z["radius"]} for z in val]
            elif camel == "textConfig" and val is not None:
                val = {"accepted_answer": val.get("acceptedAnswer", val.get("accepted_answer")),
                       "is_case_sensitive": val.get("isCaseSensitive", val.get("is_case_sensitive", False)),
                       "ignore_spelling_errors": val.get("ignoreSpellingErrors", val.get("ignore_spelling_errors", True))}
            question_data[snake] = val
    question = await question_service.update_question(db, questionId, question_data, current_user)
    return _question_to_response(question)


@router.delete("/questions/{questionId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    questionId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a question."""
    await question_service.delete_question(db, questionId, current_user)
