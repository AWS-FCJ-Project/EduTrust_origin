from datetime import datetime, timezone
from typing import Optional

from src.database.dynamodb_client import get_dynamodb_client


class UserRepository:
    """Repository for user operations using DynamoDB."""

    def __init__(self, dynamodb_client=None):
        self._client = dynamodb_client or get_dynamodb_client()

    def _table(self) -> str:
        return "users"

    def _pk(self, user_id: str) -> dict:
        return {"user_id": {"S": user_id}}

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        item = await self._client.get_item(self._table(), self._pk(user_id))
        if item:
            item["_id"] = item.get("user_id")
        return item

    async def get_by_email(self, email: str) -> Optional[dict]:
        items = await self._client.query(
            self._table(),
            index_name="email-index",
            key_condition="email = :email",
            expression_values={":email": {"S": email}},
            limit=1,
        )
        if items:
            items[0]["_id"] = items[0].get("user_id")
        return items[0] if items else None

    async def create(self, doc: dict) -> str:
        user_id = doc.get("user_id") or self._generate_id()
        item = {
            "user_id": user_id,
            "_id": user_id,
            "email": doc.get("email", ""),
            "hashed_password": doc.get("hashed_password", ""),
            "is_verified": str(doc.get("is_verified", True)).lower(),
            "name": doc.get("name", ""),
            "role": doc.get("role", "student"),
            "class_name": doc.get("class_name") or "",
            "grade": str(doc.get("grade")) if doc.get("grade") is not None else "",
            "subjects": doc.get("subjects", []),
            "created_at": doc.get("created_at", datetime.now(timezone.utc).isoformat()),
            "last_login": doc.get("last_login") or "",
        }
        # Filter empty strings
        item = {k: v for k, v in item.items() if v != "" and v is not None}
        await self._client.put_item(self._table(), item)
        return user_id

    def _generate_id(self) -> str:
        import uuid

        return str(uuid.uuid4())

    async def update(self, user_id: str, fields: dict) -> bool:
        # Remove None values
        fields = {k: v for k, v in fields.items() if v is not None}
        if not fields:
            return False
        try:
            await self._client.update_item(
                self._table(),
                self._pk(user_id),
                fields,
            )
            return True
        except Exception:
            return False

    async def delete(self, user_id: str) -> bool:
        await self._client.delete_item(self._table(), self._pk(user_id))
        return True

    async def find_one(self, query: dict) -> Optional[dict]:
        # For simple queries, use scan with filter (only for migration phase)
        key = query.get("email")
        if key:
            user = await self.get_by_email(key)
            return user
        return None

    async def find_many(self, query: dict, **kwargs) -> list[dict]:
        # Not used directly in hot paths
        return []

    async def insert_one(self, doc: dict) -> any:
        user_id = await self.create(doc)
        return user_id

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> any:
        # Strip MongoDB-style $set wrapper if present
        if "$set" in update:
            update = update["$set"]
        if "email" in query:
            user = await self.get_by_email(query["email"])
            if user:
                return await self.update(user["user_id"], update)
        return None

    async def delete_one(self, query: dict) -> any:
        if "email" in query:
            user = await self.get_by_email(query["email"])
            if user:
                await self.delete(user["user_id"])

    async def list_by_role(self, role: str) -> list[dict]:
        items = await self._client.query(
            self._table(),
            index_name="role-index",
            key_condition="role = :role",
            expression_values={":role": {"S": role}},
        )
        for item in items:
            item["_id"] = item.get("user_id")
        return items

    async def find_users_by_ids(self, user_ids: list[str]) -> dict[str, dict]:
        result = {}
        for uid in user_ids:
            user = await self.get_by_id(uid)
            if user:
                result[uid] = user
        for item in result.values():
            item["_id"] = item.get("user_id")
        return result

    async def list_students_by_class(self, class_name: str, grade: int) -> list[dict]:
        # Use scan with filter since class_id not directly queryable by name
        all_students = await self._client.scan(
            self._table(),
            filter_expression="role = :role AND class_name = :cn AND grade = :g",
            expression_values={
                ":role": {"S": "student"},
                ":cn": {"S": class_name},
                ":g": {"N": str(grade)},
            },
        )
        for item in all_students:
            item["_id"] = item.get("user_id")
        return all_students

    async def list_students_by_class_id(self, class_id: str) -> list[dict]:
        items = await self._client.query(
            self._table(),
            index_name="class-id-index",
            key_condition="class_id = :cid",
            expression_values={":cid": {"S": class_id}},
        )
        for item in items:
            item["_id"] = item.get("user_id")
        return items

    async def list_available_students(self, class_name: str, grade: int) -> list[dict]:
        all_students = await self._client.scan(
            self._table(),
            filter_expression="role = :role",
            expression_values={":role": {"S": "student"}},
        )
        # Filter out students in the given class
        for item in all_students:
            item["_id"] = item.get("user_id")
        return [
            s
            for s in all_students
            if s.get("class_name") != class_name or str(s.get("grade")) != str(grade)
        ]

    async def count_students_in_class(self, class_name: str, grade: int) -> int:
        students = await self.list_students_by_class(class_name, grade)
        return len(students)

    async def update_many(
        self,
        filter_query: dict,
        update_fields: dict,
    ) -> int:
        """
        Update multiple users matching filter_query.
        For DynamoDB, uses scan + individual updates.
        NOTE: This is expensive — avoid in hot paths.
        """

        # Build filter expression
        filter_parts = []
        expr_values = {}
        expr_names = {}

        role_filter = filter_query.get("role")
        if role_filter:
            fi = len(expr_values)
            expr_values[f":fv{fi}"] = {"S": role_filter}
            filter_parts.append(f"role = :fv{fi}")

        cn = filter_query.get("class_name")
        if cn:
            fi = len(expr_values)
            expr_values[f":fv{fi}"] = {"S": cn}
            filter_parts.append(f"class_name = :fv{fi}")

        g = filter_query.get("grade")
        if g is not None:
            fi = len(expr_values)
            expr_values[f":fv{fi}"] = {"N": str(g)}
            filter_parts.append(f"grade = :fv{fi}")

        if not filter_parts:
            return 0

        filter_expr = " AND ".join(filter_parts)

        # Scan for matching students
        all_students = await self._client.scan(
            self._table(),
            filter_expression=filter_expr,
            expression_values=expr_values,
            expression_names=expr_names,
        )

        # Update each student individually
        count = 0
        for student in all_students:
            uid = student.get("user_id")
            if not uid:
                continue
            update_data = {k: v for k, v in update_fields.items() if v is None}
            if update_data:
                await self.update(uid, update_data)
                count += 1
        return count

    async def update_last_login(self, email: str) -> None:
        user = await self.get_by_email(email)
        if user:
            await self.update(
                user["user_id"],
                {"last_login": datetime.now(timezone.utc).isoformat()},
            )
