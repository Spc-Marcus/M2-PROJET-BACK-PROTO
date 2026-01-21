from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from app.models.question import QuestionType


class QuestionOptionCreate(BaseModel):
    text_choice: str
    is_correct: bool = False
    display_order: int = 0


class QuestionOptionResponse(BaseModel):
    id: str
    text_choice: str
    is_correct: bool = False
    display_order: int = 0

    class Config:
        from_attributes = True


class MatchingPairCreate(BaseModel):
    item_left: str
    item_right: str


class MatchingPairResponse(BaseModel):
    id: str
    item_left: str
    item_right: str

    class Config:
        from_attributes = True


class ImageZoneCreate(BaseModel):
    label_name: str
    x: float
    y: float
    radius: float


class ImageZoneResponse(BaseModel):
    id: str
    label_name: str
    x: float
    y: float
    radius: float

    class Config:
        from_attributes = True


class TextConfigCreate(BaseModel):
    accepted_answer: str
    is_case_sensitive: bool = False
    ignore_spelling_errors: bool = True


class TextConfigResponse(BaseModel):
    id: str
    accepted_answer: str
    is_case_sensitive: bool = False
    ignore_spelling_errors: bool = True

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    type: QuestionType
    content_text: str
    explanation: Optional[str] = None
    media_id: Optional[str] = None
    
    # Type-specific fields
    options: Optional[List[QuestionOptionCreate]] = None
    matching_pairs: Optional[List[MatchingPairCreate]] = None
    image_zones: Optional[List[ImageZoneCreate]] = None
    text_config: Optional[TextConfigCreate] = None


class QuestionResponse(BaseModel):
    id: str
    quiz_id: str
    type: QuestionType
    content_text: str
    explanation: Optional[str] = None
    media_url: Optional[str] = None
    
    options: List[QuestionOptionResponse] = []
    matching_pairs: List[MatchingPairResponse] = []
    image_zones: List[ImageZoneResponse] = []
    text_config: Optional[TextConfigResponse] = None

    class Config:
        from_attributes = True


class QuestionForGameplay(BaseModel):
    """Question without correct answers for gameplay."""
    id: str
    type: QuestionType
    content_text: str
    media_url: Optional[str] = None
    
    # Options without is_correct
    options: Optional[List[dict]] = None
    matching_items_left: Optional[List[dict]] = None
    matching_items_right: Optional[List[dict]] = None
    image_zones_count: Optional[int] = None

    class Config:
        from_attributes = True


class MediaResponse(BaseModel):
    id: str
    url: str
    filename: str
    mime_type: str
    uploaded_at: datetime
    is_used: bool = False

    class Config:
        from_attributes = True
