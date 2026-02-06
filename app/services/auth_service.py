"""Authentication service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User, Role, StudentProfile, TeacherProfile
from app.core.security import verify_password, get_password_hash, create_access_token
from app.schemas.auth import AuthRequestDto, RegisterStudentDto


async def login(db: AsyncSession, credentials: AuthRequestDto) -> str:
    """Authenticate user and return JWT token."""
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token = create_access_token(data={"sub": user.id})
    return token


async def register_student(db: AsyncSession, data: RegisterStudentDto) -> User:
    """Register a new student account."""
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    user = User(
        email=data.email,
        password=get_password_hash(data.password),
        name=data.name,
        role=Role.STUDENT
    )
    
    student_profile = StudentProfile(
        user=user,
        level=data.level
    )
    
    db.add(user)
    db.add(student_profile)
    await db.commit()
    await db.refresh(user)
    
    return user


async def create_user(db: AsyncSession, email: str, password: str, name: str, role: Role, department: str = None) -> User:
    """Create a new user account (admin only)."""
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    user = User(
        email=email,
        password=get_password_hash(password),
        name=name,
        role=role
    )
    
    db.add(user)
    
    if role == Role.TEACHER and department:
        teacher_profile = TeacherProfile(
            user=user,
            faculty_department=department
        )
        db.add(teacher_profile)
    
    await db.commit()
    await db.refresh(user)
    
    return user


async def update_user_profile(db: AsyncSession, user: User, email: str = None, avatar: str = None) -> User:
    """Update user profile."""
    if email:
        result = await db.execute(select(User).where(User.email == email, User.id != user.id))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use"
            )
        user.email = email
    
    await db.commit()
    await db.refresh(user)
    
    return user
