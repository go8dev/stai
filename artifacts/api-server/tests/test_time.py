"""Time rules: stored and computed in UTC, shown in Asia/Manila."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import Engine, select, text
from sqlalchemy.exc import StatementError

from stai.core.time import DISPLAY_TIMEZONE, MANILA, as_utc, utcnow
from stai.db.base import UtcDateTime
from stai.db.models import User
from stai.db.session import Database

MANILA_OFFSET = timezone(timedelta(hours=8))
NEW_YORK_WINTER = timezone(timedelta(hours=-5))


def test_now_is_utc_and_carries_its_time_zone() -> None:
    now = utcnow()

    assert now.tzinfo is UTC
    assert abs(now - datetime.now(UTC)) < timedelta(seconds=5)


def test_a_time_in_another_zone_becomes_the_same_instant_in_utc() -> None:
    manila = datetime(2026, 11, 18, 4, 30, tzinfo=MANILA_OFFSET)

    converted = as_utc(manila)

    assert converted == manila
    assert converted.utcoffset() == timedelta(0)
    assert converted.isoformat() == "2026-11-17T20:30:00+00:00"


def test_a_time_without_a_zone_is_refused_not_guessed() -> None:
    with pytest.raises(ValueError, match="naive"):
        as_utc(datetime(2026, 11, 17, 20, 30))  # noqa: DTZ001


def test_the_display_zone_is_manila_eight_hours_ahead_all_year() -> None:
    assert DISPLAY_TIMEZONE == "Asia/Manila"
    for month in (1, 4, 7, 10):
        local = datetime(2026, month, 15, 12, 0, tzinfo=UTC).astimezone(MANILA)
        assert local.utcoffset() == timedelta(hours=8)
        assert local.hour == 20


def add_user(database: Database, user_id: str, moment: datetime) -> None:
    with database.session() as session:
        session.add(User(id=user_id, created_at=moment, updated_at=moment))


def test_stored_times_come_back_in_utc_whatever_zone_they_were_given_in(
    database: Database,
) -> None:
    instant = datetime(2026, 11, 17, 20, 30, 15, 123456, tzinfo=UTC)
    add_user(database, "manila", instant.astimezone(MANILA_OFFSET))
    add_user(database, "new-york", instant.astimezone(NEW_YORK_WINTER))
    add_user(database, "utc", instant)

    with database.session() as session:
        stored = session.execute(select(User.id, User.created_at)).all()

    assert len(stored) == 3
    for row in stored:
        assert row.created_at == instant
        assert row.created_at.utcoffset() == timedelta(0)
        assert row.created_at.microsecond == 123456


def test_a_time_without_a_zone_cannot_be_stored(database: Database, admin: Engine) -> None:
    naive = datetime(2026, 11, 17, 20, 30)  # noqa: DTZ001

    with pytest.raises(StatementError, match="naive datetime"):
        add_user(database, "naive", naive)

    with admin.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM users")).scalar_one() == 0


def test_an_empty_time_stays_empty(database: Database) -> None:
    add_user(database, "never-signed-in", utcnow())

    with database.session() as session:
        assert session.execute(select(User.last_login_at)).scalar_one() is None


def test_reading_is_utc_even_when_the_connection_uses_another_zone(
    database: Database, admin: Engine
) -> None:
    instant = datetime(2026, 11, 17, 20, 30, tzinfo=UTC)
    add_user(database, "u1", instant)

    with database.session() as session:
        session.execute(text("SET LOCAL TIME ZONE 'Asia/Manila'"))
        shown = session.execute(text("SELECT created_at::text FROM users")).scalar_one()
        stored = session.execute(select(User.created_at)).scalar_one()

    # PostgreSQL would display it in Manila time; the application still gets UTC.
    assert shown == "2026-11-18 04:30:00+08"
    assert stored == instant
    assert stored.utcoffset() == timedelta(0)


def test_the_column_type_handles_each_kind_of_value_on_its_own() -> None:
    column_type = UtcDateTime()
    instant = datetime(2026, 11, 17, 20, 30, tzinfo=UTC)

    assert column_type.process_bind_param(None, None) is None
    assert column_type.process_result_value(None, None) is None
    assert column_type.process_bind_param(instant.astimezone(MANILA_OFFSET), None) == instant
    assert column_type.process_bind_param(instant.astimezone(MANILA_OFFSET), None).tzinfo is UTC
    assert column_type.process_result_value(instant.astimezone(MANILA_OFFSET), None).tzinfo is UTC
    # A driver that hands back a value without a zone is taken to mean UTC.
    assert column_type.process_result_value(instant.replace(tzinfo=None), None) == instant
    with pytest.raises(ValueError, match="naive"):
        column_type.process_bind_param(instant.replace(tzinfo=None), None)
