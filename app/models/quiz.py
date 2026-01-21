from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import generate_uuid


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    module_id = Column(String(36), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    prerequisite_quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True)
    min_score_to_unlock_next = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    module = relationship("Module", back_populates="quizzes")
    prerequisite_quiz = relationship("Quiz", remote_side="Quiz.id", foreign_keys=[prerequisite_quiz_id])
    created_by = relationship("User")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    sessions = relationship("QuizSession", back_populates="quiz", cascade="all, delete-orphan")
    completed_quizzes = relationship("CompletedQuiz", back_populates="quiz", cascade="all, delete-orphan")
