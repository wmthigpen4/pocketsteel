"""Account identity, entitlements, and durable copedent profile storage.

The browser may cache or import profiles, but this module is the authority for
ownership, revisions, active selection, and paid custom-copedent capabilities.
Profile records are deterministic user context and never retrieval evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Mapping
from uuid import uuid4

from steel_guitar_rag.cloudflare_access import parse_email_set
from steel_guitar_rag.copedent_transfer import custom_e9_profile_from_payload
from steel_guitar_rag.e9_copedents import DAY_COPEDENT_ID, DEFAULT_COPEDENT_ID


ACCOUNT_COPEDENTS_ENABLED_ENV = "STEEL_RAG_ACCOUNT_COPEDENTS_ENABLED"
ACCOUNT_COPEDENTS_DB_PATH_ENV = "STEEL_RAG_ACCOUNT_COPEDENTS_DB_PATH"
CREATOR_EMAILS_ENV = "STEEL_RAG_CREATOR_EMAILS"
SESSION_PASS_EMAILS_ENV = "STEEL_RAG_SESSION_PASS_EMAILS"

COMMON_USE = "copedent.common.use"
CUSTOM_MANAGE = "copedent.custom.manage"
CUSTOM_USE = "copedent.custom.use"

COMMON_PROFILE_IDS = frozenset((DEFAULT_COPEDENT_ID, DAY_COPEDENT_ID))
CUSTOM_ENTITLEMENTS = frozenset((COMMON_USE, CUSTOM_MANAGE, CUSTOM_USE))
COMMON_ENTITLEMENTS = frozenset((COMMON_USE,))

PASS_LABELS = {
    "standing_room": "Standing Room",
    "dance_hall": "Dance Hall Pass",
    "session": "Session Pass",
    "headliner": "Headliner Pass",
    "creator": "Creator Access",
    "bandleader": "Bandleader Pass",
}


def entitlements_for_pass(pass_id: str) -> frozenset[str]:
    normalized = str(pass_id or "standing_room").strip().lower()
    if normalized in {"session", "headliner", "creator", "bandleader"}:
        return CUSTOM_ENTITLEMENTS
    if normalized == "dance_hall":
        return COMMON_ENTITLEMENTS
    return frozenset()


class AccountCopedentError(ValueError):
    """Base error for safe account-copedent responses."""


class AccountConfigurationError(RuntimeError):
    """Raised when enabled account storage cannot fail closed."""


class EntitlementRequiredError(AccountCopedentError):
    def __init__(self, message: str, required_entitlement: str = CUSTOM_MANAGE) -> None:
        super().__init__(message)
        self.required_entitlement = required_entitlement


class AccountProfileNotFoundError(AccountCopedentError):
    pass


class AccountProfileConflictError(AccountCopedentError):
    pass


@dataclass(frozen=True)
class AccountIdentity:
    provider: str
    issuer: str
    subject: str


@dataclass(frozen=True)
class AccountAccess:
    identity: AccountIdentity
    pass_id: str
    pass_label: str
    entitlements: frozenset[str]
    source: str

    def allows(self, entitlement: str) -> bool:
        return entitlement in self.entitlements

    def session_payload(self, account_id: str) -> dict[str, object]:
        return {
            "id": account_id,
            "passId": self.pass_id,
            "passLabel": self.pass_label,
            "entitlementSource": self.source,
            "billingManaged": False,
        }


def _env_flag(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def configured_account_copedents_enabled(environ: Mapping[str, object] | None = None) -> bool:
    source = environ if environ is not None else os.environ
    return _env_flag(source.get(ACCOUNT_COPEDENTS_ENABLED_ENV))


def configured_account_copedents_path(environ: Mapping[str, object] | None = None) -> Path:
    source = environ if environ is not None else os.environ
    value = str(source.get(ACCOUNT_COPEDENTS_DB_PATH_ENV) or "").strip()
    if not value:
        raise AccountConfigurationError(
            f"{ACCOUNT_COPEDENTS_DB_PATH_ENV} is required when account copedents are enabled"
        )
    return Path(value).expanduser()


def account_access_for_decision(
    decision: Any,
    *,
    environ: Mapping[str, object] | None = None,
) -> AccountAccess | None:
    """Derive product entitlements only from an already verified identity."""

    if not bool(getattr(decision, "allowed", False)):
        return None
    subject = str(getattr(decision, "identity_subject", "") or "").strip()
    issuer = str(getattr(decision, "identity_issuer", "") or "").strip()
    provider = str(getattr(decision, "identity_provider", "") or "").strip()
    if not subject or not issuer or not provider:
        return None
    identity = AccountIdentity(provider=provider, issuer=issuer, subject=subject)
    email = str(getattr(decision, "identity_email", "") or "").strip().lower()
    role = str(getattr(decision, "role", "") or "").strip().lower()
    source = environ if environ is not None else os.environ
    if email and email in parse_email_set(source.get(CREATOR_EMAILS_ENV)):
        pass_id = "creator"
        entitlement_source = "creator_grant"
    elif role == "admin":
        pass_id = "bandleader"
        entitlement_source = "admin_role"
    elif email and email in parse_email_set(source.get(SESSION_PASS_EMAILS_ENV)):
        pass_id = "session"
        entitlement_source = "beta_grant"
    else:
        pass_id = "dance_hall"
        entitlement_source = "free_account"
    entitlements = entitlements_for_pass(pass_id)
    return AccountAccess(
        identity=identity,
        pass_id=pass_id,
        pass_label=PASS_LABELS[pass_id],
        entitlements=entitlements,
        source=entitlement_source,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_payload(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class AccountCopedentRepository:
    """Small SQLite repository with strict per-account ownership boundaries."""

    schema_version = 1

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("pragma foreign_keys = on")
        connection.execute("pragma busy_timeout = 5000")
        return connection

    def _migrate(self) -> None:
        with self._connect() as connection:
            connection.execute("pragma journal_mode = wal")
            connection.executescript(
                """
                create table if not exists account_schema (
                    version integer not null
                );
                create table if not exists accounts (
                    id text primary key,
                    provider text not null,
                    issuer text not null,
                    subject text not null,
                    pass_id text not null,
                    pass_source text not null,
                    created_at text not null,
                    updated_at text not null,
                    unique(provider, issuer, subject)
                );
                create table if not exists account_copedent_profiles (
                    id text primary key,
                    account_id text not null references accounts(id) on delete cascade,
                    revision integer not null,
                    name text not null,
                    validation_status text not null,
                    payload_json text not null,
                    created_at text not null,
                    updated_at text not null
                );
                create index if not exists account_copedent_owner_idx
                    on account_copedent_profiles(account_id, updated_at);
                create table if not exists account_copedent_preferences (
                    account_id text primary key references accounts(id) on delete cascade,
                    active_profile_id text not null,
                    last_common_profile_id text not null,
                    updated_at text not null
                );
                """
            )
            row = connection.execute("select version from account_schema limit 1").fetchone()
            if row is None:
                connection.execute("insert into account_schema(version) values (?)", (self.schema_version,))
            elif int(row["version"]) != self.schema_version:
                raise AccountConfigurationError("account copedent database schema is unsupported")

    def ensure_account(self, access: AccountAccess) -> str:
        now = _utc_now()
        with self._connect() as connection:
            row = connection.execute(
                "select id from accounts where provider = ? and issuer = ? and subject = ?",
                (access.identity.provider, access.identity.issuer, access.identity.subject),
            ).fetchone()
            if row is None:
                account_id = f"acct_{uuid4().hex}"
                connection.execute(
                    """insert into accounts
                    (id, provider, issuer, subject, pass_id, pass_source, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        account_id,
                        access.identity.provider,
                        access.identity.issuer,
                        access.identity.subject,
                        access.pass_id,
                        access.source,
                        now,
                        now,
                    ),
                )
                connection.execute(
                    """insert into account_copedent_preferences
                    (account_id, active_profile_id, last_common_profile_id, updated_at)
                    values (?, ?, ?, ?)""",
                    (account_id, DEFAULT_COPEDENT_ID, DEFAULT_COPEDENT_ID, now),
                )
                return account_id
            account_id = str(row["id"])
            connection.execute(
                "update accounts set pass_id = ?, pass_source = ?, updated_at = ? where id = ?",
                (access.pass_id, access.source, now, account_id),
            )
            return account_id

    def account_bundle(self, access: AccountAccess) -> dict[str, object]:
        account_id = self.ensure_account(access)
        with self._connect() as connection:
            preference = connection.execute(
                "select active_profile_id, last_common_profile_id from account_copedent_preferences where account_id = ?",
                (account_id,),
            ).fetchone()
            rows = connection.execute(
                """select id, revision, name, validation_status, payload_json, created_at, updated_at
                from account_copedent_profiles where account_id = ? order by updated_at, id""",
                (account_id,),
            ).fetchall()
        profiles = [self._profile_row(row) for row in rows]
        requested_active = str(preference["active_profile_id"] if preference else DEFAULT_COPEDENT_ID)
        last_common = str(preference["last_common_profile_id"] if preference else DEFAULT_COPEDENT_ID)
        custom_ids = {str(profile["id"]) for profile in profiles}
        locked_active = ""
        if requested_active in custom_ids and not access.allows(CUSTOM_USE):
            locked_active = requested_active
            effective_active = last_common if last_common in COMMON_PROFILE_IDS else DEFAULT_COPEDENT_ID
        elif requested_active in COMMON_PROFILE_IDS or requested_active in custom_ids:
            effective_active = requested_active
        else:
            effective_active = DEFAULT_COPEDENT_ID
        return {
            "schemaVersion": "account_copedents_v1",
            "account": access.session_payload(account_id),
            "entitlements": sorted(access.entitlements),
            "activeProfileId": effective_active,
            "requestedActiveProfileId": requested_active,
            "lastCommonProfileId": last_common,
            "lockedActiveProfileId": locked_active or None,
            "profiles": profiles,
        }

    @staticmethod
    def _profile_row(row: sqlite3.Row) -> dict[str, object]:
        payload = json.loads(str(row["payload_json"]))
        payload.update(
            {
                "id": str(row["id"]),
                "revision": int(row["revision"]),
                "name": str(row["name"]),
                "label": str(row["name"]),
                "validationStatus": str(row["validation_status"]),
                "origin": "account_custom",
                "createdAt": str(row["created_at"]),
                "updatedAt": str(row["updated_at"]),
            }
        )
        return payload

    def create_profile(self, access: AccountAccess, snapshot: Mapping[str, Any]) -> dict[str, object]:
        if not access.allows(CUSTOM_MANAGE):
            raise EntitlementRequiredError("Session Pass is required to save a custom copedent.")
        account_id = self.ensure_account(access)
        profile_id = f"saved:account-e9-{uuid4().hex}"
        now = _utc_now()
        stored = self._validated_snapshot(snapshot, profile_id=profile_id, revision=1)
        with self._connect() as connection:
            connection.execute(
                """insert into account_copedent_profiles
                (id, account_id, revision, name, validation_status, payload_json, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile_id,
                    account_id,
                    1,
                    stored["name"],
                    stored["validationStatus"],
                    _json_payload(stored),
                    now,
                    now,
                ),
            )
        return {**stored, "createdAt": now, "updatedAt": now}

    def update_profile(
        self,
        access: AccountAccess,
        profile_id: str,
        snapshot: Mapping[str, Any],
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        if not access.allows(CUSTOM_MANAGE):
            raise EntitlementRequiredError("Session Pass is required to edit a custom copedent.")
        account_id = self.ensure_account(access)
        with self._connect() as connection:
            row = connection.execute(
                "select revision, created_at from account_copedent_profiles where id = ? and account_id = ?",
                (profile_id, account_id),
            ).fetchone()
            if row is None:
                raise AccountProfileNotFoundError("Custom copedent was not found.")
            if int(row["revision"]) != int(expected_revision):
                raise AccountProfileConflictError("This copedent changed on another device. Reload before saving again.")
            revision = int(row["revision"]) + 1
            stored = self._validated_snapshot(snapshot, profile_id=profile_id, revision=revision)
            now = _utc_now()
            connection.execute(
                """update account_copedent_profiles set revision = ?, name = ?, validation_status = ?,
                payload_json = ?, updated_at = ? where id = ? and account_id = ?""",
                (
                    revision,
                    stored["name"],
                    stored["validationStatus"],
                    _json_payload(stored),
                    now,
                    profile_id,
                    account_id,
                ),
            )
        return {**stored, "createdAt": str(row["created_at"]), "updatedAt": now}

    def delete_profile(self, access: AccountAccess, profile_id: str) -> None:
        account_id = self.ensure_account(access)
        with self._connect() as connection:
            row = connection.execute(
                "select 1 from account_copedent_profiles where id = ? and account_id = ?",
                (profile_id, account_id),
            ).fetchone()
            if row is None:
                raise AccountProfileNotFoundError("Custom copedent was not found.")
            connection.execute(
                "delete from account_copedent_profiles where id = ? and account_id = ?",
                (profile_id, account_id),
            )
            preference = connection.execute(
                "select active_profile_id, last_common_profile_id from account_copedent_preferences where account_id = ?",
                (account_id,),
            ).fetchone()
            if preference and str(preference["active_profile_id"]) == profile_id:
                fallback = str(preference["last_common_profile_id"] or DEFAULT_COPEDENT_ID)
                connection.execute(
                    "update account_copedent_preferences set active_profile_id = ?, updated_at = ? where account_id = ?",
                    (fallback, _utc_now(), account_id),
                )

    def set_active(self, access: AccountAccess, profile_id: str) -> dict[str, object]:
        account_id = self.ensure_account(access)
        profile_id = str(profile_id or "").strip()
        if profile_id in COMMON_PROFILE_IDS:
            last_common = profile_id
        else:
            if not access.allows(CUSTOM_USE):
                raise EntitlementRequiredError(
                    "Session Pass is required to use a custom copedent.",
                    CUSTOM_USE,
                )
            with self._connect() as connection:
                row = connection.execute(
                    """select validation_status from account_copedent_profiles
                    where id = ? and account_id = ?""",
                    (profile_id, account_id),
                ).fetchone()
            if row is None:
                raise AccountProfileNotFoundError("Custom copedent was not found.")
            if str(row["validation_status"]) != "valid":
                raise AccountCopedentError("Validate this copedent before making it active.")
            with self._connect() as connection:
                preference = connection.execute(
                    "select last_common_profile_id from account_copedent_preferences where account_id = ?",
                    (account_id,),
                ).fetchone()
            last_common = str(preference["last_common_profile_id"] if preference else DEFAULT_COPEDENT_ID)
        with self._connect() as connection:
            connection.execute(
                """update account_copedent_preferences set active_profile_id = ?,
                last_common_profile_id = ?, updated_at = ? where account_id = ?""",
                (profile_id, last_common, _utc_now(), account_id),
            )
        return self.account_bundle(access)

    def owned_profile(self, access: AccountAccess, profile_id: str) -> dict[str, object]:
        if not access.allows(CUSTOM_USE):
            raise EntitlementRequiredError(
                "Session Pass is required to use a custom copedent.",
                CUSTOM_USE,
            )
        account_id = self.ensure_account(access)
        with self._connect() as connection:
            row = connection.execute(
                """select id, revision, name, validation_status, payload_json, created_at, updated_at
                from account_copedent_profiles where id = ? and account_id = ?""",
                (profile_id, account_id),
            ).fetchone()
        if row is None:
            raise AccountProfileNotFoundError("Custom copedent was not found.")
        profile = self._profile_row(row)
        if str(profile["validationStatus"]) != "valid":
            raise AccountCopedentError("The selected custom copedent is not validated.")
        return profile

    def effective_active_profile(self, access: AccountAccess) -> str:
        return str(self.account_bundle(access)["activeProfileId"])

    @staticmethod
    def _validated_snapshot(
        snapshot: Mapping[str, Any],
        *,
        profile_id: str,
        revision: int,
    ) -> dict[str, Any]:
        payload = dict(snapshot)
        payload["id"] = profile_id
        payload["revision"] = int(revision)
        payload["origin"] = "account_custom"
        payload["tuningFamily"] = "E9"
        payload["stringCount"] = 10
        profile = custom_e9_profile_from_payload(payload)
        validation_status = str(payload.get("validationStatus") or payload.get("validation_status") or "draft")
        if validation_status not in {"draft", "valid", "needs_review"}:
            validation_status = "draft"
        payload["name"] = str(payload.get("name") or payload.get("label") or profile.label).strip()[:80]
        payload["label"] = payload["name"]
        payload["validationStatus"] = validation_status
        payload.pop("legacySnapshot", None)
        return payload
