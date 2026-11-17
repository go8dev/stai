"""The identity-provider client on its own: caching, key rotation and token checks."""

from __future__ import annotations

import time
from typing import Any

import httpx
import pytest

from stai.auth.oidc import (
    CLOCK_LEEWAY_SECONDS,
    IdentityClaims,
    OidcClient,
    OidcRejected,
    OidcUnavailable,
    pkce_challenge,
    random_token,
)

from .support import (
    ACCESS_TOKEN,
    CLIENT_ID,
    ISSUER,
    KEY_ID,
    OWNER_ID,
    FakeProvider,
    IssuedCode,
    public_jwk,
)

pytestmark = pytest.mark.asyncio

NONCE = "nonce-for-these-tests"
REDIRECT_URI = "https://testserver/api/callback"


class Clock:
    """Seconds since the epoch, starting at the real time so token times stay valid."""

    def __init__(self) -> None:
        self.offset = 0.0

    def __call__(self) -> float:
        return time.time() + self.offset


def make_client(provider: FakeProvider, **options: Any) -> tuple[OidcClient, httpx.AsyncClient]:
    http = httpx.AsyncClient(transport=provider.transport())
    return OidcClient(issuer_url=ISSUER, client_id=CLIENT_ID, http=http, **options), http


def token(provider: FakeProvider, **overrides: Any) -> str:
    subject = overrides.pop("subject", OWNER_ID)
    return provider.id_token(IssuedCode(subject, NONCE, "", REDIRECT_URI, overrides))


def discovery_calls(provider: FakeProvider) -> int:
    return len(provider.calls_to("/.well-known/openid-configuration"))


def key_calls(provider: FakeProvider) -> int:
    return len(provider.calls_to("/jwks"))


# -- PKCE and random values -------------------------------------------------------------------


async def test_pkce_challenge_matches_the_published_example() -> None:
    # Appendix B of RFC 7636.
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"

    assert pkce_challenge(verifier) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


async def test_random_values_are_long_and_never_repeat() -> None:
    values = {random_token() for _ in range(200)}

    assert len(values) == 200
    assert all(len(value) == 43 for value in values)


# -- provider settings ------------------------------------------------------------------------


async def test_provider_settings_are_fetched_once_and_reused(provider: FakeProvider) -> None:
    client, http = make_client(provider)
    async with http:
        first = await client.metadata()
        await client.authorization_url(
            redirect_uri=REDIRECT_URI, state="s", nonce="n", code_challenge="c"
        )
        await client.end_session_url(post_logout_redirect_uri="https://testserver")
        second = await client.metadata()

    assert first is second
    assert discovery_calls(provider) == 1


async def test_provider_settings_are_fetched_again_after_an_hour(provider: FakeProvider) -> None:
    clock = Clock()
    client, http = make_client(provider, clock=clock)
    async with http:
        await client.metadata()
        clock.offset = 3599
        await client.metadata()
        assert discovery_calls(provider) == 1

        clock.offset = 3601
        await client.metadata()

    assert discovery_calls(provider) == 2


async def test_a_failed_fetch_is_not_remembered(provider: FakeProvider) -> None:
    client, http = make_client(provider)
    async with http:
        provider.discovery_status = 500
        with pytest.raises(OidcUnavailable) as failure:
            await client.metadata()
        assert failure.value.reason == "provider_status_500"

        provider.discovery_status = 200
        metadata = await client.metadata()

    assert metadata.issuer == ISSUER


