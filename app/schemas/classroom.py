from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .auth import UserSummaryDto


class ClassroomDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(..., alias="id")
    name: str = Field(..., alias="name")
    level: str = Field(..., alias="level")
    code: str = Field(..., alias="code")
    responsible_professor: UserSummaryDto = Field(..., alias="responsibleProfessor")
    other_teachers: list[UserSummaryDto] = Field(..., alias="otherTeachers")
    student_count: int = Field(..., alias="studentCount")


class ClassroomMembersDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    classroom_id: UUID = Field(..., alias="classroomId")
    responsible_professor: UserSummaryDto = Field(..., alias="responsibleProfessor")
    other_teachers: list[UserSummaryDto] = Field(..., alias="otherTeachers")
    students: list[UserSummaryDto] = Field(..., alias="students")
    total_teachers: int = Field(..., alias="totalTeachers")
    total_students: int = Field(..., alias="totalStudents")


class AddTeacherToClassroomDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr = Field(..., alias="email")


class EnrollStudentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr = Field(..., alias="email")


class RegenerateCodeResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    classroom_id: UUID = Field(..., alias="classroomId")
    new_code: str = Field(..., alias="newCode")
    generated_at: datetime = Field(..., alias="generatedAt")
