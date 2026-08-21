from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect
import json
import math

import numpy as np
import pytest

from steel_guitar_rag.chord_reader.bar_uncertainty import (
    BAR_FEATURE_CONTRACT_SHA256,
    BAR_FEATURE_NAMES,
    BAR_UNCERTAINTY_SCHEMA,
    summarize_prediction_bars,
)
from steel_guitar_rag.chord_reader.labels import PITCH_CLASS, normalize_chord
from steel_guitar_rag.chord_reader.uncertainty import (
    attach_uncertainty,
    build_factorized_uncertainty,
)


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _uncertainty(
    duration: float,
    *,
    root_selected: list[float] | None = None,
    product_selected: list[float] | None = None,
    boundary: list[float] | None = None,
    representation_rms: list[float] | None = None,
) -> dict:
    frame_count = math.ceil(duration / 0.1)

    def values(value: float) -> list[float]:
        return [value] * frame_count

    root_selected = root_selected or values(0.8)
    product_selected = product_selected or values(0.7)
    boundary = boundary or values(0.25)
    representation_rms = representation_rms or values(1.0)
    root_logits = np.zeros((frame_count, 13), dtype=np.float32)
    root_logits[:, 1] = 1.0
    product_logits = np.zeros((frame_count, 5), dtype=np.float32)
    product_logits[:, 1] = 1.0
    boundary_logits = np.zeros((frame_count, 1), dtype=np.float32)
    heads = {
        "root": root_logits,
        "product": product_logits,
        "boundary": boundary_logits,
    }
    uncertainty = build_factorized_uncertainty(
        numpy=np,
        features=np.zeros((frame_count, 61), dtype=np.float32),
        duration_seconds=duration,
        frame_seconds=0.1,
        feature_kind="multiband_chroma_v2",
        feature_count=61,
        feature_spec_sha256="b" * 64,
        sample_rate=11_025,
        decoder_contract_sha256="6" * 64,
        model_or_ensemble_sha256="7" * 64,
        combined_heads=heads,
        member_heads=[heads],
        member_head_types=["legacy-90"],
        member_identities=[
            {
                "fileName": "synthetic.onnx",
                "modelSha256": "c" * 64,
                "runtimeContractSha256": "5" * 64,
                "bytes": 123,
            }
        ],
        common_weights=[1.0],
        joint_contributor_indices=[],
        joint_contributor_weights=[],
        joint_product_blend=0.0,
        final_roots=[1] * frame_count,
        final_products=[1] * frame_count,
    )
    temporal_delta = values(0.2)
    cosine_change = values(0.4)
    temporal_delta[0] = 0.0
    cosine_change[0] = 0.0
    uncertainty["frames"] = {
        "root": {
            "selectedClass": [1] * frame_count,
            "selectedProbability": root_selected,
            "topProbability": [min(1.0, value + 0.05) for value in root_selected],
            "margin": [min(0.1, value + 0.05) for value in root_selected],
            "normalizedEntropy": values(0.4),
        },
        "product": {
            "selectedClass": [1] * frame_count,
            "applicable": [True] * frame_count,
            "selectedProbability": product_selected,
            "topProbability": [min(1.0, value + 0.05) for value in product_selected],
            "margin": values(0.2),
            "normalizedEntropy": values(0.5),
            "directJointAgreement": [None] * frame_count,
            "directJointJensenShannon": [None] * frame_count,
        },
        "ensemble": {
            "memberRootVote": [[1] * frame_count],
            "memberProductVote": [[1] * frame_count],
            "rootSelectedVoteShare": values(1.0),
            "productSelectedVoteShare": values(1.0),
            "rootPairwiseDisagreement": values(0.0),
            "productPairwiseDisagreement": values(0.0),
            "rootSelectedProbabilityStdDev": values(0.0),
            "productSelectedProbabilityStdDev": values(0.0),
            "rootMutualInformation": values(0.0),
            "productMutualInformation": values(0.0),
        },
        "boundary": {
            "modelProbability": boundary,
            "memberMeanProbability": boundary,
            "memberStdDev": values(0.0),
        },
        "observability": {
            "profileSchemaVersion": "chord_existing_feature_matrix_observability_v1",
            "source": "existing-feature-matrix",
            "values": {
                "representationRms": representation_rms,
                "temporalDeltaRms": temporal_delta,
                "absoluteActivationConcentration": values(0.3),
                "cosineChange": cosine_change,
            },
        },
    }
    return uncertainty


