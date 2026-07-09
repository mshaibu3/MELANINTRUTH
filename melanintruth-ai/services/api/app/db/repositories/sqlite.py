from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.backend.repository import InMemoryRepository


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return str(value)


class SQLiteRepository(InMemoryRepository):
    """SQL-backed repository facade that preserves Phase 2 in-memory semantics for services."""

    def __init__(self, connection: sqlite3.Connection):
        super().__init__()
        self.connection = connection

    def persist_record(self, kind: str, record: Any, tenant_id: str | None = None, user_id: str | None = None) -> None:
        payload = asdict(record) if hasattr(record, "__dataclass_fields__") else dict(record)
        now = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            "INSERT OR REPLACE INTO records(id, kind, tenant_id, user_id, payload, created_at, updated_at, deleted_at) VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM records WHERE id = ?), ?), ?, ?)",
            (payload["id"], kind, tenant_id, user_id, json.dumps(payload, default=_json_default), payload["id"], now, now, _json_default(payload.get("deleted_at")) if payload.get("deleted_at") else None),
        )
        self.connection.commit()

    def list_records(self, kind: str, tenant_id: str | None = None, user_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT payload FROM records WHERE kind = ?"
        params: list[Any] = [kind]
        if tenant_id is not None:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)
        return [json.loads(row["payload"]) for row in self.connection.execute(query, params)]
