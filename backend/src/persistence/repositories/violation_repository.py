from datetime import datetime, timezone
from typing import Optional

from src.persistence.dynamodb_client import get_dynamodb_client


class ViolationRepository:
    """Repository for violation operations using DynamoDB."""

    def __init__(self, dynamodb_client=None):
        self._client = dynamodb_client or get_dynamodb_client()

    def _table(self) -> str:
        return "violations"

    def _pk(self, exam_id: str, student_id: str) -> dict:
        return {"exam_id": {"S": exam_id}, "student_id": {"S": student_id}}

    async def get_by_id(self, id: str) -> Optional[dict]:
        return None

    async def create(self, doc: dict) -> str:
        exam_id = doc.get("exam_id", "")
        student_id = doc.get("student_id", "")
        item = {
            "exam_id": exam_id,
            "student_id": student_id,
            "class_id": doc.get("class_id", "unknown"),
            "subject": doc.get("subject", "N/A"),
            "type": doc.get("type", ""),
            "timestamp": doc.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "violation_time": doc.get(
                "violation_time", datetime.now(timezone.utc).isoformat()
            ),
            "evidence_images": doc.get("evidence_images", []),
            "metadata": doc.get("metadata", {}),
            "created_at": doc.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updated_at": doc.get("updated_at", datetime.now(timezone.utc).isoformat()),
        }
        await self._client.put_item(self._table(), item)
        return f"{exam_id}_{student_id}"

    async def update(self, id: str, fields: dict) -> bool:
        return False

    async def delete(self, id: str) -> bool:
        return False

    async def find_one(self, query: dict) -> Optional[dict]:
        exam_id = query.get("exam_id")
        student_id = query.get("student_id")
        if exam_id and student_id:
            return await self._client.get_item(
                self._table(), self._pk(exam_id, student_id)
            )
        return None

    async def find_many(self, query: dict, **kwargs) -> list[dict]:
        return []

    async def insert_one(self, doc: dict) -> any:
        return await self.create(doc)

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> any:
        return None

    async def delete_one(self, query: dict) -> any:
        return None

    async def upsert(self, exam_id: str, student_id: str, payload: dict) -> None:
        item = {
            "exam_id": str(exam_id),
            "student_id": str(student_id),
            "class_id": payload.get("class_id", "unknown"),
            "subject": payload.get("subject", "N/A"),
            "type": payload.get("type", ""),
            "timestamp": payload.get(
                "timestamp", datetime.now(timezone.utc).isoformat()
            ),
            "violation_time": payload.get(
                "violation_time", datetime.now(timezone.utc).isoformat()
            ),
            "evidence_images": payload.get("evidence_images", []),
            "metadata": payload.get("metadata", {}),
            "created_at": payload.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            ),
            "updated_at": payload.get(
                "updated_at", datetime.now(timezone.utc).isoformat()
            ),
        }
        await self._client.put_item(self._table(), item)

    async def list_by_class(self, class_id: str) -> list[dict]:
        return await self._client.query(
            self._table(),
            index_name="class-time-index",
            key_condition="class_id = :cid",
            expression_values={":cid": {"S": class_id}},
            scan_index_forward=False,
        )

    async def list_by_exam(self, exam_id: str) -> list[dict]:
        return await self._client.query(
            self._table(),
            key_condition="exam_id = :eid",
            expression_values={":eid": {"S": exam_id}},
        )

    async def delete_by_exam_student(self, exam_id: str, student_id: str) -> bool:
        await self._client.delete_item(self._table(), self._pk(exam_id, student_id))
        return True

    async def delete_many(self, query: dict) -> any:
        return None