def _prediction(
    duration: float,
    segments: list[dict],
    *,
    uncertainty: dict | None = None,
    **metadata: object,
) -> dict:
    core = {
        "schemaVersion": "chord_prediction_v1",
        "id": "track-1",
        "durationSeconds": duration,
        "segments": segments,
        **metadata,
    }
    uncertainty = uncertainty or _uncertainty(duration)
    frame_count = uncertainty["timebase"]["frameCount"]
    for frame in range(frame_count):
        left_edge = frame * 0.1
        segment = next(
            (item for item in segments if float(item["start"]) <= left_edge < float(item["end"])),
            None,
        )
        raw_product = segment.get("productLabel") or segment.get("label") if segment is not None else None
        label = normalize_chord(str(raw_product or ""))
        if label.root is None:
            root_class = 0
            product_class = None
        else:
            root_class = PITCH_CLASS[label.root] + 1
            product_symbol = label.product_symbol
            product_class = (
                4
                if product_symbol.endswith("m7")
                else 2
                if product_symbol.endswith("m")
                else 3
                if product_symbol.endswith("7")
                else 1
            )
        uncertainty["frames"]["root"]["selectedClass"][frame] = root_class
        uncertainty["frames"]["product"]["applicable"][frame] = product_class is not None
        uncertainty["frames"]["product"]["selectedClass"][frame] = product_class
        uncertainty["frames"]["ensemble"]["memberRootVote"][0][frame] = root_class
        uncertainty["frames"]["ensemble"]["memberProductVote"][0][frame] = product_class
        product_fields = (
            "selectedProbability",
            "topProbability",
            "margin",
            "normalizedEntropy",
            "directJointAgreement",
            "directJointJensenShannon",
        )
        ensemble_product_fields = (
            "productSelectedVoteShare",
            "productPairwiseDisagreement",
            "productSelectedProbabilityStdDev",
            "productMutualInformation",
        )
        if product_class is None:
            for name in product_fields:
                uncertainty["frames"]["product"][name][frame] = None
            for name in ensemble_product_fields:
                uncertainty["frames"]["ensemble"][name][frame] = None
    prediction_core_sha256 = _canonical_sha256(core)
    uncertainty["predictionCoreSha256"] = prediction_core_sha256
    return {
        **core,
        "uncertainty": uncertainty,
        "predictionCoreSha256": prediction_core_sha256,
        "uncertaintySha256": _canonical_sha256(uncertainty),
    }


def _reseal_prediction(prediction: dict) -> dict:
    core = {
        key: value
        for key, value in prediction.items()
        if key not in {"uncertainty", "predictionCoreSha256", "uncertaintySha256"}
    }
    prediction_core_sha256 = _canonical_sha256(core)
    prediction["predictionCoreSha256"] = prediction_core_sha256
    prediction["uncertainty"]["predictionCoreSha256"] = prediction_core_sha256
    prediction["uncertaintySha256"] = _canonical_sha256(prediction["uncertainty"])
    return prediction


def _timing(
    duration: float,
    starts: list[float],
    *,
    source_class: str = "runtime",
    deployable: bool | None = None,
    prefix: float | None = None,
) -> dict:
    if deployable is None:
        deployable = source_class == "runtime"
    bar_provenance = {
        "status": "explicit",
        "sourceClass": source_class,
        "sourceId": "player-bar-detector-v1",
        "sourceContractSha256": "d" * 64,
        "deployable": deployable,
        "referenceFree": True,
    }
    payload = {
        "schemaVersion": "chord_explicit_bar_grid_v1",
        "durationSeconds": duration,
        "barStartsSeconds": starts,
        "timingProvenance": {"barStartsSeconds": bar_provenance},
    }
    if prefix is not None:
        payload["prefixExcludedSeconds"] = prefix
        bar_provenance["prefixExcludedSeconds"] = prefix
    return {**payload, "contractSha256": _canonical_sha256(payload)}


