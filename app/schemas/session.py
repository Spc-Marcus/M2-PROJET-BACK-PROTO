from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class GameSessionQuestionOptionDto(BaseModel):
    """Option for a game session question. The id field is a string identifier (e.g., 'opt1', 'opt2')."""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="id")  # String identifier like "opt1", "opt2"
    text_choice: str = Field(..., alias="textChoice")


class GameSessionQuestionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="id")
    type: str = Field(..., alias="type")
    content_text: str = Field(..., alias="contentText")
    media_url: Optional[str] = Field(None, alias="mediaUrl")
    options: Optional[list[GameSessionQuestionOptionDto]] = Field(None, alias="options")


class GameSessionStartDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId")
    questions: list[GameSessionQuestionDto] = Field(default=[], alias="questions")


class ClickedCoordinatesDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    x: float = Field(..., alias="x")
    y: float = Field(..., alias="y")


class SubmitMatchedPairDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    left_id: str = Field(..., alias="leftId")
    right_id: str = Field(..., alias="rightId")


class SubmitAnswerDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_id: str = Field(..., alias="questionId")
    type: Optional[Literal["QCM", "VRAI_FAUX", "MATCHING", "IMAGE", "TEXT"]] = Field(None, alias="type")
    selected_option_id: Optional[str] = Field(None, alias="selectedOptionId")
    clicked_coordinates: Optional[ClickedCoordinatesDto] = Field(None, alias="clickedCoordinates")
    text_response: Optional[str] = Field(None, alias="textResponse")
    matched_pairs: Optional[list[SubmitMatchedPairDto]] = Field(None, alias="matchedPairs")


class AnswerResultDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_id: str = Field(..., alias="questionId")
    is_correct: bool = Field(..., alias="isCorrect")
    message: Optional[str] = Field(None, alias="message")


class SessionResultDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId")
    quiz_id: str = Field(..., alias="quizId")
    total_score: int = Field(..., alias="totalScore")
    max_score: int = Field(..., alias="maxScore")
    passed: bool = Field(..., alias="passed")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")


class SessionReviewAnswerDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_id: str = Field(..., alias="questionId")
    is_correct: bool = Field(..., alias="isCorrect")
    answer_data: Any = Field(None, alias="answerData")


class SessionReviewDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId")
    total_score: int = Field(..., alias="totalScore")
    max_score: int = Field(..., alias="maxScore")
    passed: bool = Field(..., alias="passed")
    answers: list[SessionReviewAnswerDto] = Field(default=[], alias="answers")
