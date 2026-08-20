from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

import numpy as np
import pytest

import steel_guitar_rag.chord_reader.artifact_integrity as artifact_integrity
import steel_guitar_rag.chord_reader.harmonic_prior as harmonic_prior
from steel_guitar_rag.chord_reader.artifact_integrity import (
    seal_factorized_artifact_manifest,
)
from steel_guitar_rag.chord_reader.harmonic_prior import (
    FACTORIZED_PRODUCTS,
    HarmonicPriorIntegrityError,
    build_harmonic_prior,
    canonical_harmonic_prior_json,
    compile_harmonic_prior_scorer,
    load_harmonic_prior_artifact,
    score_harmonic_duration,
    score_harmonic_span,
    score_harmonic_transition,
    validate_harmonic_prior_artifact,
    write_harmonic_prior_artifact,
)
from steel_guitar_rag.chord_reader.split_protocol import (
    build_leak_resistant_split_manifest,
)


def _write_feature(path: Path, frames: int, *, training_weight: float = 1.0) -> None:
    np.savez_compressed(
        path,
        features=np.zeros((frames, 13), dtype=np.float16),
        labels=np.zeros(frames, dtype=np.int64),
        label_valid=np.ones(frames, dtype=np.bool_),
        training_weight=np.asarray(training_weight, dtype=np.float32),
    )


def _label_values(
    *,
    semitones: int = 0,
    incoherent: bool = False,
    variant: str = "default",
) -> dict[str, np.ndarray]:
    # C(2 frames) -> G(2) -> N(1) -> Am(3) -> E7(1).  Every pitched
    # root is transposed together so the relative transitions remain fixed.
    if variant == "default":
        roots = np.asarray([1, 1, 8, 8, 0, 10, 10, 10, 5], dtype=np.int64)
        products = np.asarray([1, 1, 1, 1, 0, 2, 2, 2, 3], dtype=np.int64)
    elif variant == "minor-seventh-only":
        roots = np.asarray([1, 1, 1, 6, 6, 6, 8, 8, 8], dtype=np.int64)
        products = np.full(len(roots), 4, dtype=np.int64)
    else:  # pragma: no cover - fixture misuse
        raise ValueError(f"Unknown label fixture variant {variant!r}.")
    roots = np.where(roots == 0, 0, 1 + ((roots - 1 + semitones) % 12))
    if incoherent:
        roots[0] = 0
        products[0] = 1
    boundary = np.zeros(len(roots), dtype=np.float32)
    boundary[1:] = (
        (roots[1:] != roots[:-1]) | (products[1:] != products[:-1])
    ).astype(np.float32)
    return {
        "root": roots,
        "mode": np.where(
            products == 0,
            0,
            np.where(np.isin(products, [2, 4]), 2, 1),
        ).astype(np.int64),
        "product": products,
        "structure": np.where(products == 0, 0, 1).astype(np.int64),
        "quality": np.where(products == 0, -1, 0).astype(np.int64),
        "bass": np.zeros(len(roots), dtype=np.int64),
        "boundary": boundary,
        "label_valid": np.ones(len(roots), dtype=np.bool_),
    }


def _write_labels(
    path: Path,
    *,
    semitones: int = 0,
    incoherent: bool = False,
    boundary_nan: bool = False,
    variant: str = "default",
) -> None:
    values = _label_values(
        semitones=semitones,
        incoherent=incoherent,
        variant=variant,
    )
    if boundary_nan:
        values["boundary"][0] = np.nan
    np.savez_compressed(path, **values)


