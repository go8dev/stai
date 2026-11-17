"""API shapes of sign-in state."""

from __future__ import annotations

from stai.auth.sessions import SessionUser
from stai.core.schemas import ApiModel


class AuthUser(ApiModel):
    id: str
    username: str | None
    first_name: str | None
    last_name: str | None
    profile_image_url: str | None

    @classmethod
    def from_session(cls, user: SessionUser) -> AuthUser:
        return cls(
            id=user.user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            profile_image_url=user.profile_image_url,
        )


class AuthUserEnvelope(ApiModel):
    user: AuthUser | None


class CsrfToken(ApiModel):
    csrf_token: str
