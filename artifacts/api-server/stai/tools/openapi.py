"""Write the API contract to lib/api-spec/openapi.yaml, or check that it is current.

python -m stai.tools.openapi           write the file
python -m stai.tools.openapi --check   exit 1 when the file differs from the code
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

import yaml

from stai.core.config import load_settings
from stai.core.openapi import build_openapi
from stai.main import build_app

REPO_ROOT = Path(__file__).resolve().parents[4]
SPEC_PATH = REPO_ROOT / "lib" / "api-spec" / "openapi.yaml"

HEADER = (
    "# Generated from the Python backend by `pnpm run openapi:export`.\n"
    "# Do not edit by hand: change the routes or schemas in artifacts/api-server/stai,\n"
    "# then export again and run `pnpm --filter @workspace/api-spec run codegen`.\n"
)


def render() -> str:
    """The contract as YAML. Needs no database, network or environment variables."""
    app = build_app(load_settings({}))
    document = build_openapi(app)
    body = yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=100)
    return HEADER + body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m stai.tools.openapi")
    parser.add_argument("--check", action="store_true", help="Compare instead of writing.")
    args = parser.parse_args(argv)

    expected = render()
    if not args.check:
        SPEC_PATH.write_text(expected, encoding="utf-8")
        sys.stdout.write(f"Wrote {SPEC_PATH.relative_to(REPO_ROOT)}\n")
        return 0

    current = SPEC_PATH.read_text(encoding="utf-8") if SPEC_PATH.exists() else ""
    if current == expected:
        sys.stdout.write("The API contract is up to date.\n")
        return 0

    diff = difflib.unified_diff(
        current.splitlines(), expected.splitlines(), "stored", "from code", lineterm="", n=2
    )
    sys.stderr.write("\n".join(list(diff)[:80]) + "\n")
    sys.stderr.write(
        "\nlib/api-spec/openapi.yaml is out of date. Run `pnpm run openapi:export`, "
        "then `pnpm --filter @workspace/api-spec run codegen`.\n"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
