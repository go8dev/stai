"""Build facts shown on the system status screen."""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_HEX = re.compile(r"^[0-9a-f]{7,64}$")


def resolve_commit(configured: str | None) -> str | None:
    """Short commit of the running code: the configured value, else the checkout, else None.

    The published machine may have no Git checkout, so None is a normal answer there.
    """
    if configured and configured.strip():
        return configured.strip()[:12]
    try:
        return _read_head(_REPO_ROOT / ".git")
    except OSError:
        return None


def _read_head(git_dir: Path) -> str | None:
    head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if _HEX.match(head):
        return head[:12]
    if not head.startswith("ref: "):
        return None

    ref = head[5:].strip()
    ref_file = git_dir / ref
    if ref_file.is_file():
        value = ref_file.read_text(encoding="utf-8").strip()
        return value[:12] if _HEX.match(value) else None

    packed = git_dir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[1].strip() == ref and _HEX.match(parts[0]):
                return parts[0][:12]
    return None
