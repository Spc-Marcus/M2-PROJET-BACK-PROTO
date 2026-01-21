from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Role
from app.models.classroom import Classroom, ClassroomStudent, ClassroomTeacher
from app.models.module import Module
from app.models.session import CompletedModule
from app.schemas.module import ModuleCreate, ModuleUpdate, ModuleResponse

router = APIRouter(tags=["Modules"])


@router.get("/api/classrooms/{classroom_id}/modules", response_model=List[ModuleResponse])
def list_modules(
    classroom_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all modules in a classroom."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_classroom_access(classroom, current_user, db)
    
    modules = db.query(Module).filter(Module.classroom_id == classroom_id).all()
    
    return [_module_to_response(m, current_user, db) for m in modules]


@router.post("/api/classrooms/{classroom_id}/modules", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
def create_module(
    classroom_id: str,
    request: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new module (responsible professor only)."""
    classroom = _get_classroom_or_404(classroom_id, db)
    _check_responsible_professor(classroom, current_user)
    
    # Check for circular prerequisites
    if request.prerequisite_module_id:
        _check_circular_prerequisite_module(request.prerequisite_module_id, None, db)
    
    module = Module(
        classroom_id=classroom_id,
        name=request.name,
        category=request.category,
        prerequisite_module_id=request.prerequisite_module_id
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    
    return _module_to_response(module, current_user, db)


@router.put("/api/modules/{module_id}", response_model=ModuleResponse)
def update_module(
    module_id: str,
    request: ModuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a module (responsible professor only)."""
    module = _get_module_or_404(module_id, db)
    classroom = db.query(Classroom).filter(Classroom.id == module.classroom_id).first()
    _check_responsible_professor(classroom, current_user)
    
    # Check for circular prerequisites
    if request.prerequisite_module_id:
        _check_circular_prerequisite_module(request.prerequisite_module_id, module_id, db)
    
    if request.name:
        module.name = request.name
    if request.category is not None:
        module.category = request.category
    if request.prerequisite_module_id is not None:
        module.prerequisite_module_id = request.prerequisite_module_id if request.prerequisite_module_id else None
    
    db.commit()
    db.refresh(module)
    
    return _module_to_response(module, current_user, db)


@router.delete("/api/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a module (responsible professor only)."""
    module = _get_module_or_404(module_id, db)
    classroom = db.query(Classroom).filter(Classroom.id == module.classroom_id).first()
    _check_responsible_professor(classroom, current_user)
    
    db.delete(module)
    db.commit()


# Helper functions
def _get_classroom_or_404(classroom_id: str, db: Session) -> Classroom:
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    return classroom


def _get_module_or_404(module_id: str, db: Session) -> Module:
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return module


def _check_responsible_professor(classroom: Classroom, user: User):
    if classroom.responsible_professor_id != user.id and user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Responsible professor only")


def _check_classroom_access(classroom: Classroom, user: User, db: Session):
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
    
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _check_circular_prerequisite_module(prereq_id: str, current_id: str, db: Session, depth: int = 0):
    if depth > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "CIRCULAR_PREREQUISITE", "message": "Maximum prerequisite depth exceeded"}
        )
    
    if prereq_id == current_id and current_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "CIRCULAR_PREREQUISITE", "message": "Circular dependency detected"}
        )
    
    prereq = db.query(Module).filter(Module.id == prereq_id).first()
    if prereq and prereq.prerequisite_module_id:
        _check_circular_prerequisite_module(prereq.prerequisite_module_id, current_id, db, depth + 1)


def _module_to_response(module: Module, user: User, db: Session) -> ModuleResponse:
    # Calculate is_locked for students
    is_locked = False
    if user.role == Role.STUDENT and module.prerequisite_module_id:
        completed = db.query(CompletedModule).filter(
            CompletedModule.student_id == user.id,
            CompletedModule.module_id == module.prerequisite_module_id
        ).first()
        is_locked = completed is None
    
    return ModuleResponse(
        id=module.id,
        classroom_id=module.classroom_id,
        name=module.name,
        category=module.category,
        prerequisite_module_id=module.prerequisite_module_id,
        is_locked=is_locked
    )
