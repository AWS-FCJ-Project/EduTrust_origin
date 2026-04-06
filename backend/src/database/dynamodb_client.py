import asyncio
from datetime import datetime
from decimal import Decimal

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.config import Config
from src.app_config import app_config


class DynamoDBClient:
    """Async-friendly DynamoDB client backed by boto3."""

    def __init__(self):
        self._client = None
        self._serializer = TypeSerializer()
        self._deserializer = TypeDeserializer()
        self._config = Config(
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=5,
            read_timeout=10,
        )

    @property
    def client(self):
        if self._client is None:
            kwargs = self.client_kwargs()
            self._client = boto3.client("dynamodb", config=self._config, **kwargs)
        return self._client

    def table_name(self, table: str) -> str:
        prefix = app_config.DYNAMODB_TABLE_PREFIX or "edutrust-backend"
        return f"{prefix}-{table}"

    def client_kwargs(self) -> dict:
        kwargs: dict = {"region_name": app_config.DYNAMODB_REGION or "ap-southeast-1"}
        if app_config.DYNAMODB_ENDPOINT:
            kwargs["endpoint_url"] = app_config.DYNAMODB_ENDPOINT
        if app_config.AWS_ACCESS_KEY_ID and app_config.AWS_SECRET_ACCESS_KEY:
            kwargs["aws_access_key_id"] = app_config.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = app_config.AWS_SECRET_ACCESS_KEY
        return kwargs

    async def get_item(
        self, table: str, key: dict, projection: str | None = None
    ) -> dict | None:
        params: dict = {"TableName": self.table_name(table), "Key": key}
        if projection:
            params["ProjectionExpression"] = projection
        result = await asyncio.to_thread(self.client.get_item, **params)
        item = result.get("Item")
        if item:
            return self._deserialize(item)
        return None

    async def put_item(
        self, table: str, item: dict, condition: str | None = None
    ) -> dict:
        params: dict = {
            "TableName": self.table_name(table),
            "Item": self._serialize(item),
        }
        if condition:
            params["ConditionExpression"] = condition
        return await asyncio.to_thread(self.client.put_item, **params)

    async def update_item(
        self,
        table: str,
        key: dict,
        updates: dict,
        condition: str | None = None,
        extra: dict | None = None,
    ) -> dict:
        params: dict = {"TableName": self.table_name(table), "Key": key}
        update_expr, expr_names, expr_values = self._build_update_expression(updates)
        params["UpdateExpression"] = update_expr
        params["ExpressionAttributeNames"] = expr_names
        params["ExpressionAttributeValues"] = expr_values
        if condition:
            params["ConditionExpression"] = condition
        if extra:
            params.update(extra)
        return await asyncio.to_thread(self.client.update_item, **params)

    async def delete_item(self, table: str, key: dict) -> dict:
        return await asyncio.to_thread(
            self.client.delete_item,
            TableName=self.table_name(table),
            Key=key,
        )

    async def query(
        self,
        table: str,
        index_name: str | None = None,
        key_condition: str | None = None,
        filter_expression: str | None = None,
        expression_values: dict | None = None,
        expression_names: dict | None = None,
        projection: str | None = None,
        limit: int | None = None,
        scan_index_forward: bool = False,
    ) -> list[dict]:
        params: dict = {"TableName": self.table_name(table)}
        if index_name:
            params["IndexName"] = index_name
        if key_condition:
            params["KeyConditionExpression"] = key_condition
        if filter_expression:
            params["FilterExpression"] = filter_expression
        if expression_values:
            params["ExpressionAttributeValues"] = expression_values
        if expression_names:
            params["ExpressionAttributeNames"] = expression_names
        if projection:
            params["ProjectionExpression"] = projection
        if limit:
            params["Limit"] = limit
        params["ScanIndexForward"] = scan_index_forward

        items = []
        paginator = self.client.get_paginator("query")

        def _collect_pages() -> list[dict]:
            collected = []
            for page in paginator.paginate(**params):
                collected.extend(page.get("Items", []))
            return collected

        raw_items = await asyncio.to_thread(_collect_pages)
        for item in raw_items:
            items.append(self._deserialize(item))
        return items

    async def scan(
        self,
        table: str,
        filter_expression: str | None = None,
        expression_values: dict | None = None,
        expression_names: dict | None = None,
        projection: str | None = None,
    ) -> list[dict]:
        params: dict = {"TableName": self.table_name(table)}
        if filter_expression:
            params["FilterExpression"] = filter_expression
        if expression_values:
            params["ExpressionAttributeValues"] = expression_values
        if expression_names:
            params["ExpressionAttributeNames"] = expression_names
        if projection:
            params["ProjectionExpression"] = projection

        paginator = self.client.get_paginator("scan")

        def _collect_pages() -> list[dict]:
            collected = []
            for page in paginator.paginate(**params):
                collected.extend(page.get("Items", []))
            return collected

        raw_items = await asyncio.to_thread(_collect_pages)
        return [self._deserialize(item) for item in raw_items]

    async def batch_write(self, table: str, items: list[dict]) -> list[dict]:
        resource = boto3.resource("dynamodb", **self.client_kwargs())
        table_resource = resource.Table(self.table_name(table))

        def _write_batch() -> None:
            with table_resource.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=item)

        await asyncio.to_thread(_write_batch)
        return []

    def _serialize(self, item: dict) -> dict:
        result = {}
        for key, value in item.items():
            if value is None:
                continue
            if isinstance(value, datetime):
                value = value.isoformat()
            result[key] = self._serializer.serialize(value)
        return result

    def _deserialize(self, item: dict) -> dict:
        result = {}
        for key, value in item.items():
            unpacked = self._deserializer.deserialize(value)
            result[key] = self._normalize_number(unpacked)
        return result

    def _normalize_number(self, value):
        if isinstance(value, Decimal):
            if value == value.to_integral_value():
                return int(value)
            return float(value)
        if isinstance(value, list):
            return [self._normalize_number(item) for item in value]
        if isinstance(value, dict):
            return {key: self._normalize_number(item) for key, item in value.items()}
        return value

    def _build_update_expression(self, updates: dict) -> tuple[str, dict, dict]:
        expr_names = {}
        expr_values = {}
        set_parts = []
        for index, (key, value) in enumerate(updates.items()):
            attr_name = f"#attr{index}"
            attr_val = f":val{index}"
            expr_names[attr_name] = key
            expr_values[attr_val] = self._serialize({"v": value})["v"]
            set_parts.append(f"{attr_name} = {attr_val}")
        return "SET " + ", ".join(set_parts), expr_names, expr_values

    def make_pk(self, table: str, id: str) -> dict:
        return {self._pk_name(table): {"S": id}}

    def _pk_name(self, table: str) -> str:
        pk_map = {
            "users": "user_id",
            "classes": "class_id",
            "class_teacher_assignments": "teacher_id",
            "exams": "exam_id",
            "submissions": "exam_id",
            "violations": "exam_id",
            "conversations": "conversation_id",
            "otps": "otp_key",
        }
        return pk_map.get(table, "id")

    def make_sk(self, table: str, value: str) -> dict:
        sk_name = self._sk_name(table)
        if not sk_name:
            return {}
        return {sk_name: {"S": value}}

    def _sk_name(self, table: str) -> str:
        sk_map = {
            "submissions": "student_id",
            "violations": "student_id",
            "class_teacher_assignments": "assignment_key",
        }
        return sk_map.get(table, "")


_dynamodb_client: DynamoDBClient | None = None


def get_dynamodb_client() -> DynamoDBClient:
    global _dynamodb_client
    if _dynamodb_client is None:
        _dynamodb_client = DynamoDBClient()
    return _dynamodb_client
