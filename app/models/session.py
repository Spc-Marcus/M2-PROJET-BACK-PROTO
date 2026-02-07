"""Quiz session models."""
import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Enum, Text
from sqlalchemy.orm import relationship
from app.db.session import Base


class SessionStatus(str, enum.Enum):
    """Session status enumeration."""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class QuizSession(Base):
    """Quiz session model."""
    __tablename__ = "quiz_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    classroom_id = Column(String, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.IN_PROGRESS, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    max_score = Column(Integer, default=0, nullable=False)
    passed = Column(Boolean, default=False, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="sessions")
    student = relationship("User", back_populates="quiz_sessions", foreign_keys=[student_id])
    classroom = relationship("Classroom", back_populates="quiz_sessions", foreign_keys=[classroom_id])
    answers = relationship("SessionAnswer", back_populates="session", cascade="all, delete-orphan")


class SessionAnswer(Base):
    """Session answer model."""
    __tablename__ = "session_answers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Store the answer data as JSON text (for review)
    answer_data = Column(Text, nullable=True)

    # Relationships
    session = relationship("QuizSession", back_populates="answers")
    question = relationship("Question", back_populates="session_answers")
