from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QuizProgressDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    quiz_id: UUID = Field(..., alias="quizId")
    quiz_title: str = Field(..., alias="quizTitle")
    is_completed: bool = Field(..., alias="isCompleted")
    best_score: int = Field(..., alias="bestScore")
    attempts_count: int = Field(..., alias="attemptsCount")
    first_attempt_at: Optional[datetime] = Field(None, alias="firstAttemptAt")
    last_attempt_at: Optional[datetime] = Field(None, alias="lastAttemptAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")


class QuizProgressSummaryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    quiz_id: UUID = Field(..., alias="quizId")
    quiz_title: str = Field(..., alias="quizTitle")
    is_completed: bool = Field(..., alias="isCompleted")
    best_score: int = Field(..., alias="bestScore")


class ModuleProgressDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    module_id: UUID = Field(..., alias="moduleId")
    module_name: str = Field(..., alias="moduleName")
    is_completed: bool = Field(..., alias="isCompleted")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    completed_quizzes_count: int = Field(..., alias="completedQuizzesCount")
    total_quizzes_count: int = Field(..., alias="totalQuizzesCount")
    completion_rate: float = Field(..., alias="completionRate")
    quizzes: Optional[list[QuizProgressSummaryDto]] = Field(None, alias="quizzes")


class ClassroomProgressDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    classroom_id: UUID = Field(..., alias="classroomId")
    classroom_name: str = Field(..., alias="classroomName")
    completed_quizzes: int = Field(..., alias="completedQuizzes")
    total_quizzes: int = Field(..., alias="totalQuizzes")
    average_score: float = Field(..., alias="averageScore")
    leitner_mastery: float = Field(..., alias="leitnerMastery")


class StudentStatsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    student_id: UUID = Field(..., alias="studentId")
    total_completed_quizzes: int = Field(..., alias="totalCompletedQuizzes")
    average_score: float = Field(..., alias="averageScore")
    leitner_mastery: float = Field(..., alias="leitnerMastery")
    classrooms_progress: list[ClassroomProgressDto] = Field(..., alias="classroomsProgress")


class HardQuestionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question_text: str = Field(..., alias="questionText")
    failure_rate: float = Field(..., alias="failureRate")


class ModuleStatsDto(BaseModel):
    """Statistics for a module in the professor dashboard."""
    model_config = ConfigDict(populate_by_name=True)

    module_name: str = Field(..., alias="moduleName")
    average_score: float = Field(..., alias="averageScore")
    completion_rate: float = Field(..., alias="completionRate")
    alert_students: list[str] = Field(..., alias="alertStudents")  # List of student names (e.g., ["Jean Dupont"])
    hardest_questions: list[HardQuestionDto] = Field(..., alias="hardestQuestions")


class LeitnerStatsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_active_students: int = Field(..., alias="totalActiveStudents")
    average_mastery: float = Field(..., alias="averageMastery")
    students_in_box5: int = Field(..., alias="studentsInBox5")


class ProfessorDashboardDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    classroom_id: UUID = Field(..., alias="classroomId")
    modules_stats: list[ModuleStatsDto] = Field(..., alias="modulesStats")
    leitner_stats: LeitnerStatsDto = Field(..., alias="leitnerStats")


class LeaderboardEntryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rank: int = Field(..., alias="rank")
    student_id: UUID = Field(..., alias="studentId")
    student_name: str = Field(..., alias="studentName")
    completed_quizzes: int = Field(..., alias="completedQuizzes")
    average_score: float = Field(..., alias="averageScore")
    leitner_mastery: float = Field(..., alias="leitnerMastery")
