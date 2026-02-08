"""Authentication routes."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User, Role
from app.schemas.auth import (
    AuthRequestDto, RegisterStudentDto, UserResponseDto,
    UpdateUserDto, CreateUserAdminDto
)
from app.services import auth_service

router = APIRouter()
users_router = APIRouter()
admin_router = APIRouter()


@router.post("/login")
async def login(
    credentials: AuthRequestDto,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Login and get JWT token."""
    token = await auth_service.login(db, credentials)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponseDto, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterStudentDto,
    db: AsyncSession = Depends(get_db)
):
    """Register a new student account."""
    user = await auth_service.register_student(db, data)
    return user


@users_router.get("/users/me", response_model=UserResponseDto)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile."""
    user = await auth_service.get_user_with_profile(db, current_user.id)
    return user


@users_router.patch("/users/me", response_model=UserResponseDto)
async def update_current_user_profile(
    data: UpdateUserDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    return await auth_service.update_user_profile(db, current_user, data.email, data.avatar)


@admin_router.post("/admin/users", response_model=UserResponseDto, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    data: CreateUserAdminDto,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)."""
    try:
        user_role = Role[data.role]
    except KeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    
    return await auth_service.create_user(db, data.email, data.password, data.name, user_role, data.department)