async def test_an_issuer_with_a_trailing_slash_is_the_same_issuer(provider: FakeProvider) -> None:
    provider.discovery_overrides["issuer"] = f"{ISSUER}/"
    client, http = make_client(provider)
    async with http:
        metadata = await client.metadata()

    assert metadata.issuer == ISSUER


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"issuer": "https://elsewhere.example/oidc"}, "metadata_issuer_mismatch"),
        ({"issuer": None}, "metadata_issuer_mismatch"),
        ({"authorization_endpoint": "http://idp.test/oidc/auth"}, "metadata_authorization_invalid"),
        ({"token_endpoint": None}, "metadata_token_invalid"),
        ({"jwks_uri": "javascript:alert(1)"}, "metadata_jwks_invalid"),
        ({"end_session_endpoint": "http://idp.test/out"}, "metadata_end_session_invalid"),
        ({"id_token_signing_alg_values_supported": ["none"]}, "metadata_no_usable_algorithm"),
        ({"id_token_signing_alg_values_supported": ["HS256"]}, "metadata_no_usable_algorithm"),
        ({"id_token_signing_alg_values_supported": []}, "metadata_no_usable_algorithm"),
    ],
)
async def test_provider_settings_that_cannot_be_trusted_are_refused(
    provider: FakeProvider, override: dict[str, Any], reason: str
) -> None:
    provider.discovery_overrides.update(override)
    client, http = make_client(provider)
    async with http:
        with pytest.raises(OidcUnavailable) as failure:
            await client.metadata()

    assert failure.value.reason == reason


async def test_only_asymmetric_algorithms_are_kept(provider: FakeProvider) -> None:
    provider.discovery_overrides["id_token_signing_alg_values_supported"] = [
        "none",
        "HS256",
        "RS256",
        "ES256",
        42,
    ]
    client, http = make_client(provider)
    async with http:
        metadata = await client.metadata()

    assert metadata.signing_algorithms == frozenset({"RS256", "ES256"})


async def test_an_unreachable_provider_is_reported_as_unavailable(provider: FakeProvider) -> None:
    provider.unreachable = True
    client, http = make_client(provider)
    async with http:
        with pytest.raises(OidcUnavailable) as failure:
            await client.metadata()

    assert failure.value.reason == "provider_unreachable"


# -- the authorization request and the code exchange ------------------------------------------


async def test_the_authorization_request_carries_no_secret(provider: FakeProvider) -> None:
    client, http = make_client(provider)
    async with http:
        url = await client.authorization_url(
            redirect_uri=REDIRECT_URI, state="state-1", nonce="nonce-1", code_challenge="chal-1"
        )

    query = dict(httpx.URL(url).params)
    assert url.startswith(f"{ISSUER}/auth?")
    assert query == {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile",
        "code_challenge": "chal-1",
        "code_challenge_method": "S256",
        "prompt": "login consent",
        "state": "state-1",
        "nonce": "nonce-1",
    }


async def test_the_code_exchange_returns_only_the_identity_token(provider: FakeProvider) -> None:
    verifier = random_token()
    code = provider.issue_code(
        subject=OWNER_ID,
        nonce=NONCE,
        code_challenge=pkce_challenge(verifier),
        redirect_uri=REDIRECT_URI,
    )
    client, http = make_client(provider)
    async with http:
        id_token = await client.exchange_code(
            code=code, redirect_uri=REDIRECT_URI, code_verifier=verifier
        )

    assert id_token == provider.last_id_token
    assert ACCESS_TOKEN not in id_token

    request = provider.calls_to("/token")[0]
    form = dict(httpx.QueryParams(request.content.decode()))
    assert request.method == "POST"
    assert form == {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": verifier,
    }
    # A public client: there is no client secret to send, in the body or in a header.
    assert "authorization" not in request.headers


@pytest.mark.parametrize(
    ("status", "error", "reason"),
    [
        (400, OidcRejected, "token_exchange_status_400"),
        (401, OidcRejected, "token_exchange_status_401"),
        (500, OidcUnavailable, "token_endpoint_status_500"),
        (503, OidcUnavailable, "token_endpoint_status_503"),
    ],
)
async def test_a_failed_code_exchange_says_whose_fault_it_was(
    provider: FakeProvider, status: int, error: type[Exception], reason: str
) -> None:
    provider.token_status = status
    client, http = make_client(provider)
    async with http:
        with pytest.raises(error) as failure:
            await client.exchange_code(code="any", redirect_uri=REDIRECT_URI, code_verifier="v")

    assert failure.value.reason == reason  # type: ignore[attr-defined]


async def test_a_wrong_verifier_fails_the_code_exchange(provider: FakeProvider) -> None:
    code = provider.issue_code(
        subject=OWNER_ID,
        nonce=NONCE,
        code_challenge=pkce_challenge(random_token()),
        redirect_uri=REDIRECT_URI,
    )
    client, http = make_client(provider)
    async with http:
        with pytest.raises(OidcRejected):
            await client.exchange_code(
                code=code, redirect_uri=REDIRECT_URI, code_verifier=random_token()
            )


