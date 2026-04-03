from typing import Optional

from src.database.repositories.class_handler import ClassRepository
from src.database.repositories.conversation_handler import ConversationRepository
from src.database.repositories.exam_handler import ExamRepository
from src.database.repositories.otp_handler import OtpRepository
from src.database.repositories.submission_handler import SubmissionRepository
from src.database.repositories.user_handler import UserRepository
from src.database.repositories.violation_handler import ViolationRepository


class PersistenceFacade:
    """
    Unified persistence facade holding all domain repositories.
    Phase 03 uses DynamoDB via boto3-backed repositories.
    """

    def __init__(self, dynamodb_client=None):
        self._dynamodb_client = dynamodb_client
        self._users: Optional[UserRepository] = None
        self._classes: Optional[ClassRepository] = None
        self._exams: Optional[ExamRepository] = None
        self._submissions: Optional[SubmissionRepository] = None
        self._violations: Optional[ViolationRepository] = None
        self._conversations: Optional[ConversationRepository] = None
        self._otps: Optional[OtpRepository] = None

    @property
    def users(self) -> UserRepository:
        if self._users is None:
            self._users = UserRepository(self._dynamodb_client)
        return self._users

    @property
    def classes(self) -> ClassRepository:
        if self._classes is None:
            self._classes = ClassRepository(self._dynamodb_client)
        return self._classes

    @property
    def exams(self) -> ExamRepository:
        if self._exams is None:
            self._exams = ExamRepository(self._dynamodb_client)
        return self._exams

    @property
    def submissions(self) -> SubmissionRepository:
        if self._submissions is None:
            self._submissions = SubmissionRepository(self._dynamodb_client)
        return self._submissions

    @property
    def violations(self) -> ViolationRepository:
        if self._violations is None:
            self._violations = ViolationRepository(self._dynamodb_client)
        return self._violations

    @property
    def conversations(self) -> ConversationRepository:
        if self._conversations is None:
            self._conversations = ConversationRepository(self._dynamodb_client)
        return self._conversations

    @property
    def otps(self) -> OtpRepository:
        if self._otps is None:
            self._otps = OtpRepository(self._dynamodb_client)
        return self._otps
