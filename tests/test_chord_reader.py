from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
import sys
import shutil

import pytest

from steel_guitar_rag.chord_reader.labels import normalize_chord, transpose_chord
from steel_guitar_rag.chord_reader.btc import load_model_registry, verify_model_snapshot
from steel_guitar_rag.chord_reader.chart_reference import build_chart_reference
from steel_guitar_rag.chord_reader.datasets import parse_aam_beatinfo, parse_guitarset_jams
from steel_guitar_rag.chord_reader.manifests import (
    WeakLabelDiagnostics,
    admit_weak_label,
    assign_group_splits,
    validate_catalog,
    validate_track_manifest,
)
from steel_guitar_rag.chord_reader.metrics import score_segments
from steel_guitar_rag.chord_reader.student import (
    STUDENT_CLASSES,
    frame_labels,
    student_index,
    student_label,
    transpose_student_index,
)
from steel_guitar_rag.chord_reader.promotion import evaluate_promotion
from steel_guitar_rag.chord_reader.review import build_travis_packet, score_travis_review


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("value", "detailed", "product", "attention"),
    [
        ("C", "C:maj", "C", False),
        ("Bb:min7", "Bb:min7", "Bbm7", False),
        ("F#7", "F#:7", "F#7", False),
        ("G:maj7/B", "G:maj7/B", "G", False),
        ("D:sus4", "D:sus4", "D", True),
        ("C#dim7", "C#:dim7", "C#", True),
        ("N.C.", "N", "N.C.", False),
        ("X", "X", "N.C.", True),
    ],
)
def test_normalize_chord(value: str, detailed: str, product: str, attention: bool) -> None:
    label = normalize_chord(value)
    assert label.detailed_symbol == detailed
    assert label.product_symbol == product
    assert label.needs_attention is attention


def test_transpose_chord_preserves_quality_and_bass() -> None:
    label = transpose_chord("Bb:min7/Db", 2)
    assert label.detailed_symbol == "C:min7/Eb"
    assert label.product_symbol == "Cm7"
    assert label.bass == "Eb"


def test_group_splits_prevent_composition_leakage() -> None:
    tracks = [
        {"id": "a", "datasetId": "aam", "groupId": "render-1", "compositionId": "same-song"},
        {"id": "b", "datasetId": "guitarset", "groupId": "player-2", "compositionId": "same-song"},
        {"id": "c", "datasetId": "aam", "groupId": "render-3", "compositionId": "other-song"},
    ]
    first = assign_group_splits(tracks)
    second = assign_group_splits(reversed(tracks))
    assert first[0]["split"] == first[1]["split"]
    assert {item["id"]: item["split"] for item in first} == {item["id"]: item["split"] for item in second}


def test_manifest_rejects_split_leakage_and_weak_weight_overflow() -> None:
    base = {
        "schemaVersion": "chord_track_manifest_v1",
        "tracks": [
            {
                "id": "a",
                "datasetId": "sgf_steel_reference",
                "split": "train",
                "splitGroup": "song",
                "labelSource": "weak_chart_alignment",
                "trainingWeight": 0.36,
            }
        ],
    }
    with pytest.raises(ValueError, match="weight ceiling"):
        validate_track_manifest(base)
    base["tracks"][0]["trainingWeight"] = 0.35
    base["tracks"].append({**base["tracks"][0], "id": "b", "split": "test", "trainingWeight": 0})
    with pytest.raises(ValueError, match="Split leakage"):
        validate_track_manifest(base)


def test_weak_label_admission_gate() -> None:
    passing = admit_weak_label(WeakLabelDiagnostics(True, True, 0.91, 0.8))
    failing = admit_weak_label(WeakLabelDiagnostics(True, True, 0.89, 0.95))
    assert passing == {
        "admitted": True,
        "trainingWeight": 0.35,
        "reasons": [],
        "diagnostics": {
            "complete_coverage": True,
            "monotonic_alignment": True,
            "boundary_within_half_beat_fraction": 0.91,
            "dual_reader_duration_agreement": 0.8,
        },
    }
    assert failing["admitted"] is False
    assert failing["trainingWeight"] == 0


