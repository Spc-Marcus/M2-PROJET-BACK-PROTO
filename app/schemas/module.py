from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ModuleCreate(BaseModel):
    name: str
    category: Optional[str] = None
    prerequisite_module_id: Optional[str] = None


class ModuleUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    prerequisite_module_id: Optional[str] = None


class ModuleResponse(BaseModel):
    id: str
    classroom_id: str
    name: str
    category: Optional[str] = None
    prerequisite_module_id: Optional[str] = None
    is_locked: bool = False

    class Config:
        from_attributes = True