def test_partial_frames_final_truncation_and_non_aligned_bar_edges_are_integrated_exactly() -> None:
    prediction = _prediction(
        0.25,
        [
            {"start": 0.0, "end": 0.2, "label": "C:maj", "productLabel": "C"},
            {"start": 0.2, "end": 0.25, "label": "G:maj", "productLabel": "G"},
        ],
        uncertainty=_uncertainty(
            0.25,
            root_selected=[0.2, 0.8, 1.0],
            product_selected=[0.4, 0.6, 0.8],
            boundary=[0.1, 0.5, 0.9],
            representation_rms=[1.0, 3.0, 5.0],
        ),
    )

    result = summarize_prediction_bars(prediction, _timing(0.25, [0.0, 0.15]))
    first, second = result["bars"]

    assert result["schemaVersion"] == BAR_UNCERTAINTY_SCHEMA
    assert result["referenceFree"] is True
    assert result["deployable"] is True
    assert result["selectorUseAllowed"] is True
    assert first["predictionProduct"] == "C"
    assert first["predictionCoverage"] == pytest.approx(1.0)
    assert first["predictionDominance"] == pytest.approx(1.0)
    assert first["predictionTransitionCount"] == 0
    # The non-aligned bar end gives winner C .10 of frame zero and .05 of frame one.
    assert first["featureValues"]["rootSelectedProbabilityMean"] == pytest.approx(0.4)
    assert first["featureValues"]["rootSelectedProbabilityMinimum"] == pytest.approx(0.2)
    # Boundary/observability sees the full bar: .10 of frame zero and .05 of frame one.
    assert first["featureValues"]["boundaryModelProbabilityMean"] == pytest.approx(7 / 30)
    assert first["featureValues"]["boundaryStartEdgeProbability"] == pytest.approx(0.1)
    # The .15 edge is exactly between model samples .1 and .2; ties choose later.
    assert first["featureValues"]["boundaryEndEdgeProbability"] == pytest.approx(0.9)
    assert first["featureValues"]["representationRmsMean"] == pytest.approx(5 / 3)

    assert second["start"] == pytest.approx(0.15)
    assert second["end"] == pytest.approx(0.25)
    # C and G each occupy .05 seconds; lexical product order breaks the tie.
    assert second["predictionProduct"] == "C"
    assert second["predictionDominance"] == pytest.approx(0.5)
    assert second["predictionTransitionCount"] == 1
    # The final frame is only .05 seconds; it receives the same duration mass as
    # the .15-.20 tail of frame one.
    assert second["featureValues"]["rootSelectedProbabilityMean"] == pytest.approx(0.8)
    assert second["featureValues"]["boundaryModelProbabilityMean"] == pytest.approx(0.7)
    assert second["featureValues"]["representationRmsMean"] == pytest.approx(4.0)
    assert second["featureValues"]["boundaryStartEdgeProbability"] == pytest.approx(0.9)
    assert second["featureValues"]["boundaryEndEdgeProbability"] is None


def test_aligned_bar_end_uses_the_transition_into_the_next_frame() -> None:
    prediction = _prediction(
        0.3,
        [{"start": 0.0, "end": 0.3, "label": "C:maj"}],
        uncertainty=_uncertainty(0.3, boundary=[0.1, 0.2, 0.8]),
    )

    first, second = summarize_prediction_bars(
        prediction,
        _timing(0.3, [0.0, 0.2]),
    )["bars"]

    assert first["featureValues"]["boundaryEndEdgeProbability"] == pytest.approx(0.8)
    assert second["featureValues"]["boundaryStartEdgeProbability"] == pytest.approx(0.8)
    assert second["featureValues"]["boundaryEndEdgeProbability"] is None


