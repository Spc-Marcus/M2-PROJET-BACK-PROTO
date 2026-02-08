"""Leitner box service for spaced repetition."""
import json
import random
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.leitner import LeitnerBox, LeitnerSession, LeitnerSessionAnswer
from app.models.question import Question
from app.models.user import User
from app.services.classroom_service import is_classroom_member
from app.services.session_service import evaluate_answer


# Leitner box selection probabilities
BOX_PROBABILITIES = {
    1: 0.50,  # 50%
    2: 0.25,  # 25%
    3: 0.15,  # 15%
    4: 0.07,  # 7%
    5: 0.03   # 3%
}

VALID_QUESTION_COUNTS = [5, 10, 15, 20]


async def get_leitner_status(db: AsyncSession, classroom_id: str, user: User) -> Dict[str, int]:
    """Get the distribution of questions across Leitner boxes."""
    if not await is_classroom_member(db, classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    result = await db.execute(
        select(LeitnerBox.box_level, func.count(LeitnerBox.id))
        .where(
            LeitnerBox.classroom_id == classroom_id,
            LeitnerBox.student_id == user.id
        )
        .group_by(LeitnerBox.box_level)
    )
    
    distribution = {i: 0 for i in range(1, 6)}
    for box_level, count in result.all():
        distribution[box_level] = count
    
    return distribution


async def start_leitner_session(
    db: AsyncSession,
    classroom_id: str,
    question_count: int,
    user: User
) -> LeitnerSession:
    """Start a Leitner revision session."""
    if not await is_classroom_member(db, classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    if question_count not in VALID_QUESTION_COUNTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_QUESTION_COUNT"
        )
    
    # Get all questions in Leitner boxes for this student
    result = await db.execute(
        select(LeitnerBox)
        .where(
            LeitnerBox.classroom_id == classroom_id,
            LeitnerBox.student_id == user.id
        )
    )
    boxes = list(result.scalars().all())
    
    if not boxes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LEITNER_NO_QUESTIONS"
        )
    
    # Group by box level
    boxes_by_level = {i: [] for i in range(1, 6)}
    for box in boxes:
        boxes_by_level[box.box_level].append(box)
    
    # Select questions based on probabilities
    selected_boxes = _select_questions_by_probability(boxes_by_level, question_count)
    
    if len(selected_boxes) < question_count:
        # Not enough questions, adjust
        question_count = len(selected_boxes)
    
    if question_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LEITNER_NO_QUESTIONS"
        )
    
    # Get the actual Question objects for the selected boxes
    selected_question_ids = [box.question_id for box in selected_boxes]
    result = await db.execute(
        select(Question).where(Question.id.in_(selected_question_ids))
    )
    selected_questions = list(result.scalars().all())
    
    # Build distribution counts
    distribution = {i: 0 for i in range(1, 6)}
    for box in selected_boxes:
        distribution[box.box_level] = distribution.get(box.box_level, 0) + 1
    
    # Create session
    session = LeitnerSession(
        classroom_id=classroom_id,
        student_id=user.id,
        question_count=question_count
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session, selected_questions, distribution


async def submit_leitner_answer(
    db: AsyncSession,
    session_id: str,
    question_id: str,
    answer_data: Dict[str, Any],
    user: User
) -> bool:
    """Submit an answer in a Leitner session."""
    result = await db.execute(select(LeitnerSession).where(LeitnerSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SESSION_NOT_FOUND")
    
    if session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    if session.completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SESSION_ALREADY_FINISHED"
        )
    
    # Check if already answered
    result = await db.execute(
        select(LeitnerSessionAnswer)
        .where(
            LeitnerSessionAnswer.session_id == session_id,
            LeitnerSessionAnswer.question_id == question_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Question already answered")
    
    # Get question
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    
    # Get current box level
    result = await db.execute(
        select(LeitnerBox)
        .where(
            LeitnerBox.classroom_id == session.classroom_id,
            LeitnerBox.student_id == user.id,
            LeitnerBox.question_id == question_id
        )
    )
    leitner_box = result.scalar_one_or_none()
    
    if not leitner_box:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not in Leitner boxes")
    
    # Evaluate answer
    is_correct = await evaluate_answer(db, question, answer_data)
    
    # Calculate new box level
    previous_box = leitner_box.box_level
    if is_correct:
        new_box = min(previous_box + 1, 5)  # Promote (max box 5)
    else:
        new_box = 1  # Demote to box 1
    
    # Store answer
    answer = LeitnerSessionAnswer(
        session_id=session_id,
        question_id=question_id,
        is_correct=is_correct,
        previous_box=previous_box,
        new_box=new_box,
        answer_data=json.dumps(answer_data)
    )
    
    db.add(answer)
    await db.commit()
    
    return is_correct


async def finish_leitner_session(db: AsyncSession, session_id: str, user: User) -> LeitnerSession:
    """Finish a Leitner session and update box levels."""
    result = await db.execute(select(LeitnerSession).where(LeitnerSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SESSION_NOT_FOUND")
    
    if session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    if session.completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SESSION_ALREADY_FINISHED"
        )
    
    # Get all answers
    result = await db.execute(
        select(LeitnerSessionAnswer)
        .where(LeitnerSessionAnswer.session_id == session_id)
    )
    answers = list(result.scalars().all())
    
    # Update box levels and calculate stats
    promoted = 0
    demoted = 0
    correct_count = 0
    wrong_count = 0
    
    for answer in answers:
        result = await db.execute(
            select(LeitnerBox)
            .where(
                LeitnerBox.classroom_id == session.classroom_id,
                LeitnerBox.student_id == user.id,
                LeitnerBox.question_id == answer.question_id
            )
        )
        leitner_box = result.scalar_one_or_none()
        
        if leitner_box:
            leitner_box.box_level = answer.new_box
            leitner_box.last_reviewed_at = datetime.utcnow()
            
            if answer.is_correct:
                correct_count += 1
                if answer.new_box > answer.previous_box:
                    promoted += 1
            else:
                wrong_count += 1
                if answer.new_box < answer.previous_box:
                    demoted += 1
    
    # Update session
    session.correct_answers = correct_count
    session.wrong_answers = wrong_count
    session.promoted = promoted
    session.demoted = demoted
    session.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    return session


async def get_leitner_review(db: AsyncSession, session_id: str, user: User) -> LeitnerSession:
    """Get Leitner session review with corrections."""
    result = await db.execute(select(LeitnerSession).where(LeitnerSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SESSION_NOT_FOUND")
    
    if session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    if not session.completed_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session not completed yet"
        )
    
    return session


def _select_questions_by_probability(boxes_by_level: Dict[int, List[LeitnerBox]], count: int) -> List[LeitnerBox]:
    """Select questions based on box probabilities."""
    # Count available questions per box
    available_counts = {level: len(boxes) for level, boxes in boxes_by_level.items()}
    total_available = sum(available_counts.values())
    
    if total_available == 0:
        return []
    
    # Calculate target counts per box
    target_counts = {}
    for level, prob in BOX_PROBABILITIES.items():
        target = int(count * prob)
        available = available_counts[level]
        target_counts[level] = min(target, available)
    
    # Adjust if we don't have enough questions
    total_selected = sum(target_counts.values())
    
    # If we selected less than requested, try to fill from lower boxes
    if total_selected < count:
        remaining = count - total_selected
        for level in [1, 2, 3, 4, 5]:
            available = available_counts[level] - target_counts[level]
            to_add = min(remaining, available)
            target_counts[level] += to_add
            remaining -= to_add
            if remaining == 0:
                break
    
    # Select random questions from each box
    selected = []
    for level, target in target_counts.items():
        if target > 0 and boxes_by_level[level]:
            selected.extend(random.sample(boxes_by_level[level], min(target, len(boxes_by_level[level]))))
    
    # Shuffle the final selection
    random.shuffle(selected)
    
    return selected[:count]
