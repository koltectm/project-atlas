"""
app/core/audit.py
=================
Audit logging utilities.

Writes to both:
  1. public.audit_logs (PostgreSQL — persistent, queryable)
  2. structlog (stdout — for Railway log aggregation)

Design: fire-and-forget for non-critical audit events; awaited for
security-critical events (login, role change, data export).
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


async def write_audit_log(
    db: AsyncSession,
    user_id: uuid.UUID | str,
    action: str,
    table_name: str | None = None,
    record_id: uuid.UUID | str | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """
    Append a row to public.audit_logs.

    This function is SECURITY DEFINER on the DB side (the trigger handles
    critical mutations). This helper is for application-level events such as
    LOGIN, LOGOUT, RUN_SIMULATION, EXPORT_DATA, and ROLE_CHANGE.

    Args:
        db:           Active async SQLAlchemy session.
        user_id:      UUID of the acting user.
        action:       Standardised action code (e.g., "LOGIN", "RUN_SIMULATION").
        table_name:   Affected table name, if applicable.
        record_id:    Primary key of the affected record, if applicable.
        old_values:   Snapshot before mutation (UPDATE/DELETE).
        new_values:   Snapshot after mutation (INSERT/UPDATE).
        ip_address:   Client IP from the request.
        user_agent:   Client User-Agent header.

    Note:
        The INSERT uses raw SQL rather than the ORM to avoid the session's
        identity map and unit-of-work overhead. Audit writes must never fail
        silently — exceptions are logged but not propagated so that the
        primary business operation is not rolled back because of an audit error.
    """
    try:
        await db.execute(
            text(
                """
                INSERT INTO public.audit_logs
                    (user_id, action, table_name, record_id,
                     old_values, new_values, ip_address, user_agent, performed_at)
                VALUES
                    (:user_id, :action, :table_name, :record_id,
                     :old_values::jsonb, :new_values::jsonb,
                     :ip_address::inet, :user_agent, NOW())
                """
            ),
            {
                "user_id":    str(user_id),
                "action":     action,
                "table_name": table_name,
                "record_id":  str(record_id) if record_id else None,
                "old_values": _jsonb_or_null(old_values),
                "new_values": _jsonb_or_null(new_values),
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        )
        logger.info(
            "audit.event",
            user_id=str(user_id),
            action=action,
            table=table_name,
            record=str(record_id) if record_id else None,
        )
    except Exception as exc:
        # Audit failure must NEVER block the primary operation.
        logger.error(
            "audit.write_failed",
            user_id=str(user_id),
            action=action,
            error=str(exc),
        )


def _jsonb_or_null(data: dict | None) -> str | None:
    """Convert a dict to a JSON string for PostgreSQL JSONB binding, or None."""
    if data is None:
        return None
    import json
    return json.dumps(data, default=str)
