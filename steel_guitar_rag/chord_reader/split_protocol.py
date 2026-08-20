"""Leak-resistant train, tuning, and confidence-calibration partitions.

This module deliberately operates only on manifest metadata.  It never opens
audio, references, feature arrays, or label sidecars.  A source track is
eligible only when its *original* split is ``train``; callers must explicitly
name every held-out source split they want ignored.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence


SPLIT_PROTOCOL_SCHEMA = "chord_reader_split_protocol_v1"
FACTORIZED_LABEL_SCHEMA = "chord_factorized_label_cache_v2"
PARTITIONS = ("train", "development", "calibration")
EXCLUDABLE_SOURCE_SPLITS = frozenset({"development", "test", "steel_test"})
CALIBRATION_PURPOSE = "bar_confidence_operating_point_only"
BAR_ELIGIBILITY_SCHEMA = "chord_calibration_bar_eligibility_v1"
BAR_ELIGIBILITY_POLICY = "explicit_native_bar_starts_only_v1"
DEFAULT_SEED = "chord-reader-v9-bar-calibration-1"
DEFAULT_RATIOS = (70, 15, 15)


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("Split manifests must contain canonical JSON values.") from exc


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _semantic_source_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize irrelevant track ordering before hashing a source manifest."""

    value = deepcopy(dict(manifest))
    tracks = value.get("tracks")
    if isinstance(tracks, list):
        value["tracks"] = sorted(
            tracks,
            key=lambda item: (
                str(item.get("datasetId", "")),
                str(item.get("id", "")),
                _canonical_json(item),
            ),
        )
    return value


def source_manifest_sha256(manifest: Mapping[str, Any]) -> str:
    """Return a stable semantic digest for a source cache manifest."""

    return _sha256_json(_semantic_source_manifest(manifest))


def _unsigned_output_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(manifest))
    protocol = value.get("splitProtocol")
    if isinstance(protocol, dict):
        protocol.pop("outputManifestSha256", None)
    return value


def output_manifest_sha256(manifest: Mapping[str, Any]) -> str:
    """Digest the complete derived manifest except its own digest field."""

    return _sha256_json(_unsigned_output_manifest(manifest))


def _normalized_ratios(ratios: Sequence[int]) -> tuple[int, int, int]:
    if len(ratios) != len(PARTITIONS):
        raise ValueError("Split ratios must provide train, development, and calibration values.")
    values = tuple(int(value) for value in ratios)
    if any(value <= 0 for value in values):
        raise ValueError("Split ratios must be positive integers.")
    return values  # type: ignore[return-value]


def _identity(
    track: Mapping[str, Any],
    explicit_group_identities: Mapping[str, str],
) -> str:
    identifier = str(track.get("id", "")).strip()
    explicit = str(explicit_group_identities.get(identifier, "")).strip()
    if not explicit:
        explicit = str(track.get("groupIdentity", "")).strip()
    if explicit:
        return f"explicit:{explicit}"

    dataset_id = str(track.get("datasetId", "")).strip()
    composition_id = str(track.get("compositionId", "")).strip()
    if composition_id:
        return f"composition:{dataset_id}:{composition_id}"

    # A previously frozen splitGroup is an explicit leakage identity.  It is
    # intentionally not combined with datasetId: an explicitly shared group
    # remains shared even when it spans source collections.
    split_group = str(track.get("splitGroup", "")).strip()
    if split_group:
        return f"explicit:{split_group}"
    raise ValueError(
        f"Track {identifier!r} needs compositionId or an explicit group identity."
    )


