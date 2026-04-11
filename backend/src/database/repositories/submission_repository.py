from datetime import datetime, timezone

from src.database.dynamodb_client import get_dynamodb_client


class SubmissionRepository:
    """Repository for submission operations using DynamoDB."""

    def __init__(self, dynamodb_client=None):
        self._client = dynamodb_client or get_dynamodb_client()

    def _table(self) -> str:
        return "submissions"

    def _pk(self, exam_id: str) -> dict:
        return {"exam_id": {"S": exam_id}}

    def _pk_sk(self, exam_id: str, student_id: str) -> dict:
        return {"exam_id": {"S": exam_id}, "student_id": {"S": student_id}}

    async def get_by_id(self, id: str) -> dict | None:
        return None

    async def create(self, doc: dict) -> str:
        import uuid

        submission_id = str(uuid.uuid4())
        item = {
            "exam_id": doc.get("exam_id", ""),
            "student_id": doc.get("student_id", ""),
            "submitted_at": doc.get(
                "submitted_at", datetime.now(timezone.utc).isoformat()
            ),
            "score": str(doc.get("score", 0)),
            "correct_count": str(doc.get("correct_count", 0)),
            "total_questions": str(doc.get("total_questions", 0)),
            "status": doc.get("status", "completed"),
            "violation_count": str(doc.get("violation_count", 0)),
        }
        item = {k: v for k, v in item.items() if v != "" and v is not None}
        await self._client.put_item(self._table(), item)
        return submission_id

    async def update(self, id: str, fields: dict) -> bool:
        return False

    async def delete(self, id: str) -> bool:
        return False

    async def find_one(self, query: dict) -> dict | None:
        exam_id = query.get("exam_id")
        student_id = query.get("student_id")
        if exam_id and student_id:
            return await self.get_by_exam_student(exam_id, student_id)
        return None

    async def find_many(self, query: dict, **kwargs) -> list[dict]:
        return []

    async def insert_one(self, doc: dict) -> any:
        return await self.create(doc)

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> any:
        return None

    async def delete_one(self, query: dict) -> any:
        return None

    async def get_by_exam_student(self, exam_id: str, student_id: str) -> dict | None:
        return await self._client.get_item(
            self._table(), self._pk_sk(exam_id, student_id)
        )

    async def list_by_exam(self, exam_id: str) -> list[dict]:
        return await self._client.query(
            self._table(),
            key_condition="exam_id = :eid",
            expression_values={":eid": {"S": exam_id}},
        )

    async def list_by_student(self, student_id: str) -> list[dict]:
        return await self._client.query(
            self._table(),
            index_name="student-index",
            key_condition="student_id = :sid",
            expression_values={":sid": {"S": student_id}},
        )

    async def delete_by_exam_student(self, exam_id: str, student_id: str) -> bool:
        await self._client.delete_item(self._table(), self._pk_sk(exam_id, student_id))
        return True

    async def aggregate(self, pipeline: list) -> list:
        # Not used in DynamoDB implementation
        return []
