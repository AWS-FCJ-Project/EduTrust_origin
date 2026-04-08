import importlib
from unittest.mock import MagicMock, patch


def test_database_module():
    mock_table = MagicMock()
    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table

    with patch("boto3.resource") as mock_boto3:
        mock_boto3.return_value = mock_resource

        import src.database

        importlib.reload(src.database)

        assert src.database.db is not None
        assert src.database.users_collection is not None
        assert src.database.exams_collection is not None

        # Resource is created lazily when collections are instantiated.
        mock_boto3.assert_called()
