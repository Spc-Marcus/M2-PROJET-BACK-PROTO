"""Media routes."""
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from app.schemas.media import MediaDto
from app.services import media_service

router = APIRouter()


@router.post("", response_model=MediaDto, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a media file."""
    media = await media_service.upload_media(db, file, current_user)
    
    return MediaDto(
        id=media.id,
        url=media.url,
        filename=media.filename,
        mimeType=media.mime_type,
        uploadedBy={"id": current_user.id, "name": current_user.name},
        uploadedAt=media.uploaded_at,
        isUsed=False
    )


@router.get("", response_model=List[MediaDto])
async def get_media_list(
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of uploaded media."""
    media_list = await media_service.get_media_list(db, current_user, page, limit)
    
    return [MediaDto(
        id=m.id,
        url=m.url,
        filename=m.filename,
        mimeType=m.mime_type,
        uploadedBy={"id": current_user.id, "name": current_user.name},
        uploadedAt=m.uploaded_at,
        isUsed=False  # Would need to check in questions
    ) for m in media_list]


@router.delete("/{mediaId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    mediaId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a media file."""
    await media_service.delete_media(db, mediaId, current_user)


@router.get("/orphaned", response_model=List[MediaDto])
async def get_orphaned_media(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get orphaned media files (admin only)."""
    media_list = await media_service.get_orphaned_media(db)
    
    return [MediaDto(
        id=m.id,
        url=m.url,
        filename=m.filename,
        mimeType=m.mime_type,
        uploadedBy={"id": m.uploaded_by_id, "name": "Unknown"},
        uploadedAt=m.uploaded_at,
        isUsed=False
    ) for m in media_list]
