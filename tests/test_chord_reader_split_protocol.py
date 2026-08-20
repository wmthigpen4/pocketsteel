from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from steel_guitar_rag.chord_reader.split_protocol import (
    CALIBRATION_PURPOSE,
    FACTORIZED_LABEL_SCHEMA,
    PARTITIONS,
    build_leak_resistant_split_manifest,
    output_manifest_sha256,
    source_manifest_sha256,
    validate_split_protocol_manifest,
)


def _track(
    identifier: str,
    dataset: str,
    composition: str,
    *,
    split: str = "train",
) -> dict[str, object]:
    return {
        "id": identifier,
        "datasetId": dataset,
        "compositionId": composition,
        "split": split,
        "path": f"/features/{identifier}.npz",
        "factorizedLabelsPath": f"/labels/{identifier}.npz",
        "provenance": {"archive": dataset, "row": identifier},
        "trainingWeight": 1.0,
    }


def _manifest(tracks: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schemaVersion": FACTORIZED_LABEL_SCHEMA,
        "featureKind": "multiband_chroma_v2",
        "featureCount": 61,
        "sampleRate": 11025,
        "frameSeconds": 0.1,
        "tracks": tracks,
    }


def _timing_manifest(tracks: list[dict[str, object]]) -> dict[str, object]:
    return {"schemaVersion": "chord_track_manifest_v1", "tracks": tracks}


def _timing_track(
    identifier: str,
    dataset: str,
    *,
    bar_starts: list[float] | None,
    status: str = "explicit",
    prefix: float | None = None,
) -> dict[str, object]:
    track: dict[str, object] = {
        "id": identifier,
        "datasetId": dataset,
        "timingProvenance": {"barStartsSeconds": {"status": status}},
    }
    if bar_starts is not None:
        track["barStartsSeconds"] = bar_starts
    if prefix is not None:
        track["gridStartSeconds"] = prefix
        track["prefixExcludedSeconds"] = prefix
    return track


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_groups_never_leak_and_feasible_datasets_reach_every_partition() -> None:
    tracks = [
        _track("a-one", "a", "one"),
        _track("a-one-alt", "a", "one"),
        _track("a-two", "a", "two"),
        _track("a-three", "a", "three"),
        _track("a-four", "a", "four"),
        _track("b-one", "b", "one"),
        _track("b-two", "b", "two"),
        _track("b-three", "b", "three"),
    ]

    output = build_leak_resistant_split_manifest(_manifest(tracks), seed="fixture-seed")

    split_by_group: dict[str, set[str]] = {}
    for track in output["tracks"]:
        split_by_group.setdefault(track["splitProtocolGroup"], set()).add(track["split"])
        assert track["path"] == f"/features/{track['id']}.npz"
        assert track["provenance"]["row"] == track["id"]
    assert all(len(splits) == 1 for splits in split_by_group.values())
    assert next(track for track in output["tracks"] if track["id"] == "a-one")["split"] == next(
        track for track in output["tracks"] if track["id"] == "a-one-alt"
    )["split"]
    report = output["splitProtocol"]["datasetRepresentation"]
    assert report["a"]["representedPartitions"] == list(PARTITIONS)
    assert report["b"]["representedPartitions"] == list(PARTITIONS)


def test_explicit_identity_can_hold_cross_dataset_tracks_together() -> None:
    source = _manifest(
        [
            _track("a-performance", "a", "local-a"),
            _track("b-performance", "b", "local-b"),
            _track("a-two", "a", "two"),
            _track("b-two", "b", "two"),
            _track("a-three", "a", "three"),
            _track("b-three", "b", "three"),
        ]
    )
    output = build_leak_resistant_split_manifest(
        source,
        explicit_group_identities={
            "a-performance": "same-composition",
            "b-performance": "same-composition",
        },
    )
    selected = {
        track["split"]
        for track in output["tracks"]
        if track["id"] in {"a-performance", "b-performance"}
    }
    assert len(selected) == 1


