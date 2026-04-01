import logging
from typing import Optional

import pymongo
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from src.app_config import app_config

logger = logging.getLogger(__name__)


class MongoClient:
    """MongoDB connection management."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_name: Optional[str] = None,
    ):

        self._connection_string = connection_string or app_config.MONGO_URI
        self._username = username or app_config.MONGO_USERNAME
        self._password = password or app_config.MONGO_PASSWORD
        self._db_name = db_name or app_config.MONGO_DB_NAME
        self._client: Optional[pymongo.MongoClient] = None
        self._db: Optional[Database] = None

    def connect_to_database(self) -> None:
        """Establish MongoDB connection and verify with ping."""
        try:
            if self._connection_string.startswith("mongodb://"):
                self._client = pymongo.MongoClient(
                    self._connection_string + "/?directConnection=true",
                    username=self._username,
                    password=self._password,
                    retryWrites=False,
                    tlsAllowInvalidHostnames=True,
                )
            else:
                self._client = pymongo.MongoClient(
                    self._connection_string,
                    retryWrites=True,
                    w="majority",
                )
            ping_result = self._client.admin.command("ping")
            logger.info(f"MongoDB ping result: {ping_result}")
            self._db = self._client[self._db_name]
            logger.info(f"Connected to database: {self._db_name}")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise

    def get_collection(self, name: str) -> pymongo.collection.Collection:
        """Get a collection from the database."""
        if self._db is None:
            raise RuntimeError(
                "Database not connected. Call connect_to_database() first."
            )
        return self._db[name]

    def get_database(self) -> Database:
        """Get the database instance."""
        if self._db is None:
            raise RuntimeError(
                "Database not connected. Call connect_to_database() first."
            )
        return self._db

    def close(self) -> None:
        """Close MongoDB connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")

    def ping(self) -> dict:
        """Ping the database to verify connection."""
        if self._client is None:
            raise RuntimeError("Client not connected")
        return self._client.admin.command("ping")
