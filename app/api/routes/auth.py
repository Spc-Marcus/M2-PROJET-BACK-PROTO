"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User, Role
from app.schemas.auth import AuthRequestDto, RegisterStudentDto, UserResponseDto
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(
    credentials: AuthRequestDto,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Login and get JWT token."""
    token = await auth_service.login(db, credentials)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponseDto)
async def register(
    data: RegisterStudentDto,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Register a new student account."""
    return await auth_service.register_student(db, data)


@router.get("/users/me", response_model=UserResponseDto)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user profile."""
    return current_user


@router.patch("/users/me", response_model=UserResponseDto)
async def update_current_user_profile(
    email: str = None,
    avatar: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Update current user profile."""
    return await auth_service.update_user_profile(db, current_user, email, avatar)


@router.post("/admin/users", response_model=UserResponseDto)
async def create_user_admin(
    email: str,
    password: str,
    name: str,
    role: str,
    department: str = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Create a new user (admin only)."""
    try:
        user_role = Role[role]
    except KeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    
    return await auth_service.create_user(db, email, password, name, user_role, department)
