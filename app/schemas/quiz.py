from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .auth import UserSummaryDto


class QuizDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(..., alias="id")
    module_id: UUID = Field(..., alias="moduleId")
    title: str = Field(..., alias="title")
    prerequisite_quiz_id: Optional[UUID] = Field(None, alias="prerequisiteQuizId")
    min_score_to_unlock_next: int = Field(..., alias="minScoreToUnlockNext")
    question_count: int = Field(..., alias="questionCount")
    is_active: bool = Field(..., alias="isActive")
    is_locked: bool = Field(..., alias="isLocked")
    created_by: UserSummaryDto = Field(..., alias="createdBy")
    created_at: datetime = Field(..., alias="createdAt")
