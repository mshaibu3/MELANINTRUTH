from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  tenant_id TEXT,
  user_id TEXT,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_records_kind ON records(kind);
CREATE INDEX IF NOT EXISTS ix_records_tenant_user ON records(tenant_id, user_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON records(json_extract(payload, '$.email')) WHERE kind = 'user';
"""


def connect_sqlite(path: str = ":memory:") -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
