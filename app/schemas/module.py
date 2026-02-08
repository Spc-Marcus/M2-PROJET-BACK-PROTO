from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateModuleDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="name")
    category: Optional[str] = Field(None, alias="category")
    prerequisite_module_id: Optional[str] = Field(None, alias="prerequisiteModuleId")


class UpdateModuleDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, alias="name")
    category: Optional[str] = Field(None, alias="category")
    prerequisite_module_id: Optional[str] = Field(None, alias="prerequisiteModuleId")


class ModuleDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., alias="id")
    classroom_id: str = Field(..., alias="classroomId")
    name: str = Field(..., alias="name")
    category: Optional[str] = Field(None, alias="category")
    prerequisite_module_id: Optional[str] = Field(None, alias="prerequisiteModuleId")
    is_locked: bool = Field(default=False, alias="isLocked")
