from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROOF_ROOT = ROOT / "ui/chord-reader-proof"


def test_visual_proof_uses_tracked_model_audio_and_expected_chords() -> None:
    proof = json.loads((PROOF_ROOT / "data/proof.json").read_text(encoding="utf-8"))
    model = ROOT / "ui/models/chord-student-v1.onnx"
    audio = ROOT / "ui/assets/song-practice/amazing-grace-2011-guide.mp3"
    assert proof["schemaVersion"] == "chord_reader_visual_proof_v1"
    assert proof["track"]["license"] == "CC BY 3.0"
    assert proof["reference"]["source"] == "hand-authored Steel Guitar RAG lesson timeline"
    assert proof["reproduce"]["modelSha256"] == hashlib.sha256(model.read_bytes()).hexdigest()
    assert proof["reproduce"]["audioSha256"] == hashlib.sha256(audio.read_bytes()).hexdigest()


def test_visual_proof_exposes_successes_and_failures_bar_by_bar() -> None:
    proof = json.loads((PROOF_ROOT / "data/proof.json").read_text(encoding="utf-8"))
    rows = {row["bar"]: row for row in proof["bars"]}
    assert proof["summary"] == {
        "barCount": 16,
        "majorMinorWcsrGain": proof["summary"]["majorMinorWcsrGain"],
        "rootWcsrGain": proof["summary"]["rootWcsrGain"],
        "studentCorrectBars": 15,
        "v2CorrectBars": 13,
    }
    assert rows[3] == {
        "bar": 3,
        "start": 9.474,
        "end": 11.842,
        "expected": "C",
        "v2": "Am7",
        "student": "C",
        "v2Correct": False,
        "studentCorrect": True,
    }
    assert rows[11]["expected"] == rows[11]["student"] == "C"
    assert rows[11]["v2"] == "G"
    assert rows[13]["expected"] == "Em"
    assert rows[13]["v2Correct"] is rows[13]["studentCorrect"] is False
    assert proof["engines"]["student"]["metrics"]["majorMinorWeightedRecall"] < proof["engines"]["v2"]["metrics"][
        "majorMinorWeightedRecall"
    ]


def test_visual_proof_discloses_exact_public_dataset_scope() -> None:
    proof = json.loads((PROOF_ROOT / "data/proof.json").read_text(encoding="utf-8"))
    benchmark = proof["publicBenchmark"]
    assert benchmark["trackCount"] == 36
    assert benchmark["engines"]["student"]["majorMinorWcsr"] > benchmark["engines"]["btc"]["majorMinorWcsr"]
    assert benchmark["engines"]["btc"]["majorMinorWcsr"] > benchmark["engines"]["v2"]["majorMinorWcsr"]
    assert "not downloaded or used" in benchmark["aamDisclosure"]
    assert "no chord progression ground truth" in benchmark["lofiDisclosure"]


def test_visual_proof_page_has_player_comparison_and_reproduction_evidence() -> None:
    html = (PROOF_ROOT / "index.html").read_text(encoding="utf-8")
    script = (PROOF_ROOT / "proof.js").read_text(encoding="utf-8")
    assert '<audio id="audio" controls' in html
    assert "Hand-authored" in html and "Current v2" in html and "Revised model" in html
    assert "The unflattering metric is visible too." in html
    assert "Regenerate the evidence locally" in html
    assert 'fetch("./data/proof.json"' in script
    assert "await new Promise" in script and "seekAndPlay(bar.start)" in script
