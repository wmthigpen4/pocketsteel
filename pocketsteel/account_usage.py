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
ACTIVITY_DEDUPE_WINDOW_SECONDS = 30

# Client-recordable events are deliberately bounded. Server-owned Ask events are
# recorded through record_success() and cannot be submitted by a browser.
PUBLIC_ACTIVITY_EVENT_TYPES = frozenset(
    {
        "explorer.position_selected",
        "explorer.chord_grip_selected",
        "explorer.scale_path_selected",
        "explorer.movement_compared",
        "melody.session_started",
        "melody.edited",
        "melody.playback_completed",
        "lesson.started",
        "lesson.section_completed",
        "lesson.exercise_completed",
        "connected.answer_to_explorer",
        "connected.lesson_to_explorer",
        "connected.lesson_to_melody",
        "connected.explorer_to_melody",
    }
)
SERVER_ACTIVITY_EVENT_TYPES = frozenset({"ask.followup", "ask.ai_assisted"})
ALL_ACTIVITY_EVENT_TYPES = PUBLIC_ACTIVITY_EVENT_TYPES | SERVER_ACTIVITY_EVENT_TYPES

EMPTY_ACTIVITY = {
    "explorer": {
        "ideasExplored": 0,
        "chordGrips": 0,
        "scalePaths": 0,
        "movementComparisons": 0,
    },
    "melodyStudio": {
        "sessions": 0,
        "melodiesEdited": 0,
        "playbacksCompleted": 0,
    },
    "lessons": {
        "lessonsPracticed": 0,
        "sectionsCompleted": 0,
        "exercisesExplored": 0,
    },
    "ask": {
        "followUps": 0,
        "answersOpenedInExplorer": 0,
    },
    "connectedLearning": {
        "transitions": 0,
        "answersOpenedInExplorer": 0,
        "lessonsContinued": 0,
        "ideasCarriedToMelody": 0,
    },
    "aiAssisted": {"actions": 0},
}


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
    activity: dict[str, dict[str, int]]
    recent_activity: dict[str, object] | None
    recent_connected_route: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": "account_usage_v1",
            "period": {
                "startsAt": self.starts_at,
                "resetsAt": self.resets_at,
            },
            "usage": {
                "successfulAnswers": self.successful_answers,
                "activity": self.activity,
                "aiAssistedActions": self.activity["aiAssisted"]["actions"],
                "recentActivity": self.recent_activity,
                "recentConnectedRoute": list(self.recent_connected_route),
            },
            "updatedAt": self.updated_at,
        }


