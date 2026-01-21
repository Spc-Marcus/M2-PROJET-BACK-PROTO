from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime
from app.schemas.question import QuestionForGameplay


class LeitnerBoxInfo(BaseModel):
    level: int
    question_count: int
    percentage: float
    selection_weight: int


class LeitnerBoxesStatus(BaseModel):
    classroom_id: str
    classroom_name: str
    total_questions: int
    boxes: List[LeitnerBoxInfo]
    last_reviewed_at: Optional[datetime] = None


class LeitnerSessionStartRequest(BaseModel):
    question_count: int  # Must be 5, 10, 15, or 20


class LeitnerQuestionForSession(BaseModel):
    id: str
    type: str
    content_text: str
    media_url: Optional[str] = None
    current_box: int
    options: Optional[List[dict]] = None
    matching_items_left: Optional[List[dict]] = None
    matching_items_right: Optional[List[dict]] = None


class LeitnerSessionStartResponse(BaseModel):
    session_id: str
    classroom_id: str
    questions: List[LeitnerQuestionForSession]
    selection_distribution: dict  # {box1: 5, box2: 3, ...}


class BoxMovements(BaseModel):
    promoted: int
    demoted: int


class LeitnerSessionResult(BaseModel):
    session_id: str
    classroom_id: str
    total_questions: int
    correct_answers: int
    wrong_answers: int
    accuracy_rate: float
    box_movements: BoxMovements
    new_box_distribution: dict


class LeitnerReviewAnswer(BaseModel):
    question_id: str
    question_text: str
    is_correct: bool
    previous_box: int
    new_box: int
    correct_answer: Any
    explanation: Optional[str] = None


class LeitnerSessionReview(BaseModel):
    session_id: str
    classroom_id: str
    answers: List[LeitnerReviewAnswer]
    summary: dict


class QuizProgress(BaseModel):
    quiz_id: str
    quiz_title: str
    is_completed: bool
    best_score: Optional[int] = None
    attempts_count: int = 0
    first_attempt_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ModuleProgress(BaseModel):
    module_id: str
    module_name: str
    is_completed: bool
    completed_at: Optional[datetime] = None
    completed_quizzes_count: int = 0
    total_quizzes_count: int = 0
    completion_rate: float = 0.0
    quizzes: Optional[List[QuizProgress]] = None


class ClassroomProgress(BaseModel):
    classroom_id: str
    classroom_name: str
    completed_quizzes: int
    total_quizzes: int
    average_score: float
    leitner_mastery: float


class StudentStats(BaseModel):
    student_id: str
    total_completed_quizzes: int
    average_score: float
    leitner_mastery: float
    classrooms_progress: List[ClassroomProgress]


class LeaderboardEntry(BaseModel):
    rank: int
    student_id: str
    student_name: str
    completed_quizzes: int
    average_score: float
    leitner_mastery: float


class HardQuestion(BaseModel):
    question_text: str
    failure_rate: float


class ModuleStats(BaseModel):
    module_name: str
    average_score: float
    completion_rate: float
    alert_students: List[str]
    hardest_questions: List[HardQuestion]


class LeitnerGlobalStats(BaseModel):
    total_active_students: int
    average_mastery: float
    students_in_box5: int


class ProfessorDashboard(BaseModel):
    classroom_id: str
    modules_stats: List[ModuleStats]
    leitner_stats: LeitnerGlobalStats
