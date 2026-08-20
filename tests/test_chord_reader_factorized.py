from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import steel_guitar_rag.chord_reader.cli as chord_reader_cli

from steel_guitar_rag.chord_reader.artifact_integrity import (
    seal_factorized_artifact_manifest,
)
from steel_guitar_rag.chord_reader.factorized import (
    FACTORIZED_LABEL_SCHEMA,
    FACTORIZED_ENSEMBLE_DECODER_SCHEMA,
    FACTORIZED_ENSEMBLE_PROVENANCE_SCHEMA,
    FACTORIZED_MIXED_JOINT_ENSEMBLE_SCHEMA,
    FACTORIZED_OPTIONAL_HEADS_SCHEMA,
    FACTORIZED_MODES,
    FACTORIZED_PRODUCTS,
    FACTORIZED_QUALITIES,
    FACTORIZED_STRUCTURES,
    FACTORIZED_SCHEMA,
    JOINT_ROOT_PRODUCT_CLASSES,
    JOINT_ROOT_PRODUCT_OUTPUT_WIDTH,
    MODE_INDEX,
    OUTPUT_WIDTH,
    PRODUCT_INDEX,
    QUALITY_INDEX,
    STRUCTURE_INDEX,
    FactorizedRecognizer,
    FactorizedEnsembleRecognizer,
    _accumulate_development_counts,
    _aggregate_factorized_selection,
    _conditioned_product_predictions,
    _conditional_product_evidence,
    _dataset_balance_statistics,
    _development_counts,
    _development_metrics,
    _factorized_metadata_joint_root_product,
    _factorized_canonical_sha256,
    _factorized_training_contract,
    _factorized_training_partitions,
    _factorized_mode_path,
    _hierarchical_product_path,
    _combine_factorized_member_outputs,
    _joint_root_product_class_weights,
    _joint_root_product_contract,
    _joint_root_product_targets,
    _normalized_ensemble_weights,
    _split_protocol_training_provenance,
    _state_root_mode,
    _training_window_weight,
    _validated_feature_contract,
    build_factorized_model,
    cache_factorized_labels,
    export_factorized_onnx,
    factorized_components,
    factorized_symbol,
    factorized_vocabulary_labels,
    joint_root_product_class,
    joint_root_product_components,
    product_class,
    product_symbol,
    quality_mode,
    quality_structure,
    split_factorized_outputs,
    transpose_joint_root_product_class,
    train_factorized_model,
)
from steel_guitar_rag.chord_reader.cli import build_parser
from steel_guitar_rag.chord_reader.metrics import score_segments, vocabulary_for_prediction
from steel_guitar_rag.chord_reader.split_protocol import (
    build_leak_resistant_split_manifest,
    output_manifest_sha256,
)


@pytest.mark.parametrize(
    ("symbol", "root", "mode", "structure", "quality", "bass"),
    [
        ("N", 0, "none", "none", -1, 0),
        ("C", 1, "major", "triad", FACTORIZED_QUALITIES.index("maj"), 0),
        ("Bb:min7/Db", 11, "minor", "seventh", FACTORIZED_QUALITIES.index("min7"), 2),
        ("F#:sus4", 7, "neutral", "suspended", FACTORIZED_QUALITIES.index("sus4"), 0),
        ("D:dim7", 3, "neutral", "diminished", FACTORIZED_QUALITIES.index("dim7"), 0),
        ("A:6", 10, "major", "sixth", FACTORIZED_QUALITIES.index("6"), 0),
    ],
)
def test_factorized_components_preserve_rich_chord_parts(
    symbol: str,
    root: int,
    mode: str,
    structure: str,
    quality: int,
    bass: int,
) -> None:
    value = factorized_components(symbol)
    assert value["root"] == root
    assert value["mode"] == MODE_INDEX[mode]
    assert value["structure"] == FACTORIZED_STRUCTURES.index(structure)
    assert value["quality"] == quality
    assert value["bass"] == bass


def test_factorized_symbol_round_trips_quality_and_inversion() -> None:
    quality = FACTORIZED_QUALITIES.index("maj7")
    assert factorized_symbol(8, quality, 12) == "G:maj7/B"
    assert factorized_symbol(8, quality, 8) == "G:maj7"
    assert factorized_symbol(0, quality, 0) == "N"


@pytest.mark.parametrize(
    ("symbol", "product"),
    [
        ("N", "N.C."),
        ("C:maj7", "C"),
        ("D:min9", "Dm"),
        ("G:13", "G7"),
        ("A:min7", "Am7"),
    ],
)
def test_product_head_target_is_independent_from_exact_quality(
    symbol: str, product: str
) -> None:
    components = factorized_components(symbol)
    root = int(components["root"])
    predicted = product_symbol(root, product_class(symbol))
    assert predicted == product


def test_factorized_vocabulary_contract_expands_without_per_track_duplication() -> None:
    specification = {
        "schemaVersion": "chord_factorized_vocabulary_v1",
        "qualities": list(FACTORIZED_QUALITIES),
        "supportsInversions": True,
    }
    expanded = vocabulary_for_prediction({"vocabularySpecification": specification})
    assert expanded == factorized_vocabulary_labels()
    assert "C:maj7/E" in expanded
    assert "F#:sus4/C" in expanded
    assert len(expanded) == 1 + 12 * len(FACTORIZED_QUALITIES) * 12


def test_product_output_and_confidence_are_scored_independently_from_rich_label() -> None:
    result = score_segments(
        [{"start": 0, "end": 2, "label": "C:maj7"}],
        [
            {
                "start": 0,
                "end": 2,
                "label": "C:7",
                "productLabel": "C",
                "confidence": 0.1,
                "productConfidence": 0.99,
            }
        ],
    )
    assert result["productWeightedRecall"] == 1
    assert result["detailedWeightedRecall"] == 0
    point = next(
        value
        for value in result["confidenceCoverage"]["curve"]
        if value["minimumConfidence"] == 0.98
    )
    assert point["coverage"] == 1
    assert point["productPrecision"] == 1


def test_quality_factorization_covers_requested_structures() -> None:
    assert quality_mode("maj13") == "major"
    assert quality_mode("min9") == "minor"
    assert quality_mode("5") == "neutral"
    assert quality_structure("maj") == "triad"
    assert quality_structure("7") == "seventh"
    assert quality_structure("min6") == "sixth"
    assert quality_structure("sus2") == "suspended"
    assert quality_structure("hdim7") == "diminished"
    assert quality_structure("aug") == "augmented"
    assert quality_structure("5") == "power"


def test_factorized_model_exposes_independent_heads() -> None:
    torch = pytest.importorskip("torch")
    model = build_factorized_model(61, "tcn")
    outputs = model(torch.zeros((2, 17, 61), dtype=torch.float32))
    assert outputs.shape == (2, 17, OUTPUT_WIDTH)
    heads = split_factorized_outputs(outputs)
    assert set(heads) == {
        "root",
        "mode",
        "product",
        "structure",
        "quality",
        "bass",
        "boundary",
    }
    assert heads["root"].shape[-1] == 13
    assert heads["mode"].shape[-1] == len(FACTORIZED_MODES)
    assert heads["product"].shape[-1] == len(FACTORIZED_PRODUCTS)
    assert heads["quality"].shape[-1] == len(FACTORIZED_QUALITIES)
    assert heads["bass"].shape[-1] == 13


def test_joint_root_product_mapping_and_transposition_contract() -> None:
    assert joint_root_product_class(0, PRODUCT_INDEX["none"]) == 0
    assert joint_root_product_class(1, PRODUCT_INDEX["major"]) == 1
    assert joint_root_product_class(12, PRODUCT_INDEX["major"]) == 12
    assert joint_root_product_class(1, PRODUCT_INDEX["minor"]) == 13
    assert joint_root_product_class(1, PRODUCT_INDEX["dominant"]) == 25
    assert joint_root_product_class(1, PRODUCT_INDEX["minor-seventh"]) == 37
    assert joint_root_product_components(48) == (
        12,
        PRODUCT_INDEX["minor-seventh"],
    )
    assert transpose_joint_root_product_class(
        joint_root_product_class(1, PRODUCT_INDEX["dominant"]),
        2,
    ) == joint_root_product_class(3, PRODUCT_INDEX["dominant"])
    assert transpose_joint_root_product_class(0, 11) == 0
    assert all(
        joint_root_product_class(*joint_root_product_components(value)) == value
        for value in range(JOINT_ROOT_PRODUCT_CLASSES)
    )
    with pytest.raises(ValueError, match="requires root class"):
        joint_root_product_class(0, PRODUCT_INDEX["major"])


def test_joint_root_product_targets_and_train_only_product_weight_expansion() -> None:
    roots = np.asarray([[0, 1, 12, 3]], dtype=np.int64)
    products = np.asarray(
        [
            [
                PRODUCT_INDEX["none"],
                PRODUCT_INDEX["major"],
                PRODUCT_INDEX["dominant"],
                PRODUCT_INDEX["minor-seventh"],
            ]
        ],
        dtype=np.int64,
    )
    targets = _joint_root_product_targets(roots, products, np)
    assert targets.tolist() == [
        [
            0,
            joint_root_product_class(1, PRODUCT_INDEX["major"]),
            joint_root_product_class(12, PRODUCT_INDEX["dominant"]),
            joint_root_product_class(3, PRODUCT_INDEX["minor-seventh"]),
        ]
    ]

    product_weights = np.asarray([0.5, 1.0, 2.0, 3.0, 4.0], dtype=np.float32)
    expanded = _joint_root_product_class_weights(product_weights, np)
    assert expanded.shape == (JOINT_ROOT_PRODUCT_CLASSES,)
    assert expanded[0] == pytest.approx(0.5)
    assert np.array_equal(expanded[1:13], np.full(12, 1.0, dtype=np.float32))
    assert np.array_equal(expanded[25:37], np.full(12, 3.0, dtype=np.float32))


def test_optional_joint_head_appends_outputs_without_changing_legacy_parameters() -> None:
    torch = pytest.importorskip("torch")
    torch.manual_seed(7)
    legacy = build_factorized_model(61, "tcn")
    torch.manual_seed(7)
    challenger = build_factorized_model(61, "tcn", joint_root_product=True)

    legacy_state = legacy.state_dict()
    challenger_state = challenger.state_dict()
    assert set(legacy_state).issubset(challenger_state)
    assert all(
        torch.equal(value, challenger_state[name])
        for name, value in legacy_state.items()
    )
    assert not any(name.startswith("joint_root_product") for name in legacy_state)

    outputs = challenger(torch.zeros((2, 17, 61), dtype=torch.float32))
    assert outputs.shape == (2, 17, JOINT_ROOT_PRODUCT_OUTPUT_WIDTH)
    heads = split_factorized_outputs(outputs, joint_root_product=True)
    assert heads["joint_root_product"].shape == (2, 17, JOINT_ROOT_PRODUCT_CLASSES)
    with pytest.raises(ValueError, match=str(OUTPUT_WIDTH)):
        split_factorized_outputs(outputs)


