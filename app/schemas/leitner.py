from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from .session import GameSessionQuestionDto


class LeitnerBoxDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    level: int = Field(..., alias="level")
    question_count: int = Field(0, alias="questionCount")
    percentage: float = Field(0.0, alias="percentage")
    selection_weight: int = Field(0, alias="selectionWeight")


class LeitnerBoxesStatusDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    classroom_id: str = Field(..., alias="classroomId")
    classroom_name: str = Field(..., alias="classroomName")
    total_questions: int = Field(0, alias="totalQuestions")
    boxes: list[LeitnerBoxDto] = Field(default=[], alias="boxes")
    last_reviewed_at: Optional[datetime] = Field(None, alias="lastReviewedAt")


class LeitnerSessionStartRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_count: int = Field(..., alias="questionCount")


class BoxDistributionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    box1: int = Field(0, alias="box1")
    box2: int = Field(0, alias="box2")
    box3: int = Field(0, alias="box3")
    box4: int = Field(0, alias="box4")
    box5: int = Field(0, alias="box5")


class LeitnerSessionQuestionDto(GameSessionQuestionDto):
    current_box: int = Field(..., alias="currentBox")


class LeitnerSessionStartResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId")
    classroom_id: str = Field(..., alias="classroomId")
    questions: list[LeitnerSessionQuestionDto] = Field(default=[], alias="questions")
    selection_distribution: BoxDistributionDto = Field(default_factory=BoxDistributionDto, alias="selectionDistribution")


class BoxMovementsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    promoted: int = Field(0, alias="promoted")
    demoted: int = Field(0, alias="demoted")


class LeitnerSessionResultDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId")
    classroom_id: str = Field(..., alias="classroomId")
    total_questions: int = Field(0, alias="totalQuestions")
    correct_answers: int = Field(0, alias="correctAnswers")
    wrong_answers: int = Field(0, alias="wrongAnswers")
    accuracy_rate: float = Field(0.0, alias="accuracyRate")
    box_movements: BoxMovementsDto = Field(default_factory=BoxMovementsDto, alias="boxMovements")
    new_box_distribution: BoxDistributionDto = Field(default_factory=BoxDistributionDto, alias="newBoxDistribution")


class LeitnerSessionReviewAnswerDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_id: str = Field(..., alias="questionId")
    question_text: str = Field("", alias="questionText")
    is_correct: bool = Field(..., alias="isCorrect")
    previous_box: int = Field(..., alias="previousBox")
    new_box: int = Field(..., alias="newBox")
    correct_answer: Any = Field(None, alias="correctAnswer")
    explanation: str = Field("", alias="explanation")


class LeitnerSessionReviewSummaryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_questions: int = Field(0, alias="totalQuestions")
    correct_answers: int = Field(0, alias="correctAnswers")
    accuracy_rate: float = Field(0.0, alias="accuracyRate")


class LeitnerSessionReviewDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId")
    classroom_id: str = Field(..., alias="classroomId")
    answers: list[LeitnerSessionReviewAnswerDto] = Field(default=[], alias="answers")
    summary: LeitnerSessionReviewSummaryDto = Field(default_factory=LeitnerSessionReviewSummaryDto, alias="summary")


class CompletedModuleDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    student_id: str = Field(..., alias="studentId")
    module_id: str = Field(..., alias="moduleId")
    completed_at: datetime = Field(..., alias="completedAt")


class CompletedQuizDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    student_id: str = Field(..., alias="studentId")
    quiz_id: str = Field(..., alias="quizId")
    completed_at: datetime = Field(..., alias="completedAt")
