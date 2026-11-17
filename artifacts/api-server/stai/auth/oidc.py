"""OpenID Connect client for the authorization-code flow with PKCE.

Server-side port of the flow in Replit's sign-in instructions, which are written for a
Node server. Kept from them: the public client (the app's REPL_ID, no client secret),
PKCE with S256, `state`, `nonce`, and `prompt=login consent`.

Narrower here: the scope is `openid profile` only. STAI needs to know which account
signed in and nothing else, so it asks for no email address and no refresh token, and it
keeps neither the access token nor the identity token after the callback.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

SCOPE = "openid profile"
PROMPT = "login consent"
CLOCK_LEEWAY_SECONDS = 60

# Signature algorithms accepted for identity tokens. Never "none", never a shared-secret one.
_ASYMMETRIC_ALGORITHMS = frozenset(
    {"RS256", "RS384", "RS512", "PS256", "PS384", "PS512", "ES256", "ES384", "ES512", "EdDSA"}
)


class OidcError(Exception):
    """Base class. `reason` is a short code for logs, never shown to visitors."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class OidcUnavailable(OidcError):
    """The identity provider could not be reached or answered with something unusable."""


class OidcRejected(OidcError):
    """The sign-in response or the identity token failed a check."""


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    end_session_endpoint: str | None
    signing_algorithms: frozenset[str]
    iss_parameter_supported: bool


@dataclass(frozen=True, slots=True)
class IdentityClaims:
    subject: str
    username: str | None
    first_name: str | None
    last_name: str | None
    profile_image_url: str | None


def random_token() -> str:
    """A fresh unguessable value for `state`, `nonce` or a PKCE verifier (43 characters)."""
    return secrets.token_urlsafe(32)


def pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _https(url: Any, name: str) -> str:
    if not isinstance(url, str) or not url.startswith("https://"):
        raise OidcUnavailable(f"metadata_{name}_invalid")
    return url


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped[:500] or None
    return None


def _https_url(value: Any) -> str | None:
    """An https address, or None. The web app puts this value in an image tag."""
    url = _text(value)
    if url is None or not url.startswith("https://") or any(char.isspace() for char in url):
        return None
    return url


