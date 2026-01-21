from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Role
from app.models.classroom import Classroom, ClassroomTeacher, ClassroomStudent
from app.schemas.classroom import (
    ClassroomCreate, ClassroomUpdate, ClassroomResponse, ClassroomMembersResponse,
    AddTeacherRequest, EnrollStudentRequest, JoinClassroomRequest, RegenerateCodeResponse
)
from app.schemas.user import UserSummary
from app.schemas.common import PaginatedResponse, create_pagination

router = APIRouter(prefix="/api/classrooms", tags=["Classrooms"])


@router.get("", response_model=List[ClassroomResponse])
def list_classrooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List classrooms based on user role."""
    if current_user.role == Role.STUDENT:
        # Get classrooms where user is enrolled
        enrollments = db.query(ClassroomStudent).filter(
            ClassroomStudent.student_id == current_user.id
        ).all()
        classroom_ids = [e.classroom_id for e in enrollments]
        classrooms = db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()
    elif current_user.role == Role.ADMIN:
        # Admin sees all
        classrooms = db.query(Classroom).all()
    else:
        # Teacher: classrooms where they're responsible or teacher
        responsible = db.query(Classroom).filter(
            Classroom.responsible_professor_id == current_user.id
        ).all()
        
        teacher_links = db.query(ClassroomTeacher).filter(
            ClassroomTeacher.teacher_id == current_user.id
        ).all()
        teacher_classroom_ids = [t.classroom_id for t in teacher_links]
        
        other = db.query(Classroom).filter(Classroom.id.in_(teacher_classroom_ids)).all()
        classrooms = list(set(responsible + other))
    
    return [_classroom_to_response(c, db) for c in classrooms]


@router.post("", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED)
def create_classroom(
    request: ClassroomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new classroom (teachers only)."""
    if current_user.role not in [Role.TEACHER, Role.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers only"
        )
    
    classroom = Classroom(
        name=request.name,
        level=request.level,
        code=Classroom.generate_code(),
        responsible_professor_id=current_user.id
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    
    return _classroom_to_response(classroom, db)


@router.get("/{classroom_id}", response_model=ClassroomResponse)
def get_classroom(
    classroom_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get classroom details."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_classroom_member(classroom, current_user, db)
    
    return _classroom_to_response(classroom, db)


@router.patch("/{classroom_id}", response_model=ClassroomResponse)
def update_classroom(
    classroom_id: str,
    request: ClassroomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update classroom (responsible professor only)."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_responsible_professor(classroom, current_user)
    
    if request.name:
        classroom.name = request.name
    if request.level:
        classroom.level = request.level
    
    db.commit()
    db.refresh(classroom)
    return _classroom_to_response(classroom, db)


@router.delete("/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classroom(
    classroom_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a classroom (responsible professor only)."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_responsible_professor(classroom, current_user)
    
    db.delete(classroom)
    db.commit()


@router.get("/{classroom_id}/members", response_model=ClassroomMembersResponse)
def list_members(
    classroom_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all members of a classroom (teachers only)."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_classroom_teacher(classroom, current_user, db)
    
    # Get responsible professor
    resp_prof = db.query(User).filter(User.id == classroom.responsible_professor_id).first()
    
    # Get other teachers
    teacher_links = db.query(ClassroomTeacher).filter(
        ClassroomTeacher.classroom_id == classroom_id
    ).all()
    teachers = [db.query(User).filter(User.id == t.teacher_id).first() for t in teacher_links]
    
    # Get students
    student_links = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id
    ).all()
    students = [db.query(User).filter(User.id == s.student_id).first() for s in student_links]
    
    return ClassroomMembersResponse(
        classroom_id=classroom_id,
        responsible_professor=_user_to_summary(resp_prof),
        other_teachers=[_user_to_summary(t) for t in teachers if t],
        students=[_user_to_summary(s) for s in students if s],
        total_teachers=len(teachers) + 1,
        total_students=len(students)
    )


@router.post("/{classroom_id}/teachers", response_model=ClassroomResponse)
def add_teacher(
    classroom_id: str,
    request: AddTeacherRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a teacher to the classroom (responsible professor only)."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_responsible_professor(classroom, current_user)
    
    teacher = db.query(User).filter(User.email == request.email).first()
    if not teacher or teacher.role != Role.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check if already a teacher
    existing = db.query(ClassroomTeacher).filter(
        ClassroomTeacher.classroom_id == classroom_id,
        ClassroomTeacher.teacher_id == teacher.id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Teacher already in classroom"
        )
    
    link = ClassroomTeacher(classroom_id=classroom_id, teacher_id=teacher.id)
    db.add(link)
    db.commit()
    db.refresh(classroom)
    
    return _classroom_to_response(classroom, db)


@router.delete("/{classroom_id}/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_teacher(
    classroom_id: str,
    teacher_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a teacher from the classroom (responsible professor only)."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_responsible_professor(classroom, current_user)
    
    link = db.query(ClassroomTeacher).filter(
        ClassroomTeacher.classroom_id == classroom_id,
        ClassroomTeacher.teacher_id == teacher_id
    ).first()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not in classroom"
        )
    
    db.delete(link)
    db.commit()


@router.post("/{classroom_id}/enroll", status_code=status.HTTP_200_OK)
def enroll_student(
    classroom_id: str,
    request: EnrollStudentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enroll a student by email (responsible professor only)."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_responsible_professor(classroom, current_user)
    
    student = db.query(User).filter(User.email == request.email).first()
    if not student or student.role != Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    existing = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id,
        ClassroomStudent.student_id == student.id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student already enrolled"
        )
    
    link = ClassroomStudent(classroom_id=classroom_id, student_id=student.id)
    db.add(link)
    db.commit()
    
    return {"message": "Student enrolled successfully"}


@router.delete("/{classroom_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student(
    classroom_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a student from the classroom (responsible professor only)."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_responsible_professor(classroom, current_user)
    
    link = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id,
        ClassroomStudent.student_id == student_id
    ).first()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not in classroom"
        )
    
    db.delete(link)
    db.commit()


@router.post("/{classroom_id}/join", response_model=ClassroomResponse)
def join_classroom(
    classroom_id: str,
    request: JoinClassroomRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Join a classroom using access code (students only)."""
    if current_user.role != Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students only"
        )
    
    classroom = _get_classroom_or_404(classroom_id, db)
    
    if classroom.code != request.code.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid classroom code"
        )
    
    existing = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id,
        ClassroomStudent.student_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already enrolled"
        )
    
    link = ClassroomStudent(classroom_id=classroom_id, student_id=current_user.id)
    db.add(link)
    db.commit()
    db.refresh(classroom)
    
    return _classroom_to_response(classroom, db)


@router.post("/{classroom_id}/regenerate-code", response_model=RegenerateCodeResponse)
def regenerate_code(
    classroom_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate classroom access code (responsible professor only)."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_responsible_professor(classroom, current_user)
    
    classroom.code = Classroom.generate_code()
    db.commit()
    
    return RegenerateCodeResponse(
        classroom_id=classroom_id,
        new_code=classroom.code,
        generated_at=datetime.utcnow()
    )


# Helper functions
def _get_classroom_or_404(classroom_id: str, db: Session) -> Classroom:
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    return classroom


def _check_responsible_professor(classroom: Classroom, user: User):
    if classroom.responsible_professor_id != user.id and user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Responsible professor only"
        )


def _check_classroom_teacher(classroom: Classroom, user: User, db: Session):
    if user.role == Role.ADMIN:
        return
    if classroom.responsible_professor_id == user.id:
        return
    teacher_link = db.query(ClassroomTeacher).filter(
        ClassroomTeacher.classroom_id == classroom.id,
        ClassroomTeacher.teacher_id == user.id
    ).first()
    if not teacher_link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Classroom teacher access required"
        )


def _check_classroom_member(classroom: Classroom, user: User, db: Session):
    if user.role == Role.ADMIN:
        return
    if classroom.responsible_professor_id == user.id:
        return
    
    teacher_link = db.query(ClassroomTeacher).filter(
        ClassroomTeacher.classroom_id == classroom.id,
        ClassroomTeacher.teacher_id == user.id
    ).first()
    if teacher_link:
        return
    
    student_link = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom.id,
        ClassroomStudent.student_id == user.id
    ).first()
    if student_link:
        return
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Classroom member access required"
    )


def _classroom_to_response(classroom: Classroom, db: Session) -> ClassroomResponse:
    resp_prof = db.query(User).filter(User.id == classroom.responsible_professor_id).first()
    
    teacher_links = db.query(ClassroomTeacher).filter(
        ClassroomTeacher.classroom_id == classroom.id
    ).all()
    other_teachers = []
    for link in teacher_links:
        teacher = db.query(User).filter(User.id == link.teacher_id).first()
        if teacher:
            other_teachers.append(_user_to_summary(teacher))
    
    student_count = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom.id
    ).count()
    
    return ClassroomResponse(
        id=classroom.id,
        name=classroom.name,
        level=classroom.level,
        code=classroom.code,
        responsible_professor=_user_to_summary(resp_prof),
        other_teachers=other_teachers,
        student_count=student_count
    )


def _user_to_summary(user: User) -> UserSummary:
    return UserSummary(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role
    )