def test_winner_mask_excludes_losing_chord_frames_but_full_bar_signals_do_not() -> None:
    prediction = _prediction(
        0.4,
        [
            {"start": 0.0, "end": 0.3, "label": "C:maj"},
            {"start": 0.3, "end": 0.4, "label": "G:maj"},
        ],
        uncertainty=_uncertainty(
            0.4,
            root_selected=[0.2, 0.2, 0.2, 1.0],
            boundary=[0.1, 0.1, 0.1, 0.9],
            representation_rms=[1.0, 1.0, 1.0, 9.0],
        ),
    )

    row = summarize_prediction_bars(prediction, _timing(0.4, [0.0]))["bars"][0]

    assert row["predictionProduct"] == "C"
    assert row["predictionDominance"] == pytest.approx(0.75)
    assert row["featureValues"]["rootSelectedProbabilityMean"] == pytest.approx(0.2)
    assert row["featureValues"]["boundaryModelProbabilityMean"] == pytest.approx(0.3)
    assert row["featureValues"]["representationRmsMean"] == pytest.approx(3.0)


def test_gaps_transitions_and_lexical_tie_break_are_deterministic() -> None:
    gaps = _prediction(
        0.5,
        [
            {"start": 0.0, "end": 0.1, "label": "C:maj"},
            {"start": 0.2, "end": 0.3, "label": "G:maj"},
            {"start": 0.4, "end": 0.5, "label": "C:maj"},
        ],
    )
    row = summarize_prediction_bars(gaps, _timing(0.5, [0.0]))["bars"][0]
    assert row["predictionProduct"] == "C"
    assert row["predictionCoverage"] == pytest.approx(0.6)
    assert row["predictionDominance"] == pytest.approx(2 / 3)
    assert row["predictionTransitionCount"] == 2

    tie = _prediction(
        0.4,
        [
            {"start": 0.0, "end": 0.1, "label": "G:maj"},
            {"start": 0.2, "end": 0.3, "label": "C:maj"},
        ],
    )
    tie_row = summarize_prediction_bars(tie, _timing(0.4, [0.0]))["bars"][0]
    assert tie_row["predictionProduct"] == "C"
    assert tie_row["predictionCoverage"] == pytest.approx(0.5)
    assert tie_row["predictionDominance"] == pytest.approx(0.5)


def test_uncovered_bar_has_no_winning_chord_features_but_keeps_full_bar_evidence() -> None:
    prediction = _prediction(0.2, [])

    row = summarize_prediction_bars(prediction, _timing(0.2, [0.0]))["bars"][0]

    assert row["predictionProduct"] is None
    assert row["predictionCoverage"] == 0.0
    assert row["predictionDominance"] == 0.0
    assert row["featureValues"]["rootSelectedProbabilityMean"] is None
    assert row["featureValues"]["productSelectedProbabilityMean"] is None
    assert row["featureValues"]["boundaryModelProbabilityMean"] == pytest.approx(0.25)
    assert row["featureValues"]["representationRmsMean"] == pytest.approx(1.0)


def test_prediction_grid_is_ignored_and_positive_prefix_requires_duplicate_certification() -> None:
    prediction = _prediction(
        0.4,
        [{"start": 0.0, "end": 0.4, "label": "C:maj"}],
        barStartsSeconds=[0.2],
    )
    timing = _timing(0.4, [0.1, 0.3], prefix=0.1)

    result = summarize_prediction_bars(prediction, timing)

    assert [bar["start"] for bar in result["bars"]] == pytest.approx([0.1, 0.3])
    assert result["timing"]["excludedPrefixDurationSeconds"] == pytest.approx(0.1)

    invalid = deepcopy(timing)
    invalid["prefixExcludedSeconds"] = 0.2
    invalid["contractSha256"] = _canonical_sha256(
        {key: value for key, value in invalid.items() if key != "contractSha256"}
    )
    with pytest.raises(ValueError, match="prefix certification"):
        summarize_prediction_bars(prediction, invalid)


