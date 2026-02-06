"""Media service."""
import os
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status, UploadFile

from app.models.media import Media
from app.models.question import Question
from app.models.user import User


async def upload_media(db: AsyncSession, file: UploadFile, user: User) -> Media:
    """Upload a media file."""
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # In production, upload to cloud storage (S3, etc.)
    # For now, we'll just create a placeholder URL
    url = f"/media/{unique_filename}"
    
    # TODO: Save file to storage
    # For now, we just save metadata
    
    media = Media(
        url=url,
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by_id=user.id
    )
    
    db.add(media)
    await db.commit()
    await db.refresh(media)
    
    return media


async def get_media_list(db: AsyncSession, user: User, page: int = 1, limit: int = 50) -> List[Media]:
    """Get list of media uploaded by user."""
    offset = (page - 1) * limit
    
    result = await db.execute(
        select(Media)
        .where(Media.uploaded_by_id == user.id)
        .order_by(Media.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
    )
    
    return list(result.scalars().all())


async def delete_media(db: AsyncSession, media_id: str, user: User):
    """Delete a media file."""
    result = await db.execute(select(Media).where(Media.id == media_id))
    media = result.scalar_one_or_none()
    
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    
    if media.uploaded_by_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="INSUFFICIENT_PERMISSIONS")
    
    # Check if media is used by any question
    result = await db.execute(
        select(Question).where(Question.media_id == media_id).limit(1)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Media is used by questions"
        )
    
    # TODO: Delete physical file from storage
    
    await db.delete(media)
    await db.commit()


async def get_orphaned_media(db: AsyncSession) -> List[Media]:
    """Get media files not used by any question (admin only)."""
    result = await db.execute(
        select(Media)
        .where(
            ~Media.id.in_(
                select(Question.media_id).where(Question.media_id.isnot(None))
            )
        )
        .order_by(Media.uploaded_at.desc())
    )
    
    return list(result.scalars().all())
