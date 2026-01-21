import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Enum, Float, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import generate_uuid


class QuestionType(str, enum.Enum):
    QCM = "QCM"
    VRAI_FAUX = "VRAI_FAUX"
    MATCHING = "MATCHING"
    IMAGE = "IMAGE"
    TEXT = "TEXT"


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(QuestionType), nullable=False)
    content_text = Column(Text, nullable=False)
    explanation = Column(Text)
    media_id = Column(String(36), ForeignKey("media.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    media = relationship("Media")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    matching_pairs = relationship("MatchingPair", back_populates="question", cascade="all, delete-orphan")
    image_zones = relationship("ImageZone", back_populates="question", cascade="all, delete-orphan")
    text_config = relationship("TextConfig", back_populates="question", uselist=False, cascade="all, delete-orphan")
    leitner_boxes = relationship("LeitnerBox", back_populates="question", cascade="all, delete-orphan")
    session_answers = relationship("SessionAnswer", back_populates="question", cascade="all, delete-orphan")
    leitner_session_answers = relationship("LeitnerSessionAnswer", back_populates="question", cascade="all, delete-orphan")


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    text_choice = Column(String(500), nullable=False)
    is_correct = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)

    question = relationship("Question", back_populates="options")


class MatchingPair(Base):
    __tablename__ = "matching_pairs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    item_left = Column(String(500), nullable=False)
    item_right = Column(String(500), nullable=False)

    question = relationship("Question", back_populates="matching_pairs")


class ImageZone(Base):
    __tablename__ = "image_zones"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    label_name = Column(String(255), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    radius = Column(Float, nullable=False)

    question = relationship("Question", back_populates="image_zones")


class TextConfig(Base):
    __tablename__ = "text_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), unique=True, nullable=False)
    accepted_answer = Column(String(500), nullable=False)
    is_case_sensitive = Column(Boolean, default=False)
    ignore_spelling_errors = Column(Boolean, default=True)

    question = relationship("Question", back_populates="text_config")


class Media(Base):
    __tablename__ = "media"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    url = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    uploaded_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    uploaded_by = relationship("User")
