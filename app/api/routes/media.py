"""Media routes."""
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_admin, get_current_teacher
from app.models.user import User
from app.models.media import Media
from app.services import media_service

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """Upload a media file."""
    media = await media_service.upload_media(db, file, current_user)
    
    return {
        "id": media.id,
        "mediaId": media.id,
        "url": media.url,
        "filename": media.filename,
        "mimeType": media.mime_type,
        "uploadedBy": {"id": current_user.id, "name": current_user.name},
        "uploadedAt": media.uploaded_at.isoformat() if media.uploaded_at else None,
        "isUsed": False
    }


@router.get("")
async def get_media_list(
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of uploaded media."""
    media_list = await media_service.get_media_list(db, current_user, page, limit)
    
    return [
        {
            "id": m.id,
            "mediaId": m.id,
            "url": m.url,
            "filename": m.filename,
            "mimeType": m.mime_type,
            "uploadedBy": {"id": current_user.id, "name": current_user.name},
            "uploadedAt": m.uploaded_at.isoformat() if m.uploaded_at else None,
            "isUsed": False
        }
        for m in media_list
    ]


@router.get("/orphaned")
async def get_orphaned_media(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get orphaned media files (admin only)."""
    media_list = await media_service.get_orphaned_media(db)
    
    return [
        {
            "id": m.id,
            "mediaId": m.id,
            "url": m.url,
            "filename": m.filename,
            "mimeType": m.mime_type,
            "uploadedBy": {"id": m.uploaded_by_id, "name": "Unknown"},
            "uploadedAt": m.uploaded_at.isoformat() if m.uploaded_at else None,
            "isUsed": False
        }
        for m in media_list
    ]


@router.get("/{mediaId}")
async def get_media(
    mediaId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific media file by ID."""
    result = await db.execute(select(Media).where(Media.id == mediaId))
    media = result.scalar_one_or_none()
    
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    
    return {
        "id": media.id,
        "mediaId": media.id,
        "url": media.url,
        "filename": media.filename,
        "mimeType": media.mime_type,
        "uploadedBy": {"id": media.uploaded_by_id, "name": "Unknown"},
        "uploadedAt": media.uploaded_at.isoformat() if media.uploaded_at else None,
        "isUsed": False
    }


@router.delete("/{mediaId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    mediaId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a media file."""
    await media_service.delete_media(db, mediaId, current_user)
