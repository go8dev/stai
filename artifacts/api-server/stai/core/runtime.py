"""The objects one running application shares between requests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

import httpx
from fastapi import Request

from stai.auth.oidc import OidcClient
from stai.core.config import Settings
from stai.core.ratelimit import RateLimiter
from stai.core.time import utcnow
from stai.db.session import Database
from stai.marketdata.okx_public import OkxPublicProbe


@dataclass(slots=True)
class Runtime:
    settings: Settings
    database: Database
    http: httpx.AsyncClient
    owns_http: bool
    oidc: OidcClient | None
    market_data_probe: OkxPublicProbe
    rate_limiter: RateLimiter = field(default_factory=RateLimiter)
    clock: Callable[[], datetime] = utcnow
    started_at: datetime = field(default_factory=utcnow)

    def now(self) -> datetime:
        return self.clock()


def get_runtime(request: Request) -> Runtime:
    """FastAPI dependency: the runtime of the application handling this request."""
    return request.app.state.runtime
