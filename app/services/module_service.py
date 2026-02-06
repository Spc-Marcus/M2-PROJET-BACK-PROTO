"""Module service."""
from typing import List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.module import Module
from app.models.classroom import Classroom
from app.models.user import User
from app.services.classroom_service import is_responsible_professor


MAX_PREREQUISITE_DEPTH = 50


async def get_modules_by_classroom(db: AsyncSession, classroom_id: str, user: User) -> List[Module]:
    """Get all modules for a classroom."""
    result = await db.execute(
        select(Module)
        .where(Module.classroom_id == classroom_id)
        .order_by(Module.created_at)
    )
    return list(result.scalars().all())


async def create_module(
    db: AsyncSession,
    classroom_id: str,
    name: str,
    category: Optional[str],
    prerequisite_module_id: Optional[str],
    user: User
) -> Module:
    """Create a new module (responsible professor only)."""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    if not await is_responsible_professor(db, classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Validate prerequisite exists and check for circular dependency
    if prerequisite_module_id:
        result = await db.execute(select(Module).where(Module.id == prerequisite_module_id))
        prereq = result.scalar_one_or_none()
        
        if not prereq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prerequisite module not found")
        
        if prereq.classroom_id != classroom_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Prerequisite module must be in the same classroom"
            )
    
    module = Module(
        classroom_id=classroom_id,
        name=name,
        category=category,
        prerequisite_module_id=prerequisite_module_id
    )
    
    db.add(module)
    await db.flush()
    
    # Check for circular dependency after adding
    if prerequisite_module_id:
        if await has_circular_module_prerequisite(db, module.id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CIRCULAR_PREREQUISITE"
            )
    
    await db.commit()
    await db.refresh(module)
    
    return module


async def update_module(
    db: AsyncSession,
    module_id: str,
    name: Optional[str],
    category: Optional[str],
    prerequisite_module_id: Optional[str],
    user: User
) -> Module:
    """Update a module (responsible professor only)."""
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    
    if not await is_responsible_professor(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Validate prerequisite
    if prerequisite_module_id:
        if prerequisite_module_id == module_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CIRCULAR_PREREQUISITE"
            )
        
        result = await db.execute(select(Module).where(Module.id == prerequisite_module_id))
        prereq = result.scalar_one_or_none()
        
        if not prereq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prerequisite module not found")
        
        if prereq.classroom_id != module.classroom_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Prerequisite module must be in the same classroom"
            )
    
    if name is not None:
        module.name = name
    if category is not None:
        module.category = category
    if prerequisite_module_id is not None:
        module.prerequisite_module_id = prerequisite_module_id
    
    await db.flush()
    
    # Check for circular dependency
    if prerequisite_module_id and await has_circular_module_prerequisite(db, module.id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CIRCULAR_PREREQUISITE"
        )
    
    await db.commit()
    await db.refresh(module)
    
    return module


async def delete_module(db: AsyncSession, module_id: str, user: User):
    """Delete a module (responsible professor only)."""
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    
    if not await is_responsible_professor(db, module.classroom_id, user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    await db.delete(module)
    await db.commit()


async def has_circular_module_prerequisite(db: AsyncSession, module_id: str, visited: Optional[Set[str]] = None, depth: int = 0) -> bool:
    """Check if a module has a circular prerequisite dependency."""
    if depth > MAX_PREREQUISITE_DEPTH:
        return True
    
    if visited is None:
        visited = set()
    
    if module_id in visited:
        return True
    
    visited.add(module_id)
    
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    
    if not module or not module.prerequisite_module_id:
        return False
    
    return await has_circular_module_prerequisite(db, module.prerequisite_module_id, visited, depth + 1)
