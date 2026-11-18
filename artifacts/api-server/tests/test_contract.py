"""The API contract: generated from the backend, stored in the repository, never stale."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi import FastAPI
from fastapi.routing import iter_route_contexts

from stai import __version__
from stai.auth.gate import PUBLIC_PATHS
from stai.core.config import load_settings
from stai.core.openapi import API_PREFIX, build_openapi
from stai.main import build_app
from stai.tools import openapi as tool

from .conftest import REPO_ROOT

GENERATED_CLIENT = REPO_ROOT / "lib" / "api-client-react" / "src" / "generated" / "api.ts"
GENERATED_CLIENT_TYPES = (
    REPO_ROOT / "lib" / "api-client-react" / "src" / "generated" / "api.schemas.ts"
)
GENERATED_VALIDATORS = REPO_ROOT / "lib" / "api-zod" / "src" / "generated" / "api.ts"

OPERATIONS = {
    ("GET", "/healthz"): "healthCheck",
    ("GET", "/system/status"): "getSystemStatus",
    ("GET", "/auth/user"): "getCurrentAuthUser",
    ("GET", "/auth/csrf"): "getCsrfToken",
    ("GET", "/login"): "beginBrowserLogin",
    ("GET", "/callback"): "handleBrowserLoginCallback",
    ("GET", "/logout"): "logoutBrowserSession",
    ("GET", "/audit/events"): "listAuditEvents",
    ("POST", "/audit/verify"): "verifyAuditTrail",
    ("GET", "/market/scanner"): "getMarketScanner",
    ("GET", "/portfolio/summary"): "getPortfolioSummary",
    ("GET", "/portfolio/ledger"): "listPortfolioLedger",
    ("GET", "/portfolio/ledger/verify"): "verifyPortfolioLedger",
    ("GET", "/committee"): "getCommitteeOverview",
    ("GET", "/committee/{run_id}"): "getCommitteeRun",
    ("GET", "/proposal-center"): "getProposalCenter",
    ("POST", "/proposals/{proposal_id}/approve"): "approveTradeProposal",
    ("POST", "/proposals/{proposal_id}/reject"): "rejectTradeProposal",
    ("GET", "/strategy-lab"): "getStrategyLabOverview",
    ("GET", "/strategy-lab/backtests"): "listStrategyBacktests",
    ("POST", "/strategy-lab/backtests"): "createStrategyBacktest",
    ("GET", "/strategy-lab/backtests/{run_id}"): "getStrategyBacktest",
    ("GET", "/strategy-lab/backtests/{run_id}/reviews"): "listStrategyBacktestReviews",
    ("POST", "/strategy-lab/backtests/{run_id}/reviews"): "createStrategyBacktestReview",
}


@pytest.fixture(scope="module")
def app() -> FastAPI:
    return build_app(load_settings({}))


@pytest.fixture(scope="module")
def stored() -> dict[str, Any]:
    return yaml.safe_load(tool.SPEC_PATH.read_text(encoding="utf-8"))


def operations(document: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (method.upper(), path): operation
        for path, item in document["paths"].items()
        for method, operation in item.items()
    }


def references(node: Any) -> set[str]:
    """Every schema name a part of the document points at."""
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                found.add(value.rsplit("/", 1)[-1])
            else:
                found |= references(value)
    elif isinstance(node, list):
        for item in node:
            found |= references(item)
    return found


# -- the stored file is what the code produces ------------------------------------------------


def test_the_stored_contract_is_what_the_backend_generates() -> None:
    stored_text = tool.SPEC_PATH.read_text(encoding="utf-8")

    assert stored_text == tool.render(), (
        "lib/api-spec/openapi.yaml is out of date. Run `pnpm run openapi:export`, then "
        "`pnpm --filter @workspace/api-spec run codegen`."
    )


def test_generating_the_contract_gives_the_same_text_every_time() -> None:
    assert tool.render() == tool.render()


def test_generating_the_contract_needs_nothing_from_the_environment(
    clean_environment: pytest.MonkeyPatch,
) -> None:
    clean_environment.setenv("STAI_ENV", "development")
    clean_environment.setenv("DATABASE_URL", "postgresql://nobody:nothing@127.0.0.1:1/none")

    assert tool.render() == tool.SPEC_PATH.read_text(encoding="utf-8")


def test_the_file_says_it_is_generated() -> None:
    first_lines = tool.SPEC_PATH.read_text(encoding="utf-8").splitlines()[:3]

    assert all(line.startswith("# ") for line in first_lines)
    assert "Do not edit by hand" in " ".join(first_lines)


# -- the check command ------------------------------------------------------------------------


@pytest.fixture
def spec_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the tool at a scratch file, so the tests never touch the real contract."""
    path = tmp_path / "lib" / "api-spec" / "openapi.yaml"
    path.parent.mkdir(parents=True)
    monkeypatch.setattr(tool, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(tool, "SPEC_PATH", path)
    return path


def test_the_check_passes_on_the_stored_contract(capsys: pytest.CaptureFixture[str]) -> None:
    assert tool.main(["--check"]) == 0
    assert capsys.readouterr().out == "The API contract is up to date.\n"


def test_export_writes_the_file_and_the_check_then_passes(
    spec_in: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert tool.main([]) == 0
    assert capsys.readouterr().out == "Wrote lib/api-spec/openapi.yaml\n"
    assert spec_in.read_text(encoding="utf-8") == tool.render()

    assert tool.main(["--check"]) == 0


def test_the_check_fails_when_the_file_is_missing(
    spec_in: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert tool.main(["--check"]) == 1
    assert "is out of date. Run `pnpm run openapi:export`" in capsys.readouterr().err
    # Checking never writes.
    assert not spec_in.exists()


def test_the_check_fails_and_shows_the_difference_when_the_file_is_stale(
    spec_in: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stale = tool.render().replace("operationId: getSystemStatus", "operationId: getOldStatus")
    spec_in.write_text(stale, encoding="utf-8")

    assert tool.main(["--check"]) == 1

    error = capsys.readouterr().err
    assert "-      operationId: getOldStatus" in error
    assert "+      operationId: getSystemStatus" in error
    assert "pnpm --filter @workspace/api-spec run codegen" in error
    assert spec_in.read_text(encoding="utf-8") == stale


def test_a_hand_edit_of_one_character_is_noticed(
    spec_in: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec_in.write_text(tool.render() + "\n", encoding="utf-8")

    assert tool.main(["--check"]) == 1


# -- what the contract describes --------------------------------------------------------------


def test_the_contract_is_openapi_3_1_served_under_the_api_path(stored: dict[str, Any]) -> None:
    assert stored["openapi"] == "3.1.0"
    assert stored["info"]["title"] == "Api"
    assert stored["info"]["version"] == __version__
    assert stored["servers"] == [{"url": "/api", "description": "Base API path"}]
    assert API_PREFIX == "/api"


def test_the_contract_lists_exactly_the_operations_of_phase_one(stored: dict[str, Any]) -> None:
    found = {key: operation["operationId"] for key, operation in operations(stored).items()}

    assert found == OPERATIONS


def test_every_route_of_the_app_is_in_the_contract_and_the_reverse(
    app: FastAPI, stored: dict[str, Any]
) -> None:
    served = {
        (method, route.path)
        for route in iter_route_contexts(app.routes)
        for method in route.methods or ()
        if method != "HEAD"
    }

    described = {(method, f"{API_PREFIX}{path}") for method, path in operations(stored)}

    assert served == described


def test_operation_names_are_unique_and_usable_as_function_names(stored: dict[str, Any]) -> None:
    names = [operation["operationId"] for operation in operations(stored).values()]

    assert len(set(names)) == len(names)
    for name in names:
        assert re.fullmatch(r"[a-z][A-Za-z0-9]+", name), name


def test_every_operation_has_a_summary_a_tag_and_a_described_answer(
    stored: dict[str, Any],
) -> None:
    known_tags = {tag["name"] for tag in stored["tags"]}

    for key, operation in operations(stored).items():
        assert operation.get("summary"), key
        assert len(operation["tags"]) == 1, key
        assert operation["tags"][0] in known_tags, key
        for status, response in operation["responses"].items():
            assert response.get("description"), (key, status)


def test_every_closed_operation_documents_the_signed_out_answer(stored: dict[str, Any]) -> None:
    for (method, path), operation in operations(stored).items():
        closed = f"{API_PREFIX}{path}" not in PUBLIC_PATHS
        assert ("401" in operation["responses"]) is closed, (method, path)


def test_every_operation_that_changes_something_documents_the_csrf_refusal(
    stored: dict[str, Any],
) -> None:
    changing = {key for key in operations(stored) if key[0] not in {"GET", "HEAD", "OPTIONS"}}

    assert changing == {
        ("POST", "/audit/verify"),
        ("POST", "/proposals/{proposal_id}/approve"),
        ("POST", "/proposals/{proposal_id}/reject"),
        ("POST", "/strategy-lab/backtests"),
        ("POST", "/strategy-lab/backtests/{run_id}/reviews"),
    }
    for key in changing:
        assert "403" in operations(stored)[key]["responses"], key


def test_every_documented_error_uses_the_one_error_shape(stored: dict[str, Any]) -> None:
    for key, operation in operations(stored).items():
        for status, response in operation["responses"].items():
            if not status.startswith(("4", "5")):
                continue
            schema = response["content"]["application/json"]["schema"]
            assert schema == {"$ref": "#/components/schemas/ErrorResponse"}, (key, status)

    error = stored["components"]["schemas"]["ErrorResponse"]
    assert set(error["properties"]) == {"error", "message", "correlationId", "details"}
    assert error["required"] == ["error", "message", "correlationId"]


def test_no_schema_is_left_unused_or_undefined(stored: dict[str, Any]) -> None:
    defined = set(stored["components"]["schemas"])

    used = references(stored["paths"])
    pending = set(used)
    while pending:
        name = pending.pop()
        for inner in references(stored["components"]["schemas"][name]) - used:
            used.add(inner)
            pending.add(inner)

    assert used == defined


def test_fields_use_camel_case_on_the_wire(stored: dict[str, Any]) -> None:
    for name, schema in stored["components"]["schemas"].items():
        for field in schema.get("properties", {}):
            assert re.fullmatch(r"[a-z][A-Za-z0-9]*", field), (name, field)


def test_object_fields_are_always_present_even_when_they_may_be_empty(
    stored: dict[str, Any],
) -> None:
    """The web app never has to tell a missing field from an empty one."""
    for name, schema in stored["components"]["schemas"].items():
        if "properties" not in schema or name == "ErrorResponse":
            continue
        assert set(schema.get("required", [])) == set(schema["properties"]), name


def test_generated_titles_are_removed_but_real_ones_stay(app: FastAPI) -> None:
    document = build_openapi(app)

    def titles(node: Any, path: str = "") -> list[str]:
        found: list[str] = []
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "title" and isinstance(value, str):
                    found.append(path)
                found += titles(value, f"{path}/{key}")
        elif isinstance(node, list):
            for item in node:
                found += titles(item, path)
        return found

    assert titles(document) == ["/info"]


def test_a_route_outside_the_api_path_cannot_enter_the_contract() -> None:
    app = build_app(load_settings({}))

    @app.get("/outside")
    def outside() -> dict[str, str]:
        return {}

    with pytest.raises(ValueError, match="outside /api"):
        build_openapi(app)


def test_the_app_does_not_serve_the_contract_or_interactive_docs(app: FastAPI) -> None:
    paths = {route.path for route in iter_route_contexts(app.routes)}

    assert not paths & {"/docs", "/redoc", "/openapi.json", "/api/docs", "/api/openapi.json"}
    assert app.openapi_url is None
    assert app.docs_url is None
    assert app.redoc_url is None


# -- the generated web clients follow the contract --------------------------------------------


def test_the_generated_web_client_has_every_operation(stored: dict[str, Any]) -> None:
    client = GENERATED_CLIENT.read_text(encoding="utf-8")

    for operation in operations(stored).values():
        name = operation["operationId"]
        assert re.search(rf"export const {name} = async", client), name
    exported = set(re.findall(r"export const (\w+) = async", client))
    assert exported == set(OPERATIONS.values())


def test_the_generated_types_and_validators_have_every_schema(stored: dict[str, Any]) -> None:
    types = GENERATED_CLIENT_TYPES.read_text(encoding="utf-8")
    validators = GENERATED_VALIDATORS.read_text(encoding="utf-8")

    for name in stored["components"]["schemas"]:
        assert re.search(rf"export (interface|type|const) {name}\b", types), name
    for operation in operations(stored).values():
        name = operation["operationId"]
        assert f"export const {name[0].upper()}{name[1:]}Response = " in validators, name
