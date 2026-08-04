"""SQLite/Postgres lightweight schema upgrades for WAREACH v2."""

from __future__ import annotations

import logging

from sqlalchemy import text

from app.db.session import engine

logger = logging.getLogger(__name__)


def ensure_schema() -> None:
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "sqlite":
            supplier_cols = {
                "groups": "TEXT DEFAULT '[]'",
                "lead_type": "VARCHAR(64) DEFAULT 'unknown'",
                "quality_tier": "VARCHAR(32) DEFAULT 'unknown'",
                "geo_clusters": "TEXT DEFAULT '[]'",
                "signals": "TEXT DEFAULT '[]'",
                "priority_score": "FLOAT DEFAULT 0",
            }
            existing_sup = {r[1] for r in conn.execute(text("PRAGMA table_info(suppliers)")).fetchall()}
            for col, ddl in supplier_cols.items():
                if existing_sup and col not in existing_sup:
                    conn.execute(text(f"ALTER TABLE suppliers ADD COLUMN {col} {ddl}"))
                    logger.info("Added suppliers.%s", col)

            existing_q = {r[1] for r in conn.execute(text("PRAGMA table_info(search_queries)")).fetchall()}
            if existing_q and "category" not in existing_q:
                conn.execute(
                    text("ALTER TABLE search_queries ADD COLUMN category VARCHAR(64) DEFAULT 'general'")
                )
                logger.info("Added search_queries.category")

            existing_c = {r[1] for r in conn.execute(text("PRAGMA table_info(contacts)")).fetchall()}
            contact_cols = {
                "verify_status": "VARCHAR(32) DEFAULT 'unverified'",
                "verify_note": "VARCHAR(255)",
                "verified_at": "DATETIME",
            }
            for col, ddl in contact_cols.items():
                if existing_c and col not in existing_c:
                    conn.execute(text(f"ALTER TABLE contacts ADD COLUMN {col} {ddl}"))
                    logger.info("Added contacts.%s", col)
            return

        # Postgres
        alters = [
            "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS groups JSONB DEFAULT '[]'::jsonb",
            "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS lead_type VARCHAR(64) DEFAULT 'unknown'",
            "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS quality_tier VARCHAR(32) DEFAULT 'unknown'",
            "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS geo_clusters JSONB DEFAULT '[]'::jsonb",
            "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS signals JSONB DEFAULT '[]'::jsonb",
            "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS priority_score FLOAT DEFAULT 0",
            "ALTER TABLE search_queries ADD COLUMN IF NOT EXISTS category VARCHAR(64) DEFAULT 'general'",
            "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS verify_status VARCHAR(32) DEFAULT 'unverified'",
            "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS verify_note VARCHAR(255)",
            "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ",
        ]
        for stmt in alters:
            conn.execute(text(stmt))


def reclaim_stale_url_jobs(max_age_minutes: int = 20) -> int:
    """Reset URLs stuck in crawling/browsing after crash/kill."""
    with engine.begin() as conn:
        # Keep it simple: any stuck in-flight status goes back to pending
        res = conn.execute(
            text(
                """
                UPDATE discovered_urls
                SET status = 'pending',
                    last_error = COALESCE(last_error, '') || ' |reclaimed_stale'
                WHERE status IN ('crawling', 'browsing')
                """
            )
        )
        n = res.rowcount or 0
        if n:
            logger.info("Reclaimed %s stale crawling/browsing URLs", n)
        return n