def test_annotation_grid_is_rejected_from_the_reference_free_selector_schema() -> None:
    prediction = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj"}],
    )

    with pytest.raises(ValueError, match="sourceClass is unsupported"):
        summarize_prediction_bars(
            prediction,
            _timing(0.2, [0.0], source_class="annotation-oracle"),
        )

    dishonest = _timing(0.2, [0.0], source_class="annotation-oracle", deployable=True)
    with pytest.raises(ValueError, match="sourceClass is unsupported"):
        summarize_prediction_bars(prediction, dishonest)

    nondeployable_runtime = _timing(0.2, [0.0], source_class="runtime", deployable=False)
    with pytest.raises(ValueError, match="Runtime bar timing must be marked deployable"):
        summarize_prediction_bars(prediction, nondeployable_runtime)


def test_missing_uncertainty_never_falls_back_to_legacy_segment_confidence() -> None:
    prediction = {
        "schemaVersion": "chord_prediction_v1",
        "id": "track-1",
        "durationSeconds": 0.2,
        "segments": [
            {
                "start": 0.0,
                "end": 0.2,
                "label": "C:maj",
                "productConfidence": 0.999,
            }
        ],
    }

    with pytest.raises(ValueError, match="prediction.uncertainty must be an object"):
        summarize_prediction_bars(prediction, _timing(0.2, [0.0]))


def test_uncertainty_and_prediction_core_hashes_are_fail_closed() -> None:
    prediction = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj"}],
    )
    prediction["uncertainty"]["frames"]["root"]["margin"][0] = 0.99
    with pytest.raises(ValueError, match="uncertaintySha256 does not match"):
        summarize_prediction_bars(prediction, _timing(0.2, [0.0]))

    prediction = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj"}],
    )
    prediction["segments"][0]["label"] = "G:maj"
    with pytest.raises(ValueError, match="predictionCoreSha256 does not match"):
        summarize_prediction_bars(prediction, _timing(0.2, [0.0]))


def test_uncertainty_cannot_be_spliced_between_same_duration_predictions() -> None:
    first = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj"}],
    )
    second = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj"}],
        id="different-track",
    )
    first["uncertainty"] = deepcopy(second["uncertainty"])
    first["uncertaintySha256"] = second["uncertaintySha256"]

    with pytest.raises(ValueError, match="uncertainty.predictionCoreSha256 does not match"):
        summarize_prediction_bars(first, _timing(0.2, [0.0]))


def test_resealed_stale_selected_classes_and_non_frame_aligned_segments_are_rejected() -> None:
    prediction = _prediction(
        0.2,
        [
            {"start": 0.0, "end": 0.1, "label": "C:maj"},
            {"start": 0.1, "end": 0.2, "label": "G:7"},
        ],
    )
    prediction["segments"][1]["label"] = "D:min"
    _reseal_prediction(prediction)
    with pytest.raises(ValueError, match="selectedClass is stale or misaligned"):
        summarize_prediction_bars(prediction, _timing(0.2, [0.0]))

    unaligned = _prediction(
        0.2,
        [
            {"start": 0.0, "end": 0.12, "label": "C:maj"},
            {"start": 0.12, "end": 0.2, "label": "G:maj"},
        ],
    )
    with pytest.raises(ValueError, match="segment ends must align"):
        summarize_prediction_bars(unaligned, _timing(0.2, [0.0]))

    contradictory = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj", "productLabel": "C"}],
    )
    contradictory["segments"][0]["label"] = "G:maj"
    _reseal_prediction(contradictory)
    with pytest.raises(ValueError, match="label and productLabel"):
        summarize_prediction_bars(contradictory, _timing(0.2, [0.0]))


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (
            lambda value: value["uncertainty"]["frames"]["root"]["margin"].append(0.2),
            "must contain exactly 2 frames",
        ),
        (
            lambda value: value["uncertainty"]["frames"]["boundary"]["modelProbability"].__setitem__(0, float("nan")),
            "canonical JSON",
        ),
        (
            lambda value: value["uncertainty"]["frames"]["product"]["selectedClass"].__setitem__(0, None),
            "numeric exactly when product is applicable",
        ),
        (
            lambda value: value["uncertainty"]["frames"]["ensemble"]["memberRootVote"].append([1, 1]),
            "contain exactly 1 member rows",
        ),
    ),
)
def test_wrong_frame_arrays_nan_and_class_alignment_are_rejected(mutate, message: str) -> None:
    prediction = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj"}],
    )
    mutate(prediction)
    if "nan" not in repr(prediction).lower():
        _reseal_prediction(prediction)
    with pytest.raises(ValueError, match=message):
        summarize_prediction_bars(prediction, _timing(0.2, [0.0]))


