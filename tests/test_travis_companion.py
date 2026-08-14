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
    build_companion_bundle,
    generate_tablature_pdf,
    validate_companion,
)
from scripts.verify_travis_companion import BLOCKED_ROUTES, verify


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "partner_companions" / "travis_howdy" / "site"


def load_draft() -> dict[str, object]:
    return json.loads(DEFAULT_COMPANION.read_text(encoding="utf-8"))


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


def test_release_validation_requires_every_human_signoff() -> None:
    data = load_draft()
    data["contentStatus"] = "approved"
    data["approvals"] = {key: True for key in data["approvals"]}
    data["copedent"]["approved"] = True
    data["print"]["approved"] = True
    data["release"]["approvalReferences"] = ["music", "chords", "audio", "brand", "print"]
    data["release"]["testerEmailCount"] = 2
    for event in data["events"]:
        event["musicalVerified"] = True
    for chord in data["chordTimeline"]:
        chord["verified"] = True
        chord["symbol"] = "C"
    validate_companion(data, release=True)
    for field in sorted(data["approvals"]):
        candidate = copy.deepcopy(data)
        candidate["approvals"][field] = False
        with pytest.raises(CompanionReleaseError, match="Release approvals incomplete"):
            validate_companion(candidate, release=True)


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
