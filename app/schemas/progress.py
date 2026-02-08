from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class QuizProgressDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    quiz_id: str = Field(..., alias="quizId")
    quiz_title: str = Field(..., alias="quizTitle")
    is_completed: bool = Field(False, alias="isCompleted")
    best_score: Optional[int] = Field(None, alias="bestScore")
    attempts_count: int = Field(0, alias="attemptsCount")
    first_attempt_at: Optional[datetime] = Field(None, alias="firstAttemptAt")
    last_attempt_at: Optional[datetime] = Field(None, alias="lastAttemptAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")


class QuizProgressSummaryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    quiz_id: str = Field(..., alias="quizId")
    quiz_title: str = Field(..., alias="quizTitle")
    is_completed: bool = Field(False, alias="isCompleted")
    best_score: Optional[int] = Field(None, alias="bestScore")


class ModuleProgressDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    module_id: str = Field(..., alias="moduleId")
    module_name: str = Field(..., alias="moduleName")
    is_completed: bool = Field(False, alias="isCompleted")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    completed_quizzes_count: int = Field(0, alias="completedQuizzesCount")
    total_quizzes_count: int = Field(0, alias="totalQuizzesCount")
    completion_rate: float = Field(0.0, alias="completionRate")
    quizzes: Optional[list[QuizProgressSummaryDto]] = Field(None, alias="quizzes")


class ClassroomProgressDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    classroom_id: str = Field(..., alias="classroomId")
    classroom_name: str = Field(..., alias="classroomName")
    completed_quizzes: int = Field(0, alias="completedQuizzes")
    total_quizzes: int = Field(0, alias="totalQuizzes")
    average_score: float = Field(0.0, alias="averageScore")
    leitner_mastery: float = Field(0.0, alias="leitnerMastery")


class StudentStatsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    student_id: str = Field(..., alias="studentId")
    total_completed_quizzes: int = Field(0, alias="totalCompletedQuizzes")
    average_score: float = Field(0.0, alias="averageScore")
    leitner_mastery: float = Field(0.0, alias="leitnerMastery")
    classrooms_progress: list[ClassroomProgressDto] = Field(default=[], alias="classroomsProgress")


class HardQuestionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_text: str = Field(..., alias="questionText")
    failure_rate: float = Field(0.0, alias="failureRate")


class ModuleStatsDto(BaseModel):
    """Statistics for a module in the professor dashboard."""
    model_config = ConfigDict(populate_by_name=True)

    module_name: str = Field(..., alias="moduleName")
    average_score: float = Field(0.0, alias="averageScore")
    completion_rate: float = Field(0.0, alias="completionRate")
    alert_students: list[str] = Field(default=[], alias="alertStudents")
    hardest_questions: list[HardQuestionDto] = Field(default=[], alias="hardestQuestions")


class LeitnerStatsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_active_students: int = Field(0, alias="totalActiveStudents")
    average_mastery: float = Field(0.0, alias="averageMastery")
    students_in_box5: int = Field(0, alias="studentsInBox5")


class ProfessorDashboardDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    classroom_id: str = Field(..., alias="classroomId")
    modules_stats: list[ModuleStatsDto] = Field(default=[], alias="modulesStats")
    leitner_stats: LeitnerStatsDto = Field(default_factory=LeitnerStatsDto, alias="leitnerStats")


class LeaderboardEntryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rank: int = Field(..., alias="rank")
    student_id: str = Field(..., alias="studentId")
    student_name: str = Field(..., alias="studentName")
    completed_quizzes: int = Field(0, alias="completedQuizzes")
    average_score: float = Field(0.0, alias="averageScore")
    leitner_mastery: float = Field(0.0, alias="leitnerMastery")
