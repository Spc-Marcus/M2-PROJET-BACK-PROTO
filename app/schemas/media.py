from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MediaUploadedByDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(..., alias="id")
    name: str = Field(..., alias="name")


class MediaDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(..., alias="id")
    url: str = Field(..., alias="url")
    filename: str = Field(..., alias="filename")
    mime_type: str = Field(..., alias="mimeType")
    uploaded_by: MediaUploadedByDto = Field(..., alias="uploadedBy")
    uploaded_at: datetime = Field(..., alias="uploadedAt")
    is_used: bool = Field(..., alias="isUsed")
