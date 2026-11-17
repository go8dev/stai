"""Base class of every API shape: snake_case in Python, camelCase on the wire."""

from __future__ import annotations

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
