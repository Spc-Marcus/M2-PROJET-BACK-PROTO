"""Question service."""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.question import (
    Question, QuestionType, QuestionOption, MatchingPair, ImageZone, TextConfig
)
from app.models.quiz import Quiz
from app.models.module import Module
from app.models.user import User
from app.services.classroom_service import is_classroom_teacher


async def get_questions_by_quiz(db: AsyncSession, quiz_id: str, user: User) -> List[Question]:
    """Get all questions for a quiz (teacher only - includes answers)."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    
    result = await db.execute(select(Module).where(Module.id == quiz.module_id))
    module = result.scalar_one_or_none()
    
    if not module or not await is_classroom_teacher(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    result = await db.execute(
        select(Question)
        .where(Question.quiz_id == quiz_id)
        .order_by(Question.created_at)
    )
    return list(result.scalars().all())


async def create_question(
    db: AsyncSession,
    quiz_id: str,
    question_data: Dict[str, Any],
    user: User
) -> Question:
    """Create a new question (teacher of course)."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    
    result = await db.execute(select(Module).where(Module.id == quiz.module_id))
    module = result.scalar_one_or_none()
    
    if not module or not await is_classroom_teacher(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    question = Question(
        quiz_id=quiz_id,
        type=question_data["type"],
        content_text=question_data["content_text"],
        explanation=question_data.get("explanation"),
        media_id=question_data.get("media_id")
    )
    
    db.add(question)
    await db.flush()
    
    # Create type-specific data
    if question_data["type"] in [QuestionType.QCM, QuestionType.VRAI_FAUX]:
        for i, option in enumerate(question_data.get("options", [])):
            question_option = QuestionOption(
                question_id=question.id,
                text_choice=option["text_choice"],
                is_correct=option["is_correct"],
                display_order=i
            )
            db.add(question_option)
    
    elif question_data["type"] == QuestionType.MATCHING:
        for pair in question_data.get("matching_pairs", []):
            matching_pair = MatchingPair(
                question_id=question.id,
                item_left=pair["item_left"],
                item_right=pair["item_right"]
            )
            db.add(matching_pair)
    
    elif question_data["type"] == QuestionType.IMAGE:
        for zone in question_data.get("image_zones", []):
            image_zone = ImageZone(
                question_id=question.id,
                label_name=zone["label_name"],
                x=zone["x"],
                y=zone["y"],
                radius=zone["radius"]
            )
            db.add(image_zone)
    
    elif question_data["type"] == QuestionType.TEXT:
        text_config = TextConfig(
            question_id=question.id,
            accepted_answer=question_data["text_config"]["accepted_answer"],
            is_case_sensitive=question_data["text_config"].get("is_case_sensitive", False),
            ignore_spelling_errors=question_data["text_config"].get("ignore_spelling_errors", True)
        )
        db.add(text_config)
    
    await db.commit()
    await db.refresh(question)
    
    return question


async def update_question(
    db: AsyncSession,
    question_id: str,
    question_data: Dict[str, Any],
    user: User
) -> Question:
    """Update a question (teacher of course)."""
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    
    result = await db.execute(select(Quiz).where(Quiz.id == question.quiz_id))
    quiz = result.scalar_one_or_none()
    
    result = await db.execute(select(Module).where(Module.id == quiz.module_id))
    module = result.scalar_one_or_none()
    
    if not module or not await is_classroom_teacher(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Update base question
    if "content_text" in question_data:
        question.content_text = question_data["content_text"]
    if "explanation" in question_data:
        question.explanation = question_data["explanation"]
    if "media_id" in question_data:
        question.media_id = question_data["media_id"]
    
    # Delete old type-specific data and recreate
    if "options" in question_data:
        await db.execute(QuestionOption.__table__.delete().where(QuestionOption.question_id == question_id))
        for i, option in enumerate(question_data["options"]):
            question_option = QuestionOption(
                question_id=question.id,
                text_choice=option["text_choice"],
                is_correct=option["is_correct"],
                display_order=i
            )
            db.add(question_option)
    
    if "matching_pairs" in question_data:
        await db.execute(MatchingPair.__table__.delete().where(MatchingPair.question_id == question_id))
        for pair in question_data["matching_pairs"]:
            matching_pair = MatchingPair(
                question_id=question.id,
                item_left=pair["item_left"],
                item_right=pair["item_right"]
            )
            db.add(matching_pair)
    
    if "image_zones" in question_data:
        await db.execute(ImageZone.__table__.delete().where(ImageZone.question_id == question_id))
        for zone in question_data["image_zones"]:
            image_zone = ImageZone(
                question_id=question.id,
                label_name=zone["label_name"],
                x=zone["x"],
                y=zone["y"],
                radius=zone["radius"]
            )
            db.add(image_zone)
    
    if "text_config" in question_data:
        await db.execute(TextConfig.__table__.delete().where(TextConfig.question_id == question_id))
        text_config = TextConfig(
            question_id=question.id,
            accepted_answer=question_data["text_config"]["accepted_answer"],
            is_case_sensitive=question_data["text_config"].get("is_case_sensitive", False),
            ignore_spelling_errors=question_data["text_config"].get("ignore_spelling_errors", True)
        )
        db.add(text_config)
    
    await db.commit()
    await db.refresh(question)
    
    return question


async def delete_question(db: AsyncSession, question_id: str, user: User):
    """Delete a question (teacher of course)."""
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    
    result = await db.execute(select(Quiz).where(Quiz.id == question.quiz_id))
    quiz = result.scalar_one_or_none()
    
    result = await db.execute(select(Module).where(Module.id == quiz.module_id))
    module = result.scalar_one_or_none()
    
    if not module or not await is_classroom_teacher(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    await db.delete(question)
    await db.commit()
