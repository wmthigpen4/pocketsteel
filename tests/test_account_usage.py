from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pytest

from steel_guitar_rag.account_copedents import AccountIdentity
from steel_guitar_rag.account_usage import (
    ACCOUNT_USAGE_DB_PATH_ENV,
    AccountUsageConfigurationError,
    AccountUsageRepository,
    configured_account_usage_path,
    pseudonymous_account_key,
)


IDENTITY = AccountIdentity(
    provider="cloudflare_access",
    issuer="https://steel.cloudflareaccess.com",
    subject="subject:player@example.test",
)


def test_enabled_usage_requires_an_external_database_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ACCOUNT_USAGE_DB_PATH_ENV, raising=False)

    with pytest.raises(AccountUsageConfigurationError):
        configured_account_usage_path()

    monkeypatch.setenv(ACCOUNT_USAGE_DB_PATH_ENV, str(Path(__file__).resolve().parents[1] / "usage.sqlite3"))
    with pytest.raises(AccountUsageConfigurationError, match="outside the repository"):
        configured_account_usage_path()


def test_monthly_usage_starts_at_zero_and_rolls_over_in_utc(tmp_path: Path) -> None:
    repository = AccountUsageRepository(tmp_path / "usage.sqlite3")
    july = datetime(2026, 7, 31, 23, 59, tzinfo=timezone.utc)
    august = datetime(2026, 8, 1, 0, 0, tzinfo=timezone.utc)

    empty = repository.current_usage(IDENTITY, at=july)
    first = repository.record_success(IDENTITY, at=july)
    next_month = repository.current_usage(IDENTITY, at=august)

    assert empty.successful_answers == 0
    assert empty.updated_at is None
    assert empty.recent_activity is None
    assert empty.recent_connected_route == ()
    assert first.successful_answers == 1
    assert first.starts_at == "2026-07-01T00:00:00+00:00"
    assert first.resets_at == "2026-08-01T00:00:00+00:00"
    assert next_month.successful_answers == 0
    assert next_month.starts_at == "2026-08-01T00:00:00+00:00"


def test_monthly_usage_is_isolated_by_pseudonymous_account(tmp_path: Path) -> None:
    repository = AccountUsageRepository(tmp_path / "usage.sqlite3")
    other = AccountIdentity(IDENTITY.provider, IDENTITY.issuer, "subject:other@example.test")
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

    repository.record_success(IDENTITY, at=now)
    repository.record_success(IDENTITY, at=now)
    repository.record_success(other, at=now)

    assert repository.current_usage(IDENTITY, at=now).successful_answers == 2
    assert repository.current_usage(other, at=now).successful_answers == 1
    assert pseudonymous_account_key(IDENTITY) != pseudonymous_account_key(other)


def test_concurrent_successes_increment_atomically(tmp_path: Path) -> None:
    repository = AccountUsageRepository(tmp_path / "usage.sqlite3")
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda _index: repository.record_success(IDENTITY, at=now), range(40)))

    assert repository.current_usage(IDENTITY, at=now).successful_answers == 40


def test_usage_store_contains_only_aggregate_and_pseudonymous_fields(tmp_path: Path) -> None:
    path = tmp_path / "usage.sqlite3"
    repository = AccountUsageRepository(path)
    repository.record_success(IDENTITY, at=datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc))

    with sqlite3.connect(path) as connection:
        columns = {
            row[1]
            for row in connection.execute("pragma table_info(monthly_answer_usage)")
        }
        row = connection.execute("select * from monthly_answer_usage").fetchone()

    assert columns == {
        "account_key",
        "period_start",
        "successful_answers",
        "first_answer_at",
        "last_answer_at",
    }
    persisted = " ".join(map(str, row))
    assert "player@example.test" not in persisted
    assert "question" not in persisted.lower()
    assert "answer text" not in persisted.lower()
    assert "127.0.0.1" not in persisted


def test_meaningful_activity_is_deduplicated_and_summarized(tmp_path: Path) -> None:
    path = tmp_path / "usage.sqlite3"
    repository = AccountUsageRepository(path)
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

    first = repository.record_activity(
        IDENTITY,
        event_type="explorer.chord_grip_selected",
        event_id="event-grip-0001",
        dedupe_key="g-major-fret-3",
        at=now,
    )
    duplicate_id = repository.record_activity(
        IDENTITY,
        event_type="explorer.chord_grip_selected",
        event_id="event-grip-0001",
        dedupe_key="g-major-fret-3",
        at=now,
    )
    rapid_duplicate = repository.record_activity(
        IDENTITY,
        event_type="explorer.chord_grip_selected",
        event_id="event-grip-0002",
        dedupe_key="g-major-fret-3",
        at=now,
    )

    usage = repository.current_usage(IDENTITY, at=now)
    assert first.recorded is True
    assert duplicate_id.recorded is False
    assert rapid_duplicate.recorded is False
    assert usage.activity["explorer"] == {
        "ideasExplored": 1,
        "chordGrips": 1,
        "scalePaths": 0,
        "movementComparisons": 0,
    }

    with sqlite3.connect(path) as connection:
        persisted = " ".join(
            map(
                str,
                [
                    *connection.execute("select * from monthly_activity_totals").fetchall(),
                    *connection.execute("select * from activity_event_dedupe").fetchall(),
                ],
            )
        )
    assert "g-major-fret-3" not in persisted
    assert "event-grip-0001" not in persisted
    assert "player@example.test" not in persisted


