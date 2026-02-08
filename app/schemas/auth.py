from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AuthRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr = Field(..., alias="email")
    password: str = Field(..., min_length=8, alias="password")


class RegisterStudentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr = Field(..., alias="email")
    password: str = Field(..., min_length=8, alias="password")
    name: str = Field(..., alias="name")
    level: Literal["L1", "L2", "L3", "M1", "M2"] = Field(..., alias="level")


class StudentProfileDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    level: str = Field(..., alias="level")

    @field_validator("level", mode="before")
    @classmethod
    def convert_level(cls, v):
        if hasattr(v, "value"):
            return v.value
        return v


class TeacherProfileDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    department: Optional[str] = Field(None, alias="department", validation_alias="faculty_department")


class UpdateUserDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: Optional[EmailStr] = Field(None, alias="email")
    avatar: Optional[str] = Field(None, alias="avatar")


class CreateUserAdminDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr = Field(..., alias="email")
    password: str = Field(..., min_length=8, alias="password")
    name: str = Field(..., alias="name")
    role: str = Field(..., alias="role")
    department: Optional[str] = Field(None, alias="department")


class UserResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., alias="id")
    email: EmailStr = Field(..., alias="email")
    role: str = Field(..., alias="role")
    student_profile: Optional[StudentProfileDto] = Field(None, alias="studentProfile")
    teacher_profile: Optional[TeacherProfileDto] = Field(None, alias="teacherProfile")

    @field_validator("role", mode="before")
    @classmethod
    def convert_role(cls, v):
        if hasattr(v, "value"):
            return v.value
        return v


class UserSummaryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., alias="id")
    email: EmailStr = Field(..., alias="email")
    name: str = Field(..., alias="name")
    role: str = Field(..., alias="role")

    @field_validator("role", mode="before")
    @classmethod
    def convert_role(cls, v):
        if hasattr(v, "value"):
            return v.value
        return v
