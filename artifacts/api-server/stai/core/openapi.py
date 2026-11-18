"""The API contract, generated from the routes.

The service is mounted under `/api`, and the generated web client adds that prefix itself,
so the document lists paths without it and names `/api` as its server.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

API_PREFIX = "/api"

TAGS = [
    {"name": "health", "description": "Health check."},
    {"name": "Auth", "description": "Owner sign-in, sign-out and session state."},
    {"name": "system", "description": "Live system checks."},
    {"name": "audit", "description": "Append-only audit trail."},
    {"name": "market-data", "description": "Public OKX market observations."},
    {"name": "portfolio", "description": "Virtual fund and paper ledger."},
    {"name": "committee", "description": "Read-only AI research and measured operating costs."},
    {"name": "proposals", "description": "Qualified paper setups and explicit owner decisions."},
]


def build_openapi(app: FastAPI) -> dict[str, Any]:
    document = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=TAGS,
        servers=[{"url": API_PREFIX, "description": "Base API path"}],
        separate_input_output_schemas=False,
    )

    paths: dict[str, Any] = {}
    for path, item in document.get("paths", {}).items():
        if not path.startswith(f"{API_PREFIX}/"):
            raise ValueError(f"route {path!r} is outside {API_PREFIX}")
        paths[path[len(API_PREFIX) :]] = item
    document["paths"] = paths
    _drop_generated_titles(document)
    return document


def _drop_generated_titles(node: Any) -> None:
    """Remove the titles Pydantic derives from field names ("Actorid"); they add nothing.

    A `title` whose value is text is the schema keyword. A property that happens to be
    called "title" has a schema object as its value and is left alone.
    """
    if isinstance(node, dict):
        if isinstance(node.get("title"), str) and "info" not in node:
            del node["title"]
        for key, value in node.items():
            if key != "info":
                _drop_generated_titles(value)
    elif isinstance(node, list):
        for item in node:
            _drop_generated_titles(item)
