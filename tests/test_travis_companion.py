from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re

import pytest

from partner_companions.travis_howdy.release import (
    CompanionReleaseError,
    DEFAULT_COMPANION,
    _normalized_artifact_hash,
    _merge_release_config,
    build_companion_bundle,
    generate_tablature_pdf,
    validate_companion,
)
from scripts.verify_travis_companion import BLOCKED_ROUTES, verify


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "partner_companions" / "travis_howdy" / "site"


def load_draft() -> dict[str, object]:
    return json.loads(DEFAULT_COMPANION.read_text(encoding="utf-8"))


def approved_release_data(*, review_phase: str = "owner_only", tester_count: int = 1) -> dict[str, object]:
    data = load_draft()
    data["contentStatus"] = "approved"
    data["approvals"] = {key: True for key in data["approvals"]}
    data["copedent"]["approved"] = True
    data["print"]["approved"] = True
    data["release"]["approvalReferences"] = ["music", "chords", "audio", "brand", "print"]
    data["release"]["reviewPhase"] = review_phase
    data["release"]["testerEmailCount"] = tester_count
    for event in data["events"]:
        event["musicalVerified"] = True
    for chord in data["chordTimeline"]:
        chord["verified"] = True
        chord["symbol"] = "C"
        chord["tabNotes"] = [
            {"string": 3, "fret": 8, "controls": [], "technique": "hold"},
            {"string": 4, "fret": 8, "controls": [], "technique": "hold"},
            {"string": 5, "fret": 8, "controls": [], "technique": "hold"},
        ]
    return data


def release_config(*, review_phase: str, tester_emails: list[str]) -> dict[str, object]:
    return {
        "reviewPhase": review_phase,
        "testerEmails": tester_emails,
        "feedbackEmail": "feedback@example.com",
        "approvalReferences": ["music", "chords", "audio", "brand", "print"],
        "approvals": {},
        "access": {
            "customDomainApplicationId": "custom-app",
            "pagesDevProductionApplicationId": "production-app",
            "pagesDevPreviewApplicationId": "preview-app",
            "customDomainAnonymousDenied": True,
            "pagesDevProductionAnonymousDenied": True,
            "pagesDevPreviewAnonymousDenied": True,
            "appSteelGuitarRagPolicyUnchanged": True,
        },
    }


def test_draft_is_deterministic_but_explicitly_unapproved() -> None:
    data = load_draft()
    validate_companion(data, release=False)
    assert data["runtimeMode"] == "published_deterministic"
    assert data["modelCallsAllowed"] is False
    assert data["contentStatus"] == "draft_review_required"
    assert not any(data["approvals"].values())
    assert all(chord["symbol"] is None and chord["verified"] is False for chord in data["chordTimeline"])
    assert all(event["musicalVerified"] is False for event in data["events"])
    with pytest.raises(CompanionReleaseError, match="contentStatus=approved"):
        validate_companion(data, release=True)


def test_all_views_share_one_event_graph() -> None:
    data = load_draft()
    events = {event["id"]: event for event in data["events"]}
    assert len(events) == 12
    assert sum(len(phrase["eventIds"]) for phrase in data["phrases"]) == len(events)
    assert {event["phraseId"] for event in events.values()} == {phrase["id"] for phrase in data["phrases"]}
    assert {event["chordEventId"] for event in events.values()} == {
        chord["id"] for chord in data["chordTimeline"]
    }
    assert all(event["tabNotes"] and event["notationPitch"] for event in events.values())


def test_chord_boundaries_are_exact_and_never_inferred() -> None:
    data = load_draft()
    by_chord: dict[str, list[dict[str, object]]] = {}
    for event in data["events"]:
        by_chord.setdefault(event["chordEventId"], []).append(event)
    for chord in data["chordTimeline"]:
        events = by_chord[chord["id"]]
        assert abs(events[0]["startMs"] - chord["startMs"]) <= 50
        assert abs(events[-1]["endMs"] - chord["endMs"]) <= 50
        assert chord["symbol"] is None


def test_normalized_artifact_hash_ignores_only_generated_fields() -> None:
    data = load_draft()
    first = _normalized_artifact_hash(data)
    generated = copy.deepcopy(data)
    generated["buildSha"] = "different"
    generated["artifactSha256"] = "different"
    generated["media"]["audioUrl"] = "/assets/example/audio.mp3"
    generated["media"]["pdfUrl"] = "/assets/example/tab.pdf"
    generated["media"]["brandHeroUrl"] = "/assets/example/photo.jpg"
    assert _normalized_artifact_hash(generated) == first
    generated["events"][0]["instruction"] = "Changed music-facing content"
    assert _normalized_artifact_hash(generated) != first