def test_partition_is_deterministic_even_when_source_track_order_changes() -> None:
    tracks = [
        _track(f"track-{index}", "set", f"song-{index}")
        for index in range(12)
    ]
    forward = build_leak_resistant_split_manifest(_manifest(tracks), seed="stable")
    reverse = build_leak_resistant_split_manifest(_manifest(list(reversed(tracks))), seed="stable")

    assert {
        track["id"]: track["split"] for track in forward["tracks"]
    } == {track["id"]: track["split"] for track in reverse["tracks"]}
    assert forward == reverse
    assert source_manifest_sha256(_manifest(tracks)) == source_manifest_sha256(
        _manifest(list(reversed(tracks)))
    )


def test_large_single_dataset_tracks_follow_requested_ratio_instead_of_inverting_it() -> None:
    source = _manifest(
        [_track(f"track-{index}", "set", f"song-{index}") for index in range(100)]
    )

    output = build_leak_resistant_split_manifest(source, ratios=(70, 15, 15))
    counts = {
        partition: sum(track["split"] == partition for track in output["tracks"])
        for partition in PARTITIONS
    }

    assert 65 <= counts["train"] <= 75
    assert 10 <= counts["development"] <= 20
    assert 10 <= counts["calibration"] <= 20


@pytest.mark.parametrize(
    ("group_count", "expected"),
    [
        (1, {"train"}),
        (2, {"train", "development"}),
        (3, set(PARTITIONS)),
    ],
)
def test_small_datasets_use_only_feasible_partitions(
    group_count: int,
    expected: set[str],
) -> None:
    source = _manifest(
        [_track(f"track-{index}", "tiny", f"song-{index}") for index in range(group_count)]
    )
    output = build_leak_resistant_split_manifest(source)

    assert {track["split"] for track in output["tracks"]} == expected
    report = output["splitProtocol"]["datasetRepresentation"]["tiny"]
    assert report["allPartitionsFeasible"] is (group_count >= 3)
    validate_split_protocol_manifest(output, source_manifest=source)


def test_held_out_source_tracks_are_rejected_unless_explicitly_excluded() -> None:
    source = _manifest(
        [
            _track("train", "set", "train"),
            _track("development", "set", "development", split="development"),
            _track("test", "set", "test", split="test"),
            _track("steel", "set", "steel", split="steel_test"),
        ]
    )
    with pytest.raises(ValueError, match="explicitly exclude"):
        build_leak_resistant_split_manifest(source)
    with pytest.raises(ValueError, match="explicitly exclude"):
        build_leak_resistant_split_manifest(
            source,
            excluded_source_splits=("development", "test"),
        )

    output = build_leak_resistant_split_manifest(
        source,
        excluded_source_splits=("development", "test", "steel_test"),
    )
    assert [track["id"] for track in output["tracks"]] == ["train"]
    assert output["splitProtocol"]["excludedTrackCount"] == 3
    assert output["splitProtocol"]["excludedTrackCountBySourceSplit"] == {
        "development": 1,
        "steel_test": 1,
        "test": 1,
    }


def test_calibration_is_dedicated_zero_weight_and_hash_locked() -> None:
    source = _manifest(
        [_track(f"track-{index}", "set", f"song-{index}") for index in range(8)]
    )
    output = build_leak_resistant_split_manifest(source)
    calibration = [track for track in output["tracks"] if track["split"] == "calibration"]
    assert calibration
    assert all(track["trainingWeight"] == 0.0 for track in calibration)
    assert all(track["sourceTrainingWeight"] == 1.0 for track in calibration)
    assert all(track["calibrationPurpose"] == CALIBRATION_PURPOSE for track in calibration)
    assert all(track["calibrationImmutable"] is True for track in calibration)
    assert output["splitProtocol"]["calibration"]["setSha256"] == output["splitProtocol"][
        "partitions"
    ]["calibration"]["tracksSha256"]
    bar_eligibility = output["splitProtocol"]["calibration"]["barEligibility"]
    assert bar_eligibility["status"] == "unavailable"
    assert bar_eligibility["tracks"] == []
    assert set(bar_eligibility["excludedIds"]) == {
        track["id"] for track in calibration
    }


