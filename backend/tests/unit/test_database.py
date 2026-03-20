import importlib
from unittest.mock import MagicMock, patch


def test_database_module():
    with patch("motor.motor_asyncio.AsyncIOMotorClient") as mock_motor:
        mock_motor.return_value = MagicMock()
        import src.database

        importlib.reload(src.database)

        assert src.database.client is not None
        assert src.database.db is not None
        assert src.database.users_collection is not None
        assert mock_motor.call_count >= 1
