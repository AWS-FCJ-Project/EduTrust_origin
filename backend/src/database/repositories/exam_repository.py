from src.database.dynamodb_client import get_dynamodb_client


class ExamRepository:
    """Repository for exam operations using DynamoDB."""

    def __init__(self, dynamodb_client=None):
        self._client = dynamodb_client or get_dynamodb_client()

    def _table(self) -> str:
        return "exams"

    def _pk(self, exam_id: str) -> dict:
        return {"exam_id": {"S": exam_id}}

    async def get_by_id(self, exam_id: str) -> dict | None:
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
            "score_total": str(doc.get("score_total", 0.0)),
            "highest_score": str(doc.get("highest_score", 0.0)),
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

    async def find_one(self, query: dict) -> dict | None:
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

    async def update_counters_safe(self, exam_id: str, score: float) -> bool:
        """
        Atomically update exam counters with optimistic locking.
        Retries up to 5 times on conditional check failure.
        Returns True if update succeeded, False otherwise.
        """
        MAX_RETRIES = 5

        for attempt in range(MAX_RETRIES):
            exam = await self.get_by_id(exam_id)
            if not exam:
                return False

            current_submission_count = int(exam.get("submission_count", 0) or 0)
            current_score_total = float(exam.get("score_total", 0) or 0)
            current_highest_score = float(exam.get("highest_score", 0) or 0)

            new_submission_count = current_submission_count + 1
            new_score_total = current_score_total + score
            new_highest_score = max(current_highest_score, score)

            # Build condition expression for optimistic locking.
            # Use fixed-precision strings to ensure "0" and "0.0" don't mismatch.
            fmt = lambda v: f"{float(v):.1f}"
            condition = "submission_count = :old_sc AND score_total = :old_st AND highest_score = :old_hs"
            expr_values = {
                ":old_sc": {"S": str(current_submission_count)},
                ":old_st": {"S": fmt(current_score_total)},
                ":old_hs": {"S": fmt(current_highest_score)},
                ":new_sc": {"S": str(new_submission_count)},
                ":new_st": {"S": fmt(new_score_total)},
                ":new_hs": {"S": fmt(new_highest_score)},
            }

            try:
                await self._client.update_item(
                    self._table(),
                    self._pk(exam_id),
                    {
                        "submission_count": str(new_submission_count),
                        "score_total": str(new_score_total),
                        "highest_score": str(new_highest_score),
                    },
                    condition=condition,
                    extra={"ExpressionAttributeValues": expr_values},
                )
                return True
            except Exception as e:
                # ConditionalCheckFailed - retry
                if "ConditionalCheckFailed" in str(e) and attempt < MAX_RETRIES - 1:
                    continue
                return False

        return False