def _sealed_split(
    root: Path,
    *,
    semitones: int = 0,
    incoherent: bool = False,
    training_weights: Mapping[str, float] | None = None,
    training_weight_overrides: Mapping[str, float] | None = None,
    variants: Mapping[str, str] | None = None,
) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    frames = len(_label_values()["root"])
    tracks = []
    for index in range(7):
        identifier = f"track-{index}"
        feature = root / f"{identifier}-feature.npz"
        labels = root / f"{identifier}-labels.npz"
        _write_feature(
            feature,
            frames,
            training_weight=float((training_weights or {}).get(identifier, 1.0)),
        )
        _write_labels(
            labels,
            semitones=semitones,
            incoherent=incoherent,
            variant=(variants or {}).get(identifier, "default"),
        )
        track = {
            "id": identifier,
            "datasetId": "fixture-dataset",
            "compositionId": f"composition-{index}",
            "split": "test" if index == 6 else "train",
            "path": str(feature.resolve()),
            "factorizedLabelsPath": str(labels.resolve()),
            "frames": frames,
            "durationSeconds": frames * 0.1,
            "trainingWeight": 1.0,
        }
        if identifier in (training_weight_overrides or {}):
            track["trainingWeightOverride"] = float(
                (training_weight_overrides or {})[identifier]
            )
        tracks.append(track)
    source = {
        "schemaVersion": "chord_factorized_label_cache_v2",
        "featureKind": "worker_chroma_v1",
        "featureCount": 13,
        "sampleRate": 11_025,
        "frameSeconds": 0.1,
        "factorizedVocabulary": {
            "qualities": ["maj"],
            "modes": ["none", "major", "minor", "neutral"],
            "products": list(FACTORIZED_PRODUCTS),
            "structures": ["none", "triad"],
            "rootClasses": 13,
            "bassClasses": 13,
        },
        "tracks": tracks,
    }
    sealed = seal_factorized_artifact_manifest(source)
    return build_leak_resistant_split_manifest(
        sealed,
        seed="harmonic-prior-fixture",
        excluded_source_splits=("test",),
    )


