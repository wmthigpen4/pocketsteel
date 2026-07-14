"""Durable, privacy-minimized monthly Ask usage for verified accounts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import sqlite3
from typing import Mapping

from pocketsteel.account_copedents import AccountIdentity


ACCOUNT_USAGE_ENABLED_ENV = "STEEL_RAG_ACCOUNT_USAGE_ENABLED"
ACCOUNT_USAGE_DB_PATH_ENV = "STEEL_RAG_ACCOUNT_USAGE_DB_PATH"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class AccountUsageConfigurationError(RuntimeError):
    """Raised when enabled usage storage cannot be configured safely."""


class AccountUsageUnavailableError(RuntimeError):
    """Raised when durable usage storage cannot be read or updated."""


@dataclass(frozen=True)
class MonthlyAnswerUsage:
    starts_at: str
    resets_at: str
    successful_answers: int
    updated_at: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": "account_usage_v1",
            "period": {
                "startsAt": self.starts_at,
                "resetsAt": self.resets_at,
            },
            "usage": {"successfulAnswers": self.successful_answers},
            "updatedAt": self.updated_at,
        }


def _env_flag(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def configured_account_usage_enabled(environ: Mapping[str, object] | None = None) -> bool:
    source = environ if environ is not None else os.environ
    return _env_flag(source.get(ACCOUNT_USAGE_ENABLED_ENV))


def configured_account_usage_path(environ: Mapping[str, object] | None = None) -> Path:
    source = environ if environ is not None else os.environ
    value = str(source.get(ACCOUNT_USAGE_DB_PATH_ENV) or "").strip()
    if not value:
        raise AccountUsageConfigurationError(
            f"{ACCOUNT_USAGE_DB_PATH_ENV} is required when account usage is enabled"
        )
    path = Path(value).expanduser().resolve(strict=False)
    try:
        path.relative_to(REPOSITORY_ROOT)
    except ValueError:
        return path
    raise AccountUsageConfigurationError(
        f"{ACCOUNT_USAGE_DB_PATH_ENV} must point outside the repository"
    )


def pseudonymous_account_key(identity: AccountIdentity) -> str:
    """Return a stable key without retaining identity claims in the usage store."""

    material = "\x1f".join((identity.provider, identity.issuer, identity.subject))
    digest = hashlib.sha256(f"steel-rag-account-usage-v1:{material}".encode("utf-8")).hexdigest()
    return f"account_sha256:{digest}"


def _utc_datetime(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _month_window(value: datetime | None = None) -> tuple[datetime, datetime]:
    current = _utc_datetime(value)
    starts_at = datetime(current.year, current.month, 1, tzinfo=timezone.utc)
    if current.month == 12:
        resets_at = datetime(current.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        resets_at = datetime(current.year, current.month + 1, 1, tzinfo=timezone.utc)
    return starts_at, resets_at


class AccountUsageRepository:
    """SQLite-backed monthly counters with one row per account and UTC month."""

    schema_version = 1

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise AccountUsageConfigurationError(
                "account usage database directory could not be created"
            ) from exc
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("pragma busy_timeout = 5000")
        return connection

    def _migrate(self) -> None:
        try:
            with self._connect() as connection:
                connection.execute("pragma journal_mode = wal")
                connection.executescript(
                    """
                    create table if not exists account_usage_schema (
                        version integer not null
                    );
                    create table if not exists monthly_answer_usage (
                        account_key text not null,
                        period_start text not null,
                        successful_answers integer not null,
                        first_answer_at text not null,
                        last_answer_at text not null,
                        primary key(account_key, period_start)
                    );
                    """
                )
                row = connection.execute("select version from account_usage_schema limit 1").fetchone()
                if row is None:
                    connection.execute(
                        "insert into account_usage_schema(version) values (?)",
                        (self.schema_version,),
                    )
                elif int(row["version"]) != self.schema_version:
                    raise AccountUsageConfigurationError("account usage database schema is unsupported")
        except AccountUsageConfigurationError:
            raise
        except (OSError, sqlite3.Error) as exc:
            raise AccountUsageConfigurationError("account usage database could not be initialized") from exc

    def record_success(
        self,
        identity: AccountIdentity,
        *,
        at: datetime | None = None,
    ) -> MonthlyAnswerUsage:
        current = _utc_datetime(at)
        starts_at, _ = _month_window(current)
        account_key = pseudonymous_account_key(identity)
        timestamp = current.isoformat()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    insert into monthly_answer_usage(
                        account_key, period_start, successful_answers, first_answer_at, last_answer_at
                    ) values (?, ?, 1, ?, ?)
                    on conflict(account_key, period_start) do update set
                        successful_answers = monthly_answer_usage.successful_answers + 1,
                        last_answer_at = excluded.last_answer_at
                    """,
                    (account_key, starts_at.isoformat(), timestamp, timestamp),
                )
        except (OSError, sqlite3.Error) as exc:
            raise AccountUsageUnavailableError("account usage could not be updated") from exc
        return self.current_usage(identity, at=current)

    def current_usage(
        self,
        identity: AccountIdentity,
        *,
        at: datetime | None = None,
    ) -> MonthlyAnswerUsage:
        starts_at, resets_at = _month_window(at)
        account_key = pseudonymous_account_key(identity)
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    select successful_answers, last_answer_at
                    from monthly_answer_usage
                    where account_key = ? and period_start = ?
                    """,
                    (account_key, starts_at.isoformat()),
                ).fetchone()
        except (OSError, sqlite3.Error) as exc:
            raise AccountUsageUnavailableError("account usage could not be read") from exc
        return MonthlyAnswerUsage(
            starts_at=starts_at.isoformat(),
            resets_at=resets_at.isoformat(),
            successful_answers=int(row["successful_answers"]) if row is not None else 0,
            updated_at=str(row["last_answer_at"]) if row is not None else None,
        )
