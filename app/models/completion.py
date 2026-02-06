"""Completion tracking models."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class CompletedQuiz(Base):
    """Completed quiz cache table."""
    __tablename__ = "completed_quizzes"

    student_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="CASCADE"), primary_key=True)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    student = relationship("User")
    quiz = relationship("Quiz")


class CompletedModule(Base):
    """Completed module cache table."""
    __tablename__ = "completed_modules"

    student_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    module_id = Column(String, ForeignKey("modules.id", ondelete="CASCADE"), primary_key=True)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    student = relationship("User")
    module = relationship("Module")
