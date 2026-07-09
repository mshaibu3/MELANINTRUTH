from __future__ import annotations

import os
import sqlite3
import sys

REQUIRED_TABLES = {
    "users",
    "sessions",
    "devices",
    "tenants",
    "tenant_members",
    "consent_records",
    "image_captures",
    "image_quality_reports",
    "lighting_analyses",
    "skin_analyses",
    "analysis_jobs",
    "authentic_renders",
    "render_safety_reports",
    "audit_logs",
    "security_events",
    "data_export_requests",
    "data_deletion_requests",
    "model_versions",
    "dataset_versions",
    "bias_reports",
    "incidents",
}


def _sqlite_tables(url: str) -> set[str]:
    path = url.replace("sqlite:///", "", 1)
    conn = sqlite3.connect(path or ":memory:")
    rows = conn.execute("select name from sqlite_master where type='table'").fetchall()
    return {row[0] for row in rows}


def _sqlalchemy_tables(url: str) -> set[str]:
    from sqlalchemy import create_engine, inspect

    engine = create_engine(url)
    return set(inspect(engine).get_table_names())


def main() -> None:
    url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    tables = _sqlite_tables(url) if url.startswith("sqlite") else _sqlalchemy_tables(url)
    missing = sorted(REQUIRED_TABLES - tables)
    if missing:
        raise SystemExit(f"Missing migrated tables: {', '.join(missing)}")
    print(f"Verified {len(REQUIRED_TABLES)} required migration tables")


if __name__ == "__main__":
    sys.exit(main())
