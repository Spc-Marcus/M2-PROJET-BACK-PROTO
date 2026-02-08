"""Quiz session service."""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.session import QuizSession, SessionAnswer, SessionStatus
from app.models.quiz import Quiz
from app.models.question import Question, QuestionType, QuestionOption, MatchingPair, ImageZone, TextConfig
from app.models.module import Module
from app.models.completion import CompletedQuiz, CompletedModule
from app.models.leitner import LeitnerBox
from app.models.user import User
from app.services.classroom_service import is_classroom_member


async def start_session(db: AsyncSession, quiz_id: str, user: User) -> QuizSession:
    """Start a new quiz session (student only)."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    
    # Check if quiz is active
    if not quiz.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="QUIZ_INACTIVE")
    
    result = await db.execute(select(Module).where(Module.id == quiz.module_id))
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    
    # Check if user is member of classroom
    if not await is_classroom_member(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Check if quiz is locked by prerequisite
    if quiz.prerequisite_quiz_id:
        result = await db.execute(
            select(CompletedQuiz)
            .where(
                CompletedQuiz.student_id == user.id,
                CompletedQuiz.quiz_id == quiz.prerequisite_quiz_id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="QUIZ_LOCKED"
            )
    
    # Check if module is locked by prerequisite
    if module.prerequisite_module_id:
        result = await db.execute(
            select(CompletedModule)
            .where(
                CompletedModule.student_id == user.id,
                CompletedModule.module_id == module.prerequisite_module_id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MODULE_LOCKED"
            )
    
    # Get question count for max_score
    result = await db.execute(
        select(func.count(Question.id)).where(Question.quiz_id == quiz_id)
    )
    question_count = result.scalar() or 0
    
    session = QuizSession(
        quiz_id=quiz_id,
        student_id=user.id,
        classroom_id=module.classroom_id,
        status=SessionStatus.IN_PROGRESS,
        max_score=question_count
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session


async def submit_answer(
    db: AsyncSession,
    session_id: str,
    question_id: str,
    answer_data: Dict[str, Any],
    user: User
) -> bool:
    """Submit an answer to a question in a session."""
    result = await db.execute(select(QuizSession).where(QuizSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SESSION_NOT_FOUND")
    
    if session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SESSION_ALREADY_FINISHED"
        )
    
    # Check for session timeout (2 hours)
    if datetime.utcnow() - session.started_at > timedelta(hours=2):
        session.status = SessionStatus.ABANDONED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SESSION_ALREADY_FINISHED"
        )
    
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="QUESTION_NOT_IN_SESSION")
    
    if question.quiz_id != session.quiz_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="QUESTION_NOT_IN_SESSION")
    
    # Check if already answered
    result = await db.execute(
        select(SessionAnswer)
        .where(SessionAnswer.session_id == session_id, SessionAnswer.question_id == question_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Question already answered")
    
    # Evaluate answer
    is_correct = await evaluate_answer(db, question, answer_data)
    
    answer = SessionAnswer(
        session_id=session_id,
        question_id=question_id,
        is_correct=is_correct,
        answer_data=json.dumps(answer_data)
    )
    
    db.add(answer)
    await db.commit()
    
    return is_correct


async def finish_session(db: AsyncSession, session_id: str, user: User) -> QuizSession:
    """Finish a quiz session and calculate score."""
    result = await db.execute(select(QuizSession).where(QuizSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SESSION_NOT_FOUND")
    
    if session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SESSION_ALREADY_FINISHED"
        )
    
    # Calculate score
    result = await db.execute(
        select(func.count(SessionAnswer.id))
        .where(SessionAnswer.session_id == session_id, SessionAnswer.is_correct == True)
    )
    correct_count = result.scalar() or 0
    
    session.total_score = correct_count
    session.status = SessionStatus.COMPLETED
    session.completed_at = datetime.utcnow()
    
    # Get quiz
    result = await db.execute(select(Quiz).where(Quiz.id == session.quiz_id))
    quiz = result.scalar_one_or_none()
    
    # Check if passed
    session.passed = session.total_score >= quiz.min_score_to_unlock_next
    
    await db.commit()
    
    # If passed, auto-create CompletedQuiz and add questions to Leitner
    if session.passed:
        await _complete_quiz(db, session.quiz_id, user.id, session.classroom_id)
    
    await db.refresh(session)
    return session


async def get_session_review(db: AsyncSession, session_id: str, user: User) -> QuizSession:
    """Get session review with corrections (after finish only)."""
    result = await db.execute(select(QuizSession).where(QuizSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SESSION_NOT_FOUND")
    
    if session.student_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    if session.status != SessionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session not completed yet"
        )
    
    return session


async def evaluate_answer(db: AsyncSession, question: Question, answer_data: Dict[str, Any]) -> bool:
    """Evaluate an answer based on question type."""
    if question.type == QuestionType.QCM:
        selected_option_ids = answer_data.get("selected_option_ids", [])
        result = await db.execute(
            select(QuestionOption).where(QuestionOption.question_id == question.id)
        )
        options = list(result.scalars().all())
        
        correct_ids = {opt.id for opt in options if opt.is_correct}
        return set(selected_option_ids) == correct_ids
    
    elif question.type == QuestionType.VRAI_FAUX:
        selected_option_id = answer_data.get("selected_option_id")
        result = await db.execute(
            select(QuestionOption)
            .where(QuestionOption.question_id == question.id, QuestionOption.is_correct == True)
        )
        correct_option = result.scalar_one_or_none()
        return selected_option_id == correct_option.id if correct_option else False
    
    elif question.type == QuestionType.MATCHING:
        pairs = answer_data.get("pairs", {})
        result = await db.execute(
            select(MatchingPair).where(MatchingPair.question_id == question.id)
        )
        correct_pairs = {pair.item_left: pair.item_right for pair in result.scalars().all()}
        return pairs == correct_pairs
    
    elif question.type == QuestionType.IMAGE:
        clicked = answer_data.get("clicked_coordinates")
        if clicked:
            # Check if click is within any correct zone's radius
            x, y = clicked.get("x", 0), clicked.get("y", 0)
            result = await db.execute(
                select(ImageZone).where(ImageZone.question_id == question.id)
            )
            zones = list(result.scalars().all())
            for zone in zones:
                dx = x - zone.x
                dy = y - zone.y
                distance = (dx * dx + dy * dy) ** 0.5
                if distance <= zone.radius:
                    return True
            return False
        else:
            # Fallback: check selected_zone_ids
            selected_zone_ids = answer_data.get("selected_zone_ids", [])
            result = await db.execute(
                select(ImageZone).where(ImageZone.question_id == question.id)
            )
            correct_zone_ids = {zone.id for zone in result.scalars().all()}
            return set(selected_zone_ids) == correct_zone_ids
    
    elif question.type == QuestionType.TEXT:
        user_answer = answer_data.get("text_answer", "").strip()
        result = await db.execute(
            select(TextConfig).where(TextConfig.question_id == question.id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            return False
        
        expected = config.accepted_answer.strip()
        
        if not config.is_case_sensitive:
            user_answer = user_answer.lower()
            expected = expected.lower()
        
        # Simple exact match (spelling check would need external library)
        return user_answer == expected
    
    return False


async def _complete_quiz(db: AsyncSession, quiz_id: str, student_id: str, classroom_id: str):
    """Auto-create CompletedQuiz and add questions to Leitner Box 1."""
    # Create CompletedQuiz if not exists
    result = await db.execute(
        select(CompletedQuiz)
        .where(CompletedQuiz.student_id == student_id, CompletedQuiz.quiz_id == quiz_id)
    )
    if not result.scalar_one_or_none():
        completed = CompletedQuiz(student_id=student_id, quiz_id=quiz_id)
        db.add(completed)
    
    # Add all questions to Leitner Box 1 (if not already in higher boxes)
    result = await db.execute(select(Question).where(Question.quiz_id == quiz_id))
    questions = list(result.scalars().all())
    
    for question in questions:
        result = await db.execute(
            select(LeitnerBox)
            .where(
                LeitnerBox.classroom_id == classroom_id,
                LeitnerBox.student_id == student_id,
                LeitnerBox.question_id == question.id
            )
        )
        if not result.scalar_one_or_none():
            leitner_box = LeitnerBox(
                classroom_id=classroom_id,
                student_id=student_id,
                question_id=question.id,
                box_level=1
            )
            db.add(leitner_box)
    
    # Check if module is completed
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if quiz:
        await _check_module_completion(db, quiz.module_id, student_id)
    
    await db.commit()


async def _check_module_completion(db: AsyncSession, module_id: str, student_id: str):
    """Check if module is completed and create CompletedModule."""
    # Get all required quizzes in module
    result = await db.execute(
        select(Quiz)
        .where(Quiz.module_id == module_id, Quiz.min_score_to_unlock_next > 0)
    )
    required_quizzes = list(result.scalars().all())
    
    # Check if all are completed
    for quiz in required_quizzes:
        result = await db.execute(
            select(CompletedQuiz)
            .where(CompletedQuiz.student_id == student_id, CompletedQuiz.quiz_id == quiz.id)
        )
        if not result.scalar_one_or_none():
            return  # Not all required quizzes completed
    
    # Create CompletedModule if not exists
    result = await db.execute(
        select(CompletedModule)
        .where(CompletedModule.student_id == student_id, CompletedModule.module_id == module_id)
    )
    if not result.scalar_one_or_none():
        completed = CompletedModule(student_id=student_id, module_id=module_id)
        db.add(completed)
        await db.commit()
