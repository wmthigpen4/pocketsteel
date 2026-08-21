from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, Sequence

import numpy as np
import pytest

import steel_guitar_rag.chord_reader.factorized as factorized_module
from steel_guitar_rag.chord_reader.bar_promotion import canonical_sha256
from steel_guitar_rag.chord_reader.factorized import (
    FACTORIZED_MODES,
    FACTORIZED_PRODUCTS,
    FACTORIZED_QUALITIES,
    FACTORIZED_STRUCTURES,
    JOINT_ROOT_PRODUCT_OUTPUT_WIDTH,
    MODE_INDEX,
    OUTPUT_WIDTH,
    PRODUCT_INDEX,
    QUALITY_INDEX,
    STRUCTURE_INDEX,
    FactorizedEnsembleRecognizer,
    FactorizedRecognizer,
    _combine_factorized_member_outputs,
    _joint_root_product_contract,
    joint_root_product_class,
    split_factorized_outputs,
)
from steel_guitar_rag.chord_reader.uncertainty import (
    FACTORIZED_UNCERTAINTY_SCHEMA,
    FACTORIZED_UNCERTAINTY_FORMULA_SHA256,
    FactorizedInferenceBundle,
    _UNCERTAINTY_CONTRACT,
    attach_uncertainty,
    build_factorized_uncertainty,
    validate_factorized_uncertainty_contract,
)


ROOT_FIELDS = {
    "selectedClass",
    "selectedProbability",
    "topProbability",
    "margin",
    "normalizedEntropy",
}
PRODUCT_FIELDS = {
    "applicable",
    "selectedClass",
    "selectedProbability",
    "topProbability",
    "margin",
    "normalizedEntropy",
    "directJointAgreement",
    "directJointJensenShannon",
}
ENSEMBLE_FIELDS = {
    "memberRootVote",
    "memberProductVote",
    "rootSelectedVoteShare",
    "productSelectedVoteShare",
    "rootPairwiseDisagreement",
    "productPairwiseDisagreement",
    "rootSelectedProbabilityStdDev",
    "productSelectedProbabilityStdDev",
    "rootMutualInformation",
    "productMutualInformation",
}


def _member_logits(
    *,
    frames: int = 3,
    root_index: int = 1,
    product_index: int = PRODUCT_INDEX["major"],
    joint_product_index: int | None = None,
    boundary: float | Sequence[float] = -8.0,
) -> np.ndarray:
    root = np.full((frames, 13), -8.0, dtype=np.float32)
    root[:, root_index] = 8.0
    mode = np.full((frames, len(FACTORIZED_MODES)), -8.0, dtype=np.float32)
    mode[:, MODE_INDEX["major"]] = 8.0
    product = np.full((frames, len(FACTORIZED_PRODUCTS)), -8.0, dtype=np.float32)
    product[:, product_index] = 8.0
    structure = np.full((frames, len(FACTORIZED_STRUCTURES)), -8.0, dtype=np.float32)
    structure[:, STRUCTURE_INDEX["triad"]] = 8.0
    quality = np.full((frames, len(FACTORIZED_QUALITIES)), -8.0, dtype=np.float32)
    quality[:, QUALITY_INDEX["maj"]] = 8.0
    bass = np.full((frames, 13), -8.0, dtype=np.float32)
    bass[:, 0] = 8.0
    boundary_values = np.asarray(boundary, dtype=np.float32)
    if boundary_values.ndim == 0:
        boundary_values = np.full(frames, boundary_values, dtype=np.float32)
    boundary_head = boundary_values.reshape(frames, 1)
    common = np.concatenate((root, mode, product, structure, quality, bass, boundary_head), axis=1)
    if joint_product_index is None:
        return common
    joint = np.full((frames, 49), -8.0, dtype=np.float32)
    joint[:, joint_root_product_class(root_index, joint_product_index)] = 8.0
    return np.concatenate((common, joint), axis=1)


def _identity(name: str) -> dict[str, Any]:
    return {
        "fileName": name,
        "modelSha256": hashlib.sha256(name.encode("utf-8")).hexdigest(),
        "bytes": len(name.encode("utf-8")) + 1,
        "runtimeContractSha256": hashlib.sha256(f"runtime:{name}".encode("utf-8")).hexdigest(),
    }