def test_coaching_cues_must_be_verbatim_and_timestamped() -> None:
    data = load_draft()
    event = data["events"][0]
    event["coachingCue"] = "Short exact lesson excerpt."
    event["sourceMoment"] = {
        "lessonTimeMs": 123_000,
        "quoteKind": "verbatim_excerpt",
        "excerpt": event["coachingCue"],
    }
    validate_companion(data, release=False)
    event["sourceMoment"]["excerpt"] = "A paraphrase is not allowed."
    with pytest.raises(CompanionReleaseError, match="verbatim excerpt"):
        validate_companion(data, release=False)


def test_draft_bundle_is_reproducible_allowlisted_and_isolated(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_manifest = tmp_path / "first-manifest.json"
    second_manifest = tmp_path / "second-manifest.json"
    result_one = build_companion_bundle(
        first,
        manifest_path=first_manifest,
        source_date_epoch=1_786_683_600,
    )
    result_two = build_companion_bundle(
        second,
        manifest_path=second_manifest,
        source_date_epoch=1_786_683_600,
    )
    assert result_one == result_two
    assert result_one["assetHashes"] == {
        path.relative_to(first).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(first.rglob("*"))
        if path.is_file()
    }
    report = verify(first, first_manifest)
    assert report["result"] == "pass"
    assert report["blockedRoutes"] == list(BLOCKED_ROUTES)
    assert not (first / "internal-release-manifest.json").exists()
    assert not list(first.rglob("*.vtt"))
    assert not list(first.rglob("*.srt"))
    assert not list(first.rglob("*.map"))


def test_local_draft_audio_is_private_and_hash_pinned(tmp_path: Path) -> None:
    audio = tmp_path / "private-preview.mp3"
    audio.write_bytes(b"ID3-local-owner-review")
    data = load_draft()
    data["media"]["audioSha256"] = hashlib.sha256(audio.read_bytes()).hexdigest()
    companion = tmp_path / "companion.json"
    companion.write_text(json.dumps(data), encoding="utf-8")
    bundle = tmp_path / "bundle"
    build_companion_bundle(
        bundle,
        companion_path=companion,
        draft_audio_path=audio,
        source_date_epoch=1,
    )
    packaged = list(bundle.rglob("howdy-backing-track.mp3"))
    assert len(packaged) == 1
    assert packaged[0].read_bytes() == audio.read_bytes()
    deployed_data = json.loads(next(bundle.rglob("lesson-companion.json")).read_text(encoding="utf-8"))
    assert deployed_data["media"]["audioUrl"].startswith("/assets/")
    assert deployed_data["media"]["draftClockOnly"] is False

    data["media"]["audioSha256"] = "0" * 64
    companion.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CompanionReleaseError, match="hash mismatch"):
        build_companion_bundle(
            tmp_path / "bad-bundle",
            companion_path=companion,
            draft_audio_path=audio,
        )