def test_timebase_frame_count_must_equal_exact_duration_ceiling() -> None:
    prediction = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj"}],
    )
    prediction["uncertainty"]["timebase"]["frameCount"] = 3
    for group in ("root", "product", "boundary"):
        for values in prediction["uncertainty"]["frames"][group].values():
            if isinstance(values, list):
                values.append(values[-1])
    for name, values in prediction["uncertainty"]["frames"]["ensemble"].items():
        if name in {"memberRootVote", "memberProductVote"}:
            values[0].append(values[0][-1])
        else:
            values.append(values[-1])
    for values in prediction["uncertainty"]["frames"]["observability"]["values"].values():
        values.append(values[-1])
    _reseal_prediction(prediction)

    with pytest.raises(ValueError, match=r"must equal ceil"):
        summarize_prediction_bars(prediction, _timing(0.2, [0.0]))


def test_output_binds_all_contracts_and_contains_no_label_or_outcome_fields() -> None:
    prediction = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "Bb:7", "productLabel": "A#7"}],
    )
    timing = _timing(0.2, [0.0])
    result = summarize_prediction_bars(prediction, timing)

    assert result["bars"][0]["predictionProduct"] == "A#7"
    assert tuple(result["bars"][0]["featureValues"]) == BAR_FEATURE_NAMES
    assert result["binding"] == {
        "predictionCoreSha256": prediction["predictionCoreSha256"],
        "uncertaintySha256": prediction["uncertaintySha256"],
        "uncertaintyContractSha256": prediction["uncertainty"]["contractSha256"],
        "sourceFeatureKind": "multiband_chroma_v2",
        "sourceFeatureSpecSha256": "b" * 64,
        "observabilityProfileSchemaVersion": "chord_existing_feature_matrix_observability_v1",
        "barFeatureContractSha256": BAR_FEATURE_CONTRACT_SHA256,
        "timingSha256": _canonical_sha256(timing),
        "timingContractSha256": timing["contractSha256"],
        "timingSourceContractSha256": "d" * 64,
    }
    payload = {key: value for key, value in result.items() if key != "summarySha256"}
    assert result["summarySha256"] == _canonical_sha256(payload)
    assert result["featureContract"]["contractSha256"] == _canonical_sha256(
        {key: value for key, value in result["featureContract"].items() if key != "contractSha256"}
    )

    forbidden = {"referenceProduct", "correct", "eligible", "label", "productConfidence"}

    def visit(value: object) -> None:
        if isinstance(value, dict):
            assert forbidden.isdisjoint(value)
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(result)


def test_external_reference_mutation_cannot_affect_summary_bytes_or_hash() -> None:
    assert tuple(inspect.signature(summarize_prediction_bars).parameters) == (
        "prediction",
        "timing_only",
    )
    prediction = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj"}],
    )
    timing = _timing(0.2, [0.0])
    external_reference = {"segments": [{"label": "C:maj"}]}
    first = summarize_prediction_bars(prediction, timing)
    first_bytes = json.dumps(first, sort_keys=True, separators=(",", ":"), allow_nan=False)

    external_reference["segments"][0]["label"] = "F#:min7"
    second = summarize_prediction_bars(prediction, timing)
    second_bytes = json.dumps(second, sort_keys=True, separators=(",", ":"), allow_nan=False)

    assert external_reference["segments"][0]["label"] == "F#:min7"
    assert second_bytes == first_bytes
    assert second["summarySha256"] == first["summarySha256"]