# -- identity tokens --------------------------------------------------------------------------


async def test_a_good_identity_token_yields_the_account(provider: FakeProvider) -> None:
    client, http = make_client(provider)
    async with http:
        claims = await client.verify_id_token(
            token(
                provider,
                username="  owner-name  ",
                first_name="",
                last_name=None,
                profile_image_url="https://images.example/owner.png",
            ),
            nonce=NONCE,
        )

    assert claims == IdentityClaims(
        subject=OWNER_ID,
        username="owner-name",
        first_name=None,
        last_name=None,
        profile_image_url="https://images.example/owner.png",
    )


@pytest.mark.parametrize(
    "address",
    [
        "http://images.example/owner.png",
        "javascript:alert(1)",
        "data:image/png;base64,AAAA",
        "//images.example/owner.png",
        "https://images.example/a b.png",
        12345,
    ],
)
async def test_a_profile_picture_that_is_not_an_https_address_is_dropped(
    provider: FakeProvider, address: Any
) -> None:
    client, http = make_client(provider)
    async with http:
        claims = await client.verify_id_token(
            token(provider, profile_image_url=address), nonce=NONCE
        )

    assert claims.profile_image_url is None


async def test_profile_text_is_cut_to_a_sane_length(provider: FakeProvider) -> None:
    client, http = make_client(provider)
    async with http:
        claims = await client.verify_id_token(
            token(provider, username="u" * 5000, first_name=["not", "text"]), nonce=NONCE
        )

    assert claims.username == "u" * 500
    assert claims.first_name is None


async def test_the_clock_may_differ_by_a_minute_and_no_more(provider: FakeProvider) -> None:
    client, http = make_client(provider)
    async with http:
        just_expired = token(provider, expires_in=-(CLOCK_LEEWAY_SECONDS - 20))
        assert (await client.verify_id_token(just_expired, nonce=NONCE)).subject == OWNER_ID

        long_expired = token(provider, expires_in=-(CLOCK_LEEWAY_SECONDS + 20))
        with pytest.raises(OidcRejected) as failure:
            await client.verify_id_token(long_expired, nonce=NONCE)
        assert failure.value.reason == "id_token_expired"

        slightly_ahead = token(provider, issued_offset=CLOCK_LEEWAY_SECONDS - 20)
        assert (await client.verify_id_token(slightly_ahead, nonce=NONCE)).subject == OWNER_ID


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"audience": "some-other-app"}, "id_token_wrong_audience"),
        ({"issuer": "https://elsewhere.example/oidc"}, "id_token_wrong_issuer"),
        ({"wrong_key": True}, "id_token_bad_signature"),
        ({"kid": "unknown-key"}, "id_token_unknown_key"),
        ({"algorithm": "none"}, "id_token_algorithm_not_allowed"),
        ({"algorithm": "HS256"}, "id_token_algorithm_not_allowed"),
        ({"algorithm": "RS384"}, "id_token_algorithm_not_allowed"),
        ({"token_nonce": "another-nonce"}, "id_token_wrong_nonce"),
        ({"drop_claims": ["nonce"]}, "id_token_wrong_nonce"),
        ({"extra_claims": {"nonce": 7}}, "id_token_wrong_nonce"),
        ({"drop_claims": ["sub"]}, "id_token_invalid"),
        ({"drop_claims": ["exp"]}, "id_token_invalid"),
        ({"drop_claims": ["iat"]}, "id_token_invalid"),
        ({"extra_claims": {"azp": "some-other-app"}}, "id_token_wrong_azp"),
        ({"audience": [CLIENT_ID, "some-other-app"]}, "id_token_missing_azp"),
        ({"extra_claims": {"sub": "   "}}, "id_token_bad_subject"),
        ({"extra_claims": {"sub": "x" * 256}}, "id_token_bad_subject"),
        ({"extra_claims": {"sub": "line\nbreak"}}, "id_token_bad_subject"),
    ],
)
async def test_each_failed_check_has_its_own_reason(
    provider: FakeProvider, overrides: dict[str, Any], reason: str
) -> None:
    client, http = make_client(provider)
    async with http:
        with pytest.raises(OidcRejected) as failure:
            await client.verify_id_token(token(provider, **overrides), nonce=NONCE)

    assert failure.value.reason == reason


