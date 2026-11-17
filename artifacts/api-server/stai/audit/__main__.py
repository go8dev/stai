"""Verify the audit trail from a shell: `python -m stai.audit verify`.

Exit status: 0 the chain is intact, 1 a break was found, 2 the check could not run.
"""

from __future__ import annotations

import argparse
import json
import sys

from pydantic import ValidationError

from stai.audit.service import verify_trail
from stai.core.config import ConfigurationError, load_settings
from stai.db.session import Database

EXIT_INTACT = 0
EXIT_BROKEN = 1
EXIT_COULD_NOT_RUN = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m stai.audit")
    parser.add_argument("command", choices=["verify"])
    parser.parse_args(argv)

    try:
        settings = load_settings()
    except (ConfigurationError, ValidationError) as exc:
        sys.stderr.write(f"The audit trail could not be read: {type(exc).__name__}\n")
        return EXIT_COULD_NOT_RUN

    database: Database | None = None
    try:
        database = Database(settings)
        with database.session() as session:
            report = verify_trail(session)
    except Exception as exc:
        # Whatever stopped the check, it must not look like "a break was found" (1), which
        # is what an uncaught error would exit with. Only the error's type is printed.
        sys.stderr.write(f"The audit trail could not be read: {type(exc).__name__}\n")
        return EXIT_COULD_NOT_RUN
    finally:
        if database is not None:
            database.dispose()

    result = report.result
    summary = {
        "ok": result.ok,
        "eventsChecked": result.events_checked,
        "firstSeq": result.first_seq,
        "lastSeq": result.last_seq,
        "headHash": result.head_hash,
        "firstBreak": None
        if result.first_break is None
        else {
            "seq": result.first_break.seq,
            "reason": result.first_break.reason,
            "detail": result.first_break.detail,
        },
        "verifiedAt": report.verified_at.isoformat(),
        "durationMs": report.duration_ms,
    }
    sys.stdout.write(json.dumps(summary, indent=2) + "\n")
    return EXIT_INTACT if result.ok else EXIT_BROKEN


if __name__ == "__main__":
    raise SystemExit(main())