def test_optional_joint_head_exports_width_and_exact_onnx_metadata(
    tmp_path: Path,
) -> None:
    pytest.importorskip("torch")
    safetensors = pytest.importorskip("safetensors.torch")
    onnx = pytest.importorskip("onnx")
    pytest.importorskip("onnxruntime")
    model_root = tmp_path / "joint-model"
    model_root.mkdir()
    weights = model_root / "weights.safetensors"
    safetensors.save_file(
        build_factorized_model(
            61,
            "tcn",
            joint_root_product=True,
        ).state_dict(),
        str(weights),
    )
    config = {
        "schemaVersion": FACTORIZED_SCHEMA,
        "sampleRate": 11_025,
        "frameSeconds": 0.1,
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "featureSpecSha256": "a" * 64,
        "architecture": "tcn",
        "outputWidth": JOINT_ROOT_PRODUCT_OUTPUT_WIDTH,
        "weights": weights.name,
        "optionalHeads": {
            "schemaVersion": FACTORIZED_OPTIONAL_HEADS_SCHEMA,
            "jointRootProduct": {
                **_joint_root_product_contract(),
                "enabled": True,
            },
        },
    }
    (model_root / "config.json").write_text(
        json.dumps(config),
        encoding="utf-8",
    )

    output = tmp_path / "joint-model.onnx"
    report = export_factorized_onnx(model_root, output)
    metadata = {
        item.key: item.value for item in onnx.load(str(output)).metadata_props
    }
    assert report["outputWidth"] == JOINT_ROOT_PRODUCT_OUTPUT_WIDTH
    assert report["jointRootProduct"] == _joint_root_product_contract()
    assert metadata["chordReaderOutputWidth"] == str(
        JOINT_ROOT_PRODUCT_OUTPUT_WIDTH
    )
    assert json.loads(metadata["chordReaderJointRootProduct"]) == (
        _joint_root_product_contract()
    )


def test_strict_browser_feature_contract_preserves_sealed_spec_hash() -> None:
    digest = "a" * 64
    contract = {
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "sampleRate": 11_025,
        "frameSeconds": 0.1,
        "featureSpecSha256": digest,
        "splitProtocol": {},
    }

    _kind, _count, _rate, feature_spec = _validated_feature_contract(
        contract,
        augmentation="none",
    )

    assert feature_spec == {
        "schemaVersion": "chord_feature_spec_reference_v1",
        "featureSpecSha256": digest,
    }


def test_strict_browser_feature_contract_rejects_missing_spec_hash() -> None:
    with pytest.raises(ValueError, match="sealed feature-spec hash"):
        _validated_feature_contract(
            {
                "featureKind": "multiband_chroma_v2",
                "featureCount": 61,
                "sampleRate": 11_025,
                "frameSeconds": 0.1,
                "splitProtocol": {},
            },
            augmentation="none",
        )


def test_factorized_mode_decoder_keeps_root_and_mode_explicit() -> None:
    root_logits = np.full((8, 13), -5.0, dtype=np.float32)
    mode_logits = np.full((8, 4), -5.0, dtype=np.float32)
    root_logits[:4, 1] = 8
    root_logits[4:, 8] = 8
    mode_logits[:, MODE_INDEX["major"]] = 8
    boundary = np.full(8, 0.05, dtype=np.float32)
    boundary[4] = 0.99
    path = _factorized_mode_path(root_logits, mode_logits, boundary, np)
    decoded = [_state_root_mode(state) for state in path]
    assert decoded[:4] == [(1, MODE_INDEX["major"])] * 4
    assert decoded[4:] == [(8, MODE_INDEX["major"])] * 4


def test_hierarchical_product_decoder_splits_quality_without_moving_root() -> None:
    root_logits = np.full((8, 13), -8.0, dtype=np.float32)
    root_logits[:, 1] = 8
    product_logits = np.full((8, len(FACTORIZED_PRODUCTS)), -8.0, dtype=np.float32)
    product_logits[:4, FACTORIZED_PRODUCTS.index("major")] = 8
    product_logits[4:, FACTORIZED_PRODUCTS.index("dominant")] = 8
    boundary = np.full(8, 0.05, dtype=np.float32)
    boundary[4] = 0.99

    roots, products = _hierarchical_product_path(
        root_logits, product_logits, boundary, np
    )

    assert roots == [1] * 8
    assert products[:4] == [FACTORIZED_PRODUCTS.index("major")] * 4
    assert products[4:] == [FACTORIZED_PRODUCTS.index("dominant")] * 4


def test_product_logits_cannot_change_hierarchically_decoded_roots() -> None:
    root_logits = np.full((8, 13), -8.0, dtype=np.float32)
    root_logits[:4, 1] = 8
    root_logits[4:, 8] = 8
    boundary = np.full(8, 0.05, dtype=np.float32)
    boundary[4] = 0.99
    first = np.zeros((8, len(FACTORIZED_PRODUCTS)), dtype=np.float32)
    second = np.flip(first + np.arange(len(FACTORIZED_PRODUCTS)), axis=1).copy()

    roots_a, _products_a = _hierarchical_product_path(root_logits, first, boundary, np)
    roots_b, _products_b = _hierarchical_product_path(root_logits, second, boundary, np)

    assert roots_a == roots_b


def test_joint_product_blend_has_exact_endpoints_and_cannot_move_root() -> None:
    frames = 8
    root_logits = np.full((frames, 13), -8.0, dtype=np.float32)
    root_logits[:, 1] = 8.0
    direct = np.full((frames, PRODUCT_INDEX["minor-seventh"] + 1), -8.0, dtype=np.float32)
    direct[:, PRODUCT_INDEX["major"]] = 8.0
    joint = np.full(
        (frames, JOINT_ROOT_PRODUCT_CLASSES),
        -8.0,
        dtype=np.float32,
    )
    joint[:, joint_root_product_class(1, PRODUCT_INDEX["dominant"])] = 8.0
    # Strong evidence at another root must be ignored once the independent C
    # root path has been frozen.
    joint[:, joint_root_product_class(7, PRODUCT_INDEX["minor-seventh"])] = 80.0
    boundary = np.full(frames, 0.05, dtype=np.float32)

    assert np.array_equal(
        _conditional_product_evidence(direct, joint, 1, 0.0, np),
        direct[:, 1:],
    )
    expected_joint = joint[:, 1:].reshape(frames, 4, 12)[:, :, 0]
    assert np.array_equal(
        _conditional_product_evidence(direct, joint, 1, 1.0, np),
        expected_joint,
    )

    legacy_roots, legacy_products = _hierarchical_product_path(
        root_logits,
        direct,
        boundary,
        np,
        joint_root_product_logits=joint,
        joint_product_blend=0.0,
    )
    joint_roots, joint_products = _hierarchical_product_path(
        root_logits,
        direct,
        boundary,
        np,
        joint_root_product_logits=joint,
        joint_product_blend=1.0,
    )
    assert legacy_roots == joint_roots == [1] * frames
    assert legacy_products == [PRODUCT_INDEX["major"]] * frames
    assert joint_products == [PRODUCT_INDEX["dominant"]] * frames


def test_joint_product_conditioning_transposes_with_the_frozen_root() -> None:
    frames = 4
    root_logits = np.full((frames, 13), -8.0, dtype=np.float32)
    root_logits[:, 3] = 8.0  # D
    direct = np.zeros((frames, len(FACTORIZED_PRODUCTS)), dtype=np.float32)
    joint = np.full((frames, JOINT_ROOT_PRODUCT_CLASSES), -8.0, dtype=np.float32)
    transposed = transpose_joint_root_product_class(
        joint_root_product_class(1, PRODUCT_INDEX["dominant"]),
        2,
    )
    joint[:, transposed] = 8.0

    roots, products = _hierarchical_product_path(
        root_logits,
        direct,
        np.full(frames, 0.05, dtype=np.float32),
        np,
        joint_root_product_logits=joint,
        joint_product_blend=1.0,
    )
    assert roots == [3] * frames
    assert products == [PRODUCT_INDEX["dominant"]] * frames


def test_joint_checkpoint_selection_uses_bound_blend_and_reports_diagnostics() -> None:
    roots = np.asarray([0, 1, 1], dtype=np.int64)
    direct = np.full((3, len(FACTORIZED_PRODUCTS)), -8.0, dtype=np.float32)
    direct[0, PRODUCT_INDEX["none"]] = 8.0
    direct[1:, PRODUCT_INDEX["major"]] = 8.0
    joint = np.full((3, JOINT_ROOT_PRODUCT_CLASSES), -8.0, dtype=np.float32)
    joint[0, 0] = 8.0
    joint[1:, joint_root_product_class(1, PRODUCT_INDEX["dominant"])] = 8.0

    assert _conditioned_product_predictions(roots, direct, joint, 0.0, np).tolist() == [
        PRODUCT_INDEX["none"],
        PRODUCT_INDEX["major"],
        PRODUCT_INDEX["major"],
    ]
    assert _conditioned_product_predictions(roots, direct, joint, 1.0, np).tolist() == [
        PRODUCT_INDEX["none"],
        PRODUCT_INDEX["dominant"],
        PRODUCT_INDEX["dominant"],
    ]

    reference_products = np.asarray(
        [
            PRODUCT_INDEX["none"],
            PRODUCT_INDEX["major"],
            PRODUCT_INDEX["dominant"],
        ],
        dtype=np.int64,
    )
    window = {
        "label_valid": np.ones(3, dtype=np.float32),
        "root": roots,
        "mode": np.asarray([0, 1, 1], dtype=np.int64),
        "product": reference_products,
        "quality": np.asarray([-1, 0, 2], dtype=np.int64),
        "bass": np.zeros(3, dtype=np.int64),
        "boundary": np.zeros(3, dtype=np.float32),
    }
    joint_targets = _joint_root_product_targets(roots, reference_products, np)
    predicted = {
        "root": roots.copy(),
        "mode": window["mode"].copy(),
        "product": np.asarray([0, 1, 1], dtype=np.int64),
        "quality": window["quality"].copy(),
        "bass": window["bass"].copy(),
        "joint_root_product": joint_targets.copy(),
        "joint_conditioned_product": np.asarray([0, 3, 3], dtype=np.int64),
        "selection_product": reference_products.copy(),
    }
    counts = _development_counts(joint_root_product=True)
    _accumulate_development_counts(
        counts,
        window,
        predicted,
        np.zeros(3, dtype=np.float32),
        joint_targets=joint_targets,
    )
    metrics = _development_metrics(counts)
    assert metrics["productAccuracy"] == pytest.approx(2 / 3)
    assert metrics["jointRootProductAccuracy"] == 1.0
    assert metrics["jointConditionedProductAccuracy"] == pytest.approx(2 / 3)
    assert metrics["selectionProductAccuracy"] == 1.0

    score, _by_dataset = _aggregate_factorized_selection(
        metrics,
        {"fixture": metrics},
        dataset_balance=False,
        product_metric="selectionProductAccuracy",
    )
    direct_score, _direct_by_dataset = _aggregate_factorized_selection(
        metrics,
        {"fixture": metrics},
        dataset_balance=False,
    )
    assert score - direct_score == pytest.approx(0.3 * (1 / 3))


