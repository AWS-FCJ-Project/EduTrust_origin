from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, AsyncIterator, Awaitable, Callable, Optional
from uuid import uuid4

import anyio
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from src.app_config import app_config
from src.logger import logger

try:
    from bson import ObjectId  # type: ignore
except Exception:  # pragma: no cover
    ObjectId = None  # type: ignore


def _normalize_table_prefix(prefix: str | None) -> str:
    value = (prefix or "").strip()
    if not value:
        return "edutrust-backend-"
    return value if value.endswith("-") else f"{value}-"


_DATETIME_FIELDS = {
    "created_at",
    "updated_at",
    "expire_at",
    "start_time",
    "end_time",
    "submitted_at",
    "violation_time",
}


def _to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _maybe_parse_datetime(key: str, value: Any) -> Any:
    if key not in _DATETIME_FIELDS or not isinstance(value, str):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return value


def _decimal_to_number(value: Decimal) -> int | float:
    if value % 1 == 0:
        return int(value)
    return float(value)


def _serialize(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, datetime):
        return _to_iso(value)

    if ObjectId is not None and isinstance(value, ObjectId):  # type: ignore[arg-type]
        return str(value)

    if isinstance(value, Decimal):
        return value

    if isinstance(value, float):
        # DynamoDB doesn't accept float; convert to Decimal.
        return Decimal(str(value))

    if isinstance(value, (int, str, bool)):
        return value

    if isinstance(value, list):
        return [_serialize(v) for v in value]

    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}

    return str(value)


def _deserialize(item: Any) -> Any:
    if item is None:
        return None
    if isinstance(item, Decimal):
        return _decimal_to_number(item)
    if isinstance(item, list):
        return [_deserialize(v) for v in item]
    if isinstance(item, dict):
        out: dict[str, Any] = {}
        for k, v in item.items():
            out[k] = _maybe_parse_datetime(k, _deserialize(v))
        return out
    return item


def _normalize_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return _to_iso(value)
    if ObjectId is not None and isinstance(value, ObjectId):  # type: ignore[arg-type]
        return str(value)
    if isinstance(value, Decimal):
        return _decimal_to_number(value)
    return value


def _iter_values_for_path(document: Any, parts: list[str]) -> list[Any]:
    if not parts:
        return [document]

    head, *tail = parts
    if isinstance(document, dict):
        if head not in document:
            return []
        return _iter_values_for_path(document[head], tail)

    if isinstance(document, list):
        values: list[Any] = []
        for entry in document:
            values.extend(_iter_values_for_path(entry, parts))
        return values

    return []


def _match_operator(doc_value: Any, operator: str, expected: Any) -> bool:
    doc_value_norm = _normalize_scalar(doc_value)

    if operator == "$in":
        expected_list = [_normalize_scalar(v) for v in (expected or [])]
        if isinstance(doc_value_norm, list):
            return any(_normalize_scalar(v) in expected_list for v in doc_value_norm)
        return doc_value_norm in expected_list

    if operator == "$ne":
        expected_norm = _normalize_scalar(expected)
        if isinstance(doc_value_norm, list):
            return all(_normalize_scalar(v) != expected_norm for v in doc_value_norm)
        return doc_value_norm != expected_norm

    if operator in {"$lt", "$lte", "$gt", "$gte"}:
        expected_norm = _normalize_scalar(expected)
        if doc_value_norm is None:
            return False
        if operator == "$lt":
            return doc_value_norm < expected_norm
        if operator == "$lte":
            return doc_value_norm <= expected_norm
        if operator == "$gt":
            return doc_value_norm > expected_norm
        if operator == "$gte":
            return doc_value_norm >= expected_norm

    return False


def _match_field(document: dict[str, Any], field: str, expected: Any) -> bool:
    parts = field.split(".")
    values = _iter_values_for_path(document, parts)
    if not values:
        return False

    if isinstance(expected, dict) and any(k.startswith("$") for k in expected.keys()):
        for val in values:
            if all(_match_operator(val, op, exp) for op, exp in expected.items()):
                return True
        return False

    expected_norm = _normalize_scalar(expected)
    for val in values:
        val_norm = _normalize_scalar(val)
        if isinstance(val_norm, list):
            if expected_norm in [_normalize_scalar(v) for v in val_norm]:
                return True
        if val_norm == expected_norm:
            return True
    return False


