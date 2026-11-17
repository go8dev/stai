"""Append-only enforcement inside the application.

The published database cannot carry triggers or grants, so the rule lives here: through
the application's engine, `audit_events` accepts INSERT and SELECT and nothing else.

* ORM objects: changing or deleting a loaded AuditEvent is refused at flush.
* ORM bulk statements: update() and delete() against the table are refused.
* Raw SQL: any statement that modifies the table other than INSERT is refused before it
  reaches the database.

This stops mistakes in application code. It is not a barrier against someone who holds
the database credentials; the hash chain is what makes such changes detectable.
Migrations use their own engine and are not affected.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import Engine, event
from sqlalchemy.orm import ORMExecuteState, Session

from stai.db.models import AuditEvent

AUDIT_TABLE = AuditEvent.__tablename__


class AuditImmutableError(RuntimeError):
    """Something tried to change or remove audit records."""


_COMMENTS = re.compile(r"/\*.*?\*/|--[^\n]*", re.DOTALL)
_TABLE = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(AUDIT_TABLE)}(?![A-Za-z0-9_])", re.IGNORECASE)
_FORBIDDEN = re.compile(
    r"(?<![A-Za-z0-9_])(UPDATE|DELETE|TRUNCATE|DROP|ALTER|MERGE|RENAME)(?![A-Za-z0-9_])",
    re.IGNORECASE,
)


def statement_violates_append_only(statement: str) -> bool:
    """True when the SQL text names the audit table together with a modifying keyword.

    `INSERT ... ON CONFLICT ... DO UPDATE` is caught as well, which is intended.
    """
    text = _COMMENTS.sub(" ", statement)
    if not _TABLE.search(text):
        return False
    return _FORBIDDEN.search(text) is not None


def _refuse(action: str) -> None:
    raise AuditImmutableError(f"audit_events is append-only: {action} is not allowed")


@event.listens_for(AuditEvent, "before_update")
def _block_orm_update(mapper: Any, connection: Any, target: Any) -> None:
    _refuse("UPDATE")


@event.listens_for(AuditEvent, "before_delete")
def _block_orm_delete(mapper: Any, connection: Any, target: Any) -> None:
    _refuse("DELETE")


@event.listens_for(Session, "do_orm_execute")
def _block_orm_bulk(state: ORMExecuteState) -> None:
    if not (state.is_update or state.is_delete):
        return
    for mapper in state.all_mappers:
        if mapper.class_ is AuditEvent:
            _refuse("UPDATE" if state.is_update else "DELETE")


def install_engine_guards(engine: Engine) -> None:
    """Refuse modifying SQL against the audit table on this engine."""

    @event.listens_for(engine, "before_cursor_execute")
    def _block_sql(
        conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
    ) -> None:
        if statement_violates_append_only(statement):
            keyword = _FORBIDDEN.search(_COMMENTS.sub(" ", statement))
            _refuse(keyword.group(1).upper() if keyword else "this statement")
