from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ModuleDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(..., alias="id")
    classroom_id: UUID = Field(..., alias="classroomId")
    name: str = Field(..., alias="name")
    category: str = Field(..., alias="category")
    prerequisite_module_id: Optional[UUID] = Field(None, alias="prerequisiteModuleId")
    is_locked: bool = Field(..., alias="isLocked")
