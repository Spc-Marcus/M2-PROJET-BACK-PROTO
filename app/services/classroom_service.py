"""Classroom service."""
import random
import string
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.classroom import Classroom, ClassroomTeacher, ClassroomStudent
from app.models.user import User, Role
from app.models.module import Module
from app.models.quiz import Quiz
from app.models.completion import CompletedModule, CompletedQuiz
from app.models.leitner import LeitnerBox, LeitnerSession


def generate_classroom_code() -> str:
    """Generate a random 6-character alphanumeric code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


async def get_classrooms_for_user(db: AsyncSession, user: User) -> List[Classroom]:
    """Get classrooms for a user based on their role."""
    if user.role == Role.STUDENT:
        result = await db.execute(
            select(Classroom)
            .join(ClassroomStudent)
            .where(ClassroomStudent.student_id == user.id)
        )
        return list(result.scalars().all())
    elif user.role == Role.TEACHER:
        result = await db.execute(
            select(Classroom)
            .where(
                (Classroom.responsible_professor_id == user.id) |
                (Classroom.id.in_(
                    select(ClassroomTeacher.classroom_id)
                    .where(ClassroomTeacher.teacher_id == user.id)
                ))
            )
        )
        return list(result.scalars().all())
    else:
        result = await db.execute(select(Classroom))
        return list(result.scalars().all())


async def create_classroom(db: AsyncSession, name: str, level: str, professor: User) -> Classroom:
    """Create a new classroom."""
    if professor.role != Role.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="INSUFFICIENT_PERMISSIONS"
        )
    
    code = generate_classroom_code()
    while (await db.execute(select(Classroom).where(Classroom.code == code))).scalar_one_or_none():
        code = generate_classroom_code()
    
    classroom = Classroom(
        name=name,
        level=level,
        code=code,
        responsible_professor_id=professor.id
    )
    
    db.add(classroom)
    await db.commit()
    await db.refresh(classroom)
    
    return classroom


async def get_classroom_by_id(db: AsyncSession, classroom_id: str, user: User) -> Classroom:
    """Get classroom by ID with permission check."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if not await is_classroom_member(db, classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    return classroom


async def update_classroom(db: AsyncSession, classroom_id: str, user: User, name: str = None, level: str = None) -> Classroom:
    """Update classroom (responsible professor only)."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if classroom.responsible_professor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    if name:
        classroom.name = name
    if level:
        classroom.level = level
    
    await db.commit()
    await db.refresh(classroom)
    
    return classroom


async def delete_classroom(db: AsyncSession, classroom_id: str, user: User):
    """Delete classroom (responsible professor only)."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if classroom.responsible_professor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    await db.delete(classroom)
    await db.commit()


async def add_teacher(db: AsyncSession, classroom_id: str, teacher_email: str, user: User) -> Classroom:
    """Add a teacher to the classroom."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if classroom.responsible_professor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    result = await db.execute(select(User).where(User.email == teacher_email))
    teacher = result.scalar_one_or_none()
    
    if not teacher or teacher.role != Role.TEACHER:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    
    result = await db.execute(
        select(ClassroomTeacher)
        .where(ClassroomTeacher.classroom_id == classroom_id, ClassroomTeacher.teacher_id == teacher.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Teacher already added")
    
    classroom_teacher = ClassroomTeacher(classroom_id=classroom_id, teacher_id=teacher.id)
    db.add(classroom_teacher)
    await db.commit()
    await db.refresh(classroom)
    
    return classroom


async def remove_teacher(db: AsyncSession, classroom_id: str, teacher_id: str, user: User):
    """Remove a teacher from the classroom."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if classroom.responsible_professor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    result = await db.execute(
        select(ClassroomTeacher)
        .where(ClassroomTeacher.classroom_id == classroom_id, ClassroomTeacher.teacher_id == teacher_id)
    )
    classroom_teacher = result.scalar_one_or_none()
    
    if not classroom_teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not in classroom")
    
    await db.delete(classroom_teacher)
    await db.commit()


