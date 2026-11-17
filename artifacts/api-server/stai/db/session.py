"""Engine and session handling.

The engine is created on first use, so the service starts and answers its health check
even when the database is missing or unreachable.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from stai.core.config import Settings


class DatabaseNotConfigured(RuntimeError):
    """DATABASE_URL is not set."""


class Database:
    """Owns the engine of one application instance."""

    def __init__(self, settings: Settings):
        self._url = settings.sqlalchemy_url
        self._engine: Engine | None = None
        self._sessionmaker: sessionmaker[Session] | None = None
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return self._url is not None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    self._engine = self._create_engine()
        return self._engine

    def _create_engine(self) -> Engine:
        if self._url is None:
            raise DatabaseNotConfigured("DATABASE_URL is not set")

        # Imported here so that building the engine always installs the append-only guards.
        from stai.audit.guards import install_engine_guards

        engine = create_engine(
            self._url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            pool_recycle=300,
            pool_timeout=10,
            # Statement parameters never reach an error message or a log line.
            hide_parameters=True,
            connect_args={"connect_timeout": 5, "application_name": "stai-api"},
        )
        install_engine_guards(engine)
        return engine

    @contextmanager
    def session(self) -> Iterator[Session]:
        """A session that commits when the block ends cleanly and rolls back otherwise."""
        if self._sessionmaker is None:
            self._sessionmaker = sessionmaker(bind=self.engine, expire_on_commit=False)
        session = self._sessionmaker()
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        with self._lock:
            if self._engine is not None:
                self._engine.dispose()
                self._engine = None
                self._sessionmaker = None


# Errors that mean the database could not be used: not configured, unreachable, or its
# structure is missing. Callers answer these with "unavailable", never with a stack trace.
DATABASE_ERRORS: tuple[type[Exception], ...] = (DatabaseNotConfigured, SQLAlchemyError)
