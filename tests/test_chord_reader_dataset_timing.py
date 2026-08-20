from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import steel_guitar_rag.chord_reader.datasets as datasets
from steel_guitar_rag.chord_reader.datasets import (
    parse_aam_beatinfo,
    parse_guitarset_jams,
    parse_idmt_chords,
    parse_nrgcp_midi,
    prepare_aam,
    prepare_guitarset,
    prepare_nrgcp,
)


def _assert_strict_native_starts(values: list[float]) -> None:
    assert values[0] == 0.0
    assert all(math.isfinite(value) and value >= 0 for value in values)
    assert all(right > left for left, right in zip(values, values[1:]))


def _aam_text() -> str:
    return (
        "@RELATION native-timing\n@DATA\n"
        "0.0,1,1,'Cmaj'\n"
        "0.47,1,2,'Cmaj'\n"
        "1.01,1,3,'Cmaj'\n"
        "1.60,1,4,'Cmaj'\n"
        "2.18,2,1,'G7'\n"
        "2.70,2,2,'G7'\n"
    )


def test_aam_preserves_variable_native_beat_and_bar_times(tmp_path: Path) -> None:
    annotation = tmp_path / "0001_beatinfo.arff"
    annotation.write_text(_aam_text(), encoding="utf-8")

    _segments, metadata = parse_aam_beatinfo(annotation, end_seconds=3.2)

    assert metadata["beatTimesSeconds"] == [0.0, 0.47, 1.01, 1.6, 2.18, 2.7]
    assert metadata["barStartsSeconds"] == [0.0, 2.18]
    _assert_strict_native_starts(metadata["beatTimesSeconds"])
    _assert_strict_native_starts(metadata["barStartsSeconds"])
    assert metadata["timingProvenance"]["barStartsSeconds"] == {
        "status": "explicit",
        "sourceRule": "column-2-quarter-count-equals-1",
    }


