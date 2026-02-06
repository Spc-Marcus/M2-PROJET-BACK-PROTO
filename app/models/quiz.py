"""Quiz model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from app.db.session import Base


class Quiz(Base):
    """Quiz model."""
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    prerequisite_quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True)
    min_score_to_unlock_next = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    module = relationship("Module", back_populates="quizzes", foreign_keys=[module_id])
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    # Self-referencing for prerequisites
    prerequisite_quiz = relationship("Quiz", remote_side=[id], foreign_keys=[prerequisite_quiz_id])
    
    # Sessions
    sessions = relationship("QuizSession", back_populates="quiz")
