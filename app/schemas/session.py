from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime
from app.models.session import SessionStatus
from app.schemas.question import QuestionForGameplay


class StartSessionRequest(BaseModel):
    quiz_id: str


class GameSessionStart(BaseModel):
    session_id: str
    questions: List[QuestionForGameplay]


class SubmitAnswerRequest(BaseModel):
    question_id: str
    type: str  # QuestionType as string
    
    # One of these depending on type
    selected_option_id: Optional[str] = None
    clicked_coordinates: Optional[dict] = None  # {x, y}
    text_response: Optional[str] = None
    matched_pairs: Optional[List[dict]] = None  # [{left_id, right_id}]


class AnswerResult(BaseModel):
    question_id: str
    is_correct: bool
    message: str = "Réponse enregistrée."


class SessionResult(BaseModel):
    session_id: str
    quiz_id: str
    total_score: int
    max_score: int
    passed: bool
    completed_at: datetime


class SessionReviewAnswer(BaseModel):
    question_id: str
    question_text: str
    is_correct: bool
    correct_answer: Any
    your_answer: Any
    explanation: Optional[str] = None


class SessionReview(BaseModel):
    session_id: str
    quiz_id: str
    total_score: int
    max_score: int
    passed: bool
    answers: List[SessionReviewAnswer]