class OidcClient:
    """Talks to one identity provider on behalf of one client ID."""

    def __init__(
        self,
        *,
        issuer_url: str,
        client_id: str,
        http: httpx.AsyncClient,
        clock: Callable[[], float] = time.time,
        metadata_ttl_seconds: float = 3600,
        jwks_ttl_seconds: float = 3600,
        jwks_min_refresh_seconds: float = 30,
    ):
        self._issuer = issuer_url.rstrip("/")
        self._client_id = client_id
        self._http = http
        self._clock = clock
        self._metadata_ttl = metadata_ttl_seconds
        self._jwks_ttl = jwks_ttl_seconds
        self._jwks_min_refresh = jwks_min_refresh_seconds

        self._metadata: ProviderMetadata | None = None
        self._metadata_at = 0.0
        self._keys: dict[str | None, Any] = {}
        self._keys_at: float | None = None

    @property
    def issuer(self) -> str:
        return self._issuer

    # -- provider metadata and keys ---------------------------------------------------------

    async def metadata(self) -> ProviderMetadata:
        now = self._clock()
        if self._metadata is not None and now - self._metadata_at < self._metadata_ttl:
            return self._metadata

        data = await self._get_json(f"{self._issuer}/.well-known/openid-configuration")
        issuer = data.get("issuer")
        if not isinstance(issuer, str) or issuer.rstrip("/") != self._issuer:
            raise OidcUnavailable("metadata_issuer_mismatch")

        advertised = data.get("id_token_signing_alg_values_supported")
        algorithms = (
            frozenset(a for a in advertised if isinstance(a, str)) & _ASYMMETRIC_ALGORITHMS
            if isinstance(advertised, list)
            else frozenset({"RS256"})
        )
        if not algorithms:
            raise OidcUnavailable("metadata_no_usable_algorithm")

        end_session = data.get("end_session_endpoint")
        self._metadata = ProviderMetadata(
            issuer=self._issuer,
            authorization_endpoint=_https(data.get("authorization_endpoint"), "authorization"),
            token_endpoint=_https(data.get("token_endpoint"), "token"),
            jwks_uri=_https(data.get("jwks_uri"), "jwks"),
            end_session_endpoint=_https(end_session, "end_session") if end_session else None,
            signing_algorithms=algorithms,
            iss_parameter_supported=data.get("authorization_response_iss_parameter_supported")
            is True,
        )
        self._metadata_at = now
        return self._metadata

    async def _get_json(self, url: str) -> dict[str, Any]:
        try:
            response = await self._http.get(url, headers={"Accept": "application/json"})
        except httpx.HTTPError as exc:
            raise OidcUnavailable("provider_unreachable") from exc
        if response.status_code != 200:
            raise OidcUnavailable(f"provider_status_{response.status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise OidcUnavailable("provider_bad_json") from exc
        if not isinstance(data, dict):
            raise OidcUnavailable("provider_bad_json")
        return data

    async def _load_keys(self, metadata: ProviderMetadata) -> None:
        data = await self._get_json(metadata.jwks_uri)
        keys: dict[str | None, Any] = {}
        for item in data.get("keys", []) if isinstance(data.get("keys"), list) else []:
            if not isinstance(item, dict) or item.get("use", "sig") != "sig":
                continue
            try:
                parsed = jwt.PyJWK.from_dict(item)
            except jwt.PyJWTError:
                continue
            keys[parsed.key_id] = parsed.key
        if not keys:
            raise OidcUnavailable("provider_no_signing_keys")
        self._keys = keys
        self._keys_at = self._clock()

    async def _signing_key(self, metadata: ProviderMetadata, key_id: str | None) -> Any:
        now = self._clock()
        if self._keys_at is None or now - self._keys_at >= self._jwks_ttl:
            await self._load_keys(metadata)

        key = self._lookup_key(key_id)
        if key is None and self._keys_at is not None:
            # The provider may have rotated its keys; look again, but not on every request.
            if self._clock() - self._keys_at >= self._jwks_min_refresh:
                await self._load_keys(metadata)
                key = self._lookup_key(key_id)
        if key is None:
            raise OidcRejected("id_token_unknown_key")
        return key

    def _lookup_key(self, key_id: str | None) -> Any | None:
        if key_id is not None:
            return self._keys.get(key_id)
        if len(self._keys) == 1:
            return next(iter(self._keys.values()))
        return None

    # -- the flow -----------------------------------------------------------------------------

    async def authorization_url(
        self, *, redirect_uri: str, state: str, nonce: str, code_challenge: str
    ) -> str:
        metadata = await self.metadata()
        query = urlencode(
            {
                "client_id": self._client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": SCOPE,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "prompt": PROMPT,
                "state": state,
                "nonce": nonce,
            }
        )
        separator = "&" if "?" in metadata.authorization_endpoint else "?"
        return f"{metadata.authorization_endpoint}{separator}{query}"

    async def exchange_code(self, *, code: str, redirect_uri: str, code_verifier: str) -> str:
        """Trade the authorization code for an identity token and return only that token."""
        metadata = await self.metadata()
        try:
            response = await self._http.post(
                metadata.token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self._client_id,
                    "code_verifier": code_verifier,
                },
                headers={"Accept": "application/json"},
            )
        except httpx.HTTPError as exc:
            raise OidcUnavailable("token_endpoint_unreachable") from exc

        if response.status_code >= 500:
            raise OidcUnavailable(f"token_endpoint_status_{response.status_code}")
        if response.status_code != 200:
            raise OidcRejected(f"token_exchange_status_{response.status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise OidcRejected("token_response_bad_json") from exc

        id_token = data.get("id_token") if isinstance(data, dict) else None
        if not isinstance(id_token, str) or not id_token:
            raise OidcRejected("token_response_without_id_token")
        return id_token

    async def verify_id_token(self, id_token: str, *, nonce: str) -> IdentityClaims:
        """Check signature, issuer, audience, times and nonce, then return the claims."""
        metadata = await self.metadata()
        try:
            header = jwt.get_unverified_header(id_token)
        except jwt.PyJWTError as exc:
            raise OidcRejected("id_token_malformed") from exc

        algorithm = header.get("alg")
        if algorithm not in metadata.signing_algorithms:
            raise OidcRejected("id_token_algorithm_not_allowed")
        key_id = header.get("kid")
        key = await self._signing_key(metadata, key_id if isinstance(key_id, str) else None)

        try:
            claims = jwt.decode(
                id_token,
                key=key,
                algorithms=[algorithm],
                audience=self._client_id,
                issuer=metadata.issuer,
                leeway=CLOCK_LEEWAY_SECONDS,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise OidcRejected("id_token_expired") from exc
        except jwt.InvalidAudienceError as exc:
            raise OidcRejected("id_token_wrong_audience") from exc
        except jwt.InvalidIssuerError as exc:
            raise OidcRejected("id_token_wrong_issuer") from exc
        except jwt.InvalidSignatureError as exc:
            raise OidcRejected("id_token_bad_signature") from exc
        except jwt.PyJWTError as exc:
            raise OidcRejected("id_token_invalid") from exc

        audience = claims.get("aud")
        authorized_party = claims.get("azp")
        if isinstance(audience, list) and len(audience) > 1 and authorized_party is None:
            raise OidcRejected("id_token_missing_azp")
        if authorized_party is not None and authorized_party != self._client_id:
            raise OidcRejected("id_token_wrong_azp")

        token_nonce = claims.get("nonce")
        if not isinstance(token_nonce, str) or not hmac.compare_digest(
            token_nonce.encode(), nonce.encode()
        ):
            raise OidcRejected("id_token_wrong_nonce")

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 255:
            raise OidcRejected("id_token_bad_subject")
        if any(ord(char) < 0x20 or ord(char) == 0x7F for char in subject):
            # The ID is stored and shown back to the visitor, so it must be plain text.
            raise OidcRejected("id_token_bad_subject")

        return IdentityClaims(
            subject=subject,
            username=_text(claims.get("username")) or _text(claims.get("preferred_username")),
            first_name=_text(claims.get("first_name")),
            last_name=_text(claims.get("last_name")),
            profile_image_url=_https_url(claims.get("profile_image_url")),
        )

    async def end_session_url(self, *, post_logout_redirect_uri: str) -> str | None:
        metadata = await self.metadata()
        if metadata.end_session_endpoint is None:
            return None
        query = urlencode(
            {
                "client_id": self._client_id,
                "post_logout_redirect_uri": post_logout_redirect_uri,
            }
        )
        separator = "&" if "?" in metadata.end_session_endpoint else "?"
        return f"{metadata.end_session_endpoint}{separator}{query}"