def _rehash(artifact: dict) -> None:
    unsigned = deepcopy(artifact)
    unsigned.pop("artifactSha256", None)
    payload = json.dumps(
        unsigned,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    artifact["artifactSha256"] = hashlib.sha256(payload).hexdigest()


def test_harmonic_prior_is_transposition_invariant_and_has_no_absolute_states(
    tmp_path: Path,
) -> None:
    original_manifest = _sealed_split(tmp_path / "original", semitones=0)
    shifted_manifest = _sealed_split(tmp_path / "shifted", semitones=5)

    original = build_harmonic_prior(original_manifest, max_duration_frames=4)
    shifted = build_harmonic_prior(shifted_manifest, max_duration_frames=4)

    assert original["transitionModel"] == shifted["transitionModel"]
    assert original["durationModel"] == shifted["durationModel"]
    assert original["trainingSummary"] == shifted["trainingSummary"]
    model_json = json.dumps(
        {
            "transitionModel": original["transitionModel"],
            "durationModel": original["durationModel"],
        }
    )
    assert "datasetId" not in model_json
    assert "fixture-dataset" not in model_json
    assert str(tmp_path) not in canonical_harmonic_prior_json(original)
    for row in original["transitionModel"]["rows"]:
        for outcome in row["outcomes"]:
            assert outcome["rootRelation"] in {
                "no-chord",
                "entry",
                *range(12),
            }


def test_builder_opens_only_train_projection_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _sealed_split(tmp_path)
    train_ids = {
        str(track["id"])
        for track in manifest["tracks"]
        if track["split"] == "train"
    }
    blocked_paths = {
        str(entry[path_name])
        for entry in manifest["artifactIntegrity"]["tracks"]
        if str(entry["id"]) not in train_ids
        for path_name in ("featurePath", "factorizedLabelsPath")
    }
    original_load_arrays = artifact_integrity._load_arrays
    original_os_open = harmonic_prior.os.open

    def guarded_load_arrays(path: Path, *args: object, **kwargs: object) -> dict:
        assert str(path) not in blocked_paths
        return original_load_arrays(path, *args, **kwargs)

    monkeypatch.setattr(artifact_integrity, "_load_arrays", guarded_load_arrays)

    def guarded_os_open(path: object, *args: object, **kwargs: object) -> int:
        assert str(path) not in blocked_paths
        return original_os_open(path, *args, **kwargs)

    monkeypatch.setattr(harmonic_prior.os, "open", guarded_os_open)

    artifact = build_harmonic_prior(manifest, max_duration_frames=4)

    assert artifact["provenance"]["trainTrackCount"] == len(train_ids)
    assert len(train_ids) < manifest["artifactIntegrity"]["trackCount"]


def test_artifact_hash_and_canonical_file_are_deterministic(tmp_path: Path) -> None:
    manifest = _sealed_split(tmp_path / "cache")

    first = build_harmonic_prior(manifest, max_duration_frames=4)
    second = build_harmonic_prior(manifest, max_duration_frames=4)
    first_path = write_harmonic_prior_artifact(first, tmp_path / "first.json")
    second_path = write_harmonic_prior_artifact(second, tmp_path / "second.json")

    assert first == second
    assert first["artifactSha256"] == second["artifactSha256"]
    assert first_path.read_bytes() == second_path.read_bytes()
    assert load_harmonic_prior_artifact(
        first_path,
        expected_split_manifest=manifest,
    ) == first


def test_smoothing_keeps_all_transition_and_duration_scores_finite(
    tmp_path: Path,
) -> None:
    artifact = build_harmonic_prior(
        _sealed_split(tmp_path),
        smoothing_alpha=0.25,
        max_duration_frames=4,
    )

    assert any(
        outcome["count"] == 0
        for row in artifact["transitionModel"]["rows"]
        for outcome in row["outcomes"]
    )
    for row in artifact["transitionModel"]["rows"]:
        probabilities = [math.exp(item["logProbability"]) for item in row["outcomes"]]
        assert all(math.isfinite(value) for value in probabilities)
        assert math.fsum(probabilities) == pytest.approx(1.0, abs=1e-12)
    for row in artifact["durationModel"]["rows"]:
        probabilities = [math.exp(value) for value in row["logProbabilities"]]
        assert all(math.isfinite(value) for value in probabilities)
        assert math.fsum(probabilities) == pytest.approx(1.0, abs=1e-12)


def test_zero_weight_is_exactly_neutral(tmp_path: Path) -> None:
    artifact = build_harmonic_prior(_sealed_split(tmp_path), max_duration_frames=4)

    transition = score_harmonic_transition(
        artifact,
        previous_root=1,
        previous_product=1,
        next_root=8,
        next_product=1,
        weight=0.0,
    )
    duration = score_harmonic_duration(
        artifact,
        root=1,
        product=1,
        duration_frames=2,
        weight=0.0,
    )
    span = score_harmonic_span(
        artifact,
        root=1,
        product=1,
        start_frame=4,
        end_frame=6,
        weight=0.0,
    )

    assert transition == 0.0 and math.copysign(1.0, transition) == 1.0
    assert duration == 0.0 and math.copysign(1.0, duration) == 1.0
    assert span == 0.0 and math.copysign(1.0, span) == 1.0


def test_prior_uses_cached_weight_times_override_and_ignores_zero_mass(
    tmp_path: Path,
) -> None:
    probe = _sealed_split(tmp_path / "probe")
    train_ids = sorted(
        str(track["id"])
        for track in probe["tracks"]
        if track["split"] == "train"
    )
    zero_id, downweighted_id = train_ids[:2]
    manifest = _sealed_split(
        tmp_path / "weighted",
        training_weights={zero_id: 0.0, downweighted_id: 0.25},
        training_weight_overrides={downweighted_id: 2.0},
        variants={
            zero_id: "minor-seventh-only",
            downweighted_id: "minor-seventh-only",
        },
    )

    artifact = build_harmonic_prior(manifest, max_duration_frames=4)

    train_count = len(train_ids)
    summary = artifact["trainingSummary"]
    assert summary["cachedTrackWeightSum"] == pytest.approx(train_count - 1.75)
    assert summary["effectiveTrackWeightSum"] == pytest.approx(train_count - 1.5)
    assert summary["positiveWeightTrackCount"] == train_count - 1
    assert summary["zeroWeightTrackCount"] == 1
    assert summary["overriddenTrackCount"] == 1
    assert artifact["provenance"]["trainingWeightPolicy"] == (
        "sealed_feature_training_weight_times_trainingWeightOverride_v1"
    )

    transition_row = artifact["transitionModel"]["rows"][4]
    assert transition_row["observedTransitionCount"] == 4
    assert transition_row["observedTransitionWeight"] == pytest.approx(1.0)
    duration_row = artifact["durationModel"]["rows"][4]
    assert duration_row["segmentCount"] == 6
    assert duration_row["segmentWeight"] == pytest.approx(1.5)
    assert duration_row["histogramCounts"][2] == 6
    assert duration_row["histogramWeights"][2] == pytest.approx(1.5)


def test_compiled_scorer_validates_once_and_zero_weight_skips_artifact_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = build_harmonic_prior(_sealed_split(tmp_path), max_duration_frames=4)
    calls = 0
    original_validate = harmonic_prior.validate_harmonic_prior_artifact

    def counted_validate(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(
        harmonic_prior,
        "validate_harmonic_prior_artifact",
        counted_validate,
    )
    scorer = compile_harmonic_prior_scorer(artifact)
    assert calls == 1
    assert isinstance(scorer.transition_log_probabilities, tuple)
    assert isinstance(scorer.duration_log_probabilities, tuple)
    with pytest.raises(AttributeError):
        setattr(scorer, "max_duration_frames", 999)

    for _ in range(5):
        score_harmonic_transition(
            scorer,
            previous_root=1,
            previous_product=1,
            next_root=8,
            next_product=1,
            weight=0.25,
        )
        score_harmonic_duration(
            scorer,
            root=1,
            product=1,
            duration_frames=2,
            weight=0.25,
        )
    assert calls == 1
    assert score_harmonic_transition(
        {},
        previous_root=-999,
        previous_product=-999,
        next_root=-999,
        next_product=-999,
        weight=0.0,
    ) == 0.0
    assert calls == 1
    with pytest.raises(HarmonicPriorIntegrityError, match="prevalidated compiled scorer"):
        score_harmonic_transition(
            artifact,
            previous_root=1,
            previous_product=1,
            next_root=8,
            next_product=1,
            weight=0.25,
        )


def test_duration_and_transition_scoring_use_learned_relative_statistics(
    tmp_path: Path,
) -> None:
    artifact = build_harmonic_prior(_sealed_split(tmp_path), max_duration_frames=4)
    scorer = compile_harmonic_prior_scorer(artifact)

    observed_duration = score_harmonic_duration(
        scorer,
        root=1,
        product=1,
        duration_frames=2,
        weight=1.0,
    )
    unseen_duration = score_harmonic_duration(
        scorer,
        root=1,
        product=1,
        duration_frames=4,
        weight=1.0,
    )
    overflow = score_harmonic_duration(
        scorer,
        root=1,
        product=1,
        duration_frames=50,
        weight=1.0,
    )
    first_overflow = score_harmonic_duration(
        scorer,
        root=1,
        product=1,
        duration_frames=5,
        weight=1.0,
    )
    relative = score_harmonic_transition(
        scorer,
        previous_root=1,
        previous_product=1,
        next_root=8,
        next_product=1,
        weight=1.0,
    )
    transposed = score_harmonic_transition(
        scorer,
        previous_root=3,
        previous_product=1,
        next_root=10,
        next_product=1,
        weight=1.0,
    )

    assert observed_duration > unseen_duration
    assert overflow == first_overflow
    assert score_harmonic_span(
        scorer,
        root=1,
        product=1,
        start_frame=10,
        end_frame=12,
        weight=1.0,
    ) == observed_duration
    assert relative == transposed


def test_builder_rejects_tampered_train_sidecar_and_incoherent_labels(
    tmp_path: Path,
) -> None:
    manifest = _sealed_split(tmp_path / "tamper")
    train_track = next(track for track in manifest["tracks"] if track["split"] == "train")
    _write_labels(Path(train_track["factorizedLabelsPath"]), semitones=1)

    with pytest.raises(HarmonicPriorIntegrityError, match="Training artifacts changed"):
        build_harmonic_prior(manifest, max_duration_frames=4)

    incoherent = _sealed_split(tmp_path / "incoherent", incoherent=True)
    with pytest.raises(HarmonicPriorIntegrityError, match="incoherent root/product"):
        build_harmonic_prior(incoherent, max_duration_frames=4)


def test_nan_sidecar_cannot_enter_a_sealed_builder_input(tmp_path: Path) -> None:
    manifest = _sealed_split(tmp_path / "nan")
    train_track = next(track for track in manifest["tracks"] if track["split"] == "train")
    _write_labels(Path(train_track["factorizedLabelsPath"]), boundary_nan=True)

    with pytest.raises(HarmonicPriorIntegrityError, match="Training artifacts changed"):
        build_harmonic_prior(manifest, max_duration_frames=4)


def test_artifact_and_provenance_tamper_are_rejected(tmp_path: Path) -> None:
    manifest = _sealed_split(tmp_path / "source-a")
    other_manifest = _sealed_split(tmp_path / "source-b", semitones=2)
    artifact = build_harmonic_prior(manifest, max_duration_frames=4)

    count_tamper = deepcopy(artifact)
    count_tamper["transitionModel"]["rows"][1]["outcomes"][0]["count"] += 1
    with pytest.raises(HarmonicPriorIntegrityError, match="artifact hash mismatch"):
        validate_harmonic_prior_artifact(count_tamper)

    provenance_tamper = deepcopy(artifact)
    provenance_tamper["provenance"]["sourceManifestSha256"] = "0" * 64
    _rehash(provenance_tamper)
    with pytest.raises(HarmonicPriorIntegrityError, match="does not match the supplied"):
        validate_harmonic_prior_artifact(
            provenance_tamper,
            expected_split_manifest=manifest,
        )
    with pytest.raises(HarmonicPriorIntegrityError, match="does not match the supplied"):
        validate_harmonic_prior_artifact(
            artifact,
            expected_split_manifest=other_manifest,
        )