def test_activity_replay_rows_are_pruned_after_the_short_dedupe_window(tmp_path: Path) -> None:
    path = tmp_path / "usage.sqlite3"
    repository = AccountUsageRepository(path)
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
    repository.record_activity(
        IDENTITY,
        event_type="explorer.position_selected",
        event_id="event-position-0001",
        dedupe_key="position-one",
        at=now,
    )
    repository.record_activity(
        IDENTITY,
        event_type="explorer.position_selected",
        event_id="event-position-0002",
        dedupe_key="position-two",
        at=now + timedelta(seconds=90),
    )

    with sqlite3.connect(path) as connection:
        replay_row_count = connection.execute(
            "select count(*) from activity_event_dedupe"
        ).fetchone()[0]
    assert replay_row_count == 1


def test_ai_and_followup_counts_are_server_owned_and_separate(tmp_path: Path) -> None:
    repository = AccountUsageRepository(tmp_path / "usage.sqlite3")
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

    repository.record_success(IDENTITY, at=now)
    repository.record_success(IDENTITY, at=now, is_followup=True, ai_assisted=True)
    usage = repository.current_usage(IDENTITY, at=now)

    assert usage.successful_answers == 2
    assert usage.activity["ask"]["followUps"] == 1
    assert usage.activity["aiAssisted"]["actions"] == 1

    with pytest.raises(ValueError, match="unsupported"):
        repository.record_activity(
            IDENTITY,
            event_type="ask.ai_assisted",
            event_id="spoofed-ai-event",
            dedupe_key="spoofed",
            at=now,
        )


def test_connected_learning_requires_a_whitelisted_transition(tmp_path: Path) -> None:
    repository = AccountUsageRepository(tmp_path / "usage.sqlite3")
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

    repository.record_activity(
        IDENTITY,
        event_type="connected.lesson_to_explorer",
        event_id="lesson-link-event",
        dedupe_key="lesson:f-lever:explorer",
        at=now,
    )
    usage = repository.current_usage(IDENTITY, at=now)
    assert usage.activity["connectedLearning"]["transitions"] == 1
    assert usage.activity["connectedLearning"]["lessonsContinued"] == 1


def test_recent_activity_and_route_are_derived_from_persisted_aggregate_timestamps(tmp_path: Path) -> None:
    repository = AccountUsageRepository(tmp_path / "usage.sqlite3")
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
    repository.record_success(IDENTITY, at=now)
    repository.record_activity(
        IDENTITY,
        event_type="connected.answer_to_explorer",
        event_id="answer-to-explorer",
        dedupe_key="answer-to-explorer",
        at=now + timedelta(minutes=1),
    )
    repository.record_activity(
        IDENTITY,
        event_type="melody.edited",
        event_id="melody-edited",
        dedupe_key="melody-edited",
        at=now + timedelta(minutes=2),
    )
    repository.record_activity(
        IDENTITY,
        event_type="connected.explorer_to_melody",
        event_id="explorer-to-melody",
        dedupe_key="explorer-to-melody",
        at=now + timedelta(minutes=3),
    )

    payload = repository.current_usage(IDENTITY, at=now).to_dict()
    assert payload["usage"]["recentActivity"] == {
        "eventType": "connected.explorer_to_melody",
        "occurredAt": "2026-07-14T12:03:00+00:00",
        "count": 1,
    }
    assert [item["eventType"] for item in payload["usage"]["recentConnectedRoute"]] == [
        "connected.answer_to_explorer",
        "connected.explorer_to_melody",
    ]
    assert "answer-to-explorer" not in str(payload)
    assert "melody-edited" not in str(payload)


def test_schema_one_usage_database_migrates_without_losing_answer_counts(tmp_path: Path) -> None:
    path = tmp_path / "usage.sqlite3"
    account_key = pseudonymous_account_key(IDENTITY)
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            create table account_usage_schema (version integer not null);
            insert into account_usage_schema(version) values (1);
            create table monthly_answer_usage (
                account_key text not null,
                period_start text not null,
                successful_answers integer not null,
                first_answer_at text not null,
                last_answer_at text not null,
                primary key(account_key, period_start)
            );
            """
        )
        connection.execute(
            "insert into monthly_answer_usage values (?, ?, 7, ?, ?)",
            (
                account_key,
                "2026-07-01T00:00:00+00:00",
                "2026-07-02T00:00:00+00:00",
                "2026-07-03T00:00:00+00:00",
            ),
        )

    repository = AccountUsageRepository(path)
    usage = repository.current_usage(
        IDENTITY,
        at=datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc),
    )
    assert usage.successful_answers == 7
    assert usage.activity["aiAssisted"]["actions"] == 0

    with sqlite3.connect(path) as connection:
        version = connection.execute("select version from account_usage_schema").fetchone()[0]
    assert version == 2
