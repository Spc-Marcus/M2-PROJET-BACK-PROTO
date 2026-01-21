import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Enum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import generate_uuid


class SessionStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.IN_PROGRESS)
    total_score = Column(Integer, default=0)
    max_score = Column(Integer, default=0)
    passed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="sessions")
    student = relationship("User", back_populates="quiz_sessions")
    classroom = relationship("Classroom", back_populates="quiz_sessions")
    answers = relationship("SessionAnswer", back_populates="session", cascade="all, delete-orphan")


class SessionAnswer(Base):
    __tablename__ = "session_answers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    is_correct = Column(Boolean, default=False)
    answer_data = Column(Text)  # JSON stored as text for the submitted answer
    answered_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("QuizSession", back_populates="answers")
    question = relationship("Question", back_populates="session_answers")


class CompletedQuiz(Base):
    __tablename__ = "completed_quizzes"

    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), primary_key=True)
    completed_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User")
    quiz = relationship("Quiz", back_populates="completed_quizzes")


class CompletedModule(Base):
    __tablename__ = "completed_modules"

    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    module_id = Column(String(36), ForeignKey("modules.id", ondelete="CASCADE"), primary_key=True)
    completed_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User")
    module = relationship("Module", back_populates="completed_modules")
