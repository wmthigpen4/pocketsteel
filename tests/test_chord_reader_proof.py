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
    models = [
        ROOT / "ui/models/chord-multiband-tcn-v2.onnx",
        ROOT / "ui/models/chord-multiband-transformer-v2.onnx",
        ROOT / "ui/models/chord-multiband-idmt-tcn-v3.onnx",
        ROOT / "ui/models/chord-harmonic-cqt-transformer-v4.onnx",
        ROOT / "ui/models/chord-boundary-transformer-v3.onnx",
        ROOT / "ui/models/chord-boundary-nrgcp-transformer-v5.onnx",
        ROOT / "ui/models/chord-quality-nrgcp-multiband-v5.onnx",
        ROOT / "ui/models/chord-quality-nrgcp-cqt-v5.onnx",
        ROOT / "ui/models/chord-domain-gate-v1.json",
    ]
    assert proof["schemaVersion"] == "chord_reader_visual_proof_v2"
    assert proof["suite"]["trackCount"] == len(proof["tracks"]) == 3
    assert proof["suite"]["barCount"] == 49
    assert proof["reproduce"]["modelSha256"] == " / ".join(
        hashlib.sha256(model.read_bytes()).hexdigest() for model in models
    )
    for item in proof["tracks"]:
        audio = ROOT / item["track"]["audioUrl"].lstrip("/")
        assert audio.is_file()
        assert proof["reproduce"]["audioSha256"][item["track"]["id"]] == hashlib.sha256(audio.read_bytes()).hexdigest()
        data_root = PROOF_ROOT / "data/tracks" / item["track"]["id"]
        assert all(
            (data_root / name).is_file() for name in ("reference.json", "v2.json", "student.json", "hybrid.json")
        )


def test_visual_proof_exposes_successes_failures_and_hybrid_bar_by_bar() -> None:
    proof = _proof()
    amazing = proof["tracks"][0]
    rows = {row["bar"]: row for row in amazing["bars"]}
    assert amazing["summary"] == {
        "barCount": 16,
        "hybridCorrectBars": 14,
        "studentCorrectBars": 14,
        "v2CorrectBars": 13,
    }
    assert rows[3]["start"] == 9.474
    assert rows[3]["expected"] == rows[3]["student"] == rows[3]["hybrid"] == "C"
    assert rows[3]["v2"] == "Am7"
    assert rows[3]["v2Correct"] is False
    assert rows[3]["studentCorrect"] is rows[3]["hybridCorrect"] is True
    assert rows[11]["expected"] == "C"
    assert rows[11]["v2"] == rows[11]["hybrid"] == "G"
    assert rows[13]["expected"] == "Em"
    assert rows[13]["v2Correct"] is rows[13]["studentCorrect"] is rows[13]["hybridCorrect"] is False


def test_visual_proof_reports_suite_wins_and_remaining_failures_without_hiding_them() -> None:
    proof = _proof()
    suite = proof["suite"]
    assert suite["barTotals"] == {"hybrid": 46, "student": 46, "v2": 43}
    assert suite["engines"]["hybrid"]["majorMinorWeightedRecall"] > suite["engines"]["v2"]["majorMinorWeightedRecall"]
    by_id = {item["track"]["id"]: item for item in proof["tracks"]}
    for identifier in ("when-the-saints-preview-v1", "oh-susanna-preview-v1"):
        item = by_id[identifier]
        assert (
            item["engines"]["hybrid"]["metrics"]["majorMinorWeightedRecall"]
            > item["engines"]["v2"]["metrics"]["majorMinorWeightedRecall"]
        )
    amazing = by_id["amazing-grace-kevin-macleod-lesson-v1"]
    assert amazing["summary"]["hybridCorrectBars"] > amazing["summary"]["v2CorrectBars"]
    assert amazing["engines"]["hybrid"]["metrics"]["majorMinorWeightedRecall"] == 0.7994272009686358
    assert amazing["engines"]["v2"]["metrics"]["majorMinorWeightedRecall"] == 0.7999394602649776
    assert [row["bar"] for row in amazing["bars"] if not row["hybridCorrect"]] == [11, 13]
    assert by_id["amazing-grace-kevin-macleod-lesson-v1"]["track"]["recordingType"] == "licensed human performance"
    assert by_id["oh-susanna-preview-v1"]["track"]["recordingType"] == "app-owned deterministic performance"


