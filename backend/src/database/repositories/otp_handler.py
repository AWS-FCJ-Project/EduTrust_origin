from datetime import datetime, timedelta, timezone
from typing import Optional

from src.database.dynamodb_client import get_dynamodb_client


class OtpRepository:
    """Repository for OTP operations using DynamoDB."""

    def __init__(self, dynamodb_client=None):
        self._client = dynamodb_client or get_dynamodb_client()

    def _table(self) -> str:
        return "otps"

    def _pk(self, email: str, purpose: str) -> dict:
        return {"otp_key": {"S": f"{email}#{purpose}"}}

    async def get_by_id(self, id: str) -> dict:
        raise NotImplementedError("OTP uses composite key")

    async def create(self, doc: dict) -> str:
        raise NotImplementedError("Use save_otp instead")

    async def update(self, id: str, fields: dict) -> bool:
        raise NotImplementedError("OTP uses save_otp for upserts")

    async def delete(self, id: str) -> bool:
        raise NotImplementedError("Use delete_otp instead")

    async def find_one(self, query: dict) -> Optional[dict]:
        return None

    async def find_many(self, query: dict, **kwargs) -> list[dict]:
        return []

    async def insert_one(self, doc: dict) -> any:
        return None

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> any:
        return None

    async def delete_one(self, query: dict) -> any:
        return None

    async def save_otp(
        self, email: str, purpose: str, otp: str, expire_seconds: int = 300
    ) -> None:
        now = datetime.now(timezone.utc)
        expire_at = now + timedelta(seconds=expire_seconds)
        expire_epoch = int(expire_at.timestamp())

        item = {
            "otp_key": f"{email}#{purpose}",
            "email": email,
            "purpose": purpose,
            "otp": otp,
            "created_at": now.isoformat(),
            "expire_at": expire_at.isoformat(),
            "expire_at_epoch": str(expire_epoch),
        }
        await self._client.put_item(self._table(), item)

    async def get_otp(self, email: str, purpose: str, otp: str) -> Optional[dict]:
        item = await self._client.get_item(self._table(), self._pk(email, purpose))
        if item and item.get("otp") == otp:
            # Parse expire_at from ISO string to datetime for caller convenience
            expire_at_str = item.get("expire_at")
            if expire_at_str:
                from datetime import datetime, timezone

                expire_at = datetime.fromisoformat(expire_at_str)
                if expire_at.tzinfo is None:
                    expire_at = expire_at.replace(tzinfo=timezone.utc)
                item = {**item, "expire_at": expire_at}
            return item
        return None

    async def delete_otp(self, email: str, purpose: str) -> None:
        await self._client.delete_item(self._table(), self._pk(email, purpose))

    async def delete_expired_otps(self) -> None:
        # TTL handles this automatically in DynamoDB
        pass
