"""Browser sessions kept in PostgreSQL.

The cookie holds a random token. The database holds only its SHA-256, so a copy of the
table cannot be used to sign in. A session ends at a fixed time after it was created.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from stai.auth.oidc import IdentityClaims
from stai.db.models import AuthSession, User


@dataclass(frozen=True, slots=True)
class SessionUser:
    """What a valid session says about who is signed in."""

    user_id: str
    username: str | None
    first_name: str | None
    last_name: str | None
    profile_image_url: str | None
    expires_at: datetime


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def upsert_user(db: Session, claims: IdentityClaims, now: datetime) -> User:
    user = db.get(User, claims.subject)
    if user is None:
        user = User(id=claims.subject, created_at=now, updated_at=now)
        db.add(user)
    user.username = claims.username
    user.first_name = claims.first_name
    user.last_name = claims.last_name
    user.profile_image_url = claims.profile_image_url
    user.updated_at = now
    user.last_login_at = now
    db.flush()
    return user


def create_session(
    db: Session, *, user_id: str, now: datetime, ttl: timedelta
) -> tuple[str, datetime]:
    """Store a new session and return the cookie token and the expiry time."""
    token = new_session_token()
    expires_at = now + ttl
    db.add(
        AuthSession(
            token_hash=hash_token(token), user_id=user_id, created_at=now, expires_at=expires_at
        )
    )
    db.flush()
    return token, expires_at


def find_session(db: Session, token: str, now: datetime) -> SessionUser | None:
    """The user behind a session token, or None when the token is unknown or expired."""
    if not token or len(token) > 512:
        return None
    row = db.execute(
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(AuthSession.token_hash == hash_token(token))
    ).first()
    if row is None:
        return None

    session, user = row
    if session.expires_at <= now:
        db.delete(session)
        return None

    return SessionUser(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        profile_image_url=user.profile_image_url,
        expires_at=session.expires_at,
    )


def delete_session(db: Session, token: str) -> str | None:
    """End a session. Returns the user ID it belonged to, or None if there was none."""
    if not token or len(token) > 512:
        return None
    session = db.get(AuthSession, hash_token(token))
    if session is None:
        return None
    user_id = session.user_id
    db.delete(session)
    db.flush()
    return user_id


def purge_expired(db: Session, now: datetime) -> int:
    result = db.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
    return int(result.rowcount or 0)