def test_aam_preparer_copies_exact_timing_and_provenance(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations"
    audio = tmp_path / "audio"
    annotations.mkdir()
    audio.mkdir()
    (annotations / "0001_beatinfo.arff").write_text(_aam_text(), encoding="utf-8")
    (audio / "0001.wav").write_bytes(b"manifest-only fixture")

    manifest = prepare_aam(annotations, audio, tmp_path / "prepared")

    track = manifest["tracks"][0]
    assert track["beatTimesSeconds"] == [0.0, 0.47, 1.01, 1.6, 2.18, 2.7]
    assert track["barStartsSeconds"] == [0.0, 2.18]
    assert track["timingProvenance"]["sourceFormat"] == "aam-beatinfo-arff"


def _guitarset_value() -> dict[str, Any]:
    beat_times = (0.0, 0.49, 1.03, 1.55, 2.12, 2.61)
    return {
        "file_metadata": {"duration": 3.0, "title": "00_BN1-129-Eb_comp"},
        "sandbox": {"tempo": 112, "time_signature": "4/4"},
        "annotations": [
            {
                "namespace": "chord",
                "data": [
                    {"time": 0, "duration": 2.12, "value": "C:maj"},
                    {"time": 2.12, "duration": 0.88, "value": "G:7"},
                ],
            },
            {
                "namespace": "chord",
                "annotation_metadata": {
                    "annotation_rules": (
                        "Chord sheet-informed symbolic chord transcription based on the "
                        "included separate string note transcriptions with the chord "
                        "segmentation and root derived from sheet music."
                    ),
                    "data_source": "Semi-automatic chord transcription with manual verification",
                },
                "data": [
                    {"time": 0, "duration": 2.12, "value": "C:maj7/1"},
                    {"time": 2.12, "duration": 0.88, "value": "G:maj/5"},
                ],
            },
            {
                "namespace": "beat_position",
                "data": [
                    {
                        "time": time,
                        "duration": 0,
                        "value": {
                            "position": 1 if index in {0, 4} else index % 4 + 1,
                            "measure": index // 4,
                            "num_beats": 4,
                            "beat_units": 4,
                        },
                    }
                    for index, time in enumerate(beat_times)
                ],
            },
        ],
    }


def test_guitarset_uses_beat_position_for_beats_and_downbeats(tmp_path: Path) -> None:
    annotation = tmp_path / "track.jams"
    annotation.write_text(json.dumps(_guitarset_value()), encoding="utf-8")

    _segments, metadata = parse_guitarset_jams(annotation)

    assert metadata["beatTimesSeconds"] == [0.0, 0.49, 1.03, 1.55, 2.12, 2.61]
    assert metadata["downbeatTimesSeconds"] == [0.0, 2.12]
    assert metadata["barStartsSeconds"] == [0.0, 2.12]
    _assert_strict_native_starts(metadata["beatTimesSeconds"])
    _assert_strict_native_starts(metadata["downbeatTimesSeconds"])
    assert metadata["timingProvenance"]["downbeatTimesSeconds"]["sourceRule"] == (
        "beat_position.value.position-equals-1"
    )
    assert metadata["timingProvenance"]["instructedChordSegmentsSeconds"]["annotationRole"] == (
        "instructed"
    )
    assert metadata["timingProvenance"]["performedChordSegmentsSeconds"]["annotationRole"] == (
        "performed"
    )


def test_guitarset_selects_roles_independently_of_annotation_order(tmp_path: Path) -> None:
    value = _guitarset_value()
    instructed, performed, beats = value["annotations"]
    value["annotations"] = [performed, beats, instructed]
    annotation = tmp_path / "00_BN1-129-Eb_comp.jams"
    annotation.write_text(json.dumps(value), encoding="utf-8")

    segments, metadata = parse_guitarset_jams(annotation)

    assert segments == [
        {"start": 0.0, "end": 2.12, "label": "C:maj"},
        {"start": 2.12, "end": 3.0, "label": "G:7"},
    ]
    assert metadata["performedSegments"] == [
        {"start": 0.0, "end": 2.12, "label": "C:maj7/1"},
        {"start": 2.12, "end": 3.0, "label": "G:maj/5"},
    ]
    assert metadata["chordProvenance"]["primaryReference"]["selectionRule"] == (
        "official-unmarked-lead-sheet-counterpart"
    )
    assert metadata["chordProvenance"]["performedReference"]["sourceNamespace"] == "chord"
    assert metadata["chordProvenance"]["performedReference"]["segmentationSource"] == (
        "instructed-chord-sheet"
    )
    assert metadata["chordProvenance"]["performedReference"]["rootSource"] == (
        "instructed-chord-sheet"
    )
    assert metadata["chordProvenance"]["performedReference"]["qualityEvidence"] == (
        "separate-string-note-transcriptions"
    )


def test_guitarset_preserves_explicit_half_open_gaps(tmp_path: Path) -> None:
    value = _guitarset_value()
    value["annotations"][0]["data"] = [
        {"time": 0.0, "duration": 0.75, "value": "C:maj"},
        {"time": 1.25, "duration": 0.5, "value": "G:7"},
    ]
    value["annotations"][1]["data"] = [
        {"time": 0.0, "duration": 0.5, "value": "C:maj7/1"},
        {"time": 1.0, "duration": 0.5, "value": "G:maj/5"},
    ]
    annotation = tmp_path / "00_BN1-129-Eb_comp.jams"
    annotation.write_text(json.dumps(value), encoding="utf-8")

    segments, metadata = parse_guitarset_jams(annotation)

    assert segments == [
        {"start": 0.0, "end": 0.75, "label": "C:maj"},
        {"start": 1.25, "end": 1.75, "label": "G:7"},
    ]
    assert metadata["performedSegments"] == [
        {"start": 0.0, "end": 0.5, "label": "C:maj7/1"},
        {"start": 1.0, "end": 1.5, "label": "G:maj/5"},
    ]


def test_guitarset_does_not_merge_same_label_across_a_gap(tmp_path: Path) -> None:
    value = _guitarset_value()
    value["annotations"][0]["data"] = [
        {"time": 0.0, "duration": 0.5, "value": "C:maj"},
        {"time": 1.0, "duration": 0.5, "value": "C:maj"},
    ]
    annotation = tmp_path / "00_BN1-129-Eb_comp.jams"
    annotation.write_text(json.dumps(value), encoding="utf-8")

    segments, _metadata = parse_guitarset_jams(annotation)

    assert segments == [
        {"start": 0.0, "end": 0.5, "label": "C:maj"},
        {"start": 1.0, "end": 1.5, "label": "C:maj"},
    ]


@pytest.mark.parametrize("annotation_index", [0, 1])
def test_guitarset_rejects_overlapping_chord_intervals(
    tmp_path: Path,
    annotation_index: int,
) -> None:
    value = _guitarset_value()
    value["annotations"][annotation_index]["data"][0]["duration"] = 2.5
    annotation = tmp_path / "00_BN1-129-Eb_comp.jams"
    annotation.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="Overlapping GuitarSet"):
        parse_guitarset_jams(annotation)


