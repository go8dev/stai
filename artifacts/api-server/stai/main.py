"""Application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from fastapi import FastAPI, Request
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse

from stai import __version__
from stai.audit import guards  # noqa: F401  (registers the append-only guards)
from stai.audit.routes import router as audit_router
from stai.auth.gate import AuthGateMiddleware
from stai.auth.oidc import OidcClient
from stai.auth.routes import router as auth_router
from stai.core.build import resolve_commit
from stai.core.config import Settings, get_settings, secret_values_from_environment
from stai.core.errors import error_response, install_error_handlers
from stai.core.logging import StructuredLogger, configure_logging, register_secret_values
from stai.core.middleware import RequestContextMiddleware
from stai.core.runtime import Runtime
from stai.core.time import utcnow
from stai.db.session import Database, DatabaseNotConfigured
from stai.marketdata.okx_public import OkxPublicProbe
from stai.system.routes import router as system_router

logger = StructuredLogger(__name__)

DESCRIPTION = "STAI API contract. Generated from the Python backend; do not edit by hand."
_USER_AGENT = f"stai/{__version__}"


def build_app(
    settings: Settings,
    *,
    http_client: httpx.AsyncClient | None = None,
    clock: Callable[[], datetime] = utcnow,
) -> FastAPI:
    """Build the application from explicit settings. Tests pass their own collaborators."""
    settings.check()

    owns_http = http_client is None
    http = http_client or httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        headers={"User-Agent": _USER_AGENT},
        follow_redirects=False,
    )
    oidc = (
        OidcClient(issuer_url=settings.issuer_url, client_id=settings.repl_id, http=http)
        if settings.repl_id
        else None
    )
    runtime = Runtime(
        settings=settings,
        database=Database(settings),
        http=http,
        owns_http=owns_http,
        oidc=oidc,
        market_data_probe=OkxPublicProbe(http, settings.okx_base_url, clock=clock),
        clock=clock,
        started_at=clock(),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info(
            "STAI backend started",
            environment=settings.environment,
            version=__version__,
            commit=resolve_commit(settings.build_commit),
            tradingMode="paper",
            databaseConfigured=runtime.database.configured,
            signInConfigured=settings.signin_configured,
            allowedHosts=len(settings.allowed_hosts),
        )
        try:
            yield
        finally:
            if runtime.owns_http:
                await runtime.http.aclose()
            runtime.database.dispose()
            logger.info("STAI backend stopped")

    app = FastAPI(
        title="Api",
        version=__version__,
        description=DESCRIPTION,
        # The contract is published as a file in the repository, not served by the app.
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.runtime = runtime

    install_error_handlers(app)

    @app.exception_handler(SQLAlchemyError)
    @app.exception_handler(DatabaseNotConfigured)
    async def _database_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Database error while handling a request")
        return error_response(
            503, "database_unavailable", "The database could not complete the request."
        )

    app.include_router(system_router)
    app.include_router(auth_router)
    app.include_router(audit_router)

    # Added last runs first: request context wraps the gate, the gate wraps every route.
    app.add_middleware(AuthGateMiddleware, runtime=runtime)
    app.add_middleware(RequestContextMiddleware, production=settings.is_production)
    return app


def create_app() -> FastAPI:
    """Entry point for the server: settings from the environment, JSON logs, secrets masked."""
    settings = get_settings()
    configure_logging(settings.log_level)
    register_secret_values(secret_values_from_environment())
    return build_app(settings)
