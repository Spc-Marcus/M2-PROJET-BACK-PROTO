from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import Role, Level


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterStudent(BaseModel):
    email: EmailStr
    password: str
    name: str
    level: Level = Level.L1


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StudentProfileResponse(BaseModel):
    level: Level

    class Config:
        from_attributes = True


class TeacherProfileResponse(BaseModel):
    department: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: Role
    student_profile: Optional[StudentProfileResponse] = None
    teacher_profile: Optional[TeacherProfileResponse] = None

    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    id: str
    email: str
    name: str
    role: Optional[Role] = None

    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    """For admin to create teacher or admin accounts."""
    email: EmailStr
    password: str
    name: str
    role: Role
    department: Optional[str] = None  # For teachers


class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