def _uncertainty_for_outputs(
    outputs: Sequence[np.ndarray],
    *,
    weights: Sequence[float],
    roots: Sequence[int],
    products: Sequence[int],
    blend: float = 0.0,
    features: np.ndarray | None = None,
    identities: Sequence[dict[str, Any]] | None = None,
    combined_heads_override: dict[str, np.ndarray] | None = None,
) -> dict[str, Any]:
    head_types = tuple(
        "joint-139" if output.shape[1] == JOINT_ROOT_PRODUCT_OUTPUT_WIDTH else "legacy-90" for output in outputs
    )
    has_joint = tuple(value == "joint-139" for value in head_types)
    if len(outputs) == 1:
        combined = outputs[0]
    else:
        combined = _combine_factorized_member_outputs(
            outputs,
            weights,
            np,
            joint_root_product=any(has_joint),
            member_joint_root_product=(has_joint if set(has_joint) == {False, True} else None),
        )
    combined_heads = (
        combined_heads_override
        if combined_heads_override is not None
        else split_factorized_outputs(combined, joint_root_product=any(has_joint))
    )
    member_heads = tuple(
        split_factorized_outputs(output, joint_root_product=joint)
        for output, joint in zip(outputs, has_joint, strict=True)
    )
    joint_indices = tuple(index for index, value in enumerate(has_joint) if value)
    joint_mass = math.fsum(weights[index] for index in joint_indices)
    joint_weights = tuple(weights[index] / joint_mass for index in joint_indices) if joint_indices else ()
    feature_values = np.zeros((len(roots), 2), dtype=np.float32) if features is None else features
    return build_factorized_uncertainty(
        numpy=np,
        features=feature_values,
        duration_seconds=len(roots) / 10,
        frame_seconds=0.1,
        feature_kind="fixture-representation-v1",
        feature_count=feature_values.shape[1],
        feature_spec_sha256="a" * 64,
        sample_rate=11_025,
        decoder_contract_sha256="b" * 64,
        model_or_ensemble_sha256="c" * 64,
        combined_heads=combined_heads,
        member_heads=member_heads,
        member_head_types=head_types,
        member_identities=(
            identities
            if identities is not None
            else tuple(_identity(f"member-{index}.onnx") for index in range(len(outputs)))
        ),
        common_weights=weights,
        joint_contributor_indices=joint_indices,
        joint_contributor_weights=joint_weights,
        joint_product_blend=blend,
        final_roots=roots,
        final_products=products,
    )


def _metadata(
    *,
    joint: bool = False,
    architecture: str = "tcn",
    window_frames: int | None = None,
) -> dict[str, str]:
    value = {
        "chordReaderArchitecture": architecture,
        "chordReaderFeatureKind": "multiband_chroma_v2",
        "chordReaderFactorizedSchema": "chord_factorized_model_v2",
        "chordReaderFrameSeconds": "0.1",
        "chordReaderOutputWidth": str(JOINT_ROOT_PRODUCT_OUTPUT_WIDTH if joint else OUTPUT_WIDTH),
        "chordReaderQualities": json.dumps(list(FACTORIZED_QUALITIES)),
        "chordReaderModes": json.dumps(list(FACTORIZED_MODES)),
        "chordReaderProducts": json.dumps(list(FACTORIZED_PRODUCTS)),
        "chordReaderStructures": json.dumps(list(FACTORIZED_STRUCTURES)),
        "chordReaderFeatureCount": "61",
        "chordReaderSampleRate": "11025",
        "chordReaderFeatureSpecSha256": "d" * 64,
    }
    if joint:
        value["chordReaderJointRootProduct"] = json.dumps(
            _joint_root_product_contract(),
            sort_keys=True,
            separators=(",", ":"),
        )
    if window_frames is not None:
        value["chordReaderWindowFrames"] = str(window_frames)
    return value