def test_chart_reference_uses_explicit_chart_spans_and_reports_admission() -> None:
    timing = {
        "id": "song",
        "engine": "timing-only",
        "durationSeconds": 4,
        "barStartsSeconds": [0, 2],
        "beatTimesSeconds": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5],
    }
    chart = {
        "id": "song-chart",
        "cells": [
            {"cell": 1, "chords": ["C"]},
            {"cell": 2, "chords": ["G7", "C"], "weights": [1, 1]},
        ],
    }
    reader = {
        "engine": "reader-a",
        "segments": [
            {"start": 0, "end": 2, "label": "C"},
            {"start": 2, "end": 3, "label": "G"},
            {"start": 3, "end": 4, "label": "C"},
        ],
    }
    reference, report = build_chart_reference(chart, timing, independent_readers=[reader, reader])
    assert reference["segments"] == [
        {"start": 0.0, "end": 2.0, "label": "C:maj"},
        {"start": 2.0, "end": 3.0, "label": "G:7"},
        {"start": 3.0, "end": 4.0, "label": "C:maj"},
    ]
    assert report["admission"]["admitted"] is True


def test_chart_reference_never_uses_reader_labels_as_ground_truth() -> None:
    timing = {"durationSeconds": 1, "barStartsSeconds": [0], "beatTimesSeconds": [0, 0.5]}
    chart = {"cells": [{"chords": ["F:min"]}]}
    wrong = {"engine": "wrong", "segments": [{"start": 0, "end": 1, "label": "B"}]}
    reference, report = build_chart_reference(chart, timing, independent_readers=[wrong, wrong])
    assert reference["segments"][0]["label"] == "F:min"
    assert report["admission"]["admitted"] is False


def test_catalog_is_valid_and_has_ten_steel_candidates() -> None:
    value = json.loads((ROOT / "chord_reader/datasets/catalog.json").read_text(encoding="utf-8"))
    validate_catalog(value)
    assert {item["id"] for item in value["datasets"]} == {
        "aam",
        "guitarset",
        "lofi_chords",
        "sgf_steel_reference",
    }
    assert len(value["steelReferenceCandidates"]) == 10


def test_segment_metrics_measure_roots_qualities_boundaries_and_edits() -> None:
    reference = [
        {"start": 0, "end": 2, "label": "C"},
        {"start": 2, "end": 4, "label": "G7"},
    ]
    prediction = [
        {"start": 0, "end": 2.1, "label": "C:maj7"},
        {"start": 2.1, "end": 4, "label": "G"},
    ]
    result = score_segments(reference, prediction, boundary_tolerance_seconds=0.25)
    assert result["evaluatedDurationSeconds"] == pytest.approx(4)
    assert result["rootWeightedRecall"] == pytest.approx(0.975)
    assert result["majorMinorWeightedRecall"] == pytest.approx(0.975)
    assert result["detailedWeightedRecall"] == 0
    assert result["boundary"]["f1"] == 1
    assert result["sequenceEditRate"] == pytest.approx(0.5)


