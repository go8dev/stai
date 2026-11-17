"""The health check: open to everyone, and independent of everything else."""

from __future__ import annotations

from starlette.testclient import TestClient

from .conftest import AppFactory

UNREACHABLE_DATABASE = "postgresql://nobody:nothing@127.0.0.1:1/none"


def test_health_check_answers_without_sign_in(client: TestClient) -> None:
    response = client.get("/api/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"] == "application/json"


def test_health_check_works_without_a_database(make_harness: AppFactory) -> None:
    harness = make_harness(use_database=False)

    assert harness.client.get("/api/healthz").status_code == 200


def test_health_check_never_opens_a_database_connection(make_harness: AppFactory) -> None:
    harness = make_harness(DATABASE_URL=UNREACHABLE_DATABASE)

    for _ in range(3):
        assert harness.client.get("/api/healthz").json() == {"status": "ok"}

    # The engine is only built when something asks the database a question.
    assert harness.runtime.database._engine is None


def test_health_check_makes_no_outside_calls(make_harness: AppFactory) -> None:
    harness = make_harness()

    harness.client.get("/api/healthz")

    assert harness.provider.requests == []


def test_health_check_works_when_sign_in_is_not_configured(make_harness: AppFactory) -> None:
    harness = make_harness(REPL_ID=None, STAI_OWNER_USER_ID=None)

    assert harness.client.get("/api/healthz").status_code == 200


def test_health_check_only_answers_get(client: TestClient) -> None:
    # Signed out, anything that is not the listed route is closed, whatever the method.
    assert client.post("/api/healthz").status_code == 405
    assert client.get("/api/healthz/").status_code == 401
    assert client.get("/api/healthz/extra").status_code == 401