def test_factorized_label_cache_reuses_frozen_features(tmp_path: Path) -> None:
    feature_path = tmp_path / "features.npz"
    np.savez_compressed(
        feature_path,
        features=np.zeros((20, 61), dtype=np.float16),
        labels=np.zeros(20, dtype=np.int64),
        label_valid=np.ones(20, dtype=np.bool_),
        training_weight=np.asarray(1.0, dtype=np.float32),
    )
    reference_path = tmp_path / "reference.json"
    reference_path.write_text(
        json.dumps(
            {
                "segments": [
                    {"start": 0.0, "end": 1.0, "label": "C:maj7/E"},
                    {"start": 1.0, "end": 2.0, "label": "D:quartal"},
                ]
            }
        ),
        encoding="utf-8",
    )
    feature_manifest = {
        "schemaVersion": "chord_feature_cache_v1",
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "sampleRate": 11025,
        "frameSeconds": 0.1,
        "tracks": [
            {
                "id": "track",
                "datasetId": "fixture",
                "split": "train",
                "path": str(feature_path),
                "frames": 20,
            }
        ],
    }
    track_manifest = {
        "tracks": [
            {
                "id": "track",
                "datasetId": "fixture",
                "split": "train",
                "compositionId": "composition",
                "groupId": "performer",
                "splitGroup": "composition",
                "referencePath": str(reference_path),
            }
        ]
    }
    output = cache_factorized_labels(feature_manifest, [track_manifest], tmp_path / "labels")
    assert output["schemaVersion"] == FACTORIZED_LABEL_SCHEMA
    assert output["exactQualityVocabularyCoverage"] == pytest.approx(0.5)
    assert output["tracks"][0]["path"] == str(feature_path)
    assert output["tracks"][0]["compositionId"] == "composition"
    assert output["tracks"][0]["groupId"] == "performer"
    assert output["tracks"][0]["splitGroup"] == "composition"
    sidecar = Path(output["tracks"][0]["factorizedLabelsPath"])
    with np.load(sidecar) as labels:
        assert labels["root"].tolist()[:10] == [1] * 10
        assert labels["quality"].tolist()[:10] == [FACTORIZED_QUALITIES.index("maj7")] * 10
        assert labels["product"].tolist()[:10] == [product_class("C:maj7/E")] * 10
        assert labels["bass"].tolist()[:10] == [5] * 10
        assert labels["quality"].tolist()[10:] == [-1] * 10


def _training_window(
    dataset_id: str,
    *,
    frames: int,
    weight: float,
    split: str = "train",
) -> dict:
    return {
        "datasetId": dataset_id,
        "split": split,
        "weight": weight,
        "label_valid": np.ones(frames, dtype=np.bool_),
    }


def _split_protocol_fixture() -> dict:
    source = {
        "schemaVersion": FACTORIZED_LABEL_SCHEMA,
        "tracks": [
            {
                "id": f"{dataset}-{index}",
                "datasetId": dataset,
                "compositionId": f"composition-{index}",
                "split": "train",
                "trainingWeight": 1.0,
            }
            for dataset in ("aam", "nrgcp")
            for index in range(4)
        ],
    }
    return build_leak_resistant_split_manifest(source, seed="factorized-test")


def _sealed_split_protocol_fixture(tmp_path: Path) -> dict:
    source = {
        "schemaVersion": FACTORIZED_LABEL_SCHEMA,
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "sampleRate": 11_025,
        "frameSeconds": 0.1,
        "tracks": [],
    }
    for dataset in ("aam", "nrgcp"):
        for index in range(4):
            identifier = f"{dataset}-{index}"
            feature = tmp_path / f"{identifier}-feature.npz"
            labels = tmp_path / f"{identifier}-labels.npz"
            np.savez_compressed(
                feature,
                features=np.zeros((4, 61), dtype=np.float16),
                labels=np.zeros(4, dtype=np.int64),
                label_valid=np.ones(4, dtype=np.bool_),
                training_weight=np.asarray(1.0, dtype=np.float32),
            )
            np.savez_compressed(
                labels,
                root=np.ones(4, dtype=np.int64),
                mode=np.ones(4, dtype=np.int64),
                product=np.ones(4, dtype=np.int64),
                structure=np.ones(4, dtype=np.int64),
                quality=np.zeros(4, dtype=np.int64),
                bass=np.zeros(4, dtype=np.int64),
                boundary=np.zeros(4, dtype=np.float32),
                label_valid=np.ones(4, dtype=np.bool_),
            )
            source["tracks"].append(
                {
                    "id": identifier,
                    "datasetId": dataset,
                    "compositionId": f"composition-{index}",
                    "split": "train",
                    "trainingWeight": 1.0,
                    "path": str(feature.resolve()),
                    "factorizedLabelsPath": str(labels.resolve()),
                    "frames": 4,
                    "durationSeconds": 0.4,
                }
            )
    sealed = seal_factorized_artifact_manifest(source)
    return build_leak_resistant_split_manifest(sealed, seed="factorized-test")


def test_dataset_balance_deterministically_equalizes_effective_train_mass() -> None:
    windows = [
        _training_window("aam", frames=100, weight=0.5),
        _training_window("aam", frames=20, weight=0.25),
        _training_window("nrgcp", frames=10, weight=2.0),
    ]
    first = _dataset_balance_statistics(windows)
    second = _dataset_balance_statistics(list(reversed(windows)))

    assert first == second
    assert first["aam"]["effectiveFrameMassBefore"] == 55
    assert first["nrgcp"]["effectiveFrameMassBefore"] == 20
    assert first["aam"]["effectiveFrameMassAfter"] == 37.5
    assert first["nrgcp"]["effectiveFrameMassAfter"] == 37.5
    balanced_mass = {
        dataset: sum(
            int(window["label_valid"].sum())
            * _training_window_weight(window, first)
            for window in windows
            if window["datasetId"] == dataset
        )
        for dataset in ("aam", "nrgcp")
    }
    assert balanced_mass == pytest.approx({"aam": 37.5, "nrgcp": 37.5})
    assert sum(balanced_mass.values()) == pytest.approx(75.0)


def test_factorized_partitions_exclude_calibration_and_test_from_training() -> None:
    manifest = _split_protocol_fixture()
    manifest["tracks"].append(
        {
            "id": "sealed-test",
            "datasetId": "fixture",
            "split": "test",
        }
    )
    selected = _factorized_training_partitions(manifest)

    assert {track["split"] for track in selected["train"]} == {"train"}
    assert {track["split"] for track in selected["development"]} == {"development"}
    selected_ids = {track["id"] for values in selected.values() for track in values}
    assert not any(
        track["id"] in selected_ids
        for track in manifest["tracks"]
        if track["split"] in {"calibration", "test"}
    )
    with pytest.raises(ValueError, match="only training windows"):
        _dataset_balance_statistics(
            [_training_window("fixture", frames=10, weight=1.0, split="calibration")]
        )


def test_factorized_training_rejects_tampered_split_protocol_before_model_setup(
    tmp_path: Path,
) -> None:
    manifest = _split_protocol_fixture()
    manifest["tracks"][0]["datasetId"] = "tampered"

    with pytest.raises(ValueError, match="hash mismatch"):
        train_factorized_model(manifest, tmp_path / "model", epochs=1)


def test_factorized_training_rejects_unsealed_strict_split_before_model_setup(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="artifactIntegrity seal"):
        train_factorized_model(
            _split_protocol_fixture(),
            tmp_path / "model",
            epochs=1,
        )


@pytest.mark.parametrize("split", ("train", "development"))
def test_factorized_training_verifies_selected_sealed_files_before_model_setup(
    tmp_path: Path,
    split: str,
) -> None:
    manifest = _sealed_split_protocol_fixture(tmp_path)
    selected = next(track for track in manifest["tracks"] if track["split"] == split)
    feature = Path(selected["path"])
    with np.load(feature, allow_pickle=False) as cached:
        features = cached["features"].copy()
        labels = cached["labels"].copy()
        label_valid = cached["label_valid"].copy()
        training_weight = cached["training_weight"].copy()
    features[0, 0] = 1
    np.savez_compressed(
        feature,
        features=features,
        labels=labels,
        label_valid=label_valid,
        training_weight=training_weight,
    )

    with pytest.raises(ValueError, match="hash or byte count changed"):
        train_factorized_model(manifest, tmp_path / "model", epochs=1)


@pytest.mark.parametrize("split", ("train", "development"))
def test_factorized_training_verifies_selected_label_files_before_model_setup(
    tmp_path: Path,
    split: str,
) -> None:
    manifest = _sealed_split_protocol_fixture(tmp_path)
    selected = next(track for track in manifest["tracks"] if track["split"] == split)
    labels_path = Path(selected["factorizedLabelsPath"])
    with np.load(labels_path, allow_pickle=False) as cached:
        arrays = {name: cached[name].copy() for name in cached.files}
    arrays["root"][0] = 2
    np.savez_compressed(labels_path, **arrays)

    with pytest.raises(ValueError, match="hash or byte count changed"):
        train_factorized_model(manifest, tmp_path / "model", epochs=1)


def test_strict_training_provenance_never_opens_calibration_artifacts(
    tmp_path: Path,
) -> None:
    manifest = _sealed_split_protocol_fixture(tmp_path)
    calibration_tracks = [
        track for track in manifest["tracks"] if track["split"] == "calibration"
    ]
    assert calibration_tracks
    for track in calibration_tracks:
        for key in ("path", "factorizedLabelsPath"):
            sealed_path = Path(track[key])
            sealed_path.rename(sealed_path.with_name(f"unavailable-{sealed_path.name}"))
    manifest_before = json.dumps(manifest, sort_keys=True)

    provenance = _split_protocol_training_provenance(manifest)

    assert json.dumps(manifest, sort_keys=True) == manifest_before
    assert provenance["artifactSetSha256"] == manifest["artifactIntegrity"][
        "artifactSetSha256"
    ]
    assert provenance["artifactFileVerification"] == {
        "metadataScope": "full sealed manifest and artifact set",
        "verifiedSplits": ["train", "development"],
        "verifiedTrackCount": sum(
            track["split"] in {"train", "development"}
            for track in manifest["tracks"]
        ),
        "calibrationFilesOpened": False,
    }


