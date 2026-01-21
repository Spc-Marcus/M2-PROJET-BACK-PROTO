from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import Level
from app.schemas.user import UserSummary


class ClassroomCreate(BaseModel):
    name: str
    level: Level


class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[Level] = None


class ClassroomResponse(BaseModel):
    id: str
    name: str
    level: Level
    code: str
    responsible_professor: UserSummary
    other_teachers: List[UserSummary] = []
    student_count: int = 0

    class Config:
        from_attributes = True


class ClassroomMembersResponse(BaseModel):
    classroom_id: str
    responsible_professor: UserSummary
    other_teachers: List[UserSummary] = []
    students: List[UserSummary] = []
    total_teachers: int = 0
    total_students: int = 0


class AddTeacherRequest(BaseModel):
    email: EmailStr


class EnrollStudentRequest(BaseModel):
    email: EmailStr


class JoinClassroomRequest(BaseModel):
    code: str


class RegenerateCodeResponse(BaseModel):
    classroom_id: str
    new_code: str
    generated_at: datetime
