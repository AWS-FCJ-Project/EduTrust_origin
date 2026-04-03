from src.database.dynamodb_client import get_dynamodb_client


class ClassRepository:
    """Repository for class operations using DynamoDB."""

    def __init__(self, dynamodb_client=None):
        self._client = dynamodb_client or get_dynamodb_client()

    def _table(self) -> str:
        return "classes"

    def _pk(self, class_id: str) -> dict:
        return {"class_id": {"S": class_id}}

    async def get_by_id(self, class_id: str) -> dict | None:
        item = await self._client.get_item(self._table(), self._pk(class_id))
        if item:
            item["_id"] = item.get("class_id")
        return item

    async def get_by_name_grade(self, name: str, grade: int) -> dict | None:
        lookup_key = f"{grade}#{name}"
        items = await self._client.query(
            self._table(),
            index_name="class-lookup-index",
            key_condition="lookup_key = :lk",
            expression_values={":lk": {"S": lookup_key}},
            limit=1,
        )
        if items:
            items[0]["_id"] = items[0].get("class_id")
        return items[0] if items else None

    async def create(self, doc: dict) -> str:
        import uuid

        class_id = doc.get("class_id") or str(uuid.uuid4())
        grade = doc.get("grade", 0)
        name = doc.get("name", "")
        item = {
            "class_id": class_id,
            "name": name,
            "grade": str(grade),
            "school_year": doc.get("school_year", ""),
            "homeroom_teacher_id": doc.get("homeroom_teacher_id") or "",
            "subject_teachers": doc.get("subject_teachers", []),
            "status": doc.get("status", "inactive"),
            "student_count": str(doc.get("student_count", 0)),
            "lookup_key": f"{grade}#{name}",
        }
        item = {k: v for k, v in item.items() if v != "" and v is not None}
        await self._client.put_item(self._table(), item)
        return class_id

    async def update(self, class_id: str, fields: dict) -> bool:
        fields = {k: v for k, v in fields.items() if v is not None}
        if not fields:
            return False
        # Recompute lookup_key if name or grade changed
        if "name" in fields or "grade" in fields:
            current = await self.get_by_id(class_id)
            if current:
                name = fields.get("name", current.get("name", ""))
                grade = fields.get("grade", current.get("grade", 0))
                fields["lookup_key"] = f"{grade}#{name}"
        try:
            await self._client.update_item(self._table(), self._pk(class_id), fields)
            return True
        except Exception:
            return False

    async def delete(self, class_id: str) -> bool:
        await self._client.delete_item(self._table(), self._pk(class_id))
        return True

    async def find_one(self, query: dict) -> dict | None:
        if "homeroom_teacher_id" in query:
            items = await self._client.query(
                self._table(),
                index_name="homeroom-teacher-index",
                key_condition="homeroom_teacher_id = :htid",
                expression_values={":htid": {"S": query["homeroom_teacher_id"]}},
            )
            if items:
                items[0]["_id"] = items[0].get("class_id")
            return items[0] if items else None
        return None

    async def find_many(self, query: dict, **kwargs) -> list[dict]:
        return []

    async def insert_one(self, doc: dict) -> any:
        return await self.create(doc)

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> any:
        # Not directly used
        return None

    async def delete_one(self, query: dict) -> any:
        # Not directly used
        return None

    async def list_all(self) -> list[dict]:
        items = await self._client.scan(self._table())
        for item in items:
            item["_id"] = item.get("class_id")
        return items

    async def list_by_teacher(self, teacher_id: str) -> list[dict]:
        items = await self._client.query(
            self._table(),
            index_name="homeroom-teacher-index",
            key_condition="homeroom_teacher_id = :tid",
            expression_values={":tid": {"S": teacher_id}},
        )
        for item in items:
            item["_id"] = item.get("class_id")
        return items

    async def list_by_homeroom_teacher(self, teacher_id: str) -> list[dict]:
        return await self.list_by_teacher(teacher_id)

    async def clear_homeroom_teacher(self, teacher_id: str) -> None:
        classes = await self.list_by_teacher(teacher_id)
        for cls in classes:
            await self.update(
                cls["class_id"], {"homeroom_teacher_id": "", "status": "inactive"}
            )

    async def pull_subject_teacher(self, teacher_id: str) -> None:
        # For each class, remove the subject teacher
        classes = await self.list_all()
        for cls in classes:
            teachers = cls.get("subject_teachers", [])
            if isinstance(teachers, list):
                remaining = [t for t in teachers if t.get("teacher_id") != teacher_id]
                if len(remaining) != len(teachers):
                    await self.update(cls["class_id"], {"subject_teachers": remaining})
