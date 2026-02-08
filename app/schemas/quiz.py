from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .auth import UserSummaryDto


class CreateQuizDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., alias="title")
    prerequisite_quiz_id: Optional[str] = Field(None, alias="prerequisiteQuizId")
    min_score_to_unlock_next: Optional[int] = Field(None, alias="minScoreToUnlockNext")
    is_active: Optional[bool] = Field(True, alias="isActive")


class UpdateQuizDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = Field(None, alias="title")
    prerequisite_quiz_id: Optional[str] = Field(None, alias="prerequisiteQuizId")
    min_score_to_unlock_next: Optional[int] = Field(None, alias="minScoreToUnlockNext")
    is_active: Optional[bool] = Field(None, alias="isActive")


class QuizDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., alias="id")
    module_id: str = Field(..., alias="moduleId")
    title: str = Field(..., alias="title")
    prerequisite_quiz_id: Optional[str] = Field(None, alias="prerequisiteQuizId")
    min_score_to_unlock_next: Optional[int] = Field(None, alias="minScoreToUnlockNext")
    question_count: int = Field(default=0, alias="questionCount")
    is_active: bool = Field(default=True, alias="isActive")
    is_locked: bool = Field(default=False, alias="isLocked")
    created_by: Optional[UserSummaryDto] = Field(None, alias="createdBy")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
