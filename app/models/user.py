"""User models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base


class Role(str, enum.Enum):
    """User role enumeration."""
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"


class Level(str, enum.Enum):
    """Academic level enumeration."""
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    M1 = "M1"
    M2 = "M2"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Classrooms where user is responsible professor
    responsible_classrooms = relationship("Classroom", back_populates="responsible_professor", foreign_keys="Classroom.responsible_professor_id")
    
    # Many-to-many relationships
    teaching_classrooms = relationship("ClassroomTeacher", back_populates="teacher")
    enrolled_classrooms = relationship("ClassroomStudent", back_populates="student")
    
    # Quiz sessions
    quiz_sessions = relationship("QuizSession", back_populates="student", foreign_keys="QuizSession.student_id")
    
    # Leitner
    leitner_boxes = relationship("LeitnerBox", back_populates="student", foreign_keys="LeitnerBox.student_id")
    leitner_sessions = relationship("LeitnerSession", back_populates="student", foreign_keys="LeitnerSession.student_id")


class StudentProfile(Base):
    """Student profile model."""
    __tablename__ = "student_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    level = Column(Enum(Level), nullable=False)

    # Relationships
    user = relationship("User", back_populates="student_profile")


class TeacherProfile(Base):
    """Teacher profile model."""
    __tablename__ = "teacher_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    faculty_department = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="teacher_profile")