def test_hashes_detect_track_and_source_manifest_tampering() -> None:
    source = _manifest(
        [_track(f"track-{index}", "set", f"song-{index}") for index in range(5)]
    )
    output = build_leak_resistant_split_manifest(source)
    assert output["splitProtocol"]["outputManifestSha256"] == output_manifest_sha256(output)

    tampered = deepcopy(output)
    tampered["tracks"][0]["path"] = "/features/replaced.npz"
    with pytest.raises(ValueError, match="hash mismatch"):
        validate_split_protocol_manifest(tampered, source_manifest=source)

    changed_source = deepcopy(source)
    changed_source["tracks"][0]["provenance"]["row"] = "changed"
    with pytest.raises(ValueError, match="Source manifest hash mismatch"):
        validate_split_protocol_manifest(output, source_manifest=changed_source)


def test_manifest_remains_compatible_with_factorized_train_and_cache_selection() -> None:
    source = _manifest(
        [_track(f"track-{index}", "set", f"song-{index}") for index in range(7)]
    )
    output = build_leak_resistant_split_manifest(source)

    assert output["schemaVersion"] == FACTORIZED_LABEL_SCHEMA
    assert any(track["split"] == "train" for track in output["tracks"])
    assert any(track["split"] == "development" for track in output["tracks"])
    assert any(track["split"] == "calibration" for track in output["tracks"])
    assert all("path" in track and "factorizedLabelsPath" in track for track in output["tracks"])


def test_freezes_only_explicit_bar_eligible_calibration_tracks() -> None:
    source_tracks = [
        *[_track(f"aam-{index}", "aam", f"aam-song-{index}") for index in range(6)],
        *[
            _track(f"winter-{index}", "winterreise", f"winter-song-{index}")
            for index in range(6)
        ],
    ]
    source = _manifest(source_tracks)
    legacy = build_leak_resistant_split_manifest(source, seed="bar-freeze")
    calibration = {
        track["id"]: track
        for track in legacy["tracks"]
        if track["split"] == "calibration"
    }
    timing = _timing_manifest(
        [
            *[
                _timing_track(
                    f"aam-{index}",
                    "aam",
                    bar_starts=[0.0, 2.18, 4.91],
                )
                for index in range(6)
            ],
            *[
                {
                    "id": f"winter-{index}",
                    "datasetId": "winterreise",
                    "tempo": 96,
                    "meter": "4/4",
                }
                for index in range(6)
            ],
        ]
    )

    output = build_leak_resistant_split_manifest(
        source,
        seed="bar-freeze",
        timing_manifests=[timing],
    )
    bar_eligibility = output["splitProtocol"]["calibration"]["barEligibility"]
    expected = [
        {"id": identifier, "datasetId": "aam", "split": "calibration"}
        for identifier, track in sorted(calibration.items())
        if track["datasetId"] == "aam"
    ]
    assert bar_eligibility["status"] == "frozen"
    assert bar_eligibility["tracks"] == expected
    assert bar_eligibility["count"] == len(expected)
    assert bar_eligibility["setSha256"] == _canonical_sha256(expected)
    assert set(bar_eligibility["excludedIds"]) == {
        identifier
        for identifier, track in calibration.items()
        if track["datasetId"] == "winterreise"
    }
    assert all(
        bar_eligibility["excludedReasons"][identifier] == "missing timingProvenance"
        for identifier in bar_eligibility["excludedIds"]
    )
    assert all(set(descriptor) == {"id", "datasetId", "split"} for descriptor in expected)


