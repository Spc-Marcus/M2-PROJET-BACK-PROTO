from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.schemas.user import UserSummary


class QuizCreate(BaseModel):
    title: str
    prerequisite_quiz_id: Optional[str] = None
    min_score_to_unlock_next: int = 0
    is_active: bool = True


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    prerequisite_quiz_id: Optional[str] = None
    min_score_to_unlock_next: Optional[int] = None
    is_active: Optional[bool] = None


class QuizResponse(BaseModel):
    id: str
    module_id: str
    title: str
    prerequisite_quiz_id: Optional[str] = None
    min_score_to_unlock_next: int = 0
    question_count: int = 0
    is_active: bool = True
    is_locked: bool = False
    created_by: Optional[UserSummary] = None
    created_at: datetime

    class Config:
        from_attributes = True
