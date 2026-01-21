import uuid
import random
import string
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import Level, generate_uuid


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    level = Column(Enum(Level), nullable=False)
    code = Column(String(6), unique=True, nullable=False, index=True)
    responsible_professor_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    responsible_professor = relationship("User", back_populates="responsible_classrooms", foreign_keys=[responsible_professor_id])
    teachers = relationship("ClassroomTeacher", back_populates="classroom", cascade="all, delete-orphan")
    students = relationship("ClassroomStudent", back_populates="classroom", cascade="all, delete-orphan")
    modules = relationship("Module", back_populates="classroom", cascade="all, delete-orphan")
    quiz_sessions = relationship("QuizSession", back_populates="classroom", cascade="all, delete-orphan")
    leitner_boxes = relationship("LeitnerBox", back_populates="classroom", cascade="all, delete-orphan")
    leitner_sessions = relationship("LeitnerSession", back_populates="classroom", cascade="all, delete-orphan")

    @staticmethod
    def generate_code(length: int = 6) -> str:
        """Generate a random classroom access code."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


class ClassroomTeacher(Base):
    __tablename__ = "classroom_teachers"

    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), primary_key=True)
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    classroom = relationship("Classroom", back_populates="teachers")
    teacher = relationship("User")


class ClassroomStudent(Base):
    __tablename__ = "classroom_students"

    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), primary_key=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    enrolled_at = Column(DateTime, default=datetime.utcnow)

    classroom = relationship("Classroom", back_populates="students")
    student = relationship("User")