def test_strict_training_provenance_rejects_calibration_seal_metadata_tamper(
    tmp_path: Path,
) -> None:
    manifest = _sealed_split_protocol_fixture(tmp_path)
    calibration_id = next(
        track["id"]
        for track in manifest["tracks"]
        if track["split"] == "calibration"
    )
    calibration_seal = next(
        entry
        for entry in manifest["artifactIntegrity"]["tracks"]
        if entry["id"] == calibration_id
    )
    calibration_seal["featureArtifact"]["sha256"] = "0" * 64
    manifest["splitProtocol"]["outputManifestSha256"] = output_manifest_sha256(
        manifest
    )

    with pytest.raises(ValueError, match="artifact-set hash mismatch"):
        _split_protocol_training_provenance(manifest)


def test_factorized_training_contract_records_balance_and_split_hashes(
    tmp_path: Path,
) -> None:
    manifest = _sealed_split_protocol_fixture(tmp_path)
    provenance = _split_protocol_training_provenance(manifest)
    statistics = {
        "aam": {
            "effectiveFrameMassBefore": 10.0,
            "scale": 1.5,
            "effectiveFrameMassAfter": 15.0,
        },
        "nrgcp": {
            "effectiveFrameMassBefore": 20.0,
            "scale": 0.75,
            "effectiveFrameMassAfter": 15.0,
        },
    }
    contract = _factorized_training_contract(
        protocol=provenance,
        dataset_balance=True,
        dataset_statistics=statistics,
        development_datasets=("aam", "nrgcp"),
        feature_kind="multiband_chroma_v2",
        feature_count=61,
        sample_rate=11_025,
        architecture="tcn",
        augmentation="none",
        epochs=10,
        batch_size=12,
        learning_rate=3e-4,
        seed=20260820,
        window_frames=256,
    )

    assert contract["splitProtocol"]["status"] == "validated"
    assert contract["splitProtocol"]["assignmentSha256"] == manifest["splitProtocol"][
        "assignmentSha256"
    ]
    assert contract["splitProtocol"]["calibrationSetSha256"] == manifest[
        "splitProtocol"
    ]["calibration"]["setSha256"]
    assert contract["splitProtocol"]["cacheManifestSha256"] == manifest[
        "splitProtocol"
    ]["outputManifestSha256"]
    assert contract["splitProtocol"]["artifactSetSha256"] == manifest[
        "artifactIntegrity"
    ]["artifactSetSha256"]
    assert contract["splitProtocol"]["artifactFileVerification"] == {
        "metadataScope": "full sealed manifest and artifact set",
        "verifiedSplits": ["train", "development"],
        "verifiedTrackCount": sum(
            track["split"] in {"train", "development"}
            for track in manifest["tracks"]
        ),
        "calibrationFilesOpened": False,
    }
    assert contract["datasetBalance"]["datasets"] == statistics
    assert contract["selection"]["aggregation"] == "dataset-macro"
    assert contract["selection"]["score"]["productAccuracy"] == 0.3
    assert "jointRootProduct" not in contract["selection"]
    assert "optionalExperiment" not in contract
    assert contract["partitionUse"]["calibration"].startswith("excluded")
    assert _split_protocol_training_provenance(
        {"schemaVersion": FACTORIZED_LABEL_SCHEMA, "tracks": []}
    )["status"] == "absent"


def test_joint_head_training_contract_records_head_loss_and_weight_policy(
    tmp_path: Path,
) -> None:
    manifest = _sealed_split_protocol_fixture(tmp_path)
    contract = _factorized_training_contract(
        protocol=_split_protocol_training_provenance(manifest),
        dataset_balance=False,
        dataset_statistics={},
        development_datasets=("fixture",),
        feature_kind="multiband_chroma_v2",
        feature_count=61,
        sample_rate=11_025,
        architecture="tcn",
        augmentation="pitch-roll",
        epochs=30,
        batch_size=12,
        learning_rate=3e-4,
        seed=20260820,
        window_frames=256,
        joint_root_product=True,
        joint_root_product_loss_weight=0.6,
        product_class_weighting=True,
        joint_root_product_selection_blend=0.5,
    )

    experiment = contract["optionalExperiment"]
    assert experiment["schemaVersion"] == FACTORIZED_OPTIONAL_HEADS_SCHEMA
    assert experiment["jointRootProduct"] == {
        **_joint_root_product_contract(),
        "enabled": True,
        "lossWeight": 0.6,
        "targetSource": "train-only root and product sidecar arrays",
        "developmentSelectionBlend": 0.5,
    }
    assert experiment["productClassWeighting"]["enabled"] is True
    assert experiment["productClassWeighting"]["scope"].startswith("train-only")
    assert contract["loss"]["jointRootProduct"] == 0.6
    assert contract["loss"]["productClassWeighting"] is True
    assert contract["selection"]["score"]["selectionProductAccuracy"] == 0.3
    assert "productAccuracy" not in contract["selection"]["score"]
    assert contract["selection"]["jointRootProduct"] == {
        "schemaVersion": "chord_joint_root_product_checkpoint_selection_v1",
        "metric": "selectionProductAccuracy",
        "diagnostics": [
            "productAccuracy",
            "jointRootProductAccuracy",
            "jointConditionedProductAccuracy",
            "selectionProductAccuracy",
        ],
        "rootAuthority": "independent root-head frame argmax",
        "noChordPolicy": "independent root N forces product N",
        "pitchedProductEvidence": (
            "four-class conditional direct/joint log-probability blend"
        ),
        "jointProductBlend": 0.5,
    }


def test_joint_checkpoint_selection_blend_fails_closed_before_model_setup(
    tmp_path: Path,
) -> None:
    manifest = _sealed_split_protocol_fixture(tmp_path)
    with pytest.raises(ValueError, match="joint_product_blend"):
        train_factorized_model(
            manifest,
            tmp_path / "model",
            epochs=1,
            joint_root_product=True,
            joint_root_product_selection_blend=1.1,
        )


def test_dataset_balanced_selection_is_unweighted_development_dataset_macro() -> None:
    perfect = {
        "rootAccuracy": 1.0,
        "productAccuracy": 1.0,
        "modeAccuracy": 1.0,
        "detailedAccuracy": 1.0,
        "boundaryF1": 1.0,
    }
    zero = {name: 0.0 for name in perfect}
    score, by_dataset = _aggregate_factorized_selection(
        perfect,
        {"large-nrgcp": perfect, "small-aam": zero},
        dataset_balance=True,
    )

    assert by_dataset == {"large-nrgcp": 1.0, "small-aam": 0.0}
    assert score == pytest.approx(0.5)


def test_factorized_cli_exposes_explicit_dataset_balance_challenger() -> None:
    args = build_parser().parse_args(
        [
            "train-factorized",
            "cache.json",
            "--output-root",
            "model",
            "--dataset-balance",
        ]
    )
    assert args.dataset_balance is True
    assert args.joint_root_product_selection_blend == pytest.approx(0.5)


def test_factorized_cli_exposes_joint_head_training_and_frozen_root_blend() -> None:
    train_args = build_parser().parse_args(
        [
            "train-factorized",
            "cache.json",
            "--output-root",
            "model",
            "--joint-root-product",
            "--joint-root-product-loss-weight",
            "0.4",
            "--joint-root-product-selection-blend",
            "0.65",
            "--product-class-weighting",
        ]
    )
    benchmark_args = build_parser().parse_args(
        [
            "benchmark-factorized-cache",
            "cache.json",
            "--track-manifest",
            "tracks.json",
            "--model",
            "model.onnx",
            "--output-root",
            "outputs",
            "--report",
            "report.json",
            "--joint-product-blend",
            "0.75",
        ]
    )

    assert train_args.joint_root_product is True
    assert train_args.joint_root_product_loss_weight == pytest.approx(0.4)
    assert train_args.joint_root_product_selection_blend == pytest.approx(0.65)
    assert train_args.product_class_weighting is True
    assert benchmark_args.joint_product_blend == pytest.approx(0.75)


def test_factorized_cli_dispatches_dataset_balance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(
        json.dumps({"schemaVersion": FACTORIZED_LABEL_SCHEMA, "tracks": []}),
        encoding="utf-8",
    )
    received: dict[str, object] = {}

    def capture(_manifest: dict, _output: Path, **kwargs: object) -> dict:
        received.update(kwargs)
        return {"datasetBalance": kwargs["dataset_balance"]}

    monkeypatch.setattr(chord_reader_cli, "train_factorized_model", capture)
    assert (
        chord_reader_cli.main(
            [
                "train-factorized",
                str(cache_path),
                "--output-root",
                str(tmp_path / "model"),
                "--dataset-balance",
                "--joint-root-product",
                "--joint-root-product-loss-weight",
                "0.4",
                "--joint-root-product-selection-blend",
                "0.65",
                "--product-class-weighting",
            ]
        )
        == 0
    )
    assert received["dataset_balance"] is True
    assert received["joint_root_product"] is True
    assert received["joint_root_product_loss_weight"] == pytest.approx(0.4)
    assert received["joint_root_product_selection_blend"] == pytest.approx(0.65)
    assert received["product_class_weighting"] is True


def test_factorized_cache_benchmark_cli_rejects_tampered_protocol_before_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _split_protocol_fixture()
    manifest["tracks"][0]["datasetId"] = "tampered"
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps(manifest), encoding="utf-8")
    tracks_path = tmp_path / "tracks.json"
    tracks_path.write_text('{"tracks": []}', encoding="utf-8")
    entered = False

    def fail_if_entered(*_args: object, **_kwargs: object) -> dict:
        nonlocal entered
        entered = True
        return {}

    monkeypatch.setattr(chord_reader_cli, "run_factorized_cache_benchmark", fail_if_entered)
    with pytest.raises(ValueError, match="hash mismatch"):
        chord_reader_cli.main(
            [
                "benchmark-factorized-cache",
                str(cache_path),
                "--track-manifest",
                str(tracks_path),
                "--model",
                str(tmp_path / "model.onnx"),
                "--output-root",
                str(tmp_path / "outputs"),
                "--report",
                str(tmp_path / "report.json"),
            ]
        )
    assert entered is False