def test_guitarset_fails_closed_on_missing_or_ambiguous_chord_roles(tmp_path: Path) -> None:
    missing = _guitarset_value()
    missing["annotations"].pop(1)
    missing_path = tmp_path / "missing_comp.jams"
    missing_path.write_text(json.dumps(missing), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one instructed and one performed"):
        parse_guitarset_jams(missing_path)

    ambiguous = _guitarset_value()
    ambiguous["annotations"][0]["annotation_metadata"] = {"annotationRole": "performed"}
    ambiguous_path = tmp_path / "ambiguous_comp.jams"
    ambiguous_path.write_text(json.dumps(ambiguous), encoding="utf-8")
    with pytest.raises(ValueError, match="Multiple GuitarSet performed"):
        parse_guitarset_jams(ambiguous_path)


def test_guitarset_requires_consistent_comp_or_solo_identity(tmp_path: Path) -> None:
    solo = _guitarset_value()
    solo["file_metadata"]["title"] = "00_BN1-129-Eb_solo"
    solo_path = tmp_path / "00_BN1-129-Eb_solo.jams"
    solo_path.write_text(json.dumps(solo), encoding="utf-8")
    assert parse_guitarset_jams(solo_path)[1]["performanceRole"] == "solo"

    missing = _guitarset_value()
    missing["file_metadata"]["title"] = "00_BN1-129-Eb"
    missing_path = tmp_path / "missing.jams"
    missing_path.write_text(json.dumps(missing), encoding="utf-8")
    with pytest.raises(ValueError, match="Missing GuitarSet comp/solo"):
        parse_guitarset_jams(missing_path)

    conflicting = _guitarset_value()
    conflicting["file_metadata"]["title"] = "00_BN1-129-Eb_solo"
    conflicting_path = tmp_path / "00_BN1-129-Eb_comp.jams"
    conflicting_path.write_text(json.dumps(conflicting), encoding="utf-8")
    with pytest.raises(ValueError, match="Conflicting GuitarSet comp/solo"):
        parse_guitarset_jams(conflicting_path)


def test_guitarset_preparer_preserves_native_timing(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations"
    audio = tmp_path / "audio"
    annotations.mkdir()
    audio.mkdir()
    name = "00_BN1-129-Eb_comp"
    (annotations / f"{name}.jams").write_text(
        json.dumps(_guitarset_value()),
        encoding="utf-8",
    )
    (audio / f"{name}.wav").write_bytes(b"manifest-only fixture")

    manifest = prepare_guitarset(annotations, audio, tmp_path / "prepared")

    track = manifest["tracks"][0]
    assert track["beatTimesSeconds"] == [0.0, 0.49, 1.03, 1.55, 2.12, 2.61]
    assert track["barStartsSeconds"] == [0.0, 2.12]
    assert track["timingProvenance"]["sourceFormat"] == (
        "guitarset-jams-beat_position"
    )
    assert track["performanceRole"] == "comp"
    assert track["labelSource"] == "ground_truth"
    assert track["labelSourceProvenance"]["annotationRole"] == "instructed"
    assert track["labelSourceProvenance"]["sourceNamespace"] == "chord"

    primary = json.loads(Path(track["referencePath"]).read_text(encoding="utf-8"))
    assert primary == {
        "schemaVersion": "chord_reference_v1",
        "id": f"guitarset-{name}",
        "segments": [
            {"start": 0.0, "end": 2.12, "label": "C:maj"},
            {"start": 2.12, "end": 3.0, "label": "G:7"},
        ],
    }
    performed = json.loads(Path(track["performedReferencePath"]).read_text(encoding="utf-8"))
    assert performed["segments"] == [
        {"start": 0.0, "end": 2.12, "label": "C:maj7/1"},
        {"start": 2.12, "end": 3.0, "label": "G:maj/5"},
    ]
    assert performed["provenance"]["annotationRole"] == "performed"
    assert performed["provenance"]["labelEncoding"] == "guitarset-harte"


def _message(kind: str, time: int = 0, **values: Any) -> SimpleNamespace:
    defaults = {"velocity": 0, "note": 0, "numerator": 4, "denominator": 4, "tempo": 500_000}
    return SimpleNamespace(type=kind, time=time, **{**defaults, **values})


def _certified_midi_messages() -> list[SimpleNamespace]:
    return [
        _message("set_tempo", tempo=500_000),
        _message("time_signature", numerator=4, denominator=4),
        _message("note_on", velocity=90, note=48),
        _message("note_on", velocity=90, note=52),
        _message("note_on", velocity=90, note=55),
        _message("set_tempo", time=1920, tempo=1_000_000),
        _message("note_on", velocity=90, note=53),
        _message("note_on", velocity=90, note=57),
        _message("note_on", velocity=90, note=60),
        _message("end_of_track", time=1920),
    ]


def _fake_mido(monkeypatch: pytest.MonkeyPatch, messages: list[SimpleNamespace]) -> None:
    midi = SimpleNamespace(ticks_per_beat=480, tracks=[messages])
    fake = SimpleNamespace(
        MidiFile=lambda _path: midi,
        merge_tracks=lambda tracks: list(tracks[0]),
    )
    real_import = datasets.importlib.import_module
    monkeypatch.setattr(
        datasets.importlib,
        "import_module",
        lambda name: fake if name == "mido" else real_import(name),
    )


def test_nrgcp_certifies_bar_ticks_through_variable_tempo_map(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_mido(monkeypatch, _certified_midi_messages())

    segments, metadata = parse_nrgcp_midi(tmp_path / "song.mid")

    assert segments == [
        {"start": 0.0, "end": 2.0, "label": "C:maj"},
        {"start": 2.0, "end": 6.0, "label": "F:maj"},
    ]
    assert metadata["durationSeconds"] == 6.0
    assert metadata["tempo"] is None
    assert metadata["barStartsSeconds"] == [0.0, 2.0]
    _assert_strict_native_starts(metadata["barStartsSeconds"])
    assert metadata["timingProvenance"]["tempoMap"] == [
        {"tick": 0, "microsecondsPerQuarter": 500_000, "timeSeconds": 0.0},
        {"tick": 1920, "microsecondsPerQuarter": 1_000_000, "timeSeconds": 2.0},
    ]
    assert metadata["timingProvenance"]["barStartsSeconds"]["status"] == "explicit"


def test_nrgcp_preparer_copies_certified_bar_timing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_mido(monkeypatch, _certified_midi_messages())
    annotations = tmp_path / "annotations"
    audio = tmp_path / "audio"
    annotations.mkdir()
    audio.mkdir()
    (annotations / "song_nrgcp_dataset.mid").write_bytes(b"fake-midi")
    (audio / "nrgcp-song.wav").write_bytes(b"manifest-only fixture")

    manifest = prepare_nrgcp(annotations, audio, tmp_path / "prepared")

    track = manifest["tracks"][0]
    assert track["barStartsSeconds"] == [0.0, 2.0]
    assert track["timingProvenance"]["barStartsSeconds"]["barPhaseAnchorTick"] == 0


def test_nrgcp_leaves_bar_phase_uncertifiable_without_signature_at_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = [
        _message("set_tempo", tempo=500_000),
        _message("note_on", velocity=90, note=48),
        _message("note_on", velocity=90, note=52),
        _message("note_on", velocity=90, note=55),
        _message("time_signature", time=480, numerator=4, denominator=4),
        _message("end_of_track", time=1440),
    ]
    _fake_mido(monkeypatch, messages)

    _segments, metadata = parse_nrgcp_midi(tmp_path / "uncertifiable.mid")

    assert "barStartsSeconds" not in metadata
    assert metadata["meter"] is None
    bar_provenance = metadata["timingProvenance"]["barStartsSeconds"]
    assert bar_provenance["status"] == "uncertifiable"
    assert "tick zero" in bar_provenance["reason"]


def test_idmt_marks_only_annotation_backed_bar_phase_as_explicit(tmp_path: Path) -> None:
    explicit = tmp_path / "country_120BPM.csv"
    explicit.write_text(
        "0.0,1.1:C\n0.5,1.2\n1.0,1.3\n1.5,1.4\n"
        "2.0,2.1:G7\n2.5,2.2\n1,1\n4,4\n",
        encoding="utf-8",
    )
    _segments, metadata = parse_idmt_chords(explicit, end_seconds=3.0)
    assert metadata["barStartsSeconds"] == [0.0, 2.0]
    assert metadata["timingProvenance"]["barStartsSeconds"]["status"] == "explicit"
    assert metadata["timingProvenance"]["tempo"] == {
        "status": "derived",
        "sourceRule": "filename BPM suffix",
        "establishesBarPhase": False,
    }

    nonzero = tmp_path / "country_intro_120BPM.csv"
    nonzero.write_text(
        "0.5,1.1:C\n1.0,1.2\n1.5,1.3\n2.0,1.4\n1,1\n4,4\n",
        encoding="utf-8",
    )
    _segments, nonzero_metadata = parse_idmt_chords(nonzero, end_seconds=2.5)
    assert nonzero_metadata["barStartsSeconds"] == [0.5]
    assert nonzero_metadata["gridStartSeconds"] == 0.5
    assert nonzero_metadata["prefixExcludedSeconds"] == 0.5
    assert nonzero_metadata["timingProvenance"]["barStartsSeconds"] == {
        "status": "explicit",
        "sourceRule": "annotated beat-number-equals-1",
        "gridStartSeconds": 0.5,
        "prefixExcludedSeconds": 0.5,
    }


def test_native_timing_rejects_nonfinite_or_duplicate_source_starts(tmp_path: Path) -> None:
    aam = tmp_path / "bad_beatinfo.arff"
    aam.write_text(
        "@DATA\n0.0,1,1,'C'\nnan,1,2,'C'\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="finite"):
        parse_aam_beatinfo(aam)

    guitarset = _guitarset_value()
    beat_annotation = next(
        item for item in guitarset["annotations"] if item["namespace"] == "beat_position"
    )
    beat_annotation["data"][1]["time"] = 0.0
    jams = tmp_path / "duplicate.jams"
    jams.write_text(json.dumps(guitarset), encoding="utf-8")
    with pytest.raises(ValueError, match="strictly increasing"):
        parse_guitarset_jams(jams)
