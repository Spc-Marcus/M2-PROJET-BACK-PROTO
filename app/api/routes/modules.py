"""Module routes."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.module import ModuleDto
from app.services import module_service

router = APIRouter(tags=["modules"])


@router.get("/api/classrooms/{cid}/modules", response_model=List[ModuleDto])
async def get_modules(
    cid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all modules for a classroom."""
    return await module_service.get_modules_by_classroom(db, cid, current_user)


@router.post("/api/classrooms/{cid}/modules", response_model=ModuleDto, status_code=status.HTTP_201_CREATED)
async def create_module(
    cid: str,
    data: ModuleDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new module."""
    return await module_service.create_module(
        db, cid, data.name, data.category, data.prerequisite_module_id, current_user
    )


@router.put("/api/modules/{id}", response_model=ModuleDto)
async def update_module(
    id: str,
    data: ModuleDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a module."""
    return await module_service.update_module(
        db, id, data.name, data.category, data.prerequisite_module_id, current_user
    )


@router.delete("/api/modules/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a module."""
    await module_service.delete_module(db, id, current_user)
