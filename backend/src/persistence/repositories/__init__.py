# Repository interfaces and base
from src.persistence.repositories.base import BaseRepository
from src.persistence.repositories.class_repository import ClassRepository
from src.persistence.repositories.conversation_repository import ConversationRepository
from src.persistence.repositories.exam_repository import ExamRepository
from src.persistence.repositories.otp_repository import OtpRepository
from src.persistence.repositories.submission_repository import SubmissionRepository
from src.persistence.repositories.user_repository import UserRepository
from src.persistence.repositories.violation_repository import ViolationRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ClassRepository",
    "ExamRepository",
    "SubmissionRepository",
    "ViolationRepository",
    "ConversationRepository",
    "OtpRepository",
]
