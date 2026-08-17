from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

from partner_companions.travis_tutorials import (
    CompanionValidationError,
    companion_sha256,
    convert_howdy_v1,
    validate_companion_v3,
)
from steel_guitar_rag.travis_companion_analysis.analysis import _arrange_notes, align_passage_to_backing, subtract_backing
from steel_guitar_rag.travis_companion_analysis.runner import RunnerClient


ROOT = Path(__file__).resolve().parents[1]


def howdy_v3() -> dict:
    source = json.loads((ROOT / "partner_companions/travis_howdy/content/howdy.draft.json").read_text())
    return convert_howdy_v1(source)


def test_howdy_converts_to_generic_v3_fixture() -> None:
    converted = howdy_v3()
    validate_companion_v3(converted)
    assert converted["schemaVersion"] == "lesson_companion_v3"
    assert converted["lesson"]["slug"] == "howdy"
    assert len(converted["passages"][0]["tabEvents"]) == 12
    assert converted["songChordTimeline"][0]["startMs"] == 0
    assert converted["songChordTimeline"][-1]["endMs"] == converted["media"]["backingTracks"][0]["durationMs"]


def test_uncertainty_can_publish_but_invalid_mechanics_cannot() -> None:
    artifact = howdy_v3()
    artifact["songChordTimeline"][0]["symbol"] = None
    artifact["songChordTimeline"][0]["reviewStatus"] = "uncertain"
    artifact["state"] = "published"
    artifact["publication"] = {"publishedAt": "2026-08-17T00:00:00Z", "contentSha256": "pending"}
    artifact["publication"]["contentSha256"] = companion_sha256(artifact)
    validate_companion_v3(artifact, for_publish=True)

    invalid = deepcopy(artifact)
    invalid["passages"][0]["tabEvents"][0]["notes"][0]["controls"] = ["E"]
    with pytest.raises(CompanionValidationError, match="does not change string"):
        validate_companion_v3(invalid, for_publish=True)


def test_chart_must_cover_primary_track_without_gaps() -> None:
    artifact = howdy_v3()
    artifact["songChordTimeline"][1]["startMs"] += 1
    with pytest.raises(CompanionValidationError, match="does not continue"):
        validate_companion_v3(artifact)


def test_hash_is_deterministic_and_excludes_its_own_value() -> None:
    artifact = howdy_v3()
    artifact["publication"] = {"publishedAt": "2026-08-17T00:00:00Z", "contentSha256": "one"}
    first = companion_sha256(artifact)
    artifact["publication"]["contentSha256"] = "two"
    assert companion_sha256(artifact) == first
    artifact["lesson"]["title"] += " edited"
    assert companion_sha256(artifact) != first


def test_alignment_finds_a_passage_and_reports_unrelated_audio() -> None:
    sample_rate = 8_000
    random = np.random.default_rng(42)
    backing = random.normal(0, 0.2, sample_rate * 8).astype(np.float32)
    performance = backing[sample_rate * 3 : sample_rate * 5].copy()
    aligned = align_passage_to_backing(performance, backing, sample_rate=sample_rate)
    assert aligned.status == "aligned"
    assert aligned.track_start_ms == pytest.approx(3_000, abs=100)

    unrelated = align_passage_to_backing(np.zeros_like(performance), backing, sample_rate=sample_rate)
    assert unrelated.status == "manual_required"
    assert unrelated.track_start_ms is None


def test_backing_subtraction_reduces_shared_signal() -> None:
    x = np.linspace(0, 2 * np.pi, 4_000, dtype=np.float32)
    backing = np.sin(x).astype(np.float32)
    steel = (0.1 * np.sin(4 * x)).astype(np.float32)
    performance = backing * 0.8 + steel
    residual = subtract_backing(performance, backing)
    assert float(np.mean(np.square(residual))) < float(np.mean(np.square(performance)))


def test_v3_copedent_routes_through_amazing_tablature() -> None:
    copedent = howdy_v3()["copedentSnapshot"]
    arranged = _arrange_notes(
        [{"id": "note-1", "startMs": 0, "endMs": 250, "pitchValue": 68, "confidence": 0.8}],
        key="D",
        copedent=copedent,
        chords=[],
    )
    assert len(arranged) == 1
    assert arranged[0]["resolvedPitch"] == "G#4"
    assert arranged[0]["mechanicalActions"][0]["destinationPitch"] == 68


def test_runner_treats_an_empty_claim_response_as_an_idle_queue(monkeypatch: pytest.MonkeyPatch) -> None:
    client = RunnerClient("http://127.0.0.1:8791", "test-token")
    monkeypatch.setattr(client, "_request", lambda *args, **kwargs: b"")
    assert client.claim() is None
