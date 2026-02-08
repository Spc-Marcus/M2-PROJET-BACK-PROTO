"""Module routes."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.module import ModuleDto, CreateModuleDto, UpdateModuleDto
from app.services import module_service

router = APIRouter()


@router.get("/classrooms/{cid}/modules", response_model=List[ModuleDto])
async def get_modules(
    cid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all modules for a classroom."""
    modules = await module_service.get_modules_by_classroom(db, cid, current_user)
    return [ModuleDto.model_validate(m) for m in modules]


@router.post("/classrooms/{cid}/modules", response_model=ModuleDto, status_code=status.HTTP_201_CREATED)
async def create_module(
    cid: str,
    data: CreateModuleDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new module."""
    module = await module_service.create_module(
        db, cid, data.name, data.category, data.prerequisite_module_id, current_user
    )
    return ModuleDto.model_validate(module)


@router.get("/modules/{id}", response_model=ModuleDto)
async def get_module(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get module by ID."""
    module = await module_service.get_module_by_id(db, id, current_user)
    return ModuleDto.model_validate(module)


@router.patch("/modules/{id}", response_model=ModuleDto)
async def update_module(
    id: str,
    data: UpdateModuleDto,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a module."""
    module = await module_service.update_module(
        db, id, data.name, data.category, data.prerequisite_module_id, current_user
    )
    return ModuleDto.model_validate(module)


@router.delete("/modules/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a module."""
    await module_service.delete_module(db, id, current_user)
