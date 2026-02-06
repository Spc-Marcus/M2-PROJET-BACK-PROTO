from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .session import GameSessionQuestionDto


class LeitnerBoxDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    level: int = Field(..., alias="level")
    question_count: int = Field(..., alias="questionCount")
    percentage: float = Field(..., alias="percentage")
    selection_weight: int = Field(..., alias="selectionWeight")


class LeitnerBoxesStatusDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    classroom_id: UUID = Field(..., alias="classroomId")
    classroom_name: str = Field(..., alias="classroomName")
    total_questions: int = Field(..., alias="totalQuestions")
    boxes: list[LeitnerBoxDto] = Field(..., alias="boxes")
    last_reviewed_at: Optional[datetime] = Field(None, alias="lastReviewedAt")


class LeitnerSessionStartRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_count: int = Field(..., alias="questionCount")


class BoxDistributionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    box1: int = Field(..., alias="box1")
    box2: int = Field(..., alias="box2")
    box3: int = Field(..., alias="box3")
    box4: int = Field(..., alias="box4")
    box5: int = Field(..., alias="box5")


class LeitnerSessionQuestionDto(GameSessionQuestionDto):
    model_config = ConfigDict(populate_by_name=True)

    current_box: int = Field(..., alias="currentBox")


class LeitnerSessionStartResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: UUID = Field(..., alias="sessionId")
    classroom_id: UUID = Field(..., alias="classroomId")
    questions: list[LeitnerSessionQuestionDto] = Field(..., alias="questions")
    selection_distribution: BoxDistributionDto = Field(..., alias="selectionDistribution")


class BoxMovementsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    promoted: int = Field(..., alias="promoted")
    demoted: int = Field(..., alias="demoted")


class LeitnerSessionResultDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: UUID = Field(..., alias="sessionId")
    classroom_id: UUID = Field(..., alias="classroomId")
    total_questions: int = Field(..., alias="totalQuestions")
    correct_answers: int = Field(..., alias="correctAnswers")
    wrong_answers: int = Field(..., alias="wrongAnswers")
    accuracy_rate: float = Field(..., alias="accuracyRate")
    box_movements: BoxMovementsDto = Field(..., alias="boxMovements")
    new_box_distribution: BoxDistributionDto = Field(..., alias="newBoxDistribution")


class LeitnerSessionReviewAnswerDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_id: UUID = Field(..., alias="questionId")
    question_text: str = Field(..., alias="questionText")
    is_correct: bool = Field(..., alias="isCorrect")
    previous_box: int = Field(..., alias="previousBox")
    new_box: int = Field(..., alias="newBox")
    correct_answer: Any = Field(..., alias="correctAnswer")
    explanation: str = Field(..., alias="explanation")


class LeitnerSessionReviewSummaryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_questions: int = Field(..., alias="totalQuestions")
    correct_answers: int = Field(..., alias="correctAnswers")
    accuracy_rate: float = Field(..., alias="accuracyRate")


class LeitnerSessionReviewDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: UUID = Field(..., alias="sessionId")
    classroom_id: UUID = Field(..., alias="classroomId")
    answers: list[LeitnerSessionReviewAnswerDto] = Field(..., alias="answers")
    summary: LeitnerSessionReviewSummaryDto = Field(..., alias="summary")


class CompletedModuleDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    student_id: UUID = Field(..., alias="studentId")
    module_id: UUID = Field(..., alias="moduleId")
    completed_at: datetime = Field(..., alias="completedAt")


class CompletedQuizDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    student_id: UUID = Field(..., alias="studentId")
    quiz_id: UUID = Field(..., alias="quizId")
    completed_at: datetime = Field(..., alias="completedAt")
