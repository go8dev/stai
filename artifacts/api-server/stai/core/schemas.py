"""Base class of every API shape: snake_case in Python, camelCase on the wire."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        # Fields without a default stay required in the contract even when they may be null.
        json_schema_serialization_defaults_required=True,
    )


def _require_response_properties(schema: dict[str, Any]) -> None:
    schema["required"] = list(schema.get("properties", {}))


class DefaultedResponse(ApiModel):
    """Read legacy/defaulted values while documenting fully populated wire responses.

    The contract intentionally uses one input/output schema mode. Per-model mode
    overrides produce dangling nested references in FastAPI's combined schema.
    Restrict this base to response-only models, not request bodies.
    """

    model_config = ConfigDict(json_schema_extra=_require_response_properties)
