import os
import sys

# Set default environment variables for testing before app_config is imported
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_jwt_auth_123!")
os.environ.setdefault("MONGO_DB_NAME", "test_db")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("EMAIL_SENDER", "test@example.com")
os.environ.setdefault("EMAIL_PASSWORD", "testpassword")

# Add the backend directory to sys.path so 'src' can be imported
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Now we can safely import app dependencies
import pytest
from src.app_config import app_config


@pytest.fixture(autouse=True)
def ensure_app_config_for_tests():
    """Ensure that app_config always has values regardless of environment overrides."""
    app_config.SECRET_KEY = os.environ["SECRET_KEY"]
    app_config.MONGO_DB_NAME = os.environ["MONGO_DB_NAME"]
    app_config.MONGO_URI = os.environ["MONGO_URI"]
    yield
