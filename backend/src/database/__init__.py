# Database layer
# Provides abstraction over storage backend (DynamoDB)
from src.database.dynamodb_facade import PersistenceFacade
from src.database.repositories import (
    BaseRepository,
    ClassRepository,
    ConversationRepository,
    ExamRepository,
    OtpRepository,
    SubmissionRepository,
    UserRepository,
    ViolationRepository,
)

__all__ = [
    "PersistenceFacade",
    "BaseRepository",
    "UserRepository",
    "ClassRepository",
    "ExamRepository",
    "SubmissionRepository",
    "ViolationRepository",
    "ConversationRepository",
    "OtpRepository",
]
