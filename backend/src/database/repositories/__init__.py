# Repository interfaces
from src.database.repositories.class_repository import ClassRepository
from src.database.repositories.conversation_repository import ConversationRepository
from src.database.repositories.exam_repository import ExamRepository
from src.database.repositories.otp_repository import OtpRepository
from src.database.repositories.submission_repository import SubmissionRepository
from src.database.repositories.user_repository import UserRepository
from src.database.repositories.violation_repository import ViolationRepository

__all__ = [
    "UserRepository",
    "ClassRepository",
    "ExamRepository",
    "SubmissionRepository",
    "ViolationRepository",
    "ConversationRepository",
    "OtpRepository",
]
