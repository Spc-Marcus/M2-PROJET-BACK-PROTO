from .auth import AuthRequestDto, RegisterStudentDto, UserResponseDto, UserSummaryDto
from .base import ErrorResponseDto, PaginatedResponseDto, PaginationDto
from .classroom import (
    AddTeacherToClassroomDto,
    ClassroomDto,
    ClassroomMembersDto,
    EnrollStudentDto,
    RegenerateCodeResponseDto,
)
from .leitner import (
    BoxDistributionDto,
    BoxMovementsDto,
    CompletedModuleDto,
    CompletedQuizDto,
    LeitnerBoxDto,
    LeitnerBoxesStatusDto,
    LeitnerSessionReviewAnswerDto,
    LeitnerSessionReviewDto,
    LeitnerSessionReviewSummaryDto,
    LeitnerSessionResultDto,
    LeitnerSessionStartRequestDto,
    LeitnerSessionStartResponseDto,
)
from .media import MediaDto, MediaUploadedByDto
from .module import ModuleDto
from .progress import (
    ClassroomProgressDto,
    LeaderboardEntryDto,
    LeitnerStatsDto,
    ModuleProgressDto,
    ModuleStatsDto,
    ProfessorDashboardDto,
    QuizProgressDto,
    StudentStatsDto,
)
from .question import (
    ImageZoneDto,
    MatchingPairDto,
    OptionDto,
    QuestionCreateDto,
    TextConfigDto,
)
from .quiz import QuizDto
from .session import (
    AnswerResultDto,
    ClickedCoordinatesDto,
    GameSessionQuestionDto,
    GameSessionStartDto,
    SubmitMatchedPairDto,
    SessionResultDto,
    SubmitAnswerDto,
)

__all__ = [
    # Auth
    "AuthRequestDto",
    "RegisterStudentDto",
    "UserResponseDto",
    "UserSummaryDto",
    # Base
    "ErrorResponseDto",
    "PaginatedResponseDto",
    "PaginationDto",
    # Classroom
    "AddTeacherToClassroomDto",
    "ClassroomDto",
    "ClassroomMembersDto",
    "EnrollStudentDto",
    "RegenerateCodeResponseDto",
    # Leitner
    "BoxDistributionDto",
    "BoxMovementsDto",
    "CompletedModuleDto",
    "CompletedQuizDto",
    "LeitnerBoxDto",
    "LeitnerBoxesStatusDto",
    "LeitnerSessionReviewAnswerDto",
    "LeitnerSessionReviewDto",
    "LeitnerSessionReviewSummaryDto",
    "LeitnerSessionResultDto",
    "LeitnerSessionStartRequestDto",
    "LeitnerSessionStartResponseDto",
    # Media
    "MediaDto",
    "MediaUploadedByDto",
    # Module
    "ModuleDto",
    # Progress
    "ClassroomProgressDto",
    "LeaderboardEntryDto",
    "LeitnerStatsDto",
    "ModuleProgressDto",
    "ModuleStatsDto",
    "ProfessorDashboardDto",
    "QuizProgressDto",
    "StudentStatsDto",
    # Question
    "ImageZoneDto",
    "MatchingPairDto",
    "OptionDto",
    "QuestionCreateDto",
    "TextConfigDto",
    # Quiz
    "QuizDto",
    # Session
    "AnswerResultDto",
    "ClickedCoordinatesDto",
    "GameSessionQuestionDto",
    "GameSessionStartDto",
    "SubmitMatchedPairDto",
    "SessionResultDto",
    "SubmitAnswerDto",
]
