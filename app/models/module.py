"""Module model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class Module(Base):
    """Module model."""
    __tablename__ = "modules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    prerequisite_module_id = Column(String, ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    classroom = relationship("Classroom", back_populates="modules")
    quizzes = relationship("Quiz", back_populates="module", cascade="all, delete-orphan", foreign_keys="Quiz.module_id")
    
    # Self-referencing for prerequisites
    prerequisite_module = relationship("Module", remote_side=[id], foreign_keys=[prerequisite_module_id])
