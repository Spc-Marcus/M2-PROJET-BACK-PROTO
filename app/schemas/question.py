from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OptionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text_choice: str = Field(..., alias="textChoice")
    is_correct: Optional[bool] = Field(None, alias="isCorrect")
    display_order: Optional[int] = Field(None, alias="displayOrder")


class MatchingPairDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    item_left: str = Field(..., alias="itemLeft")
    item_right: str = Field(..., alias="itemRight")


class ImageZoneDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label_name: str = Field(..., alias="labelName")
    x: float = Field(..., alias="x")
    y: float = Field(..., alias="y")
    radius: float = Field(..., alias="radius")


class TextConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    accepted_answer: str = Field(..., alias="acceptedAnswer")
    is_case_sensitive: Optional[bool] = Field(False, alias="isCaseSensitive")
    ignore_spelling_errors: Optional[bool] = Field(False, alias="ignoreSpellingErrors")


class QuestionCreateDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["QCM", "VRAI_FAUX", "MATCHING", "IMAGE", "TEXT"] = Field(..., alias="type")
    content_text: str = Field(..., alias="contentText")
    explanation: Optional[str] = Field(None, alias="explanation")
    media_id: Optional[str] = Field(None, alias="mediaId")
    options: Optional[list[OptionDto]] = Field(None, alias="options")
    matching_pairs: Optional[list[MatchingPairDto]] = Field(None, alias="matchingPairs")
    image_zones: Optional[list[ImageZoneDto]] = Field(None, alias="imageZones")
    text_config: Optional[TextConfigDto] = Field(None, alias="textConfig")


class QuestionResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., alias="id")
    type: str = Field(..., alias="type")
    content_text: str = Field(..., alias="contentText")
    explanation: Optional[str] = Field(None, alias="explanation")
    media_id: Optional[str] = Field(None, alias="mediaId")
    options: Optional[list[OptionDto]] = Field(None, alias="options")
    matching_pairs: Optional[list[MatchingPairDto]] = Field(None, alias="matchingPairs")
    image_zones: Optional[list[ImageZoneDto]] = Field(None, alias="imageZones")
    text_config: Optional[TextConfigDto] = Field(None, alias="textConfig")
