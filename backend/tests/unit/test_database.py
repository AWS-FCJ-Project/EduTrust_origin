import importlib
from unittest.mock import MagicMock, patch


def test_database_module():
    """Test that the database module exports the correct classes for DynamoDB."""
    import src.database

    importlib.reload(src.database)

    # Verify DynamoDB facade is exported
    assert hasattr(src.database, "PersistenceFacade")
    assert hasattr(src.database, "UserRepository")
    assert hasattr(src.database, "ClassRepository")
    assert hasattr(src.database, "ExamRepository")
    assert hasattr(src.database, "SubmissionRepository")
    assert hasattr(src.database, "ViolationRepository")
    assert hasattr(src.database, "ConversationRepository")
    assert hasattr(src.database, "OtpRepository")