def _match_filter(document: dict[str, Any], query: dict[str, Any] | None) -> bool:
    if not query:
        return True

    # Keys alongside $or/$and are implicitly AND'ed with them (Mongo behavior).
    for key, expected in query.items():
        if key.startswith("$"):
            continue
        if not _match_field(document, key, expected):
            return False

    if "$and" in query:
        and_terms = query.get("$and") or []
        if not all(_match_filter(document, q) for q in and_terms):
            return False

    if "$or" in query:
        or_terms = query.get("$or") or []
        if not any(_match_filter(document, q) for q in or_terms):
            return False

    return True


def _pull_match(item: Any, criteria: Any) -> bool:
    if isinstance(criteria, dict) and any(k.startswith("$") for k in criteria.keys()):
        # Not needed by current codebase; keep conservative.
        return False

    if isinstance(criteria, dict):
        if not isinstance(item, dict):
            return False
        for k, v in criteria.items():
            if item.get(k) != v:
                return False
        return True

    return _normalize_scalar(item) == _normalize_scalar(criteria)


@dataclass(frozen=True)
class InsertOneResult:
    inserted_id: Any


@dataclass(frozen=True)
class InsertManyResult:
    inserted_ids: list[Any]


@dataclass(frozen=True)
class UpdateResult:
    matched_count: int
    modified_count: int
    upserted_id: Any | None = None


@dataclass(frozen=True)
class DeleteResult:
    deleted_count: int


class _AsyncCursor:
    def __init__(self, loader: Callable[[], Awaitable[list[dict[str, Any]]]]):
        self._loader = loader
        self._sort: tuple[str, int] | None = None

    def sort(self, key: str, direction: int = 1) -> "_AsyncCursor":
        self._sort = (key, direction)
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        items = await self._loader()
        if self._sort is not None:
            key, direction = self._sort
            reverse = direction == -1

            def _sort_key(item: dict[str, Any]):
                parts = key.split(".")
                values = _iter_values_for_path(item, parts)
                return _normalize_scalar(values[0]) if values else None

            items.sort(key=_sort_key, reverse=reverse)

        if length is None:
            return items
        return items[: max(int(length), 0)]

    def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        async def _gen():
            items = await self.to_list(None)
            for item in items:
                yield item

        return _gen()


