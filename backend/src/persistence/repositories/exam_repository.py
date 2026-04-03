from typing import Optional

from src.persistence.dynamodb_client import get_dynamodb_client


class ExamRepository:
    """Repository for exam operations using DynamoDB."""

    def __init__(self, dynamodb_client=None):
        self._client = dynamodb_client or get_dynamodb_client()

    def _table(self) -> str:
        return "exams"

    def _pk(self, exam_id: str) -> dict:
        return {"exam_id": {"S": exam_id}}

    async def get_by_id(self, exam_id: str) -> Optional[dict]:
        return await self._client.get_item(self._table(), self._pk(exam_id))

    async def create(self, doc: dict) -> str:
        import uuid

        exam_id = doc.get("exam_id") or str(uuid.uuid4())
        item = {
            "exam_id": exam_id,
            "title": doc.get("title", ""),
            "description": doc.get("description") or "",
            "subject": doc.get("subject", ""),
            "exam_type": doc.get("exam_type", "15-minute quiz"),
            "teacher_id": doc.get("teacher_id", ""),
            "class_id": doc.get("class_id", ""),
            "class_name": doc.get("class_name") or "",
            "grade": str(doc.get("grade", "")),
            "start_time": doc.get("start_time", ""),
            "end_time": doc.get("end_time", ""),
            "duration": str(doc.get("duration", 60)),
            "secret_key": doc.get("secret_key") or "",
            "questions": doc.get("questions", []),
            "submission_count": str(doc.get("submission_count", 0)),
            "score_total": str(doc.get("score_total", 0)),
            "highest_score": str(doc.get("highest_score", 0)),
            "violation_total": str(doc.get("violation_total", 0)),
        }
        item = {k: v for k, v in item.items() if v != "" and v is not None}
        await self._client.put_item(self._table(), item)
        return exam_id

    async def update(self, exam_id: str, fields: dict) -> bool:
        fields = {k: v for k, v in fields.items() if v is not None}
        if not fields:
            return False
        try:
            await self._client.update_item(self._table(), self._pk(exam_id), fields)
            return True
        except Exception:
            return False

    async def delete(self, exam_id: str) -> bool:
        await self._client.delete_item(self._table(), self._pk(exam_id))
        return True

    async def find_one(self, query: dict) -> Optional[dict]:
        return None

    async def find_many(self, query: dict, **kwargs) -> list[dict]:
        return []

    async def insert_one(self, doc: dict) -> any:
        return await self.create(doc)

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> any:
        return None

    async def delete_one(self, query: dict) -> any:
        return None

    async def list_all(self) -> list[dict]:
        return await self._client.scan(self._table())

    async def list_by_teacher(self, teacher_id: str) -> list[dict]:
        return await self._client.query(
            self._table(),
            index_name="teacher-index",
            key_condition="teacher_id = :tid",
            expression_values={":tid": {"S": teacher_id}},
            scan_index_forward=False,
        )

    async def list_by_class(self, class_id: str) -> list[dict]:
        return await self._client.query(
            self._table(),
            index_name="class-index",
            key_condition="class_id = :cid",
            expression_values={":cid": {"S": class_id}},
            scan_index_forward=False,
        )

    async def list_by_teacher_sorted(
        self, teacher_id: str, sort_field: str = "start_time"
    ) -> list[dict]:
        return await self.list_by_teacher(teacher_id)