def test_cli_scores_json_segments(tmp_path: Path) -> None:
    reference = tmp_path / "reference.json"
    prediction = tmp_path / "prediction.json"
    output = tmp_path / "report.json"
    reference.write_text(json.dumps({"id": "truth", "segments": [{"start": 0, "end": 1, "label": "D"}]}))
    prediction.write_text(json.dumps({"id": "model", "segments": [{"start": 0, "end": 1, "label": "D"}]}))
    result = subprocess.run(
        [sys.executable, "scripts/chord_reader.py", "score", str(reference), str(prediction), "--output", str(output)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["rootWeightedRecall"] == 1
    assert report["referenceId"] == "truth"
    assert report["predictionId"] == "model"


def test_btc_registry_is_pinned_and_snapshot_verification_rejects_changes(tmp_path: Path) -> None:
    registry = load_model_registry()
    assert len(registry["upstream"]["revision"]) == 40
    fixture = tmp_path / "artifact.bin"
    fixture.write_bytes(b"trusted")
    import hashlib

    local_registry = {"files": {"artifact.bin": hashlib.sha256(b"trusted").hexdigest()}}
    verify_model_snapshot(tmp_path, local_registry)
    fixture.write_bytes(b"changed")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_model_snapshot(tmp_path, local_registry)


def test_aam_adapter_collapses_beat_labels_to_chord_segments(tmp_path: Path) -> None:
    path = tmp_path / "0001_beatinfo.arff"
    path.write_text(
        "@RELATION test\n@DATA\n0.0,1,1,'Fmaj'\n0.5,1,2,'Fmaj'\n1.0,1,3,'C7'\n1.5,1,4,'C7'\n",
        encoding="utf-8",
    )
    segments, metadata = parse_aam_beatinfo(path, end_seconds=2.0)
    assert segments == [
        {"start": 0.0, "end": 1.0, "label": "F:maj"},
        {"start": 1.0, "end": 2.0, "label": "C:7"},
    ]
    assert metadata["tempo"] == 120


def test_guitarset_adapter_reads_chord_namespace(tmp_path: Path) -> None:
    path = tmp_path / "track.jams"
    path.write_text(
        json.dumps(
            {
                "file_metadata": {"duration": 2},
                "sandbox": {"tempo": 100, "time_signature": "4/4"},
                "annotations": [
                    {
                        "namespace": "chord",
                        "data": [
                            {"time": 0, "duration": 1, "value": "G:maj"},
                            {"time": 1, "duration": 1, "value": "D:7"},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    segments, metadata = parse_guitarset_jams(path)
    assert segments[-1] == {"start": 1.0, "end": 2.0, "label": "D:7"}
    assert metadata["tempo"] == 100


def test_student_vocabulary_preserves_product_qualities_and_transposes() -> None:
    assert STUDENT_CLASSES == 49
    assert student_label(student_index("Bb:maj7")) == "A#:maj"
    assert student_label(student_index("D:min7")) == "D:min7"
    assert student_label(transpose_student_index(student_index("G:7"), 2)) == "A:7"
    assert student_label(student_index("N")) == "N"


def test_student_frame_labels_use_time_aligned_reference() -> None:
    labels = frame_labels(
        [{"start": 0, "end": 0.2, "label": "C"}, {"start": 0.2, "end": 0.4, "label": "F:min"}],
        5,
    )
    assert [student_label(value) for value in labels] == ["C:maj", "C:maj", "F:min", "F:min", "N"]


def test_promotion_gate_requires_material_gain_and_runtime() -> None:
    def report(engine: str, major_minor: float, root: float, boundary: float) -> dict:
        aggregate = {
            "majorMinorWeightedRecall": major_minor,
            "rootWeightedRecall": root,
            "boundaryF1Macro": boundary,
            "elapsedSeconds": 10,
        }
        return {
            "engine": engine,
            "aggregate": aggregate,
            "strata": {"guitarset": aggregate},
            "peakResidentMemoryBytes": 400_000_000,
            "tracks": [{"audioDurationSeconds": 240}],
        }

    passing = evaluate_promotion(report("v2", 0.4, 0.45, 0.5), report("student", 0.49, 0.51, 0.49))
    failing = evaluate_promotion(report("v2", 0.4, 0.45, 0.5), report("btc", 0.44, 0.48, 0.52))
    assert passing["passed"] is True
    assert failing["passed"] is False


def test_travis_packet_is_blinded_deterministic_and_scores_roles(tmp_path: Path) -> None:
    tracks = [
        {
            "id": f"steel-{number}",
            "split": "steel_test",
            "title": f"Song {number}",
            "audioPath": f"/private/song-{number}.wav",
        }
        for number in range(10)
    ]
    manifest = {"tracks": tracks}
    reports = tmp_path / "reports"
    for role in ("baseline", "challenger"):
        rows = []
        for track in tracks:
            prediction = reports / role / "predictions" / f"{track['id']}.json"
            prediction.parent.mkdir(parents=True, exist_ok=True)
            prediction.write_text(
                json.dumps(
                    {
                        "engine": role,
                        "durationSeconds": 1,
                        "segments": [{"start": 0, "end": 1, "label": "C" if role == "baseline" else "G"}],
                    }
                ),
                encoding="utf-8",
            )
            rows.append({"id": track["id"], "predictionFile": f"predictions/{track['id']}.json"})
        (reports / role / "report.json").write_text(
            json.dumps({"engine": role, "tracks": rows}), encoding="utf-8"
        )
    packet_root = tmp_path / "packet"
    key_path = tmp_path / "sealed-key.json"
    packet, key = build_travis_packet(
        manifest,
        reports / "baseline/report.json",
        reports / "challenger/report.json",
        packet_root,
        key_path,
    )
    assert len(packet["items"]) == 10
    assert "engine" not in json.loads((packet_root / "predictions/01-A.json").read_text(encoding="utf-8"))
    assert {item["A"] for item in key["items"]} == {"baseline", "challenger"}
    for item in packet["items"]:
        item["review"] = {"preferred": "A", "aCorrections": 1, "bCorrections": 2}
    scored = score_travis_review(packet, key)
    assert len(scored["comparisons"]) == 10
    assert all(item["baselineCorrections"] in {1, 2} for item in scored["comparisons"])


def test_travis_packet_rejects_answer_key_inside_packet(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside"):
        build_travis_packet({"tracks": []}, tmp_path / "a.json", tmp_path / "b.json", tmp_path, tmp_path / "key.json")


def test_tracked_student_model_matches_model_card_and_export() -> None:
    model = ROOT / "ui/models/chord-student-v1.onnx"
    card = json.loads((ROOT / "chord_reader/models/chord-student-v1.json").read_text(encoding="utf-8"))
    export = json.loads((ROOT / "chord_reader/models/chord-student-v1-export.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    assert digest == card["model"]["sha256"] == export["sha256"]
    assert model.stat().st_size == card["model"]["bytes"] == export["bytes"]
    assert export["maximumAbsoluteError"] < 1e-4


@pytest.mark.skipif(shutil.which("node") is None or not (ROOT / "node_modules/onnxruntime-web").is_dir(), reason="Node ONNX runtime required")
def test_browser_runtime_executes_student_onnx_on_synthetic_c_major() -> None:
    script = """
      const fs=require('fs'),ort=require('onnxruntime-web'),ml=require('./ui/chord-reader-ml-worker.js');
      (async()=>{ort.env.wasm.numThreads=1;const sr=11025,ms=2000,s=new Float32Array(sr*2);
      for(let i=0;i<s.length;i++){const t=i/sr;s[i]=(Math.sin(2*Math.PI*261.626*t)+Math.sin(2*Math.PI*329.628*t)+Math.sin(2*Math.PI*391.995*t))/3;}
      const f=ml.spectralFeatures(s,sr,ms),session=await ort.InferenceSession.create(new Uint8Array(fs.readFileSync('ui/models/chord-student-v1.onnx')),{executionProviders:['wasm']});
      const r=await session.run({features:new ort.Tensor('float32',f.values,[1,f.frameCount,13])});
      const segments=ml.segmentsFromLogits(r.logits.data,f.frameCount,ms);console.log(JSON.stringify({dims:r.logits.dims,segments}));
      })().catch(e=>{console.error(e);process.exit(1)});
    """
    result = subprocess.run(["node", "-e", script], cwd=ROOT, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["dims"] == [1, 20, 49]
    assert value["segments"][0]["symbol"] == "C"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node required")
def test_browser_client_snaps_ml_segments_to_v2_timing() -> None:
    script = """
      global.window={localStorage:{getItem:()=>null}};require('./ui/practice-analysis-client.js');
      const c=window.STEEL_RAG_ANALYSIS_CLIENT;
      const base={durationMs:4000,barStartsMs:[0,2000],beatTimesMs:[0,500,1000,1500,2000,2500,3000,3500],chords:[]};
      const ml={engine:'chord-student-v1',segments:[{startMs:80,endMs:2080,symbol:'C',confidence:.9},{startMs:2080,endMs:4000,symbol:'G7',confidence:.7}]};
      const result=c.mergeMlAnalysis(base,ml);console.log(JSON.stringify(result));
    """
    result = subprocess.run(["node", "-e", script], cwd=ROOT, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["analysisVersion"] == 3
    assert value["chordReaderEngine"] == "ml-v3"
    assert [(item["bar"], item["symbol"], item["needsAttention"]) for item in value["chords"]] == [
        (1, "C", False),
        (2, "G7", True),
    ]


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("node") is None, reason="Node and FFmpeg required")
def test_v2_adapter_emits_benchmark_segments_for_licensed_fixture(tmp_path: Path) -> None:
    audio = ROOT / "ui/assets/song-practice/amazing-grace-2011-guide.mp3"
    rights = ROOT / "ui/assets/song-practice/amazing-grace-2011-guide.RIGHTS.md"
    output = tmp_path / "v2.json"
    assert audio.is_file() and "CC BY 3.0" in rights.read_text(encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "scripts/chord_reader.py",
            "predict-v2",
            str(audio),
            "--output",
            str(output),
            "--id",
            "amazing-grace-fixture",
            "--key",
            "G",
            "--mode",
            "major",
            "--meter",
            "3/4",
            "--tempo",
            "75",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    prediction = json.loads(output.read_text(encoding="utf-8"))
    assert prediction["schemaVersion"] == "chord_prediction_v1"
    assert prediction["engine"] == "play-along-v2"
    assert prediction["analysisVersion"] == 2
    assert prediction["id"] == "amazing-grace-fixture"
    assert prediction["segments"][0]["start"] == 0
    assert prediction["segments"][-1]["end"] == pytest.approx(prediction["durationSeconds"])
    assert prediction["key"] == "G"
    assert prediction["meter"] == "3/4"
