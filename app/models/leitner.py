from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import generate_uuid


class LeitnerBox(Base):
    """Tracks which box each question is in for each student in each classroom."""
    __tablename__ = "leitner_boxes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    box_level = Column(Integer, default=1)  # 1-5
    added_at = Column(DateTime, default=datetime.utcnow)
    last_reviewed_at = Column(DateTime, nullable=True)

    classroom = relationship("Classroom", back_populates="leitner_boxes")
    student = relationship("User")
    question = relationship("Question", back_populates="leitner_boxes")


class LeitnerSession(Base):
    """A Leitner review session."""
    __tablename__ = "leitner_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_count = Column(Integer, nullable=False)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    promoted = Column(Integer, default=0)  # Questions moved up
    demoted = Column(Integer, default=0)   # Questions moved to box 1
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    classroom = relationship("Classroom", back_populates="leitner_sessions")
    student = relationship("User", back_populates="leitner_sessions")
    answers = relationship("LeitnerSessionAnswer", back_populates="session", cascade="all, delete-orphan")


class LeitnerSessionAnswer(Base):
    """Detail of each answer in a Leitner session."""
    __tablename__ = "leitner_session_answers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("leitner_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    is_correct = Column(Boolean, default=False)
    previous_box = Column(Integer, nullable=False)
    new_box = Column(Integer, nullable=False)
    answer_data = Column(Text)  # JSON stored as text
    answered_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("LeitnerSession", back_populates="answers")
    question = relationship("Question", back_populates="leitner_session_answers")