def test_unicode_track_and_timing_identity_use_the_shared_canonical_hash_encoding() -> None:
    prediction = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj"}],
    )
    prediction["id"] = "Lektion – stål"
    _reseal_prediction(prediction)
    timing = _timing(0.2, [0.0])
    timing["timingProvenance"]["barStartsSeconds"]["sourceId"] = "spelare – ångström"
    timing["contractSha256"] = _canonical_sha256(
        {key: value for key, value in timing.items() if key != "contractSha256"}
    )

    result = summarize_prediction_bars(prediction, timing)

    assert result["trackId"] == "Lektion – stål"
    assert result["timing"]["sourceId"] == "spelare – ångström"
    assert result["binding"]["timingSha256"] == _canonical_sha256(timing)


def test_real_core_uncertainty_emitter_round_trips_through_strict_bar_schema() -> None:
    features = np.asarray([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
    root = np.full((2, 13), -4.0, dtype=np.float32)
    root[0, 1] = 4.0
    root[1, 8] = 4.0
    product = np.full((2, 5), -4.0, dtype=np.float32)
    product[:, 1] = 4.0
    boundary = np.zeros((2, 1), dtype=np.float32)
    heads = {"root": root, "product": product, "boundary": boundary}
    uncertainty = build_factorized_uncertainty(
        numpy=np,
        features=features,
        duration_seconds=0.2,
        frame_seconds=0.1,
        feature_kind="synthetic_v1",
        feature_count=2,
        feature_spec_sha256="1" * 64,
        sample_rate=16_000,
        decoder_contract_sha256="2" * 64,
        model_or_ensemble_sha256="3" * 64,
        combined_heads=heads,
        member_heads=[heads],
        member_head_types=["legacy-90"],
        member_identities=[
            {
                "fileName": "synthetic.onnx",
                "modelSha256": "4" * 64,
                "runtimeContractSha256": "5" * 64,
                "bytes": 123,
            }
        ],
        common_weights=[1.0],
        joint_contributor_indices=[],
        joint_contributor_weights=[],
        joint_product_blend=0.0,
        final_roots=[1, 8],
        final_products=[1, 1],
    )
    prediction = attach_uncertainty(
        {
            "schemaVersion": "chord_prediction_v1",
            "id": "core-round-trip",
            "durationSeconds": 0.2,
            "segments": [
                {"start": 0.0, "end": 0.1, "label": "C:maj", "productLabel": "C"},
                {"start": 0.1, "end": 0.2, "label": "G:maj", "productLabel": "G"},
            ],
        },
        uncertainty,
    )

    result = summarize_prediction_bars(prediction, _timing(0.2, [0.0]))

    assert result["trackId"] == "core-round-trip"
    assert result["bars"][0]["predictionProduct"] == "C"
    assert result["bars"][0]["predictionDominance"] == pytest.approx(0.5)
    assert result["binding"]["uncertaintySha256"] == prediction["uncertaintySha256"]


def test_inferred_or_unproven_timing_is_rejected_instead_of_falling_back() -> None:
    prediction = _prediction(
        0.2,
        [{"start": 0.0, "end": 0.2, "label": "C:maj"}],
    )
    inferred = {
        "schemaVersion": "chord_explicit_bar_grid_v1",
        "durationSeconds": 0.2,
        "tempo": 120,
        "meter": "4/4",
    }
    with pytest.raises(ValueError, match="unsupported fields"):
        summarize_prediction_bars(prediction, inferred)

    timing = _timing(0.2, [0.0])
    timing["timingProvenance"]["barStartsSeconds"]["status"] = "inferred"
    timing["contractSha256"] = _canonical_sha256(
        {key: value for key, value in timing.items() if key != "contractSha256"}
    )
    with pytest.raises(ValueError, match="inferred grids are forbidden"):
        summarize_prediction_bars(prediction, timing)
