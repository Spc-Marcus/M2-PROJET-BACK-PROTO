from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import generate_uuid


class Module(Base):
    __tablename__ = "modules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(255))
    prerequisite_module_id = Column(String(36), ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    classroom = relationship("Classroom", back_populates="modules")
    prerequisite_module = relationship("Module", remote_side="Module.id", foreign_keys=[prerequisite_module_id])
    quizzes = relationship("Quiz", back_populates="module", cascade="all, delete-orphan")
    completed_modules = relationship("CompletedModule", back_populates="module", cascade="all, delete-orphan")