@dataclass(frozen=True)
class ActivityRecordResult:
    recorded: bool
    event_type: str


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
    """SQLite-backed monthly counters and bounded meaningful product activity."""

    schema_version = 2

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
                    create table if not exists monthly_activity_totals (
                        account_key text not null,
                        period_start text not null,
                        event_type text not null,
                        event_count integer not null,
                        first_event_at text not null,
                        last_event_at text not null,
                        primary key(account_key, period_start, event_type)
                    );
                    create table if not exists activity_event_dedupe (
                        account_key text not null,
                        event_id_hash text not null,
                        event_type text not null,
                        dedupe_hash text not null,
                        dedupe_bucket integer not null,
                        recorded_at text not null,
                        primary key(account_key, event_id_hash),
                        unique(account_key, event_type, dedupe_hash, dedupe_bucket)
                    );
                    """
                )
                row = connection.execute("select version from account_usage_schema limit 1").fetchone()
                if row is None:
                    connection.execute(
                        "insert into account_usage_schema(version) values (?)",
                        (self.schema_version,),
                    )
                elif int(row["version"]) == 1:
                    connection.execute(
                        "update account_usage_schema set version = ?",
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
        is_followup: bool = False,
        ai_assisted: bool = False,
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
                if is_followup:
                    self._increment_event_total(
                        connection,
                        account_key,
                        starts_at.isoformat(),
                        "ask.followup",
                        timestamp,
                    )
                if ai_assisted:
                    self._increment_event_total(
                        connection,
                        account_key,
                        starts_at.isoformat(),
                        "ask.ai_assisted",
                        timestamp,
                    )
        except (OSError, sqlite3.Error) as exc:
            raise AccountUsageUnavailableError("account usage could not be updated") from exc
        return self.current_usage(identity, at=current)

    @staticmethod
    def _increment_event_total(
        connection: sqlite3.Connection,
        account_key: str,
        period_start: str,
        event_type: str,
        timestamp: str,
    ) -> None:
        connection.execute(
            """
            insert into monthly_activity_totals(
                account_key, period_start, event_type, event_count, first_event_at, last_event_at
            ) values (?, ?, ?, 1, ?, ?)
            on conflict(account_key, period_start, event_type) do update set
                event_count = monthly_activity_totals.event_count + 1,
                last_event_at = excluded.last_event_at
            """,
            (account_key, period_start, event_type, timestamp, timestamp),
        )

    def record_activity(
        self,
        identity: AccountIdentity,
        *,
        event_type: str,
        event_id: str,
        dedupe_key: str,
        at: datetime | None = None,
    ) -> ActivityRecordResult:
        if event_type not in PUBLIC_ACTIVITY_EVENT_TYPES:
            raise ValueError("unsupported account activity event")
        current = _utc_datetime(at)
        starts_at, _ = _month_window(current)
        account_key = pseudonymous_account_key(identity)
        timestamp = current.isoformat()
        event_id_hash = hashlib.sha256(
            f"activity-event-v1:{event_id}".encode("utf-8")
        ).hexdigest()
        dedupe_hash = hashlib.sha256(
            f"activity-dedupe-v1:{dedupe_key}".encode("utf-8")
        ).hexdigest()
        dedupe_bucket = int(current.timestamp()) // ACTIVITY_DEDUPE_WINDOW_SECONDS
        try:
            with self._connect() as connection:
                # Keep only the short replay-protection window. Monthly reporting
                # is aggregate-only; it does not retain an event-by-event history.
                connection.execute(
                    "delete from activity_event_dedupe where dedupe_bucket < ?",
                    (dedupe_bucket - 1,),
                )
                cursor = connection.execute(
                    """
                    insert or ignore into activity_event_dedupe(
                        account_key, event_id_hash, event_type, dedupe_hash, dedupe_bucket, recorded_at
                    ) values (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        account_key,
                        event_id_hash,
                        event_type,
                        dedupe_hash,
                        dedupe_bucket,
                        timestamp,
                    ),
                )
                recorded = cursor.rowcount == 1
                if recorded:
                    self._increment_event_total(
                        connection,
                        account_key,
                        starts_at.isoformat(),
                        event_type,
                        timestamp,
                    )
        except (OSError, sqlite3.Error) as exc:
            raise AccountUsageUnavailableError("account activity could not be updated") from exc
        return ActivityRecordResult(recorded=recorded, event_type=event_type)

    @staticmethod
    def _activity_summary(rows: list[sqlite3.Row]) -> dict[str, dict[str, int]]:
        counts = {str(row["event_type"]): int(row["event_count"]) for row in rows}
        activity = {section: dict(values) for section, values in EMPTY_ACTIVITY.items()}

        explorer_types = {
            "explorer.position_selected",
            "explorer.chord_grip_selected",
            "explorer.scale_path_selected",
            "explorer.movement_compared",
        }
        activity["explorer"]["ideasExplored"] = sum(counts.get(item, 0) for item in explorer_types)
        activity["explorer"]["chordGrips"] = counts.get("explorer.chord_grip_selected", 0)
        activity["explorer"]["scalePaths"] = counts.get("explorer.scale_path_selected", 0)
        activity["explorer"]["movementComparisons"] = counts.get("explorer.movement_compared", 0)
        activity["melodyStudio"]["sessions"] = counts.get("melody.session_started", 0)
        activity["melodyStudio"]["melodiesEdited"] = counts.get("melody.edited", 0)
        activity["melodyStudio"]["playbacksCompleted"] = counts.get("melody.playback_completed", 0)
        activity["lessons"]["lessonsPracticed"] = counts.get("lesson.started", 0)
        activity["lessons"]["sectionsCompleted"] = counts.get("lesson.section_completed", 0)
        activity["lessons"]["exercisesExplored"] = counts.get("lesson.exercise_completed", 0)
        activity["ask"]["followUps"] = counts.get("ask.followup", 0)
        activity["ask"]["answersOpenedInExplorer"] = counts.get("connected.answer_to_explorer", 0)
        connected_types = {
            "connected.answer_to_explorer",
            "connected.lesson_to_explorer",
            "connected.lesson_to_melody",
            "connected.explorer_to_melody",
        }
        activity["connectedLearning"]["transitions"] = sum(
            counts.get(item, 0) for item in connected_types
        )
        activity["connectedLearning"]["answersOpenedInExplorer"] = counts.get(
            "connected.answer_to_explorer", 0
        )
        activity["connectedLearning"]["lessonsContinued"] = (
            counts.get("connected.lesson_to_explorer", 0)
            + counts.get("connected.lesson_to_melody", 0)
        )
        activity["connectedLearning"]["ideasCarriedToMelody"] = (
            counts.get("connected.lesson_to_melody", 0)
            + counts.get("connected.explorer_to_melody", 0)
        )
        activity["aiAssisted"]["actions"] = counts.get("ask.ai_assisted", 0)
        return activity

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
                activity_rows = connection.execute(
                    """
                    select event_type, event_count, last_event_at
                    from monthly_activity_totals
                    where account_key = ? and period_start = ?
                    """,
                    (account_key, starts_at.isoformat()),
                ).fetchall()
        except (OSError, sqlite3.Error) as exc:
            raise AccountUsageUnavailableError("account usage could not be read") from exc
        updated_candidates = [
            str(row["last_answer_at"]) if row is not None else "",
            *[str(item["last_event_at"]) for item in activity_rows],
        ]
        recent_candidates = [
            {
                "eventType": str(item["event_type"]),
                "occurredAt": str(item["last_event_at"]),
                "count": int(item["event_count"]),
            }
            for item in activity_rows
        ]
        if row is not None:
            recent_candidates.append(
                {
                    "eventType": "ask.answer",
                    "occurredAt": str(row["last_answer_at"]),
                    "count": int(row["successful_answers"]),
                }
            )
        recent_activity = max(
            recent_candidates,
            key=lambda item: str(item["occurredAt"]),
            default=None,
        )
        connected_route = sorted(
            (
                item
                for item in recent_candidates
                if str(item["eventType"]).startswith("connected.")
            ),
            key=lambda item: str(item["occurredAt"]),
        )[-3:]
        return MonthlyAnswerUsage(
            starts_at=starts_at.isoformat(),
            resets_at=resets_at.isoformat(),
            successful_answers=int(row["successful_answers"]) if row is not None else 0,
            updated_at=max(filter(None, updated_candidates), default=None),
            activity=self._activity_summary(activity_rows),
            recent_activity=recent_activity,
            recent_connected_route=tuple(connected_route),
        )
