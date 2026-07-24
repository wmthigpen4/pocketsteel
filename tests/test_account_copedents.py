from __future__ import annotations

import sqlite3
from typing import Any

import pytest

from steel_guitar_rag.access_control import AnswerAccessDecision
from steel_guitar_rag.account_copedents import (
    COMMON_ENTITLEMENTS,
    CUSTOM_ENTITLEMENTS,
    AccountCopedentRepository,
    AccountProfileConflictError,
    AccountProfileNotFoundError,
    EntitlementRequiredError,
    account_access_for_decision,
    entitlements_for_pass,
)
from tests.test_api_search import (
    DeterministicAnswerProvider,
    FakeCloudflareVerifier,
    FakeSearchIndex,
    call_app,
)


OPEN_STRINGS = ["F#", "D#", "G#", "E", "B", "G#", "F#", "E", "D", "B"]


def profile_payload(name: str = "Road E9") -> dict[str, Any]:
    return {
        "id": "browser-local-profile",
        "name": name,
        "revision": 1,
        "origin": "custom",
        "validationStatus": "valid",
        "tuningFamily": "E9",
        "stringCount": 10,
        "strings": [
            {"stringNumber": index, "openNote": note}
            for index, note in enumerate(OPEN_STRINGS, start=1)
        ],
        "pedalOrder": ["A", "B", "C"],
        "controls": [
            {
                "id": "RKL-half",
                "label": "G",
                "type": "lever",
                "physicalPosition": "RKL",
                "travel": "half-stop",
                "changes": [
                    {"stringNumber": 1, "fromNote": "F#", "toNote": "G"},
                    {"stringNumber": 6, "fromNote": "G#", "toNote": "G"},
                ],
            },
            {
                "id": "G-lower",
                "label": "GG",
                "type": "lever",
                "physicalPosition": "RKL",
                "travel": "full-stop",
                "aliases": ["RKLL"],
                "changes": [
                    {"stringNumber": 1, "fromNote": "F#", "toNote": "G#"},
                    {"stringNumber": 6, "fromNote": "G#", "toNote": "F#"},
                ],
            },
            {
                "id": "D-lower",
                "label": "D",
                "type": "lever",
                "physicalPosition": "RKR",
                "travel": "half-stop",
                "changes": [
                    {"stringNumber": 2, "fromNote": "D#", "toNote": "D"},
                    {"stringNumber": 7, "fromNote": "F#", "toNote": "G"},
                    {"stringNumber": 9, "fromNote": "D", "toNote": "C#"},
                ],
            },
            {
                "id": "RKR-full",
                "label": "DD",
                "type": "lever",
                "physicalPosition": "RKR",
                "travel": "full-stop",
                "aliases": ["RKRR"],
                "changes": [
                    {"stringNumber": 2, "fromNote": "D#", "toNote": "C#"},
                ],
            },
        ],
    }


def decision(role: str, subject: str, email: str = "") -> AnswerAccessDecision:
    return AnswerAccessDecision(
        allowed=True,
        role=role,  # type: ignore[arg-type]
        identity_email=email,
        identity_subject=subject,
        identity_issuer="https://access.example.test",
        identity_provider="cloudflare_access",
    )


def test_entitlement_matrix_keeps_common_profiles_free_and_creator_permanent() -> None:
    free = account_access_for_decision(decision("beta_user", "free-user"), environ={})
    creator = account_access_for_decision(
        decision("beta_user", "creator-user", "creator@example.test"),
        environ={"STEEL_RAG_CREATOR_EMAILS": "creator@example.test"},
    )
    session = account_access_for_decision(
        decision("beta_user", "session-user", "session@example.test"),
        environ={"STEEL_RAG_SESSION_PASS_EMAILS": "session@example.test"},
    )
    admin = account_access_for_decision(decision("admin", "admin-user"), environ={})

    assert free is not None and free.pass_id == "dance_hall" and free.entitlements == COMMON_ENTITLEMENTS
    assert creator is not None and creator.pass_id == "creator" and creator.entitlements == CUSTOM_ENTITLEMENTS
    assert session is not None and session.pass_id == "session" and session.entitlements == CUSTOM_ENTITLEMENTS
    assert admin is not None and admin.pass_id == "bandleader" and admin.entitlements == CUSTOM_ENTITLEMENTS
    assert entitlements_for_pass("standing_room") == frozenset()
    assert entitlements_for_pass("dance_hall") == COMMON_ENTITLEMENTS
    for pass_id in ("session", "headliner", "creator", "bandleader"):
        assert entitlements_for_pass(pass_id) == CUSTOM_ENTITLEMENTS