def test_factorized_cache_benchmark_cli_dispatches_joint_product_blend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_path = tmp_path / "cache.json"
    cache_path.write_text('{"tracks": []}', encoding="utf-8")
    tracks_path = tmp_path / "tracks.json"
    tracks_path.write_text('{"tracks": []}', encoding="utf-8")
    received: dict[str, object] = {}

    def capture(*_args: object, **kwargs: object) -> dict:
        received.update(kwargs)
        return {"jointProductBlend": kwargs["joint_product_blend"]}

    monkeypatch.setattr(chord_reader_cli, "run_factorized_cache_benchmark", capture)
    assert (
        chord_reader_cli.main(
            [
                "benchmark-factorized-cache",
                str(cache_path),
                "--track-manifest",
                str(tracks_path),
                "--model",
                str(tmp_path / "model.onnx"),
                "--output-root",
                str(tmp_path / "outputs"),
                "--report",
                str(tmp_path / "report.json"),
                "--joint-product-blend",
                "0.625",
                "--allow-mixed-joint-members",
            ]
        )
        == 0
    )
    assert received["joint_product_blend"] == pytest.approx(0.625)
    assert received["allow_mixed_joint_members"] is True


def test_factorized_recognizer_rejects_legacy_onnx(tmp_path: Path) -> None:
    legacy = tmp_path / "not-an-onnx-model"
    legacy.write_bytes(b"not onnx")
    with pytest.raises(Exception):
        FactorizedRecognizer(legacy)


def _fixture_factorized_recognizer_outputs() -> tuple[FactorizedRecognizer, np.ndarray]:
    frames = 8
    root = np.full((frames, 13), -10.0, dtype=np.float32)
    root[:, 1] = 10.0  # C throughout: product evidence must not move this path.
    mode = np.full((frames, len(FACTORIZED_MODES)), -10.0, dtype=np.float32)
    mode[:, MODE_INDEX["major"]] = 10.0
    product = np.full((frames, len(FACTORIZED_PRODUCTS)), -10.0, dtype=np.float32)
    product[:4, PRODUCT_INDEX["major"]] = 10.0
    product[4:, PRODUCT_INDEX["dominant"]] = 10.0
    structure = np.full((frames, len(FACTORIZED_STRUCTURES)), -10.0, dtype=np.float32)
    structure[:4, STRUCTURE_INDEX["triad"]] = 10.0
    structure[4:, STRUCTURE_INDEX["seventh"]] = 10.0
    quality = np.full((frames, len(FACTORIZED_QUALITIES)), -10.0, dtype=np.float32)
    quality[:4, QUALITY_INDEX["maj"]] = 10.0
    quality[4:, QUALITY_INDEX["7"]] = 10.0
    bass = np.full((frames, 13), -10.0, dtype=np.float32)
    bass[:, 0] = 10.0
    boundary = np.full((frames, 1), -8.0, dtype=np.float32)
    boundary[4, 0] = 8.0
    outputs = np.concatenate(
        (root, mode, product, structure, quality, bass, boundary), axis=1
    )
    assert outputs.shape == (frames, OUTPUT_WIDTH)

    recognizer = object.__new__(FactorizedRecognizer)
    recognizer.numpy = np
    recognizer.model = Path("fixture-factorized.onnx")
    recognizer.feature_kind = "fixture_features_v1"
    recognizer.feature_count = 2
    recognizer.sample_rate = 11_025
    recognizer.feature_spec_sha256 = None
    recognizer.dasheng_snapshot_root = None
    recognizer.window_frames = None
    recognizer.bass_threshold = 0.65
    recognizer.vocabulary_labels = factorized_vocabulary_labels()
    recognizer._outputs = lambda _features: outputs
    return recognizer, np.zeros((frames, 2), dtype=np.float32)


def _fixture_beat_grid(*, confidence: float = 0.9) -> dict:
    return {
        "schemaVersion": "chord_beat_grid_v1",
        "confidence": confidence,
        "source": "fixture-rhythm",
        "beats": [
            {
                "timeSeconds": time,
                "confidence": 0.9,
                "downbeat": time == 0.4,
                "downbeatConfidence": 0.95 if time == 0.4 else 0.0,
            }
            for time in (0.2, 0.4, 0.6)
        ],
    }


def test_factorized_recognizer_no_beat_invalid_and_zero_rhythm_are_byte_equivalent() -> None:
    recognizer, features = _fixture_factorized_recognizer_outputs()
    baseline = recognizer.predict_features(
        features,
        0.8,
        prediction_id="fixture",
    )
    invalid = recognizer.predict_features(
        features,
        0.8,
        prediction_id="fixture",
        beat_grid={"schemaVersion": "invalid"},
    )
    zero_confidence = recognizer.predict_features(
        features,
        0.8,
        prediction_id="fixture",
        beat_grid=_fixture_beat_grid(confidence=0.0),
    )

    assert invalid == baseline
    assert zero_confidence == baseline
    assert json.dumps(invalid, sort_keys=True, separators=(",", ":")) == json.dumps(
        baseline, sort_keys=True, separators=(",", ":")
    )
    assert "beatAware" not in baseline
    assert "segmentalDiagnostics" not in baseline


def test_factorized_recognizer_segmental_path_preserves_same_root_product_change() -> None:
    recognizer, features = _fixture_factorized_recognizer_outputs()
    prediction = recognizer.predict_features(
        features,
        0.8,
        prediction_id="fixture",
        beat_grid=_fixture_beat_grid(),
        reference_boundaries_seconds=(0.4,),
    )

    assert prediction["beatAware"] is True
    assert prediction["beatGrid"] == {
        "schemaVersion": "chord_beat_grid_v1",
        "source": "fixture-rhythm",
        "confidence": 0.9,
        "beatCount": 3,
        "meanDownbeatConfidence": 0.95,
    }
    assert prediction["segmentalDiagnostics"]["candidateRecall"] == 1
    assert prediction["segmentalDiagnostics"]["prefixLogEvidence"] is True
    assert [segment["label"] for segment in prediction["segments"]] == [
        "C:maj",
        "C:7",
    ]
    assert [segment["productLabel"] for segment in prediction["segments"]] == [
        "C",
        "C7",
    ]
    assert [segment["end"] for segment in prediction["segments"]] == [0.4, 0.8]
    assert all(segment["productConfidence"] > 0.99 for segment in prediction["segments"])
    assert all(segment["detailedConfidence"] > 0.99 for segment in prediction["segments"])


def _ensemble_member_logits(
    *,
    root_index: int,
    product_index: int,
    frames: int = 8,
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
    boundary = np.full((frames, 1), -8.0, dtype=np.float32)
    return np.concatenate(
        (root, mode, product, structure, quality, bass, boundary), axis=1
    )


def _joint_ensemble_member_logits(
    *,
    root_index: int,
    product_index: int,
    joint_product_index: int,
    frames: int = 8,
) -> np.ndarray:
    legacy = _ensemble_member_logits(
        root_index=root_index,
        product_index=product_index,
        frames=frames,
    )
    joint = np.full(
        (frames, JOINT_ROOT_PRODUCT_CLASSES),
        -8.0,
        dtype=np.float32,
    )
    joint[:, joint_root_product_class(root_index, joint_product_index)] = 8.0
    return np.concatenate((legacy, joint), axis=1)


def _ensemble_onnx_metadata(
    *,
    feature_kind: str = "multiband_chroma_v2",
    feature_count: int = 61,
    sample_rate: int = 11_025,
    feature_spec_sha256: str | None = None,
    joint_root_product: bool = False,
) -> dict[str, str]:
    metadata = {
        "chordReaderArchitecture": "tcn",
        "chordReaderFeatureKind": feature_kind,
        "chordReaderFactorizedSchema": "chord_factorized_model_v2",
        "chordReaderFrameSeconds": "0.1",
        "chordReaderOutputWidth": str(
            JOINT_ROOT_PRODUCT_OUTPUT_WIDTH if joint_root_product else OUTPUT_WIDTH
        ),
        "chordReaderQualities": json.dumps(list(FACTORIZED_QUALITIES)),
        "chordReaderModes": json.dumps(list(FACTORIZED_MODES)),
        "chordReaderProducts": json.dumps(list(FACTORIZED_PRODUCTS)),
        "chordReaderStructures": json.dumps(list(FACTORIZED_STRUCTURES)),
        "chordReaderFeatureCount": str(feature_count),
        "chordReaderSampleRate": str(sample_rate),
    }
    if feature_spec_sha256 is not None:
        metadata["chordReaderFeatureSpecSha256"] = feature_spec_sha256
    if joint_root_product:
        metadata["chordReaderJointRootProduct"] = json.dumps(
            _joint_root_product_contract(),
            sort_keys=True,
            separators=(",", ":"),
        )
    return metadata


def _install_fake_factorized_onnx_runtime(
    monkeypatch: pytest.MonkeyPatch,
    specifications: dict[str, dict],
) -> dict[str, list]:
    sessions: dict[str, list] = {path: [] for path in specifications}

    class FakeSession:
        def __init__(self, path: str, *, providers: list[str]) -> None:
            assert providers == ["CPUExecutionProvider"]
            self.path = path
            self.specification = specifications[path]
            self.run_calls = 0
            sessions[path].append(self)

        def get_modelmeta(self) -> SimpleNamespace:
            return SimpleNamespace(
                custom_metadata_map=self.specification["metadata"]
            )

        def get_inputs(self) -> list[SimpleNamespace]:
            count = int(
                self.specification["metadata"]["chordReaderFeatureCount"]
            )
            return [
                SimpleNamespace(
                    name="features",
                    type="tensor(float)",
                    shape=["batch", "frames", count],
                )
            ]

        def get_outputs(self) -> list[SimpleNamespace]:
            width = int(
                self.specification["metadata"]["chordReaderOutputWidth"]
            )
            return [
                SimpleNamespace(
                    name="outputs",
                    type="tensor(float)",
                    shape=["batch", "frames", width],
                )
            ]

        def run(self, _outputs: None, inputs: dict[str, np.ndarray]) -> list[np.ndarray]:
            self.run_calls += 1
            assert set(inputs) == {"features"}
            output = self.specification["outputs"]
            if callable(output):
                output = output(inputs["features"])
            return [np.asarray(output)[None]]

    monkeypatch.setitem(
        sys.modules,
        "onnxruntime",
        SimpleNamespace(InferenceSession=FakeSession),
    )
    return sessions


def _write_fake_ensemble_models(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    first_outputs: np.ndarray,
    second_outputs: np.ndarray,
    *,
    first_metadata: dict[str, str] | None = None,
    second_metadata: dict[str, str] | None = None,
) -> tuple[tuple[Path, Path], dict[str, list]]:
    models, sessions = _write_fake_ensemble_member_set(
        tmp_path,
        monkeypatch,
        (first_outputs, second_outputs),
        (
            first_metadata or _ensemble_onnx_metadata(),
            second_metadata or _ensemble_onnx_metadata(),
        ),
    )
    return (models[0], models[1]), sessions


def _write_fake_ensemble_member_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    outputs: tuple[np.ndarray, ...],
    metadata: tuple[dict[str, str], ...],
) -> tuple[tuple[Path, ...], dict[str, list]]:
    assert len(outputs) == len(metadata) >= 2
    names = (
        ("first.onnx", "second.onnx")
        if len(outputs) == 2
        else tuple(f"member-{index}.onnx" for index in range(len(outputs)))
    )
    models = tuple(tmp_path / name for name in names)
    for index, model in enumerate(models):
        model.write_bytes(f"fixture factorized member {index}".encode())
    specifications = {
        str(model): {
            "metadata": member_metadata,
            "outputs": member_outputs,
        }
        for model, member_metadata, member_outputs in zip(
            models,
            metadata,
            outputs,
            strict=True,
        )
    }
    sessions = _install_fake_factorized_onnx_runtime(
        monkeypatch, specifications
    )
    return models, sessions


