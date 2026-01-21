from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user
)
from app.core.config import settings
from app.models.user import User, Role, StudentProfile, TeacherProfile
from app.schemas.user import (
    AuthRequest, RegisterStudent, TokenResponse, UserResponse,
    CreateUserRequest, UpdateUserRequest, StudentProfileResponse, TeacherProfileResponse
)

router = APIRouter(prefix="/api", tags=["Authentication"])


@router.post("/auth/login", response_model=TokenResponse)
def login(request: AuthRequest, db: Session = Depends(get_db)):
    """Login and get JWT token."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value}
    )
    return TokenResponse(access_token=access_token)


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_student(request: RegisterStudent, db: Session = Depends(get_db)):
    """Register a new student account."""
    # Check if email exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=request.email,
        password=get_password_hash(request.password),
        name=request.name,
        role=Role.STUDENT
    )
    db.add(user)
    db.flush()
    
    # Create student profile
    profile = StudentProfile(
        user_id=user.id,
        level=request.level
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    
    return _user_to_response(user)


@router.get("/users/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return _user_to_response(current_user)


@router.patch("/users/me", response_model=UserResponse)
def update_current_user(
    request: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user profile."""
    if request.email:
        existing = db.query(User).filter(
            User.email == request.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use"
            )
        current_user.email = request.email
    
    if request.name:
        current_user.name = request.name
    
    db.commit()
    db.refresh(current_user)
    return _user_to_response(current_user)


@router.post("/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a teacher or admin account (admin only)."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if request.role == Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /auth/register for student accounts"
        )
    
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    user = User(
        email=request.email,
        password=get_password_hash(request.password),
        name=request.name,
        role=request.role
    )
    db.add(user)
    db.flush()
    
    if request.role == Role.TEACHER:
        profile = TeacherProfile(
            user_id=user.id,
            faculty_department=request.department
        )
        db.add(profile)
    
    db.commit()
    db.refresh(user)
    return _user_to_response(user)


def _user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse."""
    student_profile = None
    teacher_profile = None
    
    if user.student_profile:
        student_profile = StudentProfileResponse(level=user.student_profile.level)
    if user.teacher_profile:
        teacher_profile = TeacherProfileResponse(department=user.teacher_profile.faculty_department)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        student_profile=student_profile,
        teacher_profile=teacher_profile
    )
