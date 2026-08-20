from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROOF_ROOT = ROOT / "ui/chord-reader-proof"


def _proof() -> dict:
    return json.loads((PROOF_ROOT / "data/proof.json").read_text(encoding="utf-8"))


def test_visual_proof_uses_three_real_audio_assets_and_tracked_model() -> None:
    proof = _proof()
    model = ROOT / "ui/models/chord-student-v1.onnx"
    assert proof["schemaVersion"] == "chord_reader_visual_proof_v2"
    assert proof["suite"]["trackCount"] == len(proof["tracks"]) == 3
    assert proof["suite"]["barCount"] == 49
    assert proof["reproduce"]["modelSha256"] == hashlib.sha256(model.read_bytes()).hexdigest()
    for item in proof["tracks"]:
        audio = ROOT / item["track"]["audioUrl"].lstrip("/")
        assert audio.is_file()
        assert proof["reproduce"]["audioSha256"][item["track"]["id"]] == hashlib.sha256(audio.read_bytes()).hexdigest()
        data_root = PROOF_ROOT / "data/tracks" / item["track"]["id"]
        assert all((data_root / name).is_file() for name in ("reference.json", "v2.json", "student.json", "hybrid.json"))


def test_visual_proof_exposes_successes_failures_and_hybrid_bar_by_bar() -> None:
    proof = _proof()
    amazing = proof["tracks"][0]
    rows = {row["bar"]: row for row in amazing["bars"]}
    assert amazing["summary"] == {
        "barCount": 16,
        "hybridCorrectBars": 15,
        "studentCorrectBars": 15,
        "v2CorrectBars": 13,
    }
    assert rows[3]["start"] == 9.474
    assert rows[3]["expected"] == rows[3]["student"] == rows[3]["hybrid"] == "C"
    assert rows[3]["v2"] == "Am7"
    assert rows[3]["v2Correct"] is False
    assert rows[3]["studentCorrect"] is rows[3]["hybridCorrect"] is True
    assert rows[11]["expected"] == rows[11]["hybrid"] == "C"
    assert rows[11]["v2"] == "G"
    assert rows[13]["expected"] == "Em"
    assert rows[13]["v2Correct"] is rows[13]["studentCorrect"] is rows[13]["hybridCorrect"] is False


def test_visual_proof_reports_suite_wins_and_regressions_without_hiding_them() -> None:
    proof = _proof()
    suite = proof["suite"]
    assert suite["barTotals"] == {"hybrid": 47, "student": 47, "v2": 43}
    assert suite["engines"]["hybrid"]["majorMinorWeightedRecall"] > suite["engines"]["v2"]["majorMinorWeightedRecall"]
    by_id = {item["track"]["id"]: item for item in proof["tracks"]}
    for identifier in ("when-the-saints-preview-v1", "oh-susanna-preview-v1"):
        item = by_id[identifier]
        assert item["engines"]["hybrid"]["metrics"]["majorMinorWeightedRecall"] < item["engines"]["v2"]["metrics"]["majorMinorWeightedRecall"]
    assert by_id["amazing-grace-kevin-macleod-lesson-v1"]["track"]["recordingType"] == "licensed human performance"
    assert by_id["oh-susanna-preview-v1"]["track"]["recordingType"] == "app-owned deterministic performance"


def test_visual_proof_discloses_exact_public_dataset_scope_and_no_regression() -> None:
    benchmark = _proof()["publicBenchmark"]
    assert benchmark["trackCount"] == 36
    assert benchmark["engines"]["hybrid"] == benchmark["engines"]["student"]
    assert benchmark["engines"]["student"]["majorMinorWcsr"] > benchmark["engines"]["btc"]["majorMinorWcsr"]
    assert benchmark["engines"]["btc"]["majorMinorWcsr"] > benchmark["engines"]["v2"]["majorMinorWcsr"]
    assert "not downloaded or used" in benchmark["aamDisclosure"]
    assert "no chord progression ground truth" in benchmark["lofiDisclosure"]


def test_visual_proof_page_has_player_selector_hybrid_and_reproduction_evidence() -> None:
    html = (PROOF_ROOT / "index.html").read_text(encoding="utf-8")
    script = (PROOF_ROOT / "proof.js").read_text(encoding="utf-8")
    assert '<audio id="audio" controls' in html
    assert 'id="track-selector"' in html
    assert all(label in html for label in ("Hand-authored", "Current v2", "Raw model", "Hardened hybrid"))
    assert "including regressions" in html
    assert "Regenerate the evidence locally" in html
    assert 'fetch("./data/proof.json"' in script
    assert "await new Promise" in script and "seekAndPlay(bar.start)" in script
    assert '["v2", "btc", "student", "hybrid"]' in script