def _install_fake_runtime(
    monkeypatch: pytest.MonkeyPatch,
    specifications: dict[str, tuple[dict[str, str], np.ndarray]],
) -> dict[str, list[Any]]:
    sessions: dict[str, list[Any]] = {path: [] for path in specifications}

    class FakeSession:
        def __init__(self, path: str, *, providers: list[str]) -> None:
            assert providers == ["CPUExecutionProvider"]
            self.path = path
            self.metadata, self.output = specifications[path]
            self.run_calls = 0
            sessions[path].append(self)

        def get_modelmeta(self) -> SimpleNamespace:
            return SimpleNamespace(custom_metadata_map=self.metadata)

        def get_inputs(self) -> list[SimpleNamespace]:
            window = self.metadata.get("chordReaderWindowFrames")
            return [
                SimpleNamespace(
                    name="features",
                    type="tensor(float)",
                    shape=[
                        "batch",
                        int(window) if window is not None else "frames",
                        61,
                    ],
                )
            ]

        def get_outputs(self) -> list[SimpleNamespace]:
            return [
                SimpleNamespace(
                    name="outputs",
                    type="tensor(float)",
                    shape=["batch", "frames", self.output.shape[1]],
                )
            ]

        def run(self, _outputs: None, inputs: dict[str, np.ndarray]) -> list[np.ndarray]:
            self.run_calls += 1
            assert inputs["features"].shape[0] == 1
            return [self.output[None]]

    monkeypatch.setitem(
        sys.modules,
        "onnxruntime",
        SimpleNamespace(InferenceSession=FakeSession),
    )
    return sessions


def _fake_models(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    members: Sequence[tuple[str, np.ndarray, bool]],
) -> tuple[tuple[Path, ...], dict[str, list[Any]]]:
    paths: list[Path] = []
    specifications: dict[str, tuple[dict[str, str], np.ndarray]] = {}
    for name, output, joint in members:
        path = tmp_path / name
        path.write_bytes(f"fixture:{name}".encode("utf-8"))
        paths.append(path)
        specifications[str(path)] = (_metadata(joint=joint), output)
    return tuple(paths), _install_fake_runtime(monkeypatch, specifications)


def test_uncertainty_schema_metrics_nulls_hashes_and_silent_observability() -> None:
    output = _member_logits(boundary=np.asarray([-1000.0, 0.0, 1000.0], dtype=np.float32))
    heads = split_factorized_outputs(output)
    heads["root"][0] = -8
    heads["root"][0, 0] = 8
    identity = _identity("mémber-钢.onnx")
    with np.errstate(over="raise", invalid="raise"):
        uncertainty = _uncertainty_for_outputs(
            [output],
            weights=(1.0,),
            roots=(0, 1, 1),
            products=(0, 1, 1),
            identities=(identity,),
        )

    assert uncertainty["schemaVersion"] == FACTORIZED_UNCERTAINTY_SCHEMA
    assert uncertainty["referenceFree"] is True
    assert set(uncertainty["frames"]) == {
        "root",
        "product",
        "ensemble",
        "boundary",
        "observability",
    }
    assert set(uncertainty["frames"]["root"]) == ROOT_FIELDS
    assert set(uncertainty["frames"]["product"]) == PRODUCT_FIELDS
    assert set(uncertainty["frames"]["ensemble"]) == ENSEMBLE_FIELDS
    assert set(uncertainty["frames"]["boundary"]) == {
        "modelProbability",
        "memberMeanProbability",
        "memberStdDev",
    }
    assert uncertainty["timebase"] == {
        "frameSeconds": 0.1,
        "frameCount": 3,
        "durationSeconds": 0.3,
        "timestampConvention": "left-edge",
    }
    product = uncertainty["frames"]["product"]
    assert product["applicable"] == [False, True, True]
    for name in PRODUCT_FIELDS - {"applicable"}:
        assert product[name][0] is None
    assert product["directJointAgreement"] == [None, None, None]
    assert uncertainty["frames"]["ensemble"]["memberRootVote"] == [[0, 1, 1]]
    assert uncertainty["frames"]["ensemble"]["memberProductVote"] == [[None, 1, 1]]
    assert uncertainty["frames"]["ensemble"]["rootPairwiseDisagreement"] == [
        0.0,
        0.0,
        0.0,
    ]
    assert uncertainty["frames"]["ensemble"]["rootMutualInformation"] == [
        0.0,
        0.0,
        0.0,
    ]
    boundary = uncertainty["frames"]["boundary"]
    assert boundary["modelProbability"] == pytest.approx([0.0, 0.5, 1.0])
    assert boundary["memberMeanProbability"] == pytest.approx(boundary["modelProbability"])
    assert boundary["memberStdDev"] == pytest.approx([0.0, 0.0, 0.0])
    observability = uncertainty["frames"]["observability"]
    assert observability["source"] == "existing-feature-matrix"
    assert set(observability["values"]) == {
        "representationRms",
        "temporalDeltaRms",
        "absoluteActivationConcentration",
        "cosineChange",
    }
    assert all(values == [0.0, 0.0, 0.0] for values in observability["values"].values())
    assert uncertainty["members"][0]["fileName"] == "mémber-钢.onnx"
    assert "natural-log" in _UNCERTAINTY_CONTRACT["normalizedEntropy"]
    assert "float64-tiny" in _UNCERTAINTY_CONTRACT["normalizedEntropy"]
    assert "natural-log" in _UNCERTAINTY_CONTRACT["jensenShannonDivergence"]
    assert FACTORIZED_UNCERTAINTY_FORMULA_SHA256 == canonical_sha256(_UNCERTAINTY_CONTRACT)
    assert uncertainty["contractSha256"] == canonical_sha256(
        {
            "formulaContract": _UNCERTAINTY_CONTRACT,
            "binding": uncertainty["binding"],
            "members": uncertainty["members"],
        }
    )
    assert validate_factorized_uncertainty_contract(uncertainty) == uncertainty["binding"]
    json.dumps(uncertainty, ensure_ascii=False, allow_nan=False)


