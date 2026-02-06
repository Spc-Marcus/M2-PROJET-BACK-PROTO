from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
    model_config = ConfigDict(populate_by_name=True)

    level: Literal["L1", "L2", "L3", "M1", "M2"] = Field(..., alias="level")


class TeacherProfileDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    department: str = Field(..., alias="department")


class UserResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(..., alias="id")
    email: EmailStr = Field(..., alias="email")
    role: Literal["STUDENT", "TEACHER", "ADMIN"] = Field(..., alias="role")
    student_profile: Optional[StudentProfileDto] = Field(None, alias="studentProfile")
    teacher_profile: Optional[TeacherProfileDto] = Field(None, alias="teacherProfile")


class UserSummaryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(..., alias="id")
    email: EmailStr = Field(..., alias="email")
    name: str = Field(..., alias="name")
    role: Literal["STUDENT", "TEACHER", "ADMIN"] = Field(..., alias="role")