async def test_several_audiences_are_fine_when_we_are_the_authorized_party(
    provider: FakeProvider,
) -> None:
    client, http = make_client(provider)
    async with http:
        claims = await client.verify_id_token(
            token(
                provider,
                audience=[CLIENT_ID, "some-other-app"],
                extra_claims={"azp": CLIENT_ID},
            ),
            nonce=NONCE,
        )

    assert claims.subject == OWNER_ID


@pytest.mark.parametrize("garbage", ["", "not-a-token", "a.b", "a.b.c", "....", "e30.e30.e30"])
async def test_text_that_is_not_a_token_is_rejected(provider: FakeProvider, garbage: str) -> None:
    client, http = make_client(provider)
    async with http:
        with pytest.raises(OidcRejected):
            await client.verify_id_token(garbage, nonce=NONCE)


async def test_a_token_with_a_swapped_body_is_rejected(provider: FakeProvider) -> None:
    """The signature of one token does not vouch for the content of another."""
    owner = token(provider, subject="someone-else").split(".")
    forged_body = token(provider, subject=OWNER_ID).split(".")[1]
    forged = ".".join([owner[0], forged_body, owner[2]])

    client, http = make_client(provider)
    async with http:
        with pytest.raises(OidcRejected) as failure:
            await client.verify_id_token(forged, nonce=NONCE)

    assert failure.value.reason == "id_token_bad_signature"


# -- signing keys -----------------------------------------------------------------------------


async def test_signing_keys_are_fetched_once_and_reused(provider: FakeProvider) -> None:
    client, http = make_client(provider)
    async with http:
        for _ in range(3):
            await client.verify_id_token(token(provider), nonce=NONCE)

    assert key_calls(provider) == 1


async def test_a_rotated_key_is_picked_up(provider: FakeProvider) -> None:
    clock = Clock()
    client, http = make_client(provider, clock=clock)
    async with http:
        await client.verify_id_token(token(provider), nonce=NONCE)

        # The provider starts signing with a key this client has not seen yet.
        provider.jwks_keys = [public_jwk(provider.other_key, "rotated-key")]
        rotated = token(provider, wrong_key=True, kid="rotated-key")

        # Straight away the keys are not fetched again, so a flood of made-up key IDs
        # cannot turn into a flood of requests to the provider.
        with pytest.raises(OidcRejected) as failure:
            await client.verify_id_token(rotated, nonce=NONCE)
        assert failure.value.reason == "id_token_unknown_key"
        assert key_calls(provider) == 1

        clock.offset = 31
        claims = await client.verify_id_token(rotated, nonce=NONCE)

    assert claims.subject == OWNER_ID
    assert key_calls(provider) == 2


async def test_unknown_key_ids_do_not_flood_the_provider(provider: FakeProvider) -> None:
    client, http = make_client(provider)
    async with http:
        for index in range(25):
            with pytest.raises(OidcRejected):
                await client.verify_id_token(token(provider, kid=f"made-up-{index}"), nonce=NONCE)

    assert key_calls(provider) == 1


async def test_keys_not_meant_for_signatures_are_ignored(provider: FakeProvider) -> None:
    encryption_key = {**public_jwk(provider.signing_key, KEY_ID), "use": "enc"}
    provider.jwks_keys = [encryption_key]
    client, http = make_client(provider)
    async with http:
        with pytest.raises(OidcUnavailable) as failure:
            await client.verify_id_token(token(provider), nonce=NONCE)

    assert failure.value.reason == "provider_no_signing_keys"


async def test_unreadable_keys_are_skipped(provider: FakeProvider) -> None:
    provider.jwks_keys = [
        {"kty": "RSA", "kid": "broken"},
        "not-a-key",
        public_jwk(provider.signing_key, KEY_ID),
    ]
    client, http = make_client(provider)
    async with http:
        claims = await client.verify_id_token(token(provider), nonce=NONCE)

    assert claims.subject == OWNER_ID
