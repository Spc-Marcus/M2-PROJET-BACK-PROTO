"""Leitner system models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.session import Base


class LeitnerBox(Base):
    """Leitner box model - tracks question progress per student per classroom."""
    __tablename__ = "leitner_boxes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    box_level = Column(Integer, nullable=False, default=1)  # 1-5
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    classroom = relationship("Classroom", back_populates="leitner_boxes", foreign_keys=[classroom_id])
    student = relationship("User", back_populates="leitner_boxes", foreign_keys=[student_id])
    question = relationship("Question", back_populates="leitner_boxes")

    # Composite unique constraint
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class LeitnerSession(Base):
    """Leitner session model."""
    __tablename__ = "leitner_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_count = Column(Integer, nullable=False)
    correct_answers = Column(Integer, default=0, nullable=False)
    wrong_answers = Column(Integer, default=0, nullable=False)
    promoted = Column(Integer, default=0, nullable=False)
    demoted = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    classroom = relationship("Classroom", back_populates="leitner_sessions", foreign_keys=[classroom_id])
    student = relationship("User", back_populates="leitner_sessions", foreign_keys=[student_id])
    answers = relationship("LeitnerSessionAnswer", back_populates="session", cascade="all, delete-orphan")


class LeitnerSessionAnswer(Base):
    """Leitner session answer model."""
    __tablename__ = "leitner_session_answers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("leitner_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    previous_box = Column(Integer, nullable=False)
    new_box = Column(Integer, nullable=False)
    answered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Store the answer data as JSON text (for review)
    answer_data = Column(Text, nullable=True)

    # Relationships
    session = relationship("LeitnerSession", back_populates="answers")
    question = relationship("Question", back_populates="leitner_session_answers")
