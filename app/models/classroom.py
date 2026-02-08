"""Classroom models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import Level
from sqlalchemy import Enum


class Classroom(Base):
    """Classroom model."""
    __tablename__ = "classrooms"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    level = Column(Enum(Level), nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    responsible_professor_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    responsible_professor = relationship("User", back_populates="responsible_classrooms", foreign_keys=[responsible_professor_id])
    modules = relationship("Module", back_populates="classroom", cascade="all, delete-orphan")
    
    # Many-to-many relationships
    teachers = relationship("ClassroomTeacher", back_populates="classroom", cascade="all, delete-orphan")
    students = relationship("ClassroomStudent", back_populates="classroom", cascade="all, delete-orphan")
    
    # Sessions
    quiz_sessions = relationship("QuizSession", back_populates="classroom", foreign_keys="QuizSession.classroom_id", cascade="all, delete-orphan")
    
    # Leitner
    leitner_boxes = relationship("LeitnerBox", back_populates="classroom", foreign_keys="LeitnerBox.classroom_id", cascade="all, delete-orphan")
    leitner_sessions = relationship("LeitnerSession", back_populates="classroom", foreign_keys="LeitnerSession.classroom_id", cascade="all, delete-orphan")


class ClassroomTeacher(Base):
    """Many-to-many relationship between Classroom and Teacher."""
    __tablename__ = "classroom_teachers"

    classroom_id = Column(String, ForeignKey("classrooms.id", ondelete="CASCADE"), primary_key=True)
    teacher_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    classroom = relationship("Classroom", back_populates="teachers")
    teacher = relationship("User", back_populates="teaching_classrooms")


class ClassroomStudent(Base):
    """Many-to-many relationship between Classroom and Student."""
    __tablename__ = "classroom_students"

    classroom_id = Column(String, ForeignKey("classrooms.id", ondelete="CASCADE"), primary_key=True)
    student_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    classroom = relationship("Classroom", back_populates="students")
    student = relationship("User", back_populates="enrolled_classrooms")