def test_bundle_verifier_rejects_access_phase_manifest_drift(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    manifest_path = tmp_path / "manifest.json"
    build_companion_bundle(bundle, manifest_path=manifest_path, source_date_epoch=1)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["reviewPhase"] = "partner_review"
    manifest["accessTesterCount"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CompanionReleaseError, match="review phase differs"):
        verify(bundle, manifest_path)


def test_security_headers_and_route_map_are_fail_closed(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    build_companion_bundle(bundle, source_date_epoch=1)
    redirects = (bundle / "_redirects").read_text(encoding="utf-8").splitlines()
    assert redirects == [
        "/ /howdy 302",
        "/howdy /howdy/index.html 200",
        "/howdy/embed-demo /howdy/embed-demo/index.html 200",
        "/howdy/print /howdy/print/index.html 200",
    ]
    headers = (bundle / "_headers").read_text(encoding="utf-8")
    assert "default-src 'self'" in headers
    assert "connect-src 'self'" in headers
    assert "frame-ancestors 'none'" in headers
    assert "form-action 'none'" in headers
    assert "X-Robots-Tag: noindex, nofollow, noarchive" in headers
    assert "Referrer-Policy: no-referrer" in headers
    assert "X-Content-Type-Options: nosniff" in headers
    assert "Access-Control-Allow-Origin" not in headers


def test_browser_runtime_has_one_same_origin_fetch_and_no_dynamic_clients() -> None:
    script = (SITE / "companion.js").read_text(encoding="utf-8")
    assert script.count("fetch(") == 1
    assert "fetch(companionUrl.href" in script
    assert "companionUrl.origin !== window.location.origin" in script
    assert "mediaUrl.origin !== window.location.origin" in script
    for token in ("XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon", "Worker("):
        assert token not in script
    lowered = script.lower()
    for endpoint in ("/api/answer", "/api/search", "ollama", "chroma", "openai.com/v1", "anthropic.com"):
        assert endpoint not in lowered


def test_companion_has_deterministic_search_layers_chords_and_step_study() -> None:
    script = (SITE / "companion.js").read_text(encoding="utf-8")
    markup = (ROOT / "partner_companions" / "travis_howdy" / "templates" / "companion.fragment.html").read_text(
        encoding="utf-8"
    )
    assert "function renderLessonSearch()" in script
    assert "function setLayer(" in script
    assert "function renderChordChart()" in script
    assert "function stepMove(" in script
    assert 'return `${note.fret}h${pedal}`' in script
    for selector in (
        "data-lesson-search",
        "data-layer-title",
        "data-chord-chart",
        "data-key-label",
        "data-study-controls",
        "data-explore-panel",
    ):
        assert selector in markup


def test_release_validation_requires_every_human_signoff() -> None:
    data = approved_release_data()
    validate_companion(data, release=True)
    for field in sorted(data["approvals"]):
        candidate = copy.deepcopy(data)
        candidate["approvals"][field] = False
        with pytest.raises(CompanionReleaseError, match="Release approvals incomplete"):
            validate_companion(candidate, release=True)


@pytest.mark.parametrize(
    ("review_phase", "tester_count"),
    (("owner_only", 1), ("partner_review", 2)),
)
def test_release_validation_accepts_only_the_identity_count_for_the_review_phase(
    review_phase: str,
    tester_count: int,
) -> None:
    data = approved_release_data(review_phase=review_phase, tester_count=tester_count)
    validate_companion(data, release=True)

    data["release"]["testerEmailCount"] = tester_count + 1
    with pytest.raises(CompanionReleaseError, match="requires exactly"):
        validate_companion(data, release=True)


def test_release_validation_rejects_an_unrecognized_review_phase() -> None:
    data = approved_release_data(review_phase="automatic_partner_access")
    with pytest.raises(CompanionReleaseError, match="recognized review phase"):
        validate_companion(data, release=True)


@pytest.mark.parametrize(
    ("review_phase", "tester_emails"),
    (("owner_only", ["owner@example.com"]), ("partner_review", ["owner@example.com", "partner@example.com"])),
)
def test_private_release_config_enforces_phase_without_emitting_tester_addresses(
    review_phase: str,
    tester_emails: list[str],
) -> None:
    data = load_draft()
    _merge_release_config(data, release_config(review_phase=review_phase, tester_emails=tester_emails))
    assert data["release"]["reviewPhase"] == review_phase
    assert data["release"]["testerEmailCount"] == len(tester_emails)
    serialized = json.dumps(data)
    assert all(email not in serialized for email in tester_emails)


def test_owner_only_release_config_rejects_a_second_identity() -> None:
    data = load_draft()
    config = release_config(
        review_phase="owner_only",
        tester_emails=["owner@example.com", "partner@example.com"],
    )
    with pytest.raises(CompanionReleaseError, match="requires exactly 1 tester email"):
        _merge_release_config(data, config)


def test_pdf_contains_notation_tab_controls_and_revision(tmp_path: Path) -> None:
    pypdf = pytest.importorskip("pypdf")
    data = load_draft()
    output = generate_tablature_pdf(data, tmp_path / "howdy.pdf")
    reader = pypdf.PdfReader(str(output))
    assert len(reader.pages) == 2
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Howdy Solo - Companion Tablature" in extracted
    assert data["revision"] in extracted
    assert "DRAFT LAYOUT PROOF" in extracted
    assert "A=A pedal" in extracted
    assert all(phrase["label"] in extracted for phrase in data["phrases"])
    assert re.search(r"Page 1 of 2", extracted)