def test_factorized_ensemble_combines_each_head_before_one_decode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_outputs = _ensemble_member_logits(
        root_index=1, product_index=PRODUCT_INDEX["major"]
    )
    second_outputs = _ensemble_member_logits(
        root_index=8, product_index=PRODUCT_INDEX["dominant"]
    )
    models, sessions = _write_fake_ensemble_models(
        tmp_path, monkeypatch, first_outputs, second_outputs
    )
    recognizer = FactorizedEnsembleRecognizer(models)
    features = np.zeros((8, 61), dtype=np.float32)

    outputs = recognizer._outputs(features)
    expected = _combine_factorized_member_outputs(
        (first_outputs, second_outputs), (0.5, 0.5), np
    )
    assert np.array_equal(outputs, expected)
    prediction = recognizer.predict_features(
        features, 0.8, prediction_id="ensemble-fixture"
    )

    assert prediction["engine"] == "chord-factorized-logit-ensemble-v9"
    assert prediction["model"] == recognizer.ensemble_id
    assert prediction["modelProvenance"]["schemaVersion"] == (
        FACTORIZED_ENSEMBLE_PROVENANCE_SCHEMA
    )
    assert prediction["ensembleDecoderContract"]["schemaVersion"] == (
        FACTORIZED_ENSEMBLE_DECODER_SCHEMA
    )
    assert prediction["ensembleDecoderContract"]["aggregation"] == {
        "domain": "pre-decode logits",
        "root": "member-weighted arithmetic mean",
        "conditionalQualityHeads": ["mode", "product", "structure", "quality"],
        "conditionalQuality": "independent member-weighted arithmetic mean per head",
        "bass": "member-weighted arithmetic mean",
        "boundary": "member-weighted arithmetic mean before sigmoid",
        "decodedSegments": "never averaged or voted",
    }
    assert all(
        session.run_calls == 2
        for member_sessions in sessions.values()
        for session in member_sessions
    )


def test_factorized_ensemble_one_hot_endpoint_exactly_reproduces_member_decode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_outputs = _ensemble_member_logits(
        root_index=1, product_index=PRODUCT_INDEX["major"]
    )
    second_outputs = _ensemble_member_logits(
        root_index=8, product_index=PRODUCT_INDEX["dominant"]
    )
    models, _sessions = _write_fake_ensemble_models(
        tmp_path, monkeypatch, first_outputs, second_outputs
    )
    endpoint = FactorizedEnsembleRecognizer(models, weights=(0.0, 1.0))
    member = FactorizedRecognizer(models[1])
    features = np.zeros((8, 61), dtype=np.float32)

    assert np.array_equal(endpoint._outputs(features), member._outputs(features))
    ensemble_prediction = endpoint.predict_features(
        features, 0.8, prediction_id="fixture"
    )
    member_prediction = member.predict_features(
        features, 0.8, prediction_id="fixture"
    )
    assert ensemble_prediction["segments"] == member_prediction["segments"]


@pytest.mark.parametrize(
    "weights",
    [
        (1.0,),
        (-0.1, 1.1),
        (float("nan"), 1.0),
        (float("inf"), 0.0),
        (0.4, 0.4),
        (0.0, 0.0),
        (True, False),
    ],
)
def test_factorized_ensemble_rejects_bad_weights(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    weights: tuple[float, ...],
) -> None:
    outputs = _ensemble_member_logits(
        root_index=1, product_index=PRODUCT_INDEX["major"]
    )
    models, _sessions = _write_fake_ensemble_models(
        tmp_path, monkeypatch, outputs, outputs
    )
    with pytest.raises(ValueError, match="weights"):
        FactorizedEnsembleRecognizer(models, weights=weights)


def test_factorized_ensemble_rejects_incompatible_member_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = _ensemble_member_logits(
        root_index=1, product_index=PRODUCT_INDEX["major"]
    )
    second_metadata = _ensemble_onnx_metadata(
        feature_kind="harmonic_cqt_v3", feature_count=145
    )
    models, _sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        outputs,
        outputs,
        second_metadata=second_metadata,
    )
    with pytest.raises(ValueError, match="incompatible feature"):
        FactorizedEnsembleRecognizer(models)


def test_joint_head_metadata_is_exact_and_mixed_ensembles_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = _ensemble_onnx_metadata(joint_root_product=True)
    assert _factorized_metadata_joint_root_product(metadata) is True
    tampered = dict(metadata)
    tampered["chordReaderJointRootProduct"] = json.dumps(
        {**_joint_root_product_contract(), "classes": 48}
    )
    with pytest.raises(ValueError, match="incompatible"):
        _factorized_metadata_joint_root_product(tampered)

    legacy = _ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
    )
    challenger = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    models, _sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        legacy,
        challenger,
        second_metadata=metadata,
    )
    with pytest.raises(ValueError, match="requires a model with the optional joint head"):
        FactorizedRecognizer(models[0], joint_product_blend=0.5)
    with pytest.raises(ValueError, match="incompatible feature"):
        FactorizedEnsembleRecognizer(models)


def test_mixed_joint_ensemble_combines_common_heads_globally_and_joint_subset_only() -> None:
    legacy = _ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        frames=3,
    )
    first_joint = _joint_ensemble_member_logits(
        root_index=3,
        product_index=PRODUCT_INDEX["minor"],
        joint_product_index=PRODUCT_INDEX["dominant"],
        frames=3,
    )
    second_joint = _joint_ensemble_member_logits(
        root_index=8,
        product_index=PRODUCT_INDEX["dominant"],
        joint_product_index=PRODUCT_INDEX["minor-seventh"],
        frames=3,
    )
    weights = (0.5, 0.3, 0.2)

    combined = _combine_factorized_member_outputs(
        (legacy, first_joint, second_joint),
        weights,
        np,
        joint_root_product=True,
        member_joint_root_product=(False, True, True),
    )

    expected_common = (
        weights[0] * legacy.astype(np.float64)
        + weights[1] * first_joint[:, :OUTPUT_WIDTH].astype(np.float64)
        + weights[2] * second_joint[:, :OUTPUT_WIDTH].astype(np.float64)
    ).astype(np.float32)
    expected_joint = (
        0.6 * first_joint[:, OUTPUT_WIDTH:].astype(np.float64)
        + 0.4 * second_joint[:, OUTPUT_WIDTH:].astype(np.float64)
    ).astype(np.float32)
    assert combined.shape == (3, JOINT_ROOT_PRODUCT_OUTPUT_WIDTH)
    assert np.array_equal(combined[:, :OUTPUT_WIDTH], expected_common)
    assert np.array_equal(combined[:, OUTPUT_WIDTH:], expected_joint)


def test_mixed_joint_ensemble_requires_explicit_opt_in_and_binds_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = _ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
    )
    challenger = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    models, _sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        legacy,
        challenger,
        second_metadata=_ensemble_onnx_metadata(joint_root_product=True),
    )

    recognizer = FactorizedEnsembleRecognizer(
        models,
        weights=(0.75, 0.25),
        joint_product_blend=1.0,
        allow_mixed_joint_members=True,
    )
    outputs = recognizer._outputs(np.zeros((8, 61), dtype=np.float32))
    prediction = recognizer.predict_features(
        np.zeros((8, 61), dtype=np.float32),
        0.8,
        prediction_id="mixed-fixture",
    )

    policy = recognizer.mixed_joint_ensemble_policy
    assert policy is not None
    assert policy == {
        "schemaVersion": FACTORIZED_MIXED_JOINT_ENSEMBLE_SCHEMA,
        "memberHeadTypes": ["legacy-90", "joint-139"],
        "commonHeads": {
            "memberIndices": [0, 1],
            "normalizedGlobalWeights": [0.75, 0.25],
            "aggregation": (
                "member-weighted arithmetic mean of common pre-decode logits"
            ),
        },
        "jointRootProduct": {
            "contributorIndices": [1],
            "globalWeightMass": 0.25,
            "normalizedContributorWeights": [1.0],
            "aggregation": (
                "joint-contributor-weighted arithmetic mean of pre-decode logits"
            ),
        },
        "output": {
            "width": JOINT_ROOT_PRODUCT_OUTPUT_WIDTH,
            "headOrder": [
                "root",
                "mode",
                "product",
                "structure",
                "quality",
                "bass",
                "boundary",
                "joint_root_product",
            ],
        },
    }
    assert np.array_equal(outputs[:, OUTPUT_WIDTH:], challenger[:, OUTPUT_WIDTH:])
    assert recognizer.output_width == JOINT_ROOT_PRODUCT_OUTPUT_WIDTH
    assert prediction["segments"][0]["productLabel"] == "C7"
    assert prediction["modelProvenance"]["mixedJointEnsemblePolicy"] == policy
    assert prediction["ensembleDecoderContract"]["aggregation"][
        "mixedJointMembers"
    ] == policy
    assert [
        member["headType"] for member in prediction["modelProvenance"]["members"]
    ] == ["legacy-90", "joint-139"]


@pytest.mark.parametrize("joint_root_product", [False, True])
def test_homogeneous_factorized_ensembles_keep_default_bit_exact_aggregation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    joint_root_product: bool,
) -> None:
    if joint_root_product:
        first_outputs = _joint_ensemble_member_logits(
            root_index=1,
            product_index=PRODUCT_INDEX["major"],
            joint_product_index=PRODUCT_INDEX["major"],
        )
        second_outputs = _joint_ensemble_member_logits(
            root_index=8,
            product_index=PRODUCT_INDEX["dominant"],
            joint_product_index=PRODUCT_INDEX["dominant"],
        )
    else:
        first_outputs = _ensemble_member_logits(
            root_index=1,
            product_index=PRODUCT_INDEX["major"],
        )
        second_outputs = _ensemble_member_logits(
            root_index=8,
            product_index=PRODUCT_INDEX["dominant"],
        )
    metadata = _ensemble_onnx_metadata(joint_root_product=joint_root_product)
    models, _sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        first_outputs,
        second_outputs,
        first_metadata=metadata,
        second_metadata=metadata,
    )
    recognizer = FactorizedEnsembleRecognizer(models, weights=(0.25, 0.75))

    expected = (
        0.25 * first_outputs.astype(np.float64)
        + 0.75 * second_outputs.astype(np.float64)
    ).astype(np.float32)
    actual = recognizer._outputs(np.zeros((8, 61), dtype=np.float32))
    assert np.array_equal(actual, expected)
    assert recognizer.allow_mixed_joint_members is False
    assert recognizer.mixed_joint_ensemble_policy is None
    assert "mixedJointEnsemblePolicy" not in recognizer.model_provenance
    assert all("headType" not in item for item in recognizer.model_provenance["members"])