def _seeded_value(seed: str, *parts: str) -> int:
    payload = ":".join((seed, *parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def _assign_groups(
    groups: Mapping[str, Mapping[str, Any]],
    *,
    seed: str,
    ratios: tuple[int, int, int],
) -> dict[str, str]:
    """Assign whole groups while retaining dataset coverage whenever possible."""

    keys = sorted(groups, key=lambda key: (_seeded_value(seed, "group", key), key))
    assignments: dict[str, str] = {}

    dataset_groups: dict[str, list[str]] = defaultdict(list)
    for key, group in groups.items():
        for dataset_id in group["datasets"]:
            dataset_groups[str(dataset_id)].append(key)

    # A dataset with at least three independent groups can be represented in
    # every partition.  Fill those roles before global seeding, preferring
    # dataset-exclusive groups so a shared identity remains available to the
    # other datasets that depend on it.
    for dataset_id in sorted(dataset_groups):
        candidates = sorted(
            dataset_groups[dataset_id],
            key=lambda key: (_seeded_value(seed, "dataset", dataset_id, key), key),
        )
        if len(candidates) < len(PARTITIONS):
            continue
        represented = {assignments[key] for key in candidates if key in assignments}
        for partition in PARTITIONS:
            if partition in represented:
                continue
            available = [key for key in candidates if key not in assignments]
            if not available:
                # This can only arise with an explicitly shared cross-dataset
                # group.  The report will disclose that coverage was infeasible
                # under the global no-leakage constraint.
                break
            chosen = min(
                available,
                key=lambda key: (
                    len(groups[key]["datasets"]),
                    _seeded_value(seed, "coverage", dataset_id, partition, key),
                    key,
                ),
            )
            assignments[chosen] = partition
            represented.add(partition)

    # With one or two total groups, train and development take precedence
    # because the model trainer requires both.  Three or more groups freeze all
    # three roles, including a dedicated calibration partition.
    represented_global = set(assignments.values())
    for partition in PARTITIONS:
        if partition in represented_global:
            continue
        available = [key for key in keys if key not in assignments]
        if not available:
            break
        chosen = min(
            available,
            key=lambda key: (_seeded_value(seed, "global", partition, key), key),
        )
        assignments[chosen] = partition
        represented_global.add(partition)

    ratio_total = sum(ratios)
    ratio_by_partition = dict(zip(PARTITIONS, ratios))
    target_global = {
        partition: len(groups) * ratio_by_partition[partition] / ratio_total
        for partition in PARTITIONS
    }
    target_dataset = {
        dataset_id: {
            partition: len(keys_for_dataset) * ratio_by_partition[partition] / ratio_total
            for partition in PARTITIONS
        }
        for dataset_id, keys_for_dataset in dataset_groups.items()
    }

    global_counts = {partition: 0 for partition in PARTITIONS}
    dataset_counts = {
        dataset_id: {partition: 0 for partition in PARTITIONS}
        for dataset_id in dataset_groups
    }
    for key, partition in assignments.items():
        global_counts[partition] += 1
        for dataset_id in groups[key]["datasets"]:
            dataset_counts[str(dataset_id)][partition] += 1

    for key in keys:
        if key in assignments:
            continue
        datasets = tuple(str(value) for value in groups[key]["datasets"])

        def cost(partition: str) -> tuple[float, int, int]:
            global_target = max(1.0, target_global[partition])
            current_global_error = (
                global_counts[partition] - target_global[partition]
            ) ** 2 / global_target
            next_global_error = (
                global_counts[partition] + 1 - target_global[partition]
            ) ** 2 / global_target
            # Compare the *change* in squared error. Comparing absolute error
            # would perversely avoid the largest partition because its target
            # starts farthest from zero.
            score = next_global_error - current_global_error
            for dataset_id in datasets:
                dataset_target = max(1.0, target_dataset[dataset_id][partition])
                current_dataset_error = (
                    dataset_counts[dataset_id][partition]
                    - target_dataset[dataset_id][partition]
                ) ** 2 / dataset_target
                next_dataset_error = (
                    dataset_counts[dataset_id][partition]
                    + 1
                    - target_dataset[dataset_id][partition]
                ) ** 2 / dataset_target
                score += 2.0 * (next_dataset_error - current_dataset_error)
            return (
                score,
                _seeded_value(seed, "tie", key, partition),
                PARTITIONS.index(partition),
            )

        chosen = min(PARTITIONS, key=cost)
        assignments[key] = chosen
        global_counts[chosen] += 1
        for dataset_id in datasets:
            dataset_counts[dataset_id][chosen] += 1
    return assignments


def _partition_summaries(tracks: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    values = [dict(track) for track in tracks]
    summaries: dict[str, Any] = {}
    for partition in PARTITIONS:
        selected = sorted(
            (track for track in values if track.get("split") == partition),
            key=lambda track: (str(track.get("datasetId", "")), str(track.get("id", ""))),
        )
        datasets: dict[str, Any] = {}
        for dataset_id in sorted({str(track["datasetId"]) for track in selected}):
            dataset_tracks = [track for track in selected if str(track["datasetId"]) == dataset_id]
            datasets[dataset_id] = {
                "trackCount": len(dataset_tracks),
                "groupCount": len(
                    {str(track["splitProtocolGroup"]) for track in dataset_tracks}
                ),
            }
        summaries[partition] = {
            "trackCount": len(selected),
            "groupCount": len({str(track["splitProtocolGroup"]) for track in selected}),
            "tracksSha256": _sha256_json(selected),
            "datasets": datasets,
        }
    return summaries


def _representation_report(tracks: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    values = list(tracks)
    datasets = sorted({str(track["datasetId"]) for track in values})
    output: dict[str, Any] = {}
    for dataset_id in datasets:
        selected = [track for track in values if str(track["datasetId"]) == dataset_id]
        group_count = len({str(track["splitProtocolGroup"]) for track in selected})
        represented = [
            partition
            for partition in PARTITIONS
            if any(track.get("split") == partition for track in selected)
        ]
        output[dataset_id] = {
            "groupCount": group_count,
            "allPartitionsFeasible": group_count >= len(PARTITIONS),
            "representedPartitions": represented,
            "allFeasiblePartitionsRepresented": (
                group_count < len(PARTITIONS) or len(represented) == len(PARTITIONS)
            ),
        }
    return output


def _timing_manifest_values(
    timing_manifests: Iterable[Mapping[str, Any]] | None,
) -> list[Mapping[str, Any]] | None:
    if timing_manifests is None:
        return None
    values = list(timing_manifests)
    for manifest in values:
        if not isinstance(manifest, Mapping) or not isinstance(manifest.get("tracks"), list):
            raise ValueError("Every timing manifest must contain a tracks list.")
    return values


def _timing_index(
    timing_manifests: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Mapping[str, Any]], list[str]]:
    tracks: dict[str, Mapping[str, Any]] = {}
    hashes: list[str] = []
    for manifest in timing_manifests:
        hashes.append(source_manifest_sha256(manifest))
        for track in manifest.get("tracks", []):
            identifier = str(track.get("id", "")).strip()
            if not identifier or identifier in tracks:
                raise ValueError("Timing-manifest track ids must be non-empty and unique.")
            tracks[identifier] = track
    return tracks, sorted(hashes)


def _bar_timing_exclusion(track: Mapping[str, Any]) -> str | None:
    provenance = track.get("timingProvenance")
    if not isinstance(provenance, Mapping):
        return "missing timingProvenance"
    bar_provenance = provenance.get("barStartsSeconds")
    if not isinstance(bar_provenance, Mapping) or bar_provenance.get("status") != "explicit":
        return "bar timing is not source-explicit"
    starts = track.get("barStartsSeconds")
    if not isinstance(starts, Sequence) or isinstance(starts, (str, bytes)) or not starts:
        return "barStartsSeconds is missing or empty"
    normalized: list[float] = []
    for value in starts:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "barStartsSeconds contains a non-numeric value"
        number = float(value)
        if not math.isfinite(number) or number < 0:
            return "barStartsSeconds contains an invalid value"
        normalized.append(number)
    if any(right <= left for left, right in zip(normalized, normalized[1:])):
        return "barStartsSeconds is not strictly increasing"
    first = normalized[0]
    if first == 0:
        return None
    prefix = track.get(
        "prefixExcludedSeconds",
        bar_provenance.get("prefixExcludedSeconds"),
    )
    if (
        isinstance(prefix, bool)
        or not isinstance(prefix, (int, float))
        or not math.isfinite(float(prefix))
        or float(prefix) != first
    ):
        return "positive grid start lacks an equal explicit prefixExcludedSeconds"
    grid_start = track.get(
        "gridStartSeconds",
        bar_provenance.get("gridStartSeconds"),
    )
    if (
        isinstance(grid_start, bool)
        or not isinstance(grid_start, (int, float))
        or float(grid_start) != first
    ):
        return "positive grid start lacks an equal gridStartSeconds"
    return None


def _bar_eligibility(
    tracks: Sequence[Mapping[str, Any]],
    timing_manifests: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    calibration_tracks = sorted(
        (track for track in tracks if track.get("split") == "calibration"),
        key=lambda track: str(track.get("id", "")),
    )
    timing_hashes: list[str] = []
    timing_by_id: dict[str, Mapping[str, Any]] = {}
    status = "unavailable" if timing_manifests is None else "frozen"
    if timing_manifests is not None:
        timing_by_id, timing_hashes = _timing_index(timing_manifests)

    descriptors: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    for track in calibration_tracks:
        identifier = str(track["id"])
        dataset_id = str(track["datasetId"])
        timing = timing_by_id.get(identifier)
        if timing_manifests is None:
            reason = "timing manifests were not supplied"
        elif timing is None:
            reason = "track is absent from supplied timing manifests"
        elif str(timing.get("datasetId", "")) != dataset_id:
            raise ValueError(f"Timing metadata for {identifier!r} has a different datasetId.")
        else:
            reason = _bar_timing_exclusion(timing)
        if reason is None:
            descriptors.append(
                {"id": identifier, "datasetId": dataset_id, "split": "calibration"}
            )
        else:
            excluded.append({"id": identifier, "reason": reason})
    descriptors.sort(key=lambda item: item["id"])
    excluded.sort(key=lambda item: item["id"])
    excluded_ids = [item["id"] for item in excluded]
    excluded_reasons = {item["id"]: item["reason"] for item in excluded}
    return {
        "schemaVersion": BAR_ELIGIBILITY_SCHEMA,
        "policy": BAR_ELIGIBILITY_POLICY,
        "status": status,
        "tracks": descriptors,
        "count": len(descriptors),
        "setSha256": _sha256_json(descriptors),
        "excludedIds": excluded_ids,
        "excludedReasons": excluded_reasons,
        "excludedSha256": _sha256_json(excluded),
        "timingManifestCount": len(timing_hashes),
        "timingManifestSemanticSha256": timing_hashes,
        "timingManifestSetSha256": _sha256_json(timing_hashes),
    }


def _validate_bar_eligibility(
    value: Any,
    tracks: Sequence[Mapping[str, Any]],
    timing_manifests: Sequence[Mapping[str, Any]] | None,
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("Calibration bar-eligibility metadata is missing.")
    if value.get("schemaVersion") != BAR_ELIGIBILITY_SCHEMA:
        raise ValueError(f"Calibration bar eligibility must use {BAR_ELIGIBILITY_SCHEMA}.")
    if value.get("policy") != BAR_ELIGIBILITY_POLICY:
        raise ValueError("Calibration bar-eligibility policy was changed.")
    status = value.get("status")
    if status not in {"frozen", "unavailable"}:
        raise ValueError("Calibration bar eligibility has an invalid status.")

    descriptors = value.get("tracks")
    if not isinstance(descriptors, list):
        raise ValueError("Calibration bar-eligible tracks must be a list.")
    normalized: list[dict[str, str]] = []
    calibration_by_id = {
        str(track["id"]): track for track in tracks if track.get("split") == "calibration"
    }
    eligible_ids: set[str] = set()
    for descriptor in descriptors:
        if not isinstance(descriptor, Mapping) or set(descriptor) != {"id", "datasetId", "split"}:
            raise ValueError("Bar-eligible descriptors may contain only id, datasetId, and split.")
        item = {key: str(descriptor[key]) for key in ("id", "datasetId", "split")}
        identifier = item["id"]
        calibration_track = calibration_by_id.get(identifier)
        if (
            not identifier
            or identifier in eligible_ids
            or item["split"] != "calibration"
            or calibration_track is None
            or str(calibration_track["datasetId"]) != item["datasetId"]
        ):
            raise ValueError("Bar-eligible descriptor does not identify one calibration track.")
        eligible_ids.add(identifier)
        normalized.append(item)
    expected_order = sorted(normalized, key=lambda item: item["id"])
    if normalized != expected_order:
        raise ValueError("Bar-eligible track descriptors are not in canonical order.")
    if int(value.get("count", -1)) != len(normalized):
        raise ValueError("Calibration bar-eligible track count mismatch.")
    if value.get("setSha256") != _sha256_json(normalized):
        raise ValueError("Calibration bar-eligible set hash mismatch.")

    excluded_ids = value.get("excludedIds")
    excluded_reasons = value.get("excludedReasons")
    if not isinstance(excluded_ids, list) or not isinstance(excluded_reasons, Mapping):
        raise ValueError("Calibration bar exclusions are missing.")
    if excluded_ids != sorted(set(str(identifier) for identifier in excluded_ids)):
        raise ValueError("Calibration bar-exclusion ids are not unique and sorted.")
    if set(excluded_ids) != set(calibration_by_id) - eligible_ids:
        raise ValueError("Calibration bar eligibility does not cover the exact calibration set.")
    reasons_by_id = {str(key): str(reason) for key, reason in excluded_reasons.items()}
    if len(reasons_by_id) != len(excluded_reasons) or set(reasons_by_id) != set(excluded_ids):
        raise ValueError("Calibration bar-exclusion reasons do not match excluded ids.")
    excluded = []
    for identifier in excluded_ids:
        reason = reasons_by_id[identifier].strip()
        if not reason:
            raise ValueError("Every calibration bar exclusion requires a reason.")
        excluded.append({"id": identifier, "reason": reason})
    if value.get("excludedSha256") != _sha256_json(excluded):
        raise ValueError("Calibration bar-exclusion hash mismatch.")

    timing_hashes = value.get("timingManifestSemanticSha256")
    if not isinstance(timing_hashes, list) or timing_hashes != sorted(timing_hashes):
        raise ValueError("Timing-manifest hashes must be a sorted list.")
    if any(
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        for digest in timing_hashes
    ):
        raise ValueError("Timing-manifest hashes must be lowercase SHA-256 values.")
    if int(value.get("timingManifestCount", -1)) != len(timing_hashes):
        raise ValueError("Timing-manifest count mismatch.")
    if value.get("timingManifestSetSha256") != _sha256_json(timing_hashes):
        raise ValueError("Timing-manifest set hash mismatch.")
    if status == "unavailable":
        if normalized or timing_hashes:
            raise ValueError("Unavailable bar eligibility cannot contain eligible tracks or timing hashes.")
        if any(
            reasons_by_id[identifier] != "timing manifests were not supplied"
            for identifier in excluded_ids
        ):
            raise ValueError("Unavailable bar eligibility has an invalid exclusion reason.")
    if timing_manifests is not None:
        expected = _bar_eligibility(tracks, timing_manifests)
        if dict(value) != expected:
            raise ValueError(
                "Calibration bar eligibility does not match the supplied timing manifests."
            )


def build_leak_resistant_split_manifest(
    source_manifest: Mapping[str, Any],
    *,
    seed: str = DEFAULT_SEED,
    ratios: Sequence[int] = DEFAULT_RATIOS,
    explicit_group_identities: Mapping[str, str] | None = None,
    excluded_source_splits: Iterable[str] = (),
    timing_manifests: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Repartition source-train groups into train, tuning, and calibration.

    ``excluded_source_splits`` is fail-closed by design.  For example, a
    source manifest containing development and test rows requires
    ``excluded_source_splits=("development", "test")``.  Those rows are
    counted and hashed but never copied into the derived manifest.
    """

    if source_manifest.get("schemaVersion") != FACTORIZED_LABEL_SCHEMA:
        raise ValueError(
            f"Split protocol requires a {FACTORIZED_LABEL_SCHEMA} source manifest."
        )
    source_tracks = source_manifest.get("tracks")
    if not isinstance(source_tracks, list):
        raise ValueError("Source manifest tracks must be a list.")
    ratio_values = _normalized_ratios(ratios)
    seed = str(seed).strip()
    if not seed:
        raise ValueError("Split seed must be non-empty.")
    timing_values = _timing_manifest_values(timing_manifests)
    requested_exclusions = frozenset(str(value) for value in excluded_source_splits)
    invalid_exclusions = requested_exclusions - EXCLUDABLE_SOURCE_SPLITS
    if invalid_exclusions:
        raise ValueError(
            "Only source development, test, and steel_test splits may be explicitly excluded."
        )

    explicit = {str(key): str(value) for key, value in (explicit_group_identities or {}).items()}
    source_ids: set[str] = set()
    eligible: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for source in source_tracks:
        track = dict(source)
        identifier = str(track.get("id", "")).strip()
        dataset_id = str(track.get("datasetId", "")).strip()
        if not identifier or identifier in source_ids:
            raise ValueError("Source track ids must be non-empty and unique.")
        if not dataset_id:
            raise ValueError(f"Source track {identifier!r} needs datasetId.")
        source_ids.add(identifier)
        split = str(track.get("split", "")).strip()
        if split == "train":
            eligible.append(track)
        elif split in requested_exclusions:
            excluded.append(track)
        else:
            raise ValueError(
                f"Source track {identifier!r} has non-train split {split!r}; "
                "explicitly exclude every held-out source split."
            )
    if not eligible:
        raise ValueError("Split protocol requires at least one original train track.")

    groups: dict[str, dict[str, Any]] = {}
    group_for_id: dict[str, str] = {}
    for track in eligible:
        key = _identity(track, explicit)
        identifier = str(track["id"])
        group_for_id[identifier] = key
        group = groups.setdefault(key, {"datasets": set(), "trackIds": []})
        group["datasets"].add(str(track["datasetId"]))
        group["trackIds"].append(identifier)
    assignments = _assign_groups(groups, seed=seed, ratios=ratio_values)

    output_tracks: list[dict[str, Any]] = []
    for source in eligible:
        identifier = str(source["id"])
        group = group_for_id[identifier]
        partition = assignments[group]
        track = dict(source)
        track["sourceSplit"] = "train"
        track["split"] = partition
        track["splitProtocolGroup"] = group
        track["splitProtocolSeed"] = seed
        if not str(track.get("splitGroup", "")).strip():
            track["splitGroup"] = group
        if partition == "calibration":
            track["sourceTrainingWeight"] = float(track.get("trainingWeight", 1.0))
            track["trainingWeight"] = 0.0
            track["calibrationPurpose"] = CALIBRATION_PURPOSE
            track["calibrationImmutable"] = True
        output_tracks.append(track)
    output_tracks.sort(key=lambda track: (str(track["datasetId"]), str(track["id"])))

    summaries = _partition_summaries(output_tracks)
    representation = _representation_report(output_tracks)
    excluded_by_split = {
        split: len([track for track in excluded if str(track.get("split")) == split])
        for split in sorted(requested_exclusions)
    }
    assignment_rows = [
        {"group": group, "partition": assignments[group]}
        for group in sorted(assignments)
    ]
    protocol = {
        "schemaVersion": SPLIT_PROTOCOL_SCHEMA,
        "seed": seed,
        "ratios": dict(zip(PARTITIONS, ratio_values)),
        "sourceManifestSha256": source_manifest_sha256(source_manifest),
        "sourceTrackCount": len(source_tracks),
        "eligibleOriginalTrainTrackCount": len(eligible),
        "eligibleOriginalTrainTracksSha256": _sha256_json(
            sorted(eligible, key=lambda track: (str(track["datasetId"]), str(track["id"])))
        ),
        "excludedSourceSplits": sorted(requested_exclusions),
        "excludedTrackCount": len(excluded),
        "excludedTrackCountBySourceSplit": excluded_by_split,
        "excludedTracksSha256": _sha256_json(
            sorted(excluded, key=lambda track: (str(track["datasetId"]), str(track["id"])))
        ),
        "grouping": "explicit identity, otherwise datasetId+compositionId",
        "groupCount": len(groups),
        "assignmentSha256": _sha256_json(assignment_rows),
        "partitionRoles": {
            "train": "model fitting only",
            "development": "model selection and tuning only",
            "calibration": CALIBRATION_PURPOSE,
        },
        "partitions": summaries,
        "datasetRepresentation": representation,
        "calibration": {
            "split": "calibration",
            "purpose": CALIBRATION_PURPOSE,
            "immutable": True,
            "setSha256": summaries["calibration"]["tracksSha256"],
            "allowedUse": "fit one bar-confidence operating point after model selection",
            "prohibitedUses": [
                "model training",
                "architecture selection",
                "hyperparameter tuning",
                "test or steel-test threshold retuning",
            ],
            "barEligibility": _bar_eligibility(output_tracks, timing_values),
        },
    }
    output = {
        **{key: deepcopy(value) for key, value in source_manifest.items() if key != "tracks"},
        "tracks": output_tracks,
        "splitProtocol": protocol,
    }
    protocol["outputManifestSha256"] = output_manifest_sha256(output)
    validate_split_protocol_manifest(
        output,
        source_manifest=source_manifest,
        timing_manifests=timing_values,
    )
    return output


def validate_split_protocol_manifest(
    manifest: Mapping[str, Any],
    *,
    source_manifest: Mapping[str, Any] | None = None,
    timing_manifests: Iterable[Mapping[str, Any]] | None = None,
) -> Mapping[str, Any]:
    """Validate partition isolation, locks, counts, and tamper-evident hashes."""

    timing_values = _timing_manifest_values(timing_manifests)
    if manifest.get("schemaVersion") != FACTORIZED_LABEL_SCHEMA:
        raise ValueError(f"Derived manifest must retain {FACTORIZED_LABEL_SCHEMA}.")
    protocol = manifest.get("splitProtocol")
    if not isinstance(protocol, Mapping) or protocol.get("schemaVersion") != SPLIT_PROTOCOL_SCHEMA:
        raise ValueError(f"Derived manifest needs {SPLIT_PROTOCOL_SCHEMA} metadata.")
    expected_output_hash = str(protocol.get("outputManifestSha256", ""))
    if expected_output_hash != output_manifest_sha256(manifest):
        raise ValueError("Derived manifest hash mismatch; the split artifact was modified.")

    tracks = manifest.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise ValueError("Derived split manifest must contain tracks.")
    ids: set[str] = set()
    partition_by_group: dict[str, str] = {}
    for track in tracks:
        identifier = str(track.get("id", "")).strip()
        if not identifier or identifier in ids:
            raise ValueError("Derived track ids must be non-empty and unique.")
        ids.add(identifier)
        partition = str(track.get("split", ""))
        if partition not in PARTITIONS:
            raise ValueError(f"Derived track {identifier!r} has invalid partition {partition!r}.")
        if track.get("sourceSplit") != "train":
            raise ValueError(f"Derived track {identifier!r} was not an original train track.")
        group = str(track.get("splitProtocolGroup", "")).strip()
        if not group:
            raise ValueError(f"Derived track {identifier!r} needs splitProtocolGroup.")
        prior = partition_by_group.setdefault(group, partition)
        if prior != partition:
            raise ValueError(
                f"Split leakage: group {group!r} appears in {prior!r} and {partition!r}."
            )
        if partition == "calibration":
            if track.get("calibrationPurpose") != CALIBRATION_PURPOSE:
                raise ValueError(f"Calibration track {identifier!r} has the wrong purpose.")
            if track.get("calibrationImmutable") is not True:
                raise ValueError(f"Calibration track {identifier!r} is not immutable.")
            if float(track.get("trainingWeight", 1.0)) != 0.0:
                raise ValueError(f"Calibration track {identifier!r} has non-zero training weight.")

    summaries = _partition_summaries(tracks)
    if protocol.get("partitions") != summaries:
        raise ValueError("Partition counts or hashes do not match the derived tracks.")
    representation = _representation_report(tracks)
    if protocol.get("datasetRepresentation") != representation:
        raise ValueError("Dataset representation report does not match the derived tracks.")
    if any(
        report["allPartitionsFeasible"] and not report["allFeasiblePartitionsRepresented"]
        for report in representation.values()
    ):
        raise ValueError("A feasible dataset is not represented in every partition.")
    calibration = protocol.get("calibration")
    if not isinstance(calibration, Mapping):
        raise ValueError("Calibration lock metadata is missing.")
    if (
        calibration.get("immutable") is not True
        or calibration.get("purpose") != CALIBRATION_PURPOSE
        or calibration.get("setSha256") != summaries["calibration"]["tracksSha256"]
    ):
        raise ValueError("Calibration lock metadata does not match the calibration set.")
    _validate_bar_eligibility(calibration.get("barEligibility"), tracks, timing_values)
    if protocol.get("partitionRoles") != {
        "train": "model fitting only",
        "development": "model selection and tuning only",
        "calibration": CALIBRATION_PURPOSE,
    }:
        raise ValueError("Partition roles are missing or have been repurposed.")

    assignments = [
        {"group": group, "partition": partition_by_group[group]}
        for group in sorted(partition_by_group)
    ]
    if protocol.get("assignmentSha256") != _sha256_json(assignments):
        raise ValueError("Group assignment hash does not match the derived tracks.")
    if int(protocol.get("groupCount", -1)) != len(partition_by_group):
        raise ValueError("Group count does not match the derived tracks.")

    if source_manifest is not None:
        source_hash = source_manifest_sha256(source_manifest)
        if protocol.get("sourceManifestSha256") != source_hash:
            raise ValueError("Source manifest hash mismatch.")
        sources = {str(track.get("id")): track for track in source_manifest.get("tracks", [])}
        exclusions = set(protocol.get("excludedSourceSplits", []))
        eligible_ids = {
            identifier
            for identifier, track in sources.items()
            if str(track.get("split")) == "train"
        }
        if ids != eligible_ids:
            raise ValueError("Derived tracks do not exactly match original train tracks.")
        for identifier in ids:
            source = sources[identifier]
            derived = next(track for track in tracks if str(track.get("id")) == identifier)
            for key, value in source.items():
                if key == "split":
                    continue
                if key == "trainingWeight" and derived.get("split") == "calibration":
                    if float(derived.get("sourceTrainingWeight", 1.0)) != float(value):
                        raise ValueError(
                            f"Calibration track {identifier!r} lost its source training weight."
                        )
                    continue
                if derived.get(key) != value:
                    raise ValueError(
                        f"Derived track {identifier!r} changed source field {key!r}."
                    )
        non_train = [
            track
            for track in source_manifest.get("tracks", [])
            if str(track.get("split")) != "train"
        ]
        if any(str(track.get("split")) not in exclusions for track in non_train):
            raise ValueError("A held-out source split was not explicitly excluded.")
        excluded_sorted = sorted(
            (dict(track) for track in non_train),
            key=lambda track: (str(track["datasetId"]), str(track["id"])),
        )
        if protocol.get("excludedTracksSha256") != _sha256_json(excluded_sorted):
            raise ValueError("Excluded source-track hash mismatch.")
        if int(protocol.get("excludedTrackCount", -1)) != len(non_train):
            raise ValueError("Excluded source-track count mismatch.")
    return manifest
