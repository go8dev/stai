"""Run the backend: `python -m stai` (add `--reload` in development)."""

from __future__ import annotations

import argparse
import fcntl
import os
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

import uvicorn
from pydantic import ValidationError

from stai.core.config import ConfigurationError, get_settings
from stai.core.logging import configure_logging

GRACEFUL_SHUTDOWN_SECONDS = 10
# A restart may start the new backend while the old one is still finishing its requests.
PORT_CLAIM_WAIT_SECONDS = GRACEFUL_SHUTDOWN_SECONDS + 2.0
_PORT_CLAIM_POLL_SECONDS = 0.25


class PortClaim:
    """This process's claim on a port. It ends when closed or when the process ends."""

    def __init__(self, descriptor: int | None) -> None:
        self._descriptor = descriptor

    def close(self) -> None:
        if self._descriptor is not None:
            os.close(self._descriptor)
            self._descriptor = None


def claim_port(
    port: int,
    *,
    directory: Path | None = None,
    wait_seconds: float = PORT_CLAIM_WAIT_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> PortClaim | None:
    """Make this the only STAI backend for `port` on this machine.

    Returns None when another backend still holds the port after `wait_seconds`.

    With `--reload` the port is opened by a child process. When two copies are started at
    the same moment, the losing copy would otherwise stay alive without a server, serve
    nothing, and take the port over at the next code change, with its log out of sight.
    The claim is a lock on a file in the temporary directory, which the operating system
    releases when the process ends, however it ends. Nothing is written to the file.
    """
    path = (directory or Path(tempfile.gettempdir())) / f"stai-backend-{port}.lock"
    try:
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    except OSError:
        # No usable temporary directory: start without the claim rather than not at all.
        return PortClaim(None)

    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if time.monotonic() >= deadline:
                os.close(descriptor)
                return None
            sleep(_PORT_CLAIM_POLL_SECONDS)
        else:
            return PortClaim(descriptor)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m stai", description="Run the STAI backend.")
    parser.add_argument(
        "--reload", action="store_true", help="Restart on code changes. Development only."
    )
    args = parser.parse_args(argv)

    try:
        settings = get_settings()
    except (ConfigurationError, ValidationError) as exc:
        # ValidationError text names the variable and the rule, never the value.
        detail = (
            "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
            if isinstance(exc, ValidationError)
            else str(exc)
        )
        sys.stderr.write(f"STAI cannot start: {detail}\n")
        return 2

    if settings.port is None:
        sys.stderr.write("STAI cannot start: PORT is not set.\n")
        return 2
    if args.reload and settings.is_production:
        sys.stderr.write("STAI cannot start: --reload needs STAI_ENV=development.\n")
        return 2

    claim = claim_port(settings.port)
    if claim is None:
        sys.stderr.write(
            f"STAI cannot start: another STAI backend is already running on port {settings.port}.\n"
        )
        return 2

    configure_logging(settings.log_level)
    try:
        _serve(settings.port, reload=args.reload)
    finally:
        claim.close()
    return 0


def _serve(port: int, *, reload: bool) -> None:
    uvicorn.run(
        "stai.main:create_app",
        factory=True,
        # Replit's proxy reaches the service on this port from outside the loopback interface.
        host="0.0.0.0",  # noqa: S104
        port=port,
        # Logging is configured by STAI: JSON lines, and its own access log without queries.
        log_config=None,
        access_log=False,
        server_header=False,
        # Forwarded headers are read where needed and checked against the configured hosts.
        proxy_headers=False,
        reload=reload,
        reload_dirs=[str(Path(__file__).resolve().parent)] if reload else None,
        timeout_graceful_shutdown=GRACEFUL_SHUTDOWN_SECONDS,
    )


if __name__ == "__main__":
    raise SystemExit(main())
