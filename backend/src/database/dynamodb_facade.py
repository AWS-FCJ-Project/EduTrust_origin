from src.database.repositories.class_repository import ClassRepository
from src.database.repositories.conversation_repository import ConversationRepository
from src.database.repositories.exam_repository import ExamRepository
from src.database.repositories.otp_repository import OtpRepository
from src.database.repositories.submission_repository import SubmissionRepository
from src.database.repositories.user_repository import UserRepository
from src.database.repositories.violation_repository import ViolationRepository


class PersistenceFacade:
    """
    Unified persistence facade holding all domain repositories.
    Phase 03 uses DynamoDB via boto3-backed repositories.
    """

    def __init__(self, dynamodb_client=None):
        self._dynamodb_client = dynamodb_client
        self._users: UserRepository | None = None
        self._classes: ClassRepository | None = None
        self._exams: ExamRepository | None = None
        self._submissions: SubmissionRepository | None = None
        self._violations: ViolationRepository | None = None
        self._conversations: ConversationRepository | None = None
        self._otps: OtpRepository | None = None

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