def test_repository_syncs_profiles_with_revisions_and_preserves_them_on_downgrade(tmp_path: Any) -> None:
    repository = AccountCopedentRepository(tmp_path / "accounts.sqlite3")
    creator = account_access_for_decision(
        decision("beta_user", "same-account", "creator@example.test"),
        environ={"STEEL_RAG_CREATOR_EMAILS": "creator@example.test"},
    )
    assert creator is not None
    created = repository.create_profile(creator, profile_payload())
    repository.set_active(creator, str(created["id"]))
    updated = repository.update_profile(
        creator,
        str(created["id"]),
        {**created, "name": "Road E9 revised"},
        expected_revision=1,
    )

    assert updated["revision"] == 2
    other_admin = account_access_for_decision(decision("admin", "different-account"), environ={})
    assert other_admin is not None
    with pytest.raises(AccountProfileNotFoundError):
        repository.owned_profile(other_admin, str(created["id"]))
    with pytest.raises(AccountProfileConflictError):
        repository.update_profile(
            creator,
            str(created["id"]),
            updated,
            expected_revision=1,
        )

    free = account_access_for_decision(decision("beta_user", "same-account"), environ={})
    assert free is not None
    downgraded = repository.account_bundle(free)
    assert downgraded["activeProfileId"] == "emmons-e9-basic"
    assert downgraded["lockedActiveProfileId"] == created["id"]
    assert [profile["name"] for profile in downgraded["profiles"]] == ["Road E9 revised"]
    with pytest.raises(EntitlementRequiredError):
        repository.set_active(free, str(created["id"]))

    with sqlite3.connect(repository.path) as connection:
        account_columns = {row[1] for row in connection.execute("pragma table_info(accounts)")}
    assert "email" not in account_columns


def test_account_api_enforces_free_paid_and_cross_account_boundaries(tmp_path: Any) -> None:
    repository = AccountCopedentRepository(tmp_path / "accounts.sqlite3")

    status, _, free_session = call_app(
        "/api/session",
        account_copedents_enabled=True,
        account_copedent_repository=repository,
    )
    assert status == "200 OK"
    assert free_session["account"]["passId"] == "dance_hall"
    assert free_session["entitlements"] == ["copedent.common.use"]

    status, _, day = call_app(
        "/api/account/copedents/active",
        method="PUT",
        json_body={"profileId": "day-e9-basic"},
        account_copedents_enabled=True,
        account_copedent_repository=repository,
    )
    assert status == "200 OK"
    assert day["activeProfileId"] == "day-e9-basic"

    status, _, blocked = call_app(
        "/api/account/copedents",
        method="POST",
        json_body={"profile": profile_payload()},
        account_copedents_enabled=True,
        account_copedent_repository=repository,
    )
    assert status == "403 Forbidden"
    assert blocked == {
        "error": "Session Pass is required to save a custom copedent.",
        "code": "entitlement_required",
        "requiredEntitlement": "copedent.custom.manage",
        "upgradePath": "/ui/steel-guitar-rag-mock.html#backstage-pass",
    }

    status, _, created = call_app(
        "/api/account/copedents/import",
        method="POST",
        access_role="admin",
        json_body={"profile": profile_payload()},
        account_copedents_enabled=True,
        account_copedent_repository=repository,
    )
    assert status == "201 Created"
    profile_id = created["profile"]["id"]
    assert profile_id.startswith("saved:account-e9-")

    status, _, updated = call_app(
        f"/api/account/copedents/{profile_id.replace(':', '%3A')}",
        method="PUT",
        access_role="admin",
        json_body={
            "profile": {**created["profile"], "name": "Road E9 synchronized"},
            "expectedRevision": 1,
        },
        account_copedents_enabled=True,
        account_copedent_repository=repository,
    )
    assert status == "200 OK"
    assert updated["profile"]["revision"] == 2

    status, _, other_account = call_app(
        "/api/account/copedents",
        account_copedents_enabled=True,
        account_copedent_repository=repository,
    )
    assert status == "200 OK"
    assert other_account["profiles"] == []

    status, _, bypass = call_app(
        "/api/explorer/e9",
        method="POST",
        json_body={"key": "G", "copedentContext": {"profileId": profile_id}},
        account_copedents_enabled=True,
        account_copedent_repository=repository,
    )
    assert status == "403 Forbidden"
    assert bypass["code"] == "entitlement_required"