def test_homogeneous_joint_ensemble_preserves_adversarial_normalized_weights_verbatim() -> None:
    raw_weights = (
        0.06871806943489511,
        0.7685706272824713,
        0.16271130328263375,
    )
    weights = _normalized_ensemble_weights(3, raw_weights)
    assert math.fsum(weights) == 0.9999999999999999
    outputs = [
        _joint_ensemble_member_logits(
            root_index=1,
            product_index=PRODUCT_INDEX["major"],
            joint_product_index=PRODUCT_INDEX["major"],
            frames=1,
        ).astype(np.float64)
        for _index in range(3)
    ]
    values = [2.4580338977940386, 4.835739785214589]
    values.append(
        -(weights[0] * values[0] + weights[1] * values[1]) / weights[2]
    )
    for output, value in zip(outputs, values, strict=True):
        output[0, OUTPUT_WIDTH] = value

    actual = _combine_factorized_member_outputs(
        outputs,
        weights,
        np,
        joint_root_product=True,
    )
    expected_evidence = np.zeros(outputs[0].shape, dtype=np.float64)
    for weight, output in zip(weights, outputs, strict=True):
        expected_evidence += weight * output
    expected = expected_evidence.astype(np.float32)
    assert np.array_equal(actual, expected)
    assert actual[:, OUTPUT_WIDTH:].tobytes() == expected[:, OUTPUT_WIDTH:].tobytes()


def test_mixed_joint_one_hot_joint_endpoint_exactly_reproduces_joint_member(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = _ensemble_member_logits(
        root_index=8,
        product_index=PRODUCT_INDEX["minor"],
    )
    joint_outputs = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    models, _sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        legacy,
        joint_outputs,
        second_metadata=_ensemble_onnx_metadata(joint_root_product=True),
    )
    mixed = FactorizedEnsembleRecognizer(
        models,
        weights=(0.0, 1.0),
        joint_product_blend=0.7,
        allow_mixed_joint_members=True,
    )
    joint_member = FactorizedRecognizer(models[1], joint_product_blend=0.7)
    features = np.zeros((8, 61), dtype=np.float32)

    assert np.array_equal(mixed._outputs(features), joint_member._outputs(features))
    assert mixed.predict_features(
        features,
        0.8,
        prediction_id="endpoint",
    )["segments"] == joint_member.predict_features(
        features,
        0.8,
        prediction_id="endpoint",
    )["segments"]


def test_mixed_blend_one_ignores_direct_product_and_never_moves_frame_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    joint_metadata = _ensemble_onnx_metadata(joint_root_product=True)
    joint_major_direct = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    (tmp_path / "major-direct").mkdir()
    first_models, _first_sessions = _write_fake_ensemble_models(
        tmp_path / "major-direct",
        monkeypatch,
        _ensemble_member_logits(
            root_index=1,
            product_index=PRODUCT_INDEX["major"],
        ),
        joint_major_direct,
        second_metadata=joint_metadata,
    )
    first = FactorizedEnsembleRecognizer(
        first_models,
        weights=(0.5, 0.5),
        joint_product_blend=1.0,
        allow_mixed_joint_members=True,
    )

    joint_minor_direct = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["minor"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    (tmp_path / "minor-direct").mkdir()
    second_models, _second_sessions = _write_fake_ensemble_models(
        tmp_path / "minor-direct",
        monkeypatch,
        _ensemble_member_logits(
            root_index=1,
            product_index=PRODUCT_INDEX["minor"],
        ),
        joint_minor_direct,
        second_metadata=joint_metadata,
    )
    second = FactorizedEnsembleRecognizer(
        second_models,
        weights=(0.5, 0.5),
        joint_product_blend=1.0,
        allow_mixed_joint_members=True,
    )
    features = np.zeros((8, 61), dtype=np.float32)
    first_prediction = first.predict_features(
        features,
        0.8,
        prediction_id="direct-major",
    )
    second_prediction = second.predict_features(
        features,
        0.8,
        prediction_id="direct-minor",
    )

    assert first_prediction["segments"][0]["productLabel"] == "C7"
    assert second_prediction["segments"][0]["productLabel"] == "C7"
    assert first_prediction["segments"][0]["productConfidence"] == pytest.approx(
        second_prediction["segments"][0]["productConfidence"],
        abs=1e-12,
    )
    heads = split_factorized_outputs(
        first._outputs(features),
        joint_root_product=True,
    )
    boundary = 1 / (1 + np.exp(-heads["boundary"][:, 0]))
    roots_direct, _products_direct = _hierarchical_product_path(
        heads["root"],
        heads["product"],
        boundary,
        np,
        joint_root_product_logits=heads["joint_root_product"],
        joint_product_blend=0.0,
    )
    roots_joint, _products_joint = _hierarchical_product_path(
        heads["root"],
        heads["product"],
        boundary,
        np,
        joint_root_product_logits=heads["joint_root_product"],
        joint_product_blend=1.0,
    )
    assert roots_direct == roots_joint == [1] * 8


def test_mixed_product_confidence_uses_post_aggregation_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = _ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
    )
    joint_major = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["major"],
    )
    joint_dominant = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    joint_metadata = _ensemble_onnx_metadata(joint_root_product=True)
    models, _sessions = _write_fake_ensemble_member_set(
        tmp_path,
        monkeypatch,
        (legacy, joint_major, joint_dominant),
        (_ensemble_onnx_metadata(), joint_metadata, joint_metadata),
    )
    recognizer = FactorizedEnsembleRecognizer(
        models,
        weights=(0.5, 0.25, 0.25),
        joint_product_blend=1.0,
        allow_mixed_joint_members=True,
    )
    features = np.zeros((8, 61), dtype=np.float32)
    prediction = recognizer.predict_features(
        features,
        0.8,
        prediction_id="confidence",
    )
    heads = split_factorized_outputs(
        recognizer._outputs(features),
        joint_root_product=True,
    )
    root_probability = np.exp(
        heads["root"][0, 1] - np.log(np.exp(heads["root"][0]).sum())
    )
    conditional = _conditional_product_evidence(
        heads["product"],
        heads["joint_root_product"],
        1,
        1.0,
        np,
    )
    conditional_probability = np.exp(
        conditional[0, 0] - np.log(np.exp(conditional[0]).sum())
    )
    expected_confidence = float(np.sqrt(root_probability * conditional_probability))

    assert prediction["segments"][0]["productLabel"] == "C"
    assert prediction["segments"][0]["productConfidence"] == pytest.approx(
        expected_confidence,
        abs=1e-6,
    )
    assert prediction["segments"][0]["productConfidence"] < 0.72


def test_mixed_joint_ensemble_member_order_weights_and_policy_bind_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = _ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
    )
    challenger = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    models, _sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        legacy,
        challenger,
        second_metadata=_ensemble_onnx_metadata(joint_root_product=True),
    )
    arguments = {
        "weights": (0.75, 0.25),
        "joint_product_blend": 1.0,
        "allow_mixed_joint_members": True,
    }
    first = FactorizedEnsembleRecognizer(models, **arguments)
    duplicate = FactorizedEnsembleRecognizer(models, **arguments)
    reordered = FactorizedEnsembleRecognizer(
        tuple(reversed(models)),
        weights=(0.25, 0.75),
        joint_product_blend=1.0,
        allow_mixed_joint_members=True,
    )
    reweighted = FactorizedEnsembleRecognizer(
        models,
        weights=(0.6, 0.4),
        joint_product_blend=1.0,
        allow_mixed_joint_members=True,
    )
    features = np.zeros((8, 61), dtype=np.float32)
    predictions = [
        recognizer.predict_features(features, 0.8, prediction_id="hash-fixture")
        for recognizer in (first, duplicate, reordered, reweighted)
    ]
    prediction_file_hashes = [
        hashlib.sha256(
            (json.dumps(prediction, indent=2, sort_keys=True) + "\n").encode("utf-8")
        ).hexdigest()
        for prediction in predictions
    ]

    assert first.ensemble_sha256 == duplicate.ensemble_sha256
    assert first.decoder_contract_sha256 == duplicate.decoder_contract_sha256
    assert first.model_provenance == duplicate.model_provenance
    assert _factorized_canonical_sha256(predictions[0]) == (
        _factorized_canonical_sha256(predictions[1])
    )
    assert prediction_file_hashes[0] == prediction_file_hashes[1]
    assert len(
        {
            first.ensemble_sha256,
            reordered.ensemble_sha256,
            reweighted.ensemble_sha256,
        }
    ) == 3
    assert len(
        {
            first.decoder_contract_sha256,
            reordered.decoder_contract_sha256,
            reweighted.decoder_contract_sha256,
        }
    ) == 3
    assert len(
        {
            _factorized_canonical_sha256(predictions[0]),
            _factorized_canonical_sha256(predictions[2]),
            _factorized_canonical_sha256(predictions[3]),
        }
    ) == 3
    assert len(
        {
            prediction_file_hashes[0],
            prediction_file_hashes[2],
            prediction_file_hashes[3],
        }
    ) == 3


@pytest.mark.parametrize(
    ("weights", "member_types", "message"),
    [
        ((1.0, 0.0), ("legacy", "joint"), "positive total weight"),
        ((0.5, 0.5), ("legacy", "legacy"), "at least one legacy and one joint"),
        ((0.5, 0.5), ("joint", "joint"), "at least one legacy and one joint"),
    ],
)
def test_mixed_joint_ensemble_rejects_zero_joint_mass_or_nonmixed_members(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    weights: tuple[float, float],
    member_types: tuple[str, str],
    message: str,
) -> None:
    legacy = _ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
    )
    challenger = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    outputs = {"legacy": legacy, "joint": challenger}
    metadata = {
        "legacy": _ensemble_onnx_metadata(),
        "joint": _ensemble_onnx_metadata(joint_root_product=True),
    }
    models, _sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        outputs[member_types[0]],
        outputs[member_types[1]],
        first_metadata=metadata[member_types[0]],
        second_metadata=metadata[member_types[1]],
    )
    with pytest.raises(ValueError, match=message):
        FactorizedEnsembleRecognizer(
            models,
            weights=weights,
            joint_product_blend=(
                1.0 if member_types == ("legacy", "joint") else 0.0
            ),
            allow_mixed_joint_members=True,
        )


