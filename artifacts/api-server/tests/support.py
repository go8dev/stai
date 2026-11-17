"""Shared test helpers: a fake identity provider, a fake OKX, a clock and sign-in steps.

Nothing here talks to the network, and every identifier is made up for the tests.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.testclient import TestClient

ISSUER = "https://idp.test/oidc"
OKX_BASE = "https://okx.test"
CLIENT_ID = "stai-test-client"
OWNER_ID = "owner-account-0001"
OTHER_ID = "other-account-0002"
APP_HOST = "testserver"
APP_ORIGIN = f"https://{APP_HOST}"
KEY_ID = "test-signing-key-1"
ACCESS_TOKEN = "access-token-that-stai-never-keeps"


class FakeClock:
    """A clock the test moves by hand."""

    def __init__(self, start: datetime | None = None):
        self.now = start or datetime.now(UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs: float) -> None:
        self.now = self.now + timedelta(**kwargs)


def generate_signing_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def public_jwk(key: rsa.RSAPrivateKey, key_id: str) -> dict[str, Any]:
    numbers = key.public_key().public_numbers()

    def as_bytes(value: int) -> bytes:
        return value.to_bytes((value.bit_length() + 7) // 8, "big")

    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": key_id,
        "n": _b64url(as_bytes(numbers.n)),
        "e": _b64url(as_bytes(numbers.e)),
    }


@dataclass
class IssuedCode:
    subject: str
    nonce: str
    code_challenge: str
    redirect_uri: str
    overrides: dict[str, Any] = field(default_factory=dict)


class FakeProvider:
    """Stands in for the identity provider and for OKX behind one httpx transport."""

    def __init__(self, signing_key: rsa.RSAPrivateKey, other_key: rsa.RSAPrivateKey):
        self.signing_key = signing_key
        self.other_key = other_key
        self.requests: list[httpx.Request] = []
        self.codes: dict[str, IssuedCode] = {}
        self.last_id_token: str | None = None

        # Identity provider behaviour
        self.discovery_status = 200
        self.discovery_overrides: dict[str, Any] = {}
        self.jwks_keys: list[dict[str, Any]] = [public_jwk(signing_key, KEY_ID)]
        self.token_status = 200
        self.unreachable = False

        # OKX behaviour
        self.okx_status = 200
        self.okx_body: Callable[[], Any] | None = None
        self.okx_error: Exception | None = None
        self.okx_time: Callable[[], datetime] = lambda: datetime.now(UTC)

    # -- transport --------------------------------------------------------------------------

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handle)

    def calls_to(self, fragment: str) -> list[httpx.Request]:
        return [request for request in self.requests if fragment in str(request.url)]

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        url = str(request.url)

        if url.startswith(OKX_BASE):
            return self._okx(request)

        if self.unreachable:
            raise httpx.ConnectError("connection refused", request=request)

        if url == f"{ISSUER}/.well-known/openid-configuration":
            if self.discovery_status != 200:
                return httpx.Response(self.discovery_status, json={"error": "unavailable"})
            return httpx.Response(200, json=self.discovery_document())
        if url == f"{ISSUER}/jwks":
            return httpx.Response(200, json={"keys": self.jwks_keys})
        if url == f"{ISSUER}/token":
            return self._token(request)
        return httpx.Response(404, json={"error": "not_found"})

    def discovery_document(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "issuer": ISSUER,
            "authorization_endpoint": f"{ISSUER}/auth",
            "token_endpoint": f"{ISSUER}/token",
            "jwks_uri": f"{ISSUER}/jwks",
            "end_session_endpoint": f"{ISSUER}/session/end",
            "id_token_signing_alg_values_supported": ["PS256", "RS256"],
            "authorization_response_iss_parameter_supported": True,
        }
        document.update(self.discovery_overrides)
        return document

    # -- identity provider ------------------------------------------------------------------

    def issue_code(
        self, *, subject: str, nonce: str, code_challenge: str, redirect_uri: str, **overrides: Any
    ) -> str:
        code = secrets.token_urlsafe(16)
        self.codes[code] = IssuedCode(subject, nonce, code_challenge, redirect_uri, overrides)
        return code

    def _token(self, request: httpx.Request) -> httpx.Response:
        if self.token_status != 200:
            return httpx.Response(self.token_status, json={"error": "server_error"})

        form = {key: values[0] for key, values in parse_qs(request.content.decode()).items()}
        issued = self.codes.pop(form.get("code", ""), None)
        if issued is None or form.get("grant_type") != "authorization_code":
            return httpx.Response(400, json={"error": "invalid_grant"})
        if form.get("client_id") != CLIENT_ID or form.get("redirect_uri") != issued.redirect_uri:
            return httpx.Response(400, json={"error": "invalid_grant"})

        verifier = form.get("code_verifier", "")
        challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
        if challenge != issued.code_challenge:
            return httpx.Response(400, json={"error": "invalid_grant"})

        self.last_id_token = self.id_token(issued)
        return httpx.Response(
            200,
            json={
                "id_token": self.last_id_token,
                "access_token": ACCESS_TOKEN,
                "token_type": "Bearer",
            },
        )

    def id_token(self, issued: IssuedCode) -> str:
        options = issued.overrides
        now = int(time.time())
        claims: dict[str, Any] = {
            "iss": options.get("issuer", ISSUER),
            "aud": options.get("audience", CLIENT_ID),
            "sub": issued.subject,
            "iat": now + int(options.get("issued_offset", 0)),
            "exp": now + int(options.get("expires_in", 300)),
            "nonce": options.get("token_nonce", issued.nonce),
            "username": options.get("username", "test-user"),
            "first_name": options.get("first_name", "Test"),
            "last_name": options.get("last_name", "User"),
            "profile_image_url": options.get("profile_image_url"),
        }
        claims.update(options.get("extra_claims", {}))
        for name in options.get("drop_claims", ()):
            claims.pop(name, None)

        algorithm = options.get("algorithm", "RS256")
        headers = {"kid": options.get("kid", KEY_ID)}
        if algorithm == "none":
            return jwt.encode(claims, key=None, algorithm="none", headers=headers)
        if algorithm == "HS256":
            return jwt.encode(claims, key="s" * 48, algorithm="HS256", headers=headers)
        key = self.other_key if options.get("wrong_key") else self.signing_key
        return jwt.encode(claims, key=key, algorithm=algorithm, headers=headers)

    # -- OKX ----------------------------------------------------------------------------------

    def _okx(self, request: httpx.Request) -> httpx.Response:
        if self.okx_error is not None:
            raise self.okx_error
        if self.okx_status != 200:
            return httpx.Response(self.okx_status, text="blocked")
        if self.okx_body is not None:
            body = self.okx_body()
            if isinstance(body, str | bytes):
                return httpx.Response(200, content=body)
            return httpx.Response(200, json=body)
        millis = int(self.okx_time().timestamp() * 1000)
        return httpx.Response(200, json={"code": "0", "msg": "", "data": [{"ts": str(millis)}]})


# -- sign-in steps ----------------------------------------------------------------------------


def begin_login(client: TestClient, **params: str) -> dict[str, str]:
    """Call /api/login and return the query parameters sent to the identity provider."""
    response = client.get("/api/login", params=params or None)
    assert response.status_code == 302, response.text
    location = response.headers["location"]
    assert location.startswith(f"{ISSUER}/auth?"), location
    return {key: values[0] for key, values in parse_qs(urlsplit(location).query).items()}


def finish_login(
    client: TestClient,
    provider: FakeProvider,
    authorization: dict[str, str],
    *,
    subject: str = OWNER_ID,
    callback_params: dict[str, str | None] | None = None,
    **overrides: Any,
) -> httpx.Response:
    """Play the identity provider's part and call /api/callback.

    `callback_params` replaces query parameters of the callback; None removes one.
    """
    code = provider.issue_code(
        subject=subject,
        nonce=authorization["nonce"],
        code_challenge=authorization["code_challenge"],
        redirect_uri=authorization["redirect_uri"],
        **overrides,
    )
    params: dict[str, str | None] = {
        "code": code,
        "state": authorization["state"],
        "iss": ISSUER,
    }
    params.update(callback_params or {})
    query = {key: value for key, value in params.items() if value is not None}
    return client.get("/api/callback", params=query)


def sign_in(
    client: TestClient, provider: FakeProvider, *, subject: str = OWNER_ID, **overrides: Any
) -> httpx.Response:
    return finish_login(client, provider, begin_login(client), subject=subject, **overrides)


def csrf_headers(client: TestClient) -> dict[str, str]:
    """Headers a same-origin page sends with a state-changing request."""
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrfToken"], "Origin": APP_ORIGIN}


def redirect_target(response: httpx.Response) -> tuple[str, dict[str, str]]:
    """Path and query of a redirect back into the app."""
    assert response.status_code == 302, response.text
    parts = urlsplit(response.headers["location"])
    return parts.path, {key: values[0] for key, values in parse_qs(parts.query).items()}


def set_cookie_headers(response: httpx.Response) -> dict[str, str]:
    """Set-Cookie headers of a response, keyed by cookie name."""
    cookies: dict[str, str] = {}
    for value in response.headers.get_list("set-cookie"):
        cookies[value.split("=", 1)[0]] = value
    return cookies


def cookie_attributes(header: str) -> set[str]:
    """The attributes of one Set-Cookie header, without the name and value."""
    return {part.strip() for part in header.split(";")[1:]}


def replace_cookie(client: TestClient, name: str, value: str) -> None:
    """Change a cookie in the browser's jar, the way someone editing their cookies could."""
    client.cookies.delete(name)
    client.cookies.set(name, value)


def error_code(response: httpx.Response) -> str:
    body = response.json()
    assert set(body) >= {"error", "message", "correlationId"}, body
    return body["error"]


def as_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)