def test_production_creator_session_uses_verified_subject_without_exposing_email(monkeypatch: Any, tmp_path: Any) -> None:
    repository = AccountCopedentRepository(tmp_path / "accounts.sqlite3")
    monkeypatch.setenv("STEEL_RAG_CF_ACCESS_ISSUER", "https://steel.cloudflareaccess.com")
    monkeypatch.setenv("STEEL_RAG_CF_ACCESS_AUD", "aud-tag")
    monkeypatch.setenv("STEEL_RAG_BETA_USER_EMAILS", "beta@example.test")
    monkeypatch.setenv("STEEL_RAG_CREATOR_EMAILS", "beta@example.test")

    status, _, payload = call_app(
        "/api/session",
        answer_auth_mode="production",
        auth_provider="cloudflare_access",
        access_role=None,
        cloudflare_token="valid-beta",
        cloudflare_verifier=FakeCloudflareVerifier(),
        account_copedents_enabled=True,
        account_copedent_repository=repository,
    )

    assert status == "200 OK"
    assert payload["account"]["passId"] == "creator"
    assert payload["account"]["passLabel"] == "Creator Access"
    assert payload["account"]["billingManaged"] is False
    assert payload["entitlements"] == sorted(CUSTOM_ENTITLEMENTS)
    assert "beta@example.test" not in str(payload)


def test_production_rejects_direct_custom_snapshot_even_for_creator(monkeypatch: Any, tmp_path: Any) -> None:
    repository = AccountCopedentRepository(tmp_path / "accounts.sqlite3")
    monkeypatch.setenv("STEEL_RAG_CF_ACCESS_ISSUER", "https://steel.cloudflareaccess.com")
    monkeypatch.setenv("STEEL_RAG_CF_ACCESS_AUD", "aud-tag")
    monkeypatch.setenv("STEEL_RAG_BETA_USER_EMAILS", "beta@example.test")
    monkeypatch.setenv("STEEL_RAG_CREATOR_EMAILS", "beta@example.test")

    status, _, payload = call_app(
        "/api/explorer/e9",
        method="POST",
        answer_auth_mode="production",
        auth_provider="cloudflare_access",
        access_role=None,
        cloudflare_token="valid-beta",
        cloudflare_verifier=FakeCloudflareVerifier(),
        json_body={
            "key": "G",
            "copedentContext": {
                "profileId": "saved:browser-local-profile",
                "profileRevision": 1,
                "profileSnapshot": profile_payload(),
            },
        },
        account_copedents_enabled=True,
        account_copedent_repository=repository,
    )

    assert status == "400 Bad Request"
    assert "Import this custom copedent" in payload["error"]


def test_account_active_custom_profile_drives_every_personalized_workspace(tmp_path: Any) -> None:
    repository = AccountCopedentRepository(tmp_path / "accounts.sqlite3")
    local_admin = account_access_for_decision(
        AnswerAccessDecision(
            allowed=True,
            role="admin",
            identity_subject="local-dev:admin",
            identity_issuer="local_dev",
            identity_provider="local_dev",
        ),
        environ={},
    )
    assert local_admin is not None
    created = repository.create_profile(local_admin, profile_payload("Creator road E9"))
    repository.set_active(local_admin, str(created["id"]))

    common = {
        "access_role": "admin",
        "account_copedents_enabled": True,
        "account_copedent_repository": repository,
    }
    status, _, answer = call_app(
        "/api/answer",
        method="POST",
        json_body={"question": "What does my RKL do?"},
        **common,
    )
    assert status == "200 OK"
    assert answer["targetCopedentId"] == created["id"]
    assert answer["targetCopedentLabel"] == "Creator road E9"
    assert "G — RKL, half-stop travel" in answer["answer"]
    assert "GG — RKL, full-stop travel" in answer["answer"]

    status, _, explorer = call_app(
        "/api/explorer/e9",
        method="POST",
        json_body={"key": "G"},
        **common,
    )
    assert status == "200 OK"
    assert explorer["targetCopedentId"] == created["id"]
    assert explorer["selected_copedent"]["id"] == created["id"]

    status, _, lesson = call_app(
        "/api/lessons/build",
        method="POST",
        json_body={"lessonId": "f-lever"},
        **common,
    )
    assert status == "200 OK"
    assert lesson["targetCopedentId"] == created["id"]
    assert lesson["status"] == "unavailable"

    status, _, melody = call_app(
        "/api/answer",
        method="POST",
        json_body={
            "question": "Build an E9 melody exercise from G4.",
            "mode": "tab",
            "melodyRequest": {
                "kind": "user_melody",
                "key": "G",
                "tuning": "E9",
                "melody": [{"pitch": "G4", "pitchValue": 67, "durationBeats": 1}],
            },
        },
        search_index=FakeSearchIndex({"results": [], "warnings": []}),
        answer_provider=DeterministicAnswerProvider(),
        melody_exercise_enabled=True,
        **common,
    )
    assert status == "200 OK"
    assert melody["melody_exercise"]["targetCopedentId"] == created["id"]
    assert melody["melody_exercise"]["arrangedFor"] == "Creator road E9"
    assert melody["tab_example"]["context"]["targetCopedentId"] == created["id"]
    assert melody["fretboard"]["copedent"]["id"] == created["id"]
