# Repository interfaces and base
from src.database.repositories.base import BaseRepository
from src.database.repositories.class_handler import ClassRepository
from src.database.repositories.conversation_handler import ConversationRepository
from src.database.repositories.exam_handler import ExamRepository
from src.database.repositories.otp_handler import OtpRepository
from src.database.repositories.submission_handler import SubmissionRepository
from src.database.repositories.user_handler import UserRepository
from src.database.repositories.violation_handler import ViolationRepository

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