@pytest.mark.parametrize("mismatch", ["feature", "vocabulary"])
def test_mixed_joint_ensemble_rejects_common_contract_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mismatch: str,
) -> None:
    legacy = _ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
    )
    challenger = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    metadata = _ensemble_onnx_metadata(joint_root_product=True)
    if mismatch == "feature":
        metadata.update(
            _ensemble_onnx_metadata(
                feature_kind="harmonic_cqt_v3",
                feature_count=145,
                joint_root_product=True,
            )
        )
    else:
        metadata["chordReaderProducts"] = json.dumps(
            list(reversed(FACTORIZED_PRODUCTS))
        )
    models, _sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        legacy,
        challenger,
        second_metadata=metadata,
    )
    with pytest.raises(ValueError, match="incompatible"):
        FactorizedEnsembleRecognizer(
            models,
            allow_mixed_joint_members=True,
        )


def test_joint_recognizer_blend_changes_product_only_and_binds_decoder_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
    )
    metadata = _ensemble_onnx_metadata(joint_root_product=True)
    models, _sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        outputs,
        outputs,
        first_metadata=metadata,
        second_metadata=metadata,
    )
    direct = FactorizedRecognizer(models[0], joint_product_blend=0.0)
    joint = FactorizedRecognizer(models[0], joint_product_blend=1.0)
    features = np.zeros((8, 61), dtype=np.float32)

    direct_prediction = direct.predict_features(
        features,
        0.8,
        prediction_id="joint-fixture",
    )
    joint_prediction = joint.predict_features(
        features,
        0.8,
        prediction_id="joint-fixture",
    )
    assert [segment["productLabel"] for segment in direct_prediction["segments"]] == [
        "C"
    ]
    assert [segment["productLabel"] for segment in joint_prediction["segments"]] == [
        "C7"
    ]
    assert all(
        segment["label"].startswith("C:")
        for prediction in (direct_prediction, joint_prediction)
        for segment in prediction["segments"]
    )
    assert direct_prediction["decoderContractSha256"] != joint_prediction[
        "decoderContractSha256"
    ]
    assert direct_prediction["jointProductBlend"] == 0.0
    assert joint_prediction["jointProductBlend"] == 1.0


def test_joint_zero_blend_confidence_is_continuous_without_changing_legacy_confidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["major"],
    )
    product_offset = 13 + len(FACTORIZED_MODES)
    outputs[:, product_offset + PRODUCT_INDEX["none"]] = 8.0
    legacy_outputs = outputs[:, :OUTPUT_WIDTH].copy()
    joint_metadata = _ensemble_onnx_metadata(joint_root_product=True)

    legacy_root = tmp_path / "legacy"
    legacy_root.mkdir()
    legacy_models, _legacy_sessions = _write_fake_ensemble_models(
        legacy_root,
        monkeypatch,
        legacy_outputs,
        legacy_outputs,
    )
    legacy = FactorizedRecognizer(legacy_models[0])

    joint_root = tmp_path / "joint"
    joint_root.mkdir()
    joint_models, _joint_sessions = _write_fake_ensemble_models(
        joint_root,
        monkeypatch,
        outputs,
        outputs,
        first_metadata=joint_metadata,
        second_metadata=joint_metadata,
    )
    joint_zero = FactorizedRecognizer(joint_models[0], joint_product_blend=0.0)
    joint_epsilon = FactorizedRecognizer(
        joint_models[0],
        joint_product_blend=1e-9,
    )
    features = np.zeros((8, 61), dtype=np.float32)

    legacy_prediction = legacy.predict_features(
        features,
        0.8,
        prediction_id="confidence-fixture",
    )
    zero_prediction = joint_zero.predict_features(
        features,
        0.8,
        prediction_id="confidence-fixture",
    )
    epsilon_prediction = joint_epsilon.predict_features(
        features,
        0.8,
        prediction_id="confidence-fixture",
    )
    assert [
        prediction["segments"][0]["productLabel"]
        for prediction in (legacy_prediction, zero_prediction, epsilon_prediction)
    ] == ["C", "C", "C"]
    legacy_confidence = legacy_prediction["segments"][0]["productConfidence"]
    zero_confidence = zero_prediction["segments"][0]["productConfidence"]
    epsilon_confidence = epsilon_prediction["segments"][0]["productConfidence"]
    assert legacy_confidence == pytest.approx(2**-0.5, abs=1e-5)
    assert zero_confidence > 0.999
    assert epsilon_confidence == pytest.approx(zero_confidence, abs=1e-8)


@pytest.mark.parametrize(
    ("metadata_key", "metadata_value", "message"),
    [
        ("chordReaderFrameSeconds", "0.2", "frame grid"),
        ("chordReaderOutputWidth", "1", "output width"),
        ("chordReaderQualities", '["maj"]', "incompatible vocabulary"),
    ],
)
def test_factorized_ensemble_rejects_invalid_member_runtime_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    metadata_key: str,
    metadata_value: str,
    message: str,
) -> None:
    outputs = _ensemble_member_logits(
        root_index=1, product_index=PRODUCT_INDEX["major"]
    )
    metadata = _ensemble_onnx_metadata()
    metadata[metadata_key] = metadata_value
    models, _sessions = _write_fake_ensemble_models(
        tmp_path, monkeypatch, outputs, outputs, second_metadata=metadata
    )
    with pytest.raises(ValueError, match=message):
        FactorizedEnsembleRecognizer(models)


def test_factorized_ensemble_fails_closed_on_nonfinite_or_misaligned_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_outputs = _ensemble_member_logits(
        root_index=1, product_index=PRODUCT_INDEX["major"]
    )
    invalid_outputs = first_outputs.copy()
    invalid_outputs[0, 0] = np.nan
    models, _sessions = _write_fake_ensemble_models(
        tmp_path, monkeypatch, first_outputs, invalid_outputs
    )
    recognizer = FactorizedEnsembleRecognizer(models)

    with pytest.raises(ValueError, match="finite floating-point logits"):
        recognizer.predict_features(
            np.zeros((8, 61), dtype=np.float32),
            0.8,
            prediction_id="fixture",
        )
    with pytest.raises(ValueError, match="non-empty finite numeric"):
        recognizer.predict_features(
            np.full((8, 61), np.nan, dtype=np.float32),
            0.8,
            prediction_id="fixture",
        )


def test_factorized_ensemble_provenance_is_content_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_outputs = _ensemble_member_logits(
        root_index=1, product_index=PRODUCT_INDEX["major"]
    )
    second_outputs = _ensemble_member_logits(
        root_index=8, product_index=PRODUCT_INDEX["dominant"]
    )
    models, _sessions = _write_fake_ensemble_models(
        tmp_path, monkeypatch, first_outputs, second_outputs
    )
    first = FactorizedEnsembleRecognizer(models, weights=(0.25, 0.75))
    second = FactorizedEnsembleRecognizer(models, weights=(0.25, 0.75))

    assert first.ensemble_id == second.ensemble_id
    assert first.ensemble_sha256 == second.ensemble_sha256
    assert first.model_provenance == second.model_provenance
    assert len(first.decoder_contract_sha256) == 64
    assert [member["fileName"] for member in first.model_provenance["members"]] == [
        "first.onnx",
        "second.onnx",
    ]
    assert all(
        len(member["sha256"]) == 64
        for member in first.model_provenance["members"]
    )


def test_factorized_dasheng_ensemble_extracts_one_shared_feature_array(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames = 3
    outputs = _ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        frames=frames,
    )
    dasheng_metadata = _ensemble_onnx_metadata(
        feature_kind="dasheng_base_v1",
        feature_count=768,
        sample_rate=16_000,
        feature_spec_sha256="a" * 64,
    )
    models, sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        outputs,
        outputs,
        first_metadata=dasheng_metadata,
        second_metadata=dasheng_metadata,
    )
    from steel_guitar_rag.chord_reader import dasheng

    extraction_calls = 0

    def extract_once(_audio: Path, snapshot_root: Path) -> tuple[np.ndarray, float]:
        nonlocal extraction_calls
        extraction_calls += 1
        assert snapshot_root == tmp_path / "snapshot"
        return np.zeros((frames, 768), dtype=np.float32), 0.3

    monkeypatch.setattr(dasheng, "extract_dasheng_features", extract_once)
    recognizer = FactorizedEnsembleRecognizer(
        models, dasheng_snapshot_root=tmp_path / "snapshot"
    )
    prediction = recognizer.predict(tmp_path / "fixture.wav")

    assert prediction["featureKind"] == "dasheng_base_v1"
    assert extraction_calls == 1
    assert all(
        session.run_calls == 1
        for member_sessions in sessions.values()
        for session in member_sessions
    )


def test_mixed_joint_dasheng_ensemble_extracts_features_once_per_audio(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames = 3
    legacy = _ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        frames=frames,
    )
    joint = _joint_ensemble_member_logits(
        root_index=1,
        product_index=PRODUCT_INDEX["major"],
        joint_product_index=PRODUCT_INDEX["dominant"],
        frames=frames,
    )
    dasheng_metadata = _ensemble_onnx_metadata(
        feature_kind="dasheng_base_v1",
        feature_count=768,
        sample_rate=16_000,
        feature_spec_sha256="a" * 64,
    )
    joint_dasheng_metadata = _ensemble_onnx_metadata(
        feature_kind="dasheng_base_v1",
        feature_count=768,
        sample_rate=16_000,
        feature_spec_sha256="a" * 64,
        joint_root_product=True,
    )
    models, sessions = _write_fake_ensemble_models(
        tmp_path,
        monkeypatch,
        legacy,
        joint,
        first_metadata=dasheng_metadata,
        second_metadata=joint_dasheng_metadata,
    )
    from steel_guitar_rag.chord_reader import dasheng

    extraction_calls = 0

    def extract_once(_audio: Path, snapshot_root: Path) -> tuple[np.ndarray, float]:
        nonlocal extraction_calls
        extraction_calls += 1
        assert snapshot_root == tmp_path / "snapshot"
        return np.zeros((frames, 768), dtype=np.float32), 0.3

    monkeypatch.setattr(dasheng, "extract_dasheng_features", extract_once)
    recognizer = FactorizedEnsembleRecognizer(
        models,
        dasheng_snapshot_root=tmp_path / "snapshot",
        joint_product_blend=1.0,
        allow_mixed_joint_members=True,
    )
    prediction = recognizer.predict(tmp_path / "fixture.wav")

    assert prediction["featureKind"] == "dasheng_base_v1"
    assert prediction["segments"][0]["productLabel"] == "C7"
    assert extraction_calls == 1
    assert all(
        session.run_calls == 1
        for member_sessions in sessions.values()
        for session in member_sessions
    )
