from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

import pytest

from pocketsteel.account_copedents import AccountIdentity
from pocketsteel.account_usage import (
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
