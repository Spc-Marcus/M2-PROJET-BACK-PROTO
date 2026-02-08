"""Question models."""
import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Float, Integer, Text, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base


class QuestionType(str, enum.Enum):
    """Question type enumeration."""
    QCM = "QCM"
    VRAI_FAUX = "VRAI_FAUX"
    MATCHING = "MATCHING"
    IMAGE = "IMAGE"
    TEXT = "TEXT"


class Question(Base):
    """Question model (polymorphic)."""
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(QuestionType), nullable=False)
    content_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    media_id = Column(String, ForeignKey("media.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    media = relationship("Media", foreign_keys=[media_id])
    
    # Polymorphic relationships
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    matching_pairs = relationship("MatchingPair", back_populates="question", cascade="all, delete-orphan")
    image_zones = relationship("ImageZone", back_populates="question", cascade="all, delete-orphan")
    text_config = relationship("TextConfig", back_populates="question", uselist=False, cascade="all, delete-orphan")
    
    # Answers
    session_answers = relationship("SessionAnswer", back_populates="question", cascade="all, delete-orphan")
    leitner_boxes = relationship("LeitnerBox", back_populates="question", cascade="all, delete-orphan")
    leitner_session_answers = relationship("LeitnerSessionAnswer", back_populates="question", cascade="all, delete-orphan")


class QuestionOption(Base):
    """Question option for QCM and VRAI_FAUX."""
    __tablename__ = "question_options"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    text_choice = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    display_order = Column(Integer, nullable=False, default=0)

    # Relationships
    question = relationship("Question", back_populates="options")


class MatchingPair(Base):
    """Matching pair for MATCHING questions."""
    __tablename__ = "matching_pairs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    item_left = Column(String, nullable=False)
    item_right = Column(String, nullable=False)

    # Relationships
    question = relationship("Question", back_populates="matching_pairs")


class ImageZone(Base):
    """Image zone for IMAGE questions."""
    __tablename__ = "image_zones"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    label_name = Column(String, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    radius = Column(Float, nullable=False)

    # Relationships
    question = relationship("Question", back_populates="image_zones")


class TextConfig(Base):
    """Text configuration for TEXT questions."""
    __tablename__ = "text_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String, ForeignKey("questions.id", ondelete="CASCADE"), unique=True, nullable=False)
    accepted_answer = Column(String, nullable=False)
    is_case_sensitive = Column(Boolean, default=False, nullable=False)
    ignore_spelling_errors = Column(Boolean, default=True, nullable=False)

    # Relationships
    question = relationship("Question", back_populates="text_config")