def test_mixed_member_product_votes_use_each_members_own_heads_and_pairwise_formula() -> None:
    legacy = _member_logits(product_index=PRODUCT_INDEX["major"])
    joint = _member_logits(
        product_index=PRODUCT_INDEX["minor"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    uncertainty = _uncertainty_for_outputs(
        [legacy, joint],
        weights=(0.5, 0.5),
        roots=(1, 1, 1),
        products=(3, 3, 3),
        blend=1.0,
    )

    ensemble = uncertainty["frames"]["ensemble"]
    assert ensemble["memberProductVote"] == [[1, 1, 1], [3, 3, 3]]
    assert ensemble["productSelectedVoteShare"] == pytest.approx([0.5] * 3)
    assert ensemble["productPairwiseDisagreement"] == pytest.approx([0.5] * 3)
    assert uncertainty["frames"]["product"]["directJointAgreement"] == [
        False,
        False,
        False,
    ]
    assert all(
        value is not None and 0 <= value <= 1 for value in uncertainty["frames"]["product"]["directJointJensenShannon"]
    )
    assert uncertainty["members"][0]["headType"] == "legacy-90"
    assert uncertainty["members"][0]["jointContributorWeight"] is None
    assert uncertainty["members"][1]["headType"] == "joint-139"
    assert uncertainty["members"][1]["jointContributorWeight"] == 1.0


def test_blend_one_product_metrics_ignore_direct_logits_and_roots_stay_frozen() -> None:
    major_direct = _member_logits(
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    minor_direct = _member_logits(
        product_index=PRODUCT_INDEX["minor"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    first = _uncertainty_for_outputs(
        [major_direct],
        weights=(1.0,),
        roots=(1, 1, 1),
        products=(3, 3, 3),
        blend=1.0,
    )
    second = _uncertainty_for_outputs(
        [minor_direct],
        weights=(1.0,),
        roots=(1, 1, 1),
        products=(3, 3, 3),
        blend=1.0,
    )

    assert first["frames"]["root"] == second["frames"]["root"]
    for name in (
        "selectedClass",
        "selectedProbability",
        "topProbability",
        "margin",
        "normalizedEntropy",
    ):
        assert first["frames"]["product"][name] == second["frames"]["product"][name]
    assert first["frames"]["ensemble"]["memberProductVote"] == [[3, 3, 3]]
    assert second["frames"]["ensemble"]["memberProductVote"] == [[3, 3, 3]]


def test_boundary_reports_post_aggregation_sigmoid_and_member_probability_spread() -> None:
    first = _member_logits(boundary=0.0)
    second = _member_logits(boundary=2.0)
    uncertainty = _uncertainty_for_outputs(
        [first, second],
        weights=(0.5, 0.5),
        roots=(1, 1, 1),
        products=(1, 1, 1),
    )
    boundary = uncertainty["frames"]["boundary"]
    sigmoid_two = 1 / (1 + math.exp(-2))
    expected_mean = (0.5 + sigmoid_two) / 2
    expected_std = math.sqrt(((0.5 - expected_mean) ** 2 + (sigmoid_two - expected_mean) ** 2) / 2)
    assert boundary["modelProbability"] == pytest.approx([1 / (1 + math.exp(-1))] * 3)
    assert boundary["memberMeanProbability"] == pytest.approx([expected_mean] * 3)
    assert boundary["memberStdDev"] == pytest.approx([expected_std] * 3)
    assert boundary["modelProbability"] != pytest.approx(boundary["memberMeanProbability"])


def test_member_order_and_unicode_are_bound_by_canonical_contract_hash() -> None:
    legacy = _member_logits()
    joint = _member_logits(joint_product_index=PRODUCT_INDEX["major"])
    identities = (_identity("á.onnx"), _identity("钢.onnx"))
    first = _uncertainty_for_outputs(
        [legacy, joint],
        weights=(0.5, 0.5),
        roots=(1, 1, 1),
        products=(1, 1, 1),
        identities=identities,
    )
    second = _uncertainty_for_outputs(
        [joint, legacy],
        weights=(0.5, 0.5),
        roots=(1, 1, 1),
        products=(1, 1, 1),
        identities=tuple(reversed(identities)),
    )

    assert first["binding"]["memberOrderSha256"] == canonical_sha256(first["members"])
    assert second["binding"]["memberOrderSha256"] == canonical_sha256(second["members"])
    assert first["binding"]["memberOrderSha256"] != second["binding"]["memberOrderSha256"]
    assert first["contractSha256"] != second["contractSha256"]
    tampered = json.loads(json.dumps(first))
    tampered["members"][0]["commonWeight"] = 0.25
    with pytest.raises(ValueError, match="common weight"):
        validate_factorized_uncertainty_contract(tampered)
    not_reference_free = json.loads(json.dumps(first))
    not_reference_free["referenceFree"] = False
    with pytest.raises(ValueError, match="explicitly reference-free"):
        validate_factorized_uncertainty_contract(not_reference_free)


def test_uncertainty_hash_cross_links_prediction_core_and_detects_splicing() -> None:
    uncertainty = _uncertainty_for_outputs(
        [_member_logits()],
        weights=(1.0,),
        roots=(1, 1, 1),
        products=(1, 1, 1),
    )
    first = attach_uncertainty({"id": "first", "segments": []}, uncertainty)
    second = attach_uncertainty({"id": "second", "segments": []}, uncertainty)

    assert first["uncertainty"]["predictionCoreSha256"] == first["predictionCoreSha256"]
    assert second["uncertainty"]["predictionCoreSha256"] == second["predictionCoreSha256"]
    assert first["predictionCoreSha256"] != second["predictionCoreSha256"]
    assert first["uncertaintySha256"] == canonical_sha256(first["uncertainty"])
    assert second["uncertaintySha256"] == canonical_sha256(second["uncertainty"])
    spliced = dict(second)
    spliced["uncertainty"] = first["uncertainty"]
    spliced["uncertaintySha256"] = first["uncertaintySha256"]
    assert spliced["uncertaintySha256"] == canonical_sha256(spliced["uncertainty"])
    assert spliced["uncertainty"]["predictionCoreSha256"] != spliced["predictionCoreSha256"]


def test_uncertainty_fails_closed_on_nan_duration_and_missing_combined_joint() -> None:
    joint = _member_logits(joint_product_index=PRODUCT_INDEX["major"])
    combined_heads = dict(split_factorized_outputs(joint, joint_root_product=True))
    combined_heads.pop("joint_root_product")
    with pytest.raises(ValueError, match="present exactly"):
        _uncertainty_for_outputs(
            [joint],
            weights=(1.0,),
            roots=(1, 1, 1),
            products=(1, 1, 1),
            combined_heads_override=combined_heads,
        )

    bad_features = np.zeros((3, 2), dtype=np.float32)
    bad_features[1, 0] = np.nan
    with pytest.raises(ValueError, match="finite matrix"):
        _uncertainty_for_outputs(
            [_member_logits()],
            weights=(1.0,),
            roots=(1, 1, 1),
            products=(1, 1, 1),
            features=bad_features,
        )

    with pytest.raises(ValueError, match="frame count"):
        build_factorized_uncertainty(
            numpy=np,
            features=np.zeros((2, 2), dtype=np.float32),
            duration_seconds=0.3,
            frame_seconds=0.1,
            feature_kind="fixture",
            feature_count=2,
            feature_spec_sha256="a" * 64,
            sample_rate=11_025,
            decoder_contract_sha256="b" * 64,
            model_or_ensemble_sha256="c" * 64,
            combined_heads=split_factorized_outputs(_member_logits(frames=2)),
            member_heads=(split_factorized_outputs(_member_logits(frames=2)),),
            member_head_types=("legacy-90",),
            member_identities=(_identity("member.onnx"),),
            common_weights=(1.0,),
            joint_contributor_indices=(),
            joint_contributor_weights=(),
            joint_product_blend=0,
            final_roots=(1, 1),
            final_products=(1, 1),
        )


@pytest.mark.parametrize(
    ("tamper", "message"),
    (
        ("extra-root-field", "exactly the required fields"),
        ("transposed-member-votes", "vote matrices"),
        ("legacy-joint-diagnostic", "null without joint evidence"),
        ("entropy-out-of-range", "invalid frame value"),
        ("timebase-mismatch", "frameCount does not match"),
        ("observability-out-of-range", "invalid frame value"),
    ),
)
def test_full_payload_validator_rejects_frame_contract_tamper(
    tamper: str,
    message: str,
) -> None:
    uncertainty = _uncertainty_for_outputs(
        [_member_logits()],
        weights=(1.0,),
        roots=(1, 1, 1),
        products=(1, 1, 1),
    )
    if tamper == "extra-root-field":
        uncertainty["frames"]["root"]["unexpected"] = [0.0] * 3
    elif tamper == "transposed-member-votes":
        uncertainty["frames"]["ensemble"]["memberRootVote"] = [[1], [1], [1]]
    elif tamper == "legacy-joint-diagnostic":
        uncertainty["frames"]["product"]["directJointAgreement"][0] = True
    elif tamper == "entropy-out-of-range":
        uncertainty["frames"]["root"]["normalizedEntropy"][0] = 1.1
    elif tamper == "timebase-mismatch":
        uncertainty["timebase"]["frameCount"] = 4
    elif tamper == "observability-out-of-range":
        uncertainty["frames"]["observability"]["values"]["absoluteActivationConcentration"][0] = 1.1
    else:  # pragma: no cover - parameter table is exhaustive
        raise AssertionError(tamper)
    with pytest.raises(ValueError, match=message):
        validate_factorized_uncertainty_contract(uncertainty)


def test_inference_bundle_is_immutable() -> None:
    output = _member_logits()
    bundle = FactorizedInferenceBundle(output, (output,))
    with pytest.raises(FrozenInstanceError):
        bundle.combined_logits = output.copy()  # type: ignore[misc]
    with pytest.raises(ValueError, match="at least one"):
        FactorizedInferenceBundle(output, ())


def test_default_prediction_is_byte_exact_and_has_no_uncertainty_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = _member_logits()
    models, _sessions = _fake_models(
        tmp_path,
        monkeypatch,
        (("first.onnx", outputs, False), ("second.onnx", outputs, False)),
    )
    recognizer = FactorizedEnsembleRecognizer(models)
    features = np.zeros((3, 61), dtype=np.float32)
    implicit = recognizer.predict_features(features, 0.3, prediction_id="fixture")
    explicit = recognizer.predict_features(
        features,
        0.3,
        prediction_id="fixture",
        emit_uncertainty=False,
    )

    assert implicit == explicit
    assert json.dumps(implicit, sort_keys=True, separators=(",", ":"), allow_nan=False) == json.dumps(
        explicit, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    assert (
        not {
            "uncertainty",
            "predictionCoreSha256",
            "uncertaintySha256",
        }
        & implicit.keys()
    )


def test_mixed_ensemble_emits_after_metadata_and_runs_each_member_and_combine_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = _member_logits(product_index=PRODUCT_INDEX["major"])
    joint = _member_logits(
        product_index=PRODUCT_INDEX["minor"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    models, sessions = _fake_models(
        tmp_path,
        monkeypatch,
        (("legacy.onnx", legacy, False), ("joint.onnx", joint, True)),
    )
    recognizer = FactorizedEnsembleRecognizer(
        models,
        weights=(0.5, 0.5),
        joint_product_blend=0.75,
        allow_mixed_joint_members=True,
    )
    combine_calls = 0
    original_combine = factorized_module._combine_factorized_member_outputs

    def counted_combine(*args: Any, **kwargs: Any) -> np.ndarray:
        nonlocal combine_calls
        combine_calls += 1
        return original_combine(*args, **kwargs)

    monkeypatch.setattr(
        factorized_module,
        "_combine_factorized_member_outputs",
        counted_combine,
    )
    prediction = recognizer.predict_features(
        np.zeros((3, 61), dtype=np.float32),
        0.3,
        prediction_id="fixture",
        emit_uncertainty=True,
    )

    assert combine_calls == 1
    assert all(session.run_calls == 1 for member_sessions in sessions.values() for session in member_sessions)
    core = dict(prediction)
    uncertainty = core.pop("uncertainty")
    core_sha256 = core.pop("predictionCoreSha256")
    uncertainty_sha256 = core.pop("uncertaintySha256")
    assert core_sha256 == canonical_sha256(core)
    assert uncertainty_sha256 == canonical_sha256(uncertainty)
    assert uncertainty["predictionCoreSha256"] == core_sha256
    assert core["engine"] == "chord-factorized-logit-ensemble-v9"
    assert core["model"] == recognizer.ensemble_id
    assert core["modelProvenance"] == recognizer.model_provenance
    assert uncertainty["binding"]["modelOrEnsembleSha256"] == (recognizer.ensemble_sha256)
    assert "predictionCoreSha256" not in uncertainty["binding"]
    assert uncertainty["binding"]["commonWeights"] == [0.5, 0.5]
    assert uncertainty["binding"]["jointContributorIndices"] == [1]
    assert uncertainty["binding"]["jointContributorWeights"] == [1.0]
    assert len(uncertainty["frames"]["ensemble"]["memberRootVote"]) == 2


def test_fixed_window_member_uses_one_normal_inference_traversal_per_prediction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_path = tmp_path / "fixed.onnx"
    dynamic_path = tmp_path / "dynamic.onnx"
    fixed_path.write_bytes(b"fixed-window-member")
    dynamic_path.write_bytes(b"dynamic-member")
    sessions = _install_fake_runtime(
        monkeypatch,
        {
            str(fixed_path): (
                _metadata(architecture="transformer", window_frames=256),
                _member_logits(frames=256),
            ),
            str(dynamic_path): (_metadata(), _member_logits(frames=513)),
        },
    )
    recognizer = FactorizedEnsembleRecognizer((fixed_path, dynamic_path))
    combine_calls = 0
    original_combine = factorized_module._combine_factorized_member_outputs

    def counted_combine(*args: Any, **kwargs: Any) -> np.ndarray:
        nonlocal combine_calls
        combine_calls += 1
        return original_combine(*args, **kwargs)

    monkeypatch.setattr(
        factorized_module,
        "_combine_factorized_member_outputs",
        counted_combine,
    )
    features = np.zeros((513, 61), dtype=np.float32)
    without_uncertainty = recognizer.predict_features(
        features,
        51.3,
        prediction_id="fixed-window-default",
    )
    assert without_uncertainty["segments"][-1]["end"] == 51.3
    assert sessions[str(fixed_path)][0].run_calls == 3
    assert sessions[str(dynamic_path)][0].run_calls == 1
    assert combine_calls == 1

    with_uncertainty = recognizer.predict_features(
        features,
        51.3,
        prediction_id="fixed-window-uncertainty",
        emit_uncertainty=True,
    )
    assert with_uncertainty["uncertainty"]["timebase"]["frameCount"] == 513
    assert sessions[str(fixed_path)][0].run_calls == 6
    assert sessions[str(dynamic_path)][0].run_calls == 2
    assert combine_calls == 2


def test_single_legacy_uncertainty_binds_model_runtime_and_decoder_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = _member_logits()
    models, sessions = _fake_models(
        tmp_path,
        monkeypatch,
        (("módèl.onnx", outputs, False),),
    )
    recognizer = FactorizedRecognizer(models[0])
    prediction = recognizer.predict_features(
        np.zeros((3, 61), dtype=np.float32),
        0.3,
        prediction_id="fixture",
        emit_uncertainty=True,
    )

    assert sessions[str(models[0])][0].run_calls == 1
    uncertainty = prediction["uncertainty"]
    assert uncertainty["binding"]["decoderContractSha256"] == (recognizer.decoder_contract_sha256)
    assert uncertainty["binding"]["modelOrEnsembleSha256"] == (recognizer.model_sha256)
    assert uncertainty["members"] == [
        {
            "fileName": "módèl.onnx",
            "modelSha256": recognizer.model_sha256,
            "bytes": recognizer.model_bytes,
            "runtimeContractSha256": recognizer.runtime_contract_sha256,
            "ordinal": 0,
            "headType": "legacy-90",
            "commonWeight": 1.0,
            "jointContributorWeight": None,
        }
    ]


def test_emit_uncertainty_extracts_shared_features_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = _member_logits()
    models, sessions = _fake_models(
        tmp_path,
        monkeypatch,
        (("first.onnx", outputs, False), ("second.onnx", outputs, False)),
    )
    from steel_guitar_rag.chord_reader import student

    extraction_calls = 0
    features = np.zeros((3, 61), dtype=np.float32)

    def extract_once(_audio: Path, _feature_kind: str) -> tuple[np.ndarray, float]:
        nonlocal extraction_calls
        extraction_calls += 1
        return features, 0.3

    monkeypatch.setattr(student, "extract_student_features", extract_once)
    recognizer = FactorizedEnsembleRecognizer(models)
    prediction = recognizer.predict(
        tmp_path / "fixture.wav",
        emit_uncertainty=True,
    )

    assert prediction["uncertainty"]["referenceFree"] is True
    assert extraction_calls == 1
    assert all(session.run_calls == 1 for member_sessions in sessions.values() for session in member_sessions)


def test_reference_boundaries_are_rejected_before_ensemble_inference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = _member_logits()
    models, sessions = _fake_models(
        tmp_path,
        monkeypatch,
        (("first.onnx", outputs, False), ("second.onnx", outputs, False)),
    )
    recognizer = FactorizedEnsembleRecognizer(models)
    materializations = 0

    def references() -> Any:
        nonlocal materializations
        materializations += 1
        yield 0.1

    with pytest.raises(ValueError, match="Reference-free"):
        recognizer.predict_features(
            np.zeros((3, 61), dtype=np.float32),
            0.3,
            prediction_id="fixture",
            reference_boundaries_seconds=references(),
            emit_uncertainty=True,
        )

    assert materializations == 1
    assert all(session.run_calls == 0 for member_sessions in sessions.values() for session in member_sessions)

    with pytest.raises(ValueError, match="beat grid"):
        recognizer.predict_features(
            np.zeros((3, 61), dtype=np.float32),
            0.3,
            prediction_id="fixture",
            beat_grid={"schemaVersion": "adversarial-oracle"},
            emit_uncertainty=True,
        )
    assert all(session.run_calls == 0 for member_sessions in sessions.values() for session in member_sessions)