async def enroll_student(db: AsyncSession, classroom_id: str, student_email: str, user: User):
    """Enroll a student in the classroom."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if classroom.responsible_professor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    result = await db.execute(select(User).where(User.email == student_email))
    student = result.scalar_one_or_none()
    
    if not student or student.role != Role.STUDENT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    result = await db.execute(
        select(ClassroomStudent)
        .where(ClassroomStudent.classroom_id == classroom_id, ClassroomStudent.student_id == student.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ALREADY_ENROLLED")
    
    classroom_student = ClassroomStudent(classroom_id=classroom_id, student_id=student.id)
    db.add(classroom_student)
    await db.commit()


async def remove_student(db: AsyncSession, classroom_id: str, student_id: str, user: User):
    """Remove a student from the classroom."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if classroom.responsible_professor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    result = await db.execute(
        select(ClassroomStudent)
        .where(ClassroomStudent.classroom_id == classroom_id, ClassroomStudent.student_id == student_id)
    )
    classroom_student = result.scalar_one_or_none()
    
    if not classroom_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not in classroom")
    
    # Clean up student progress and Leitner data
    await db.execute(
        CompletedModule.__table__.delete().where(
            CompletedModule.student_id == student_id,
            CompletedModule.module_id.in_(
                select(Module.id).join(Classroom).where(Classroom.id == classroom_id)
            )
        )
    )
    await db.execute(
        CompletedQuiz.__table__.delete().where(
            CompletedQuiz.student_id == student_id,
            CompletedQuiz.quiz_id.in_(
                select(Quiz.id).join(Module).join(Classroom).where(Classroom.id == classroom_id)
            )
        )
    )
    await db.execute(
        LeitnerBox.__table__.delete().where(
            LeitnerBox.student_id == student_id,
            LeitnerBox.classroom_id == classroom_id
        )
    )
    
    await db.delete(classroom_student)
    await db.commit()


async def join_classroom(db: AsyncSession, classroom_id: str, code: str, user: User) -> Classroom:
    """Join a classroom using a code (student only)."""
    if user.role != Role.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if classroom.code != code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CLASSROOM_CODE_INVALID")
    
    result = await db.execute(
        select(ClassroomStudent)
        .where(ClassroomStudent.classroom_id == classroom_id, ClassroomStudent.student_id == user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ALREADY_ENROLLED")
    
    classroom_student = ClassroomStudent(classroom_id=classroom_id, student_id=user.id)
    db.add(classroom_student)
    await db.commit()
    await db.refresh(classroom)
    
    return classroom


async def regenerate_code(db: AsyncSession, classroom_id: str, user: User) -> str:
    """Regenerate classroom access code."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if classroom.responsible_professor_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    code = generate_classroom_code()
    while (await db.execute(select(Classroom).where(Classroom.code == code))).scalar_one_or_none():
        code = generate_classroom_code()
    
    classroom.code = code
    await db.commit()
    
    return code


async def get_classroom_members(db: AsyncSession, classroom_id: str, user: User):
    """Get all members of a classroom."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if not await is_classroom_teacher(db, classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    result = await db.execute(
        select(User)
        .join(ClassroomTeacher)
        .where(ClassroomTeacher.classroom_id == classroom_id)
    )
    teachers = list(result.scalars().all())
    
    result = await db.execute(
        select(User)
        .join(ClassroomStudent)
        .where(ClassroomStudent.classroom_id == classroom_id)
    )
    students = list(result.scalars().all())
    
    return {
        "teachers": teachers,
        "students": students,
        "responsible_professor": classroom.responsible_professor
    }


async def is_classroom_member(db: AsyncSession, classroom_id: str, user_id: str) -> bool:
    """Check if user is a member of the classroom."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        return False
    
    if classroom.responsible_professor_id == user_id:
        return True
    
    result = await db.execute(
        select(ClassroomTeacher)
        .where(ClassroomTeacher.classroom_id == classroom_id, ClassroomTeacher.teacher_id == user_id)
    )
    if result.scalar_one_or_none():
        return True
    
    result = await db.execute(
        select(ClassroomStudent)
        .where(ClassroomStudent.classroom_id == classroom_id, ClassroomStudent.student_id == user_id)
    )
    return result.scalar_one_or_none() is not None


async def is_classroom_teacher(db: AsyncSession, classroom_id: str, user_id: str) -> bool:
    """Check if user is a teacher in the classroom."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        return False
    
    if classroom.responsible_professor_id == user_id:
        return True
    
    result = await db.execute(
        select(ClassroomTeacher)
        .where(ClassroomTeacher.classroom_id == classroom_id, ClassroomTeacher.teacher_id == user_id)
    )
    return result.scalar_one_or_none() is not None


async def is_responsible_professor(db: AsyncSession, classroom_id: str, user_id: str) -> bool:
    """Check if user is the responsible professor of the classroom."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        return False
    
    return classroom.responsible_professor_id == user_id