def test_explicit_positive_grid_start_requires_matching_disclosed_prefix() -> None:
    source = _manifest(
        [_track(f"idmt-{index}", "idmt_guitar", f"song-{index}") for index in range(6)]
    )
    timing = _timing_manifest(
        [
            _timing_track(
                f"idmt-{index}",
                "idmt_guitar",
                bar_starts=[8.0, 10.0, 12.0],
                prefix=8.0,
            )
            for index in range(6)
        ]
    )

    output = build_leak_resistant_split_manifest(source, timing_manifests=[timing])
    bar_eligibility = output["splitProtocol"]["calibration"]["barEligibility"]
    assert bar_eligibility["tracks"]
    assert bar_eligibility["excludedIds"] == []

    without_prefix = deepcopy(timing)
    for track in without_prefix["tracks"]:
        track.pop("gridStartSeconds")
        track.pop("prefixExcludedSeconds")
    excluded = build_leak_resistant_split_manifest(source, timing_manifests=[without_prefix])
    excluded_bar = excluded["splitProtocol"]["calibration"]["barEligibility"]
    assert excluded_bar["tracks"] == []
    assert all(
        "prefixExcludedSeconds" in reason
        for reason in excluded_bar["excludedReasons"].values()
    )


def test_tempo_meter_or_inferred_provenance_never_admits_a_bar_track() -> None:
    source = _manifest(
        [_track(f"track-{index}", "set", f"song-{index}") for index in range(6)]
    )
    timing = _timing_manifest(
        [
            {
                **_timing_track(
                    f"track-{index}",
                    "set",
                    bar_starts=[0.0, 2.0],
                    status="inferred",
                ),
                "tempo": 120,
                "meter": "4/4",
            }
            for index in range(6)
        ]
    )

    output = build_leak_resistant_split_manifest(source, timing_manifests=[timing])
    bar_eligibility = output["splitProtocol"]["calibration"]["barEligibility"]
    assert bar_eligibility["tracks"] == []
    assert all(
        reason == "bar timing is not source-explicit"
        for reason in bar_eligibility["excludedReasons"].values()
    )


def test_timing_manifest_and_bar_set_are_order_invariant() -> None:
    source = _manifest(
        [
            *[_track(f"a-{index}", "a", f"song-a-{index}") for index in range(5)],
            *[_track(f"b-{index}", "b", f"song-b-{index}") for index in range(5)],
        ]
    )
    a_tracks = [
        _timing_track(f"a-{index}", "a", bar_starts=[0.0, 1.91, 4.02])
        for index in range(5)
    ]
    b_tracks = [
        _timing_track(f"b-{index}", "b", bar_starts=[0.0, 2.0, 4.0])
        for index in range(5)
    ]
    forward = build_leak_resistant_split_manifest(
        source,
        seed="timing-order",
        timing_manifests=[_timing_manifest(a_tracks), _timing_manifest(b_tracks)],
    )
    reverse = build_leak_resistant_split_manifest(
        source,
        seed="timing-order",
        timing_manifests=[
            _timing_manifest(list(reversed(b_tracks))),
            _timing_manifest(list(reversed(a_tracks))),
        ],
    )

    assert forward == reverse


def test_bar_eligibility_and_timing_hash_tampering_fail_closed() -> None:
    source = _manifest(
        [_track(f"track-{index}", "set", f"song-{index}") for index in range(6)]
    )
    timing = _timing_manifest(
        [
            _timing_track(f"track-{index}", "set", bar_starts=[0.0, 2.0, 4.0])
            for index in range(6)
        ]
    )
    output = build_leak_resistant_split_manifest(source, timing_manifests=[timing])

    tampered = deepcopy(output)
    bar_eligibility = tampered["splitProtocol"]["calibration"]["barEligibility"]
    bar_eligibility["count"] += 1
    tampered["splitProtocol"]["outputManifestSha256"] = output_manifest_sha256(tampered)
    with pytest.raises(ValueError, match="count mismatch"):
        validate_split_protocol_manifest(tampered, source_manifest=source)

    changed_timing = deepcopy(timing)
    changed_timing["tracks"][0]["barStartsSeconds"][1] = 2.25
    with pytest.raises(ValueError, match="supplied timing manifests"):
        validate_split_protocol_manifest(
            output,
            source_manifest=source,
            timing_manifests=[changed_timing],
        )
