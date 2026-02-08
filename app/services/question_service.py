"""Question service."""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.question import (
    Question, QuestionType, QuestionOption, MatchingPair, ImageZone, TextConfig
)
from app.models.quiz import Quiz
from app.models.module import Module
from app.models.user import User
from app.services.classroom_service import is_classroom_teacher


def _question_eager_options():
    """Return selectinload options for Question relationships."""
    return [
        selectinload(Question.options),
        selectinload(Question.matching_pairs),
        selectinload(Question.image_zones),
        selectinload(Question.text_config),
    ]


async def _reload_question(db: AsyncSession, question_id: str) -> Question:
    """Reload a question with all relationships eagerly loaded."""
    result = await db.execute(
        select(Question)
        .where(Question.id == question_id)
        .options(*_question_eager_options())
    )
    return result.scalar_one()


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
        .options(*_question_eager_options())
        .order_by(Question.created_at)
    )
    return list(result.scalars().all())


async def get_question_by_id(db: AsyncSession, question_id: str, user: User) -> Question:
    """Get a question by ID."""
    result = await db.execute(
        select(Question)
        .where(Question.id == question_id)
        .options(*_question_eager_options())
    )
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    
    return question


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
    
    # Validate type-specific data
    qtype = question_data["type"]
    
    if qtype in ["QCM", QuestionType.QCM]:
        options = question_data.get("options") or []
        if not options:
            raise HTTPException(status_code=400, detail="QCM questions require options")
        if not any(o.get("is_correct") for o in options):
            raise HTTPException(status_code=400, detail="QCM questions require at least one correct option")
    
    elif qtype in ["VRAI_FAUX", QuestionType.VRAI_FAUX]:
        options = question_data.get("options") or []
        if len(options) != 2:
            raise HTTPException(status_code=400, detail="VRAI_FAUX questions require exactly 2 options")
    
    elif qtype in ["MATCHING", QuestionType.MATCHING]:
        pairs = question_data.get("matching_pairs") or []
        if len(pairs) < 2:
            raise HTTPException(status_code=400, detail="MATCHING questions require at least 2 pairs")
    
    elif qtype in ["TEXT", QuestionType.TEXT]:
        tc = question_data.get("text_config")
        if not tc or not tc.get("accepted_answer"):
            raise HTTPException(status_code=400, detail="TEXT questions require textConfig with acceptedAnswer")
    
    elif qtype in ["IMAGE", QuestionType.IMAGE]:
        if not question_data.get("media_id"):
            raise HTTPException(status_code=400, detail="IMAGE questions require a mediaId")
        zones = question_data.get("image_zones") or []
        if not zones:
            raise HTTPException(status_code=400, detail="IMAGE questions require imageZones")
        # Validate media exists
        from app.models.media import Media
        media_result = await db.execute(select(Media).where(Media.id == question_data["media_id"]))
        if not media_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Media not found")
    
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
    
    return await _reload_question(db, question.id)


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
    
    return await _reload_question(db, question.id)


async def delete_question(db: AsyncSession, question_id: str, user: User):
    """Delete a question (teacher of course)."""
    from app.models.leitner import LeitnerBox, LeitnerSessionAnswer
    from app.models.session import SessionAnswer
    result = await db.execute(
        select(Question)
        .where(Question.id == question_id)
        .options(
            *_question_eager_options(),
            selectinload(Question.leitner_boxes),
            selectinload(Question.leitner_session_answers),
            selectinload(Question.session_answers),
        )
    )
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