def test_visual_proof_discloses_all_sealed_corpora_and_weakest_result() -> None:
    benchmark = _proof()["publicBenchmark"]
    assert {item["id"] for item in benchmark["datasets"]} == {
        "aam",
        "babyslakh",
        "guitarset",
        "idmt_guitar",
        "nrgcp",
        "winterreise",
    }
    assert sum(item["trackCount"] for item in benchmark["datasets"]) == 366
    assert benchmark["confirmation"]["trackCount"] == 500
    assert benchmark["confirmation"]["compositionOverlapWithTrainingOrPriorEvaluation"] == 0
    assert min(item["majorMinorWeightedRecall"] for item in benchmark["datasets"]) < 0.6
    assert "Enharmonic" in benchmark["metricSemantics"]
    assert "98% objective has not been met" in benchmark["disclosure"]
    assert "Travis songs were not used" in benchmark["disclosure"]


def test_visual_proof_page_has_player_selector_hybrid_and_reproduction_evidence() -> None:
    html = (PROOF_ROOT / "index.html").read_text(encoding="utf-8")
    script = (PROOF_ROOT / "proof.js").read_text(encoding="utf-8")
    assert '<audio id="audio" controls' in html
    assert 'id="track-selector"' in html
    assert all(label in html for label in ("Hand-authored", "Current v2", "Domain-gated v8", "Safety overlay"))
    assert "including regressions" in html
    assert "Regenerate the evidence locally" in html
    assert 'fetch("./data/proof.json"' in script
    assert "await new Promise" in script and "seekAndPlay(bar.start)" in script
    assert "[...benchmark.datasets" in script


def test_visual_proof_supports_ignored_local_v9_listening_bundle() -> None:
    html = (PROOF_ROOT / "index.html").read_text(encoding="utf-8")
    script = (PROOF_ROOT / "proof.js").read_text(encoding="utf-8")
    css = (PROOF_ROOT / "proof.css").read_text(encoding="utf-8")
    builder = (ROOT / "scripts/build_local_chord_reader_test.py").read_text(encoding="utf-8")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert 'query.get("v") === "9"' in script
    assert 'fetch("./local-tests/proof.json"' in script
    assert 'proof.schemaVersion === "chord_reader_local_song_test_v1"' in script
    assert "Confidence is the model's own probability, not measured correctness." in script
    assert 'id="hero-eyebrow"' in html and 'id="footer-status"' in html
    assert ".local-mode .current-chord.v2" in css
    assert "ui/chord-reader-proof/local-tests/" in ignore
    assert "StudentHeterogeneousBoundaryGuidedEnsembleRecognizer" in builder
    assert '"NO-GO — listening test only; no operating threshold or accuracy claim"' in builder
    assert "shutil.copyfile(source, destination)" in builder
    assert '"sourcePath"' not in builder
    assert 'id="crosscheck-section"' in html
    assert "renderCrossCheck" in script
    assert "Agreement is not accuracy" in script
    assert ".local-mode.has-crosscheck" in css
    assert "three-system consensus" in script
    assert "Open-source BTC" in script
    assert 'id="crosscheck-head"' in html
    assert ".local-mode.has-open-source" in css
    assert "add_open_source_consensus.py --local-files-only" in script
    comparator = (ROOT / "scripts/add_chordify_crosscheck.py").read_text(encoding="utf-8")
    assert "user-authorized premium time-aligned MIDI export" in comparator
    assert "It is not ground-truth accuracy" in comparator
    assert "mido" not in comparator
    open_source = (ROOT / "scripts/add_open_source_consensus.py").read_text(encoding="utf-8")
    assert "product_viterbi=True" in open_source
    assert "fitCount" not in open_source
    assert "chord-extractor" in open_source
