"""No secret or personal value of this environment is written anywhere in the project.

This is the one module that looks at real values from the environment. It never prints
them: a failure names the variable and the file, nothing else.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from stai.core.config import secret_values_from_environment

from .conftest import REPO_ROOT

# Directories that are not part of the project's files: dependencies, caches and
# platform state. Everything else is read, whether Git tracks it yet or not.
SKIPPED_DIRECTORIES = {
    ".git",
    "node_modules",
    ".pythonlibs",
    ".venv",
    ".cache",
    ".local",
    ".config",
    ".upm",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "generated-artifacts",
}

# Variables whose value identifies the owner. Not secrets, but not for files either.
PERSONAL_VARIABLES = ("REPL_OWNER_ID",)

MIN_LENGTH = 6
# A short value made only of letters is an ordinary word. It appears in normal text, so
# finding it proves nothing. A development database password can be such a word; the
# connection details that contain it are looked for instead.
MIN_WORD_LENGTH = 12


def worth_looking_for(value: str) -> bool:
    if len(value) < MIN_LENGTH:
        return False
    return not (value.isalpha() and len(value) < MIN_WORD_LENGTH)


def connection_details(url: str) -> list[str]:
    """`user:password@host` of a database address, however the rest of it is written."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return []
    return [parts.netloc] if parts.password else []


def project_files() -> list[Path]:
    found: list[Path] = []
    for directory, directories, files in os.walk(REPO_ROOT):
        directories[:] = [name for name in directories if name not in SKIPPED_DIRECTORIES]
        found += [Path(directory) / name for name in files]
    return sorted(found)


def values_to_look_for() -> dict[str, list[bytes]]:
    """Variable name -> the forms of its value that must not appear in a file."""
    wanted: dict[str, list[bytes]] = {}
    for name, value in os.environ.items():
        values = secret_values_from_environment({name: value})
        if name in PERSONAL_VARIABLES:
            values.append(value)
        if name == "DATABASE_URL":
            values += connection_details(value)
        forms = [item.encode("utf-8") for item in values if worth_looking_for(item)]
        if forms:
            wanted[name] = forms
    return wanted


def files_holding_a_real_value() -> list[str]:
    """`<path> holds the value of <VARIABLE>`. The values themselves stay in here."""
    wanted = values_to_look_for()
    findings: list[str] = []
    for path in project_files():
        try:
            data = path.read_bytes()
        except OSError:
            continue
        for name, forms in wanted.items():
            if any(form in data for form in forms):
                findings.append(f"{path.relative_to(REPO_ROOT)} holds the value of {name}")
    return findings


def test_the_scan_covers_the_project_and_knows_what_to_look_for() -> None:
    names = {str(path.relative_to(REPO_ROOT)) for path in project_files()}

    for expected in (
        ".replit",
        "replit.md",
        "pyproject.toml",
        "docs/example.env",
        "docs/ENVIRONMENT.md",
        "artifacts/api-server/stai/main.py",
        "artifacts/api-server/tests/test_no_real_values.py",
        "artifacts/stai/src/App.tsx",
        "lib/api-spec/openapi.yaml",
        ".agents/memory/MEMORY.md",
    ):
        assert expected in names, expected
    assert not [name for name in names if "node_modules/" in name or name.startswith(".git/")]
    # The database address is always there, because these tests cannot run without it.
    assert "DATABASE_URL" in values_to_look_for()


def test_the_scan_finds_a_value_that_is_written_down(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STAI_TEST_ONLY_API_KEY", "made-up-value-for-this-test")
    (tmp_path / "notes.txt").write_text("key: made-up-value-for-this-test\n", encoding="utf-8")
    (tmp_path / "clean.txt").write_text("nothing here\n", encoding="utf-8")
    monkeypatch.setattr(f"{__name__}.REPO_ROOT", tmp_path)

    assert files_holding_a_real_value() == ["notes.txt holds the value of STAI_TEST_ONLY_API_KEY"]


def test_the_connection_details_of_a_database_address_are_found_in_any_spelling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://stai:secret@db.internal:5432/stai")
    (tmp_path / "config.ini").write_text(
        "url = postgresql+psycopg://stai:secret@db.internal:5432/stai?sslmode=require\n",
        encoding="utf-8",
    )
    (tmp_path / "prose.md").write_text("Keep every secret in Replit Secrets.\n", encoding="utf-8")
    monkeypatch.setattr(f"{__name__}.REPO_ROOT", tmp_path)

    assert files_holding_a_real_value() == ["config.ini holds the value of DATABASE_URL"]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", False),
        ("abc12", False),
        ("secret", False),
        ("password", False),
        ("elevenchars", False),
        ("twelve-chars", True),
        ("twelvelettrs", True),
        ("123456", True),
        ("a@b.co", True),
        ("sk-made-up-value", True),
    ],
)
def test_ordinary_short_words_are_not_treated_as_evidence(value: str, expected: bool) -> None:
    assert worth_looking_for(value) is expected


def test_no_file_in_the_project_holds_a_secret_or_personal_value() -> None:
    assert files_holding_a_real_value() == []
