import os
import sys
from pathlib import Path

# Thêm đường dẫn gốc của project vào PYTHONPATH (backend/)
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Mock environment variables needed for module imports during test collection
os.environ["AGENTS_CONFIG_PATH"] = "config/agents.yaml"
os.environ["LLMS_CONFIG_PATH"] = "config/llms.yaml"
os.environ["AGENT_MODEL"] = "gpt-3.5-turbo"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["MONGO_DB_NAME"] = "test_db"
os.environ["LOGFIRE_TOKEN"] = "test-token"
os.environ["TAVILY_API_KEY"] = "tvly-test-key"
os.environ["LITELLM_API_KEY"] = "sk-test-key"
