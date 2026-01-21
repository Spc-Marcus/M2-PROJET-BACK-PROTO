"""Media upload and management endpoints."""
import os
import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User, Role
from app.models.question import Media, Question
from app.schemas.question import MediaResponse
from app.schemas.common import PaginatedResponse, create_pagination

router = APIRouter(prefix="/api/media", tags=["Media"])

# Allowed file types
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an image file (teachers only)."""
    if current_user.role not in [Role.TEACHER, Role.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers only"
        )
    
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    
    # In production, save to cloud storage (S3, Azure Blob, etc.)
    # For prototype, we'll save to local uploads directory
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Generate URL (in production, use CDN URL)
    file_url = f"/uploads/{unique_filename}"
    
    # Save to database
    media = Media(
        url=file_url,
        filename=file.filename,
        mime_type=file.content_type,
        uploaded_by_id=current_user.id
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    
    return {
        "mediaId": media.id,
        "url": media.url
    }


@router.get("", response_model=PaginatedResponse)
def list_media(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all media uploaded by current user (teachers only)."""
    if current_user.role not in [Role.TEACHER, Role.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers only"
        )
    
    # Count total
    total = db.query(Media).filter(Media.uploaded_by_id == current_user.id).count()
    
    # Get paginated results
    medias = db.query(Media).filter(
        Media.uploaded_by_id == current_user.id
    ).offset((page - 1) * limit).limit(limit).all()
    
    # Check if each media is used
    result = []
    for m in medias:
        is_used = db.query(Question).filter(Question.media_id == m.id).first() is not None
        result.append(MediaResponse(
            id=m.id,
            url=m.url,
            filename=m.filename,
            mime_type=m.mime_type,
            uploaded_at=m.uploaded_at,
            is_used=is_used
        ))
    
    return PaginatedResponse(
        data=result,
        pagination=create_pagination(page, limit, total)
    )


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a media file (owner only)."""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    # Check ownership (or admin)
    if media.uploaded_by_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this media"
        )
    
    # Check if media is used by any question
    used_by = db.query(Question).filter(Question.media_id == media_id).first()
    if used_by:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete media: it is used by a question"
        )
    
    # Delete physical file
    if media.url.startswith("/uploads/"):
        file_path = media.url[1:]  # Remove leading /
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Delete from database
    db.delete(media)
    db.commit()


@router.get("/orphaned", response_model=List[MediaResponse])
def list_orphaned_media(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all media not used by any question (admin only)."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )
    
    # Get all media IDs used by questions
    used_ids = db.query(Question.media_id).filter(Question.media_id.isnot(None)).distinct().all()
    used_ids = [x[0] for x in used_ids]
    
    # Get orphaned media
    orphaned = db.query(Media).filter(Media.id.notin_(used_ids)).all()
    
    return [
        MediaResponse(
            id=m.id,
            url=m.url,
            filename=m.filename,
            mime_type=m.mime_type,
            uploaded_at=m.uploaded_at,
            is_used=False
        )
        for m in orphaned
    ]