class DynamoMongoCollection:
    def __init__(self, table, *, name: str):
        self._table = table
        self._name = name

    async def _scan_all(self) -> list[dict[str, Any]]:
        def _do_scan():
            items: list[dict[str, Any]] = []
            exclusive_start_key = None
            while True:
                kwargs: dict[str, Any] = {}
                if exclusive_start_key is not None:
                    kwargs["ExclusiveStartKey"] = exclusive_start_key
                resp = self._table.scan(**kwargs)
                items.extend(resp.get("Items", []) or [])
                exclusive_start_key = resp.get("LastEvaluatedKey")
                if not exclusive_start_key:
                    break
            return items

        raw_items = await anyio.to_thread.run_sync(_do_scan)
        return [_deserialize(i) for i in raw_items]

    async def find_one(
        self, query: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        if query and set(query.keys()) == {"_id"}:
            key = _normalize_scalar(query.get("_id"))

            def _do_get():
                return self._table.get_item(Key={"_id": _serialize(key)}).get("Item")

            item = await anyio.to_thread.run_sync(_do_get)
            return _deserialize(item) if item else None

        items = await self._scan_all()
        for item in items:
            if _match_filter(item, query):
                return item
        return None

    def find(self, query: dict[str, Any] | None = None) -> _AsyncCursor:
        async def _load():
            items = await self._scan_all()
            return [i for i in items if _match_filter(i, query)]

        return _AsyncCursor(_load)

    def aggregate(self, pipeline: list[dict[str, Any]] | None = None) -> _AsyncCursor:
        async def _load():
            items = await self._scan_all()
            current: list[dict[str, Any]] = list(items)

            for stage in pipeline or []:
                if "$match" in stage:
                    match_query = stage.get("$match") or {}
                    current = [i for i in current if _match_filter(i, match_query)]
                    continue

                if "$group" in stage:
                    spec = stage.get("$group") or {}
                    group_id = spec.get("_id")
                    group_field: str | None = None
                    if isinstance(group_id, str) and group_id.startswith("$"):
                        group_field = group_id[1:]

                    groups: dict[Any, dict[str, Any]] = {}
                    for item in current:
                        key = item.get(group_field) if group_field else group_id
                        group = groups.setdefault(key, {"_id": key})
                        for out_field, expr in spec.items():
                            if out_field == "_id":
                                continue
                            if not isinstance(expr, dict):
                                continue

                            if "$sum" in expr:
                                source = expr.get("$sum")
                                if isinstance(source, (int, float, Decimal)):
                                    inc = source
                                elif isinstance(source, str) and source.startswith("$"):
                                    inc = item.get(source[1:], 0) or 0
                                else:
                                    inc = 0
                                group[out_field] = (group.get(out_field, 0) or 0) + inc
                                continue

                            if "$max" in expr:
                                source = expr.get("$max")
                                if isinstance(source, str) and source.startswith("$"):
                                    val = item.get(source[1:])
                                else:
                                    val = source
                                if val is None:
                                    continue
                                cur = group.get(out_field)
                                group[out_field] = val if cur is None else max(cur, val)
                                continue

                            if "$avg" in expr:
                                source = expr.get("$avg")
                                if isinstance(source, str) and source.startswith("$"):
                                    val = item.get(source[1:])
                                else:
                                    val = source
                                if val is None:
                                    continue
                                sum_key = f"__avg_{out_field}_sum"
                                cnt_key = f"__avg_{out_field}_count"
                                group[sum_key] = (group.get(sum_key, 0) or 0) + val
                                group[cnt_key] = (group.get(cnt_key, 0) or 0) + 1
                                continue

                    aggregated = list(groups.values())
                    for group in aggregated:
                        for k in list(group.keys()):
                            if k.startswith("__avg_") and k.endswith("_sum"):
                                out_field = k[len("__avg_") : -len("_sum")]
                                cnt_key = f"__avg_{out_field}_count"
                                total = group.get(k, 0) or 0
                                count = group.get(cnt_key, 0) or 0
                                group[out_field] = (total / count) if count else 0
                                group.pop(k, None)
                                group.pop(cnt_key, None)

                    current = aggregated
                    continue

            return current

        return _AsyncCursor(_load)

    async def _find_all(
        self, query: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        items = await self._scan_all()
        return [i for i in items if _match_filter(i, query)]

    async def count_documents(self, query: dict[str, Any] | None = None) -> int:
        return len(await self._find_all(query))

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        doc = dict(document)
        if "_id" not in doc:
            doc["_id"] = str(ObjectId()) if ObjectId is not None else str(uuid4())  # type: ignore[call-arg]

        def _do_put():
            self._table.put_item(Item=_serialize(doc))

        await anyio.to_thread.run_sync(_do_put)
        return InsertOneResult(inserted_id=doc["_id"])

    async def insert_many(
        self, documents: list[dict[str, Any]], ordered: bool = False
    ) -> InsertManyResult:
        del ordered
        inserted_ids: list[Any] = []

        def _do_batch_write():
            with self._table.batch_writer() as batch:
                for doc_in in documents:
                    doc = dict(doc_in)
                    if "_id" not in doc:
                        doc["_id"] = str(ObjectId()) if ObjectId is not None else str(uuid4())  # type: ignore[call-arg]
                    inserted_ids.append(doc["_id"])
                    batch.put_item(Item=_serialize(doc))

        await anyio.to_thread.run_sync(_do_batch_write)
        return InsertManyResult(inserted_ids=inserted_ids)

    async def update_one(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> UpdateResult:
        existing = await self.find_one(query)
        if existing is None and not upsert:
            return UpdateResult(matched_count=0, modified_count=0)

        if existing is None:
            existing = {
                k: _normalize_scalar(v)
                for k, v in (query or {}).items()
                if not k.startswith("$")
            }
            existing["_id"] = str(ObjectId()) if ObjectId is not None else str(uuid4())  # type: ignore[call-arg]
            matched_count = 0
            upserted_id = existing["_id"]
            is_insert = True
        else:
            matched_count = 1
            upserted_id = None
            is_insert = False

        new_doc = dict(existing)

        # Operators used in this codebase.
        set_on_insert = (
            (update.get("$setOnInsert") or {}) if isinstance(update, dict) else {}
        )
        set_ops = (update.get("$set") or {}) if isinstance(update, dict) else {}
        pull_ops = (update.get("$pull") or {}) if isinstance(update, dict) else {}

        if is_insert and isinstance(set_on_insert, dict):
            for k, v in set_on_insert.items():
                new_doc.setdefault(k, v)

        if isinstance(set_ops, dict):
            for k, v in set_ops.items():
                new_doc[k] = v

        if isinstance(pull_ops, dict):
            for field, criteria in pull_ops.items():
                current = new_doc.get(field)
                if not isinstance(current, list):
                    continue
                new_doc[field] = [x for x in current if not _pull_match(x, criteria)]

        def _do_put():
            self._table.put_item(Item=_serialize(new_doc))

        await anyio.to_thread.run_sync(_do_put)
        return UpdateResult(
            matched_count=matched_count, modified_count=1, upserted_id=upserted_id
        )

    async def update_many(
        self, query: dict[str, Any], update: dict[str, Any]
    ) -> UpdateResult:
        items = await self._find_all(query)
        modified = 0
        for item in items:
            await self.update_one({"_id": item["_id"]}, update, upsert=False)
            modified += 1
        return UpdateResult(matched_count=len(items), modified_count=modified)

    async def delete_one(self, query: dict[str, Any]) -> DeleteResult:
        existing = await self.find_one(query)
        if existing is None:
            return DeleteResult(deleted_count=0)

        def _do_delete():
            self._table.delete_item(Key={"_id": _serialize(existing["_id"])})

        await anyio.to_thread.run_sync(_do_delete)
        return DeleteResult(deleted_count=1)

    async def delete_many(self, query: dict[str, Any]) -> DeleteResult:
        items = await self._find_all(query)
        deleted = 0
        for item in items:
            await self.delete_one({"_id": item["_id"]})
            deleted += 1
        return DeleteResult(deleted_count=deleted)


class DynamoDatabase:
    def __init__(self):
        self._resource = None
        self._tables: dict[str, DynamoMongoCollection] = {}

    def _get_resource(self):
        if self._resource is not None:
            return self._resource

        region = (app_config.AWS_REGION or "ap-southeast-1").strip() or "ap-southeast-1"
        client_kwargs: dict[str, Any] = {
            "region_name": region,
            "config": Config(retries={"max_attempts": 10, "mode": "standard"}),
        }
        if app_config.AWS_ACCESS_KEY_ID and app_config.AWS_SECRET_ACCESS_KEY:
            client_kwargs.update(
                {
                    "aws_access_key_id": app_config.AWS_ACCESS_KEY_ID,
                    "aws_secret_access_key": app_config.AWS_SECRET_ACCESS_KEY,
                }
            )
        endpoint_url = (
            getattr(app_config, "DYNAMODB_ENDPOINT_URL", None) or ""
        ).strip() or None
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        self._resource = boto3.resource("dynamodb", **client_kwargs)
        return self._resource

    def __getitem__(self, collection_name: str) -> DynamoMongoCollection:
        name = (collection_name or "").strip()
        if not name:
            raise KeyError("collection_name is required")

        if name in self._tables:
            return self._tables[name]

        prefix = _normalize_table_prefix(app_config.DYNAMODB_TABLE_PREFIX)
        table_name = f"{prefix}{name}"
        table = self._get_resource().Table(table_name)

        collection = DynamoMongoCollection(table, name=name)
        self._tables[name] = collection
        return collection


db = DynamoDatabase()

users_collection = db["users"]
exams_collection = db["exams"]
classes_collection = db["classes"]
violations_collection = db["violations"]
submissions_collection = db["submissions"]
