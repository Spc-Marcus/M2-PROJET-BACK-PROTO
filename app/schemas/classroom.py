from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .auth import UserSummaryDto


class CreateClassroomDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="name")
    level: str = Field(..., alias="level")


class UpdateClassroomDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, alias="name")
    level: Optional[str] = Field(None, alias="level")


class JoinClassroomDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., alias="code")


class ClassroomDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., alias="id")
    name: str = Field(..., alias="name")
    level: str = Field(..., alias="level")
    code: str = Field(..., alias="code")
    responsible_professor: UserSummaryDto = Field(..., alias="responsibleProfessor")
    other_teachers: list[UserSummaryDto] = Field(default=[], alias="otherTeachers")
    student_count: int = Field(default=0, alias="studentCount")

    @field_validator("level", mode="before")
    @classmethod
    def convert_level(cls, v):
        if hasattr(v, "value"):
            return v.value
        return v


class ClassroomMembersDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    classroom_id: str = Field(..., alias="classroomId")
    responsible_professor: UserSummaryDto = Field(..., alias="responsibleProfessor")
    other_teachers: list[UserSummaryDto] = Field(default=[], alias="otherTeachers")
    students: list[UserSummaryDto] = Field(default=[], alias="students")
    total_teachers: int = Field(default=0, alias="totalTeachers")
    total_students: int = Field(default=0, alias="totalStudents")


class AddTeacherToClassroomDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr = Field(..., alias="email")


class EnrollStudentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr = Field(..., alias="email")


class RegenerateCodeResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    classroom_id: str = Field(..., alias="classroomId")
    new_code: str = Field(..., alias="newCode")
    generated_at: datetime = Field(..., alias="generatedAt")
