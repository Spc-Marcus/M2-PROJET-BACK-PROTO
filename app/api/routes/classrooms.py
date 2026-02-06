"""Classroom routes."""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_teacher
from app.models.user import User
from app.schemas.classroom import (
    ClassroomDto, ClassroomMembersDto, AddTeacherToClassroomDto,
    EnrollStudentDto, RegenerateCodeResponseDto
)
from app.services import classroom_service

router = APIRouter(prefix="/api/classrooms", tags=["classrooms"])


@router.get("", response_model=List[ClassroomDto])
async def get_classrooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all classrooms for current user."""
    classrooms = await classroom_service.get_classrooms_for_user(db, current_user)
    
    # Convert to DTOs
    result = []
    for classroom in classrooms:
        other_teachers = [t.teacher for t in classroom.teachers]
        result.append(ClassroomDto(
            id=classroom.id,
            name=classroom.name,
            level=classroom.level,
            code=classroom.code,
            responsibleProfessor={
                "id": classroom.responsible_professor.id,
                "email": classroom.responsible_professor.email,
                "name": classroom.responsible_professor.name,
                "role": classroom.responsible_professor.role
            },
            otherTeachers=[{
                "id": t.id,
                "email": t.email,
                "name": t.name,
                "role": t.role
            } for t in other_teachers],
            studentCount=len(classroom.students)
        ))
    
    return result


@router.post("", response_model=ClassroomDto, status_code=status.HTTP_201_CREATED)
async def create_classroom(
    name: str,
    level: str,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """Create a new classroom."""
    classroom = await classroom_service.create_classroom(db, name, level, current_user)
    
    return ClassroomDto(
        id=classroom.id,
        name=classroom.name,
        level=classroom.level,
        code=classroom.code,
        responsibleProfessor={
            "id": classroom.responsible_professor.id,
            "email": classroom.responsible_professor.email,
            "name": classroom.responsible_professor.name,
            "role": classroom.responsible_professor.role
        },
        otherTeachers=[],
        studentCount=0
    )


@router.get("/{id}", response_model=ClassroomDto)
async def get_classroom(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get classroom by ID."""
    classroom = await classroom_service.get_classroom_by_id(db, id, current_user)
    
    other_teachers = [t.teacher for t in classroom.teachers]
    
    return ClassroomDto(
        id=classroom.id,
        name=classroom.name,
        level=classroom.level,
        code=classroom.code,
        responsibleProfessor={
            "id": classroom.responsible_professor.id,
            "email": classroom.responsible_professor.email,
            "name": classroom.responsible_professor.name,
            "role": classroom.responsible_professor.role
        },
        otherTeachers=[{
            "id": t.id,
            "email": t.email,
            "name": t.name,
            "role": t.role
        } for t in other_teachers],
        studentCount=len(classroom.students)
    )


@router.patch("/{id}", response_model=ClassroomDto)
async def update_classroom(
    id: str,
    name: str = None,
    level: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update classroom (responsible professor only)."""
    classroom = await classroom_service.update_classroom(db, id, current_user, name, level)
    
    other_teachers = [t.teacher for t in classroom.teachers]
    
    return ClassroomDto(
        id=classroom.id,
        name=classroom.name,
        level=classroom.level,
        code=classroom.code,
        responsibleProfessor={
            "id": classroom.responsible_professor.id,
            "email": classroom.responsible_professor.email,
            "name": classroom.responsible_professor.name,
            "role": classroom.responsible_professor.role
        },
        otherTeachers=[{
            "id": t.id,
            "email": t.email,
            "name": t.name,
            "role": t.role
        } for t in other_teachers],
        studentCount=len(classroom.students)
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_classroom(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete classroom."""
    await classroom_service.delete_classroom(db, id, current_user)


@router.get("/{id}/members", response_model=ClassroomMembersDto)
async def get_classroom_members(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all classroom members."""
    members = await classroom_service.get_classroom_members(db, id, current_user)
    
    return ClassroomMembersDto(
        classroomId=id,
        responsibleProfessor={
            "id": members["responsible_professor"].id,
            "email": members["responsible_professor"].email,
            "name": members["responsible_professor"].name,
            "role": members["responsible_professor"].role
        },
        otherTeachers=[{
            "id": t.id,
            "email": t.email,
            "name": t.name,
            "role": t.role
        } for t in members["teachers"]],
        students=[{
            "id": s.id,
            "email": s.email,
            "name": s.name,
            "role": s.role
        } for s in members["students"]],
        totalTeachers=len(members["teachers"]),
        totalStudents=len(members["students"])
    )


@router.post("/{id}/teachers", response_model=ClassroomDto)
async def add_teacher(
    id: str,
    data: AddTeacherToClassroomDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add teacher to classroom."""
    classroom = await classroom_service.add_teacher(db, id, data.email, current_user)
    
    other_teachers = [t.teacher for t in classroom.teachers]
    
    return ClassroomDto(
        id=classroom.id,
        name=classroom.name,
        level=classroom.level,
        code=classroom.code,
        responsibleProfessor={
            "id": classroom.responsible_professor.id,
            "email": classroom.responsible_professor.email,
            "name": classroom.responsible_professor.name,
            "role": classroom.responsible_professor.role
        },
        otherTeachers=[{
            "id": t.id,
            "email": t.email,
            "name": t.name,
            "role": t.role
        } for t in other_teachers],
        studentCount=len(classroom.students)
    )


@router.delete("/{id}/teachers/{teacherId}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_teacher(
    id: str,
    teacherId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove teacher from classroom."""
    await classroom_service.remove_teacher(db, id, teacherId, current_user)


@router.post("/{id}/enroll", status_code=status.HTTP_200_OK)
async def enroll_student(
    id: str,
    data: EnrollStudentDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enroll student in classroom."""
    await classroom_service.enroll_student(db, id, data.email, current_user)
    return {"message": "Student enrolled successfully"}


@router.delete("/{id}/students/{studentId}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student(
    id: str,
    studentId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove student from classroom."""
    await classroom_service.remove_student(db, id, studentId, current_user)


@router.post("/{id}/join", response_model=ClassroomDto)
async def join_classroom(
    id: str,
    code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join classroom with code."""
    classroom = await classroom_service.join_classroom(db, id, code, current_user)
    
    other_teachers = [t.teacher for t in classroom.teachers]
    
    return ClassroomDto(
        id=classroom.id,
        name=classroom.name,
        level=classroom.level,
        code=classroom.code,
        responsibleProfessor={
            "id": classroom.responsible_professor.id,
            "email": classroom.responsible_professor.email,
            "name": classroom.responsible_professor.name,
            "role": classroom.responsible_professor.role
        },
        otherTeachers=[{
            "id": t.id,
            "email": t.email,
            "name": t.name,
            "role": t.role
        } for t in other_teachers],
        studentCount=len(classroom.students)
    )


@router.post("/{id}/regenerate-code", response_model=RegenerateCodeResponseDto)
async def regenerate_code(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate classroom access code."""
    code = await classroom_service.regenerate_code(db, id, current_user)
    
    return RegenerateCodeResponseDto(
        classroomId=id,
        newCode=code,
        generatedAt=datetime.utcnow()
    )
