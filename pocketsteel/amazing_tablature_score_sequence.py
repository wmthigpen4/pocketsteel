"""Private discovery-only full-line score sequence challenger.

This module intentionally keeps PyTorch optional.  The application runtime can
import the Lane 20 workflow without installing a neural-network dependency;
training inserts an ignored private dependency directory only for the duration
of the command.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


SCORE_SEQUENCE_CHALLENGER_VERSION = "full-line-score-sequence-ctc-v3"
SCORE_SEQUENCE_CHALLENGER_SCHEMA_VERSION = (
    "amazing-tablature-full-line-score-sequence-challenger-v1"
)
BLANK_TOKEN = 0
GROUP_END_TOKEN = 1
PITCH_TOKEN_OFFSET = 2
MIN_PITCH = 36
MAX_PITCH = 96
VOCABULARY_SIZE = PITCH_TOKEN_OFFSET + MAX_PITCH - MIN_PITCH + 1


class ScoreSequenceTrainingError(RuntimeError):
    """Raised when private sequence training cannot satisfy its contract."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(dict(value), handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def encode_pitch_groups(groups: Sequence[Sequence[int]]) -> list[int]:
    """Encode simultaneous pitch groups as a CTC-safe token sequence."""

    encoded: list[int] = []
    for raw_group in groups:
        group = sorted(int(value) for value in raw_group)
        if not group:
            raise ScoreSequenceTrainingError("A score attack group cannot be empty.")
        for pitch in group:
            if not MIN_PITCH <= pitch <= MAX_PITCH:
                raise ScoreSequenceTrainingError(
                    f"Pitch {pitch} is outside the fixed {MIN_PITCH}-{MAX_PITCH} vocabulary."
                )
            encoded.append(PITCH_TOKEN_OFFSET + pitch - MIN_PITCH)
        encoded.append(GROUP_END_TOKEN)
    if not encoded:
        raise ScoreSequenceTrainingError("A score line cannot have an empty target.")
    return encoded


def decode_pitch_tokens(tokens: Sequence[int]) -> tuple[list[list[int]], bool]:
    """Decode tokens and report whether the sequence is structurally complete."""

    groups: list[list[int]] = []
    current: list[int] = []
    well_formed = True
    for raw_token in tokens:
        token = int(raw_token)
        if token == BLANK_TOKEN:
            continue
        if token == GROUP_END_TOKEN:
            if not current:
                well_formed = False
            else:
                groups.append(sorted(current))
                current = []
            continue
        pitch = MIN_PITCH + token - PITCH_TOKEN_OFFSET
        if not MIN_PITCH <= pitch <= MAX_PITCH:
            well_formed = False
            continue
        current.append(pitch)
    if current:
        well_formed = False
        groups.append(sorted(current))
    if not groups:
        well_formed = False
    return groups, well_formed


def collapse_ctc_path(path: Sequence[int]) -> list[int]:
    """Greedily collapse a CTC path without deleting separated repeats."""

    collapsed: list[int] = []
    previous: int | None = None
    for raw_token in path:
        token = int(raw_token)
        if token != previous and token != BLANK_TOKEN:
            collapsed.append(token)
        previous = token
    return collapsed


def _edit_distance(left: Sequence[int], right: Sequence[int]) -> int:
    prior = list(range(len(right) + 1))
    for left_index, left_value in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_value in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    prior[right_index] + 1,
                    prior[right_index - 1] + (left_value != right_value),
                )
            )
        prior = current
    return prior[-1]


def sequence_metrics(
    targets: Sequence[Sequence[Sequence[int]]],
    predictions: Sequence[Sequence[Sequence[int]]],
    *,
    well_formed: Sequence[bool] | None = None,
) -> dict[str, Any]:
    if len(targets) != len(predictions):
        raise ScoreSequenceTrainingError("Targets and predictions must have equal length.")
    completeness = list(well_formed or [True] * len(predictions))
    if len(completeness) != len(predictions):
        raise ScoreSequenceTrainingError("Prediction completeness length changed.")

    exact_lines = 0
    exact_attack_counts = 0
    exact_groups = 0
    total_groups = 0
    token_edits = 0
    token_total = 0
    for target, prediction in zip(targets, predictions, strict=True):
        normalized_target = [sorted(map(int, group)) for group in target]
        normalized_prediction = [sorted(map(int, group)) for group in prediction]
        exact_lines += normalized_target == normalized_prediction
        exact_attack_counts += len(normalized_target) == len(normalized_prediction)
        total_groups += len(normalized_target)
        exact_groups += sum(
            expected == observed
            for expected, observed in zip(
                normalized_target, normalized_prediction, strict=False
            )
        )
        target_tokens = encode_pitch_groups(normalized_target)
        prediction_tokens = (
            encode_pitch_groups(normalized_prediction) if normalized_prediction else []
        )
        token_edits += _edit_distance(target_tokens, prediction_tokens)
        token_total += len(target_tokens)
    return {
        "caseCount": len(targets),
        "sequenceExactLineCount": exact_lines,
        "sequenceExactLineRate": round(exact_lines / len(targets), 6) if targets else 0.0,
        "attackCountExactLineCount": exact_attack_counts,
        "attackCountExactLineRate": (
            round(exact_attack_counts / len(targets), 6) if targets else 0.0
        ),
        "exactAttackGroupCount": exact_groups,
        "attackGroupCount": total_groups,
        "exactAttackGroupRate": round(exact_groups / total_groups, 6) if total_groups else 0.0,
        "tokenEditCount": token_edits,
        "targetTokenCount": token_total,
        "tokenErrorRate": round(token_edits / token_total, 6) if token_total else 0.0,
        "wellFormedLineCount": sum(bool(value) for value in completeness),
        "blankLineCount": sum(not prediction for prediction in predictions),
    }


def grouped_development_split(
    cases: Sequence[Mapping[str, Any]], *, calibration_fraction: float = 0.22
) -> tuple[list[str], list[str]]:
    """Return deterministic content-unit grouped train/calibration case IDs."""

    if not 0.1 <= calibration_fraction <= 0.4:
        raise ScoreSequenceTrainingError("Calibration fraction must be between 0.1 and 0.4.")
    by_group: dict[str, list[str]] = defaultdict(list)
    for case in cases:
        group = str(case.get("contentUnitId") or "")
        case_id = str(case.get("caseId") or "")
        if not group or not case_id:
            raise ScoreSequenceTrainingError("Every development case needs stable IDs.")
        by_group[group].append(case_id)
    ranked = sorted(
        by_group,
        key=lambda value: hashlib.sha256(
            f"score-sequence-calibration-v1:{value}".encode("utf-8")
        ).hexdigest(),
    )
    target_count = max(1, round(len(cases) * calibration_fraction))
    calibration_groups: set[str] = set()
    calibration_count = 0
    for group in ranked:
        if calibration_count >= target_count and calibration_groups:
            break
        calibration_groups.add(group)
        calibration_count += len(by_group[group])
    training = sorted(
        case_id
        for group, case_ids in by_group.items()
        if group not in calibration_groups
        for case_id in case_ids
    )
    calibration = sorted(
        case_id
        for group, case_ids in by_group.items()
        if group in calibration_groups
        for case_id in case_ids
    )
    if not training or not calibration:
        raise ScoreSequenceTrainingError("Grouped development split is empty.")
    return training, calibration


def _target_groups(case: Mapping[str, Any]) -> list[list[int]]:
    return [
        [int(note["pitchValue"]) for note in group.get("notes") or []]
        for group in case.get("target") or []
    ]


def _baseline_groups(result: Mapping[str, Any]) -> list[list[int]]:
    events = list((result.get("prediction") or {}).get("scoreEvents") or [])
    grouped: dict[tuple[str, float], list[int]] = defaultdict(list)
    for event in events:
        if event.get("rest") or event.get("pitchValue") is None:
            continue
        constrained = event.get("sourceCountConstrainedGroup")
        if constrained is not None:
            key = ("group", float(constrained))
        else:
            key = ("x", round(float(event.get("defaultX") or 0.0), 2))
        grouped[key].append(int(event["pitchValue"]))
    return [sorted(grouped[key]) for key in sorted(grouped, key=lambda value: value[1])]


def _load_manifest(dataset_root: Path) -> tuple[Path, dict[str, Any]]:
    paths = sorted(dataset_root.glob("manifest-*.json"))
    if len(paths) != 1:
        raise ScoreSequenceTrainingError(
            "Exactly one immutable score-sequence manifest is required."
        )
    path = paths[0]
    manifest = json.loads(path.read_text(encoding="utf-8"))
    digest = str(manifest.get("manifestDigest") or "")
    core = {key: value for key, value in manifest.items() if key != "manifestDigest"}
    if digest != _sha256_json(core):
        raise ScoreSequenceTrainingError("The score-sequence manifest digest changed.")
    if manifest.get("partition") != "discovery":
        raise ScoreSequenceTrainingError("Sequence training is discovery-only.")
    if manifest.get("validationAccessed") or manifest.get("sealedTestAccessed"):
        raise ScoreSequenceTrainingError("Held-out access is forbidden for this trainer.")
    return path, manifest


def _load_semantic_baseline(
    automation_root: Path, benchmark_digest: str
) -> tuple[Path, dict[str, Any]]:
    candidates: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(
        (automation_root / "source-score-notehead-challenger").glob(
            "semantic-repair-*.json"
        )
    ):
        value = json.loads(path.read_text(encoding="utf-8"))
        if (
            value.get("repairVersion") == "source-score-semantic-repair-v2"
            and value.get("benchmarkManifestDigest") == benchmark_digest
        ):
            candidates.append((path, value))
    if len(candidates) != 1:
        raise ScoreSequenceTrainingError(
            "Exactly one current source-score semantic baseline is required."
        )
    path, baseline = candidates[0]
    digest = str(baseline.get("reportDigest") or "")
    core = {key: value for key, value in baseline.items() if key != "reportDigest"}
    if digest != _sha256_json(core):
        raise ScoreSequenceTrainingError("The semantic baseline digest changed.")
    return path, baseline


def _private_torch(dependency_root: Path) -> Any:
    dependency_root = dependency_root.expanduser().resolve()
    if not dependency_root.is_dir():
        raise ScoreSequenceTrainingError(
            f"Private trainer dependencies are missing at {dependency_root}."
        )
    sys.path.insert(0, str(dependency_root))
    try:
        import torch  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ScoreSequenceTrainingError(
            "Install PyTorch into the ignored private trainer dependency directory."
        ) from exc
    return torch


def _prepare_image(
    path: Path,
    *,
    height: int,
    augment: bool,
    rng: random.Random,
) -> np.ndarray:
    with Image.open(path) as opened:
        image = opened.convert("L")
    if augment:
        image = ImageEnhance.Contrast(image).enhance(rng.uniform(0.75, 1.3))
        image = ImageEnhance.Brightness(image).enhance(rng.uniform(0.85, 1.15))
        if rng.random() < 0.25:
            image = image.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.1, 0.65)))
        horizontal_scale = rng.uniform(0.9, 1.1)
    else:
        horizontal_scale = 1.0
    width = max(32, round(image.width * height / image.height * horizontal_scale))
    image = image.resize((width, height), Image.Resampling.BILINEAR)
    values = (255.0 - np.asarray(image, dtype=np.float32)) / 255.0
    if augment and rng.random() < 0.5:
        noise = np.random.default_rng(rng.randrange(2**32)).normal(
            0.0, rng.uniform(0.005, 0.025), values.shape
        )
        values = np.clip(values + noise, 0.0, 1.0)
    return values[None, :, :].astype(np.float32)


def _synthetic_score_image(
    case: Mapping[str, Any], *, height: int, rng: random.Random
) -> np.ndarray:
    """Render a rights-safe scan-style staff from approved pitch labels."""

    target = list(case.get("target") or [])
    spacing = rng.uniform(6.0, 9.0)
    horizontal_step = rng.uniform(28.0, 48.0)
    left_margin = rng.uniform(42.0, 70.0)
    right_margin = rng.uniform(20.0, 45.0)
    width = max(96, round(left_margin + len(target) * horizontal_step + right_margin))
    image = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(image)
    bottom_line = rng.uniform(height * 0.56, height * 0.69)
    ink = rng.randint(5, 45)
    line_width = rng.choice((1, 1, 1, 2))
    for line in range(5):
        y = round(bottom_line - line * spacing)
        draw.line((8, y, width - 8, y), fill=ink, width=line_width)

    # A compact clef/time-signature surrogate prevents the network from using
    # the first note as an absolute left-edge cue while keeping pitch learning
    # anchored to the staff itself.
    draw.text((12, round(bottom_line - spacing * 3.7)), "&", fill=ink)
    draw.text((29, round(bottom_line - spacing * 3.5)), "4", fill=ink)
    draw.text((29, round(bottom_line - spacing * 1.5)), "4", fill=ink)
    diatonic_step = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}
    e4_index = 4 * 7 + diatonic_step["E"]
    prior_measure = 0
    for attack_index, group in enumerate(target):
        x = left_margin + attack_index * horizontal_step + rng.uniform(-2.5, 2.5)
        if attack_index and attack_index % rng.choice((3, 4, 4, 5)) == 0:
            bar_x = round(x - horizontal_step * 0.45)
            draw.line(
                (
                    bar_x,
                    round(bottom_line - spacing * 4),
                    bar_x,
                    round(bottom_line),
                ),
                fill=ink,
                width=line_width,
            )
            prior_measure += 1
        ys: list[float] = []
        notes = list(group.get("notes") or [])
        for note in notes:
            step = str(note.get("pitchStep") or "C").upper()
            octave = int(note.get("octave") or 4)
            index = octave * 7 + diatonic_step.get(step, 0)
            y = bottom_line - (index - e4_index) * spacing / 2
            ys.append(y)
            radius_x = spacing * rng.uniform(0.44, 0.58)
            radius_y = spacing * rng.uniform(0.30, 0.39)
            draw.ellipse(
                (x - radius_x, y - radius_y, x + radius_x, y + radius_y),
                fill=ink,
            )
            if int(note.get("pitchAlter") or 0) > 0:
                draw.text((round(x - spacing * 1.65), round(y - spacing * 0.75)), "#", fill=ink)
            elif int(note.get("pitchAlter") or 0) < 0:
                draw.text((round(x - spacing * 1.4), round(y - spacing * 0.9)), "b", fill=ink)
            # Ledger lines are essential octave evidence outside the staff.
            ledger_y = bottom_line + spacing
            while y >= ledger_y - spacing * 0.3:
                draw.line(
                    (x - spacing * 0.9, round(ledger_y), x + spacing * 0.9, round(ledger_y)),
                    fill=ink,
                    width=line_width,
                )
                ledger_y += spacing
            ledger_y = bottom_line - spacing * 5
            while y <= ledger_y + spacing * 0.3:
                draw.line(
                    (x - spacing * 0.9, round(ledger_y), x + spacing * 0.9, round(ledger_y)),
                    fill=ink,
                    width=line_width,
                )
                ledger_y -= spacing
        if ys:
            if sum(ys) / len(ys) < bottom_line - spacing * 2:
                stem_y = max(ys)
                draw.line(
                    (round(x - spacing * 0.48), round(stem_y), round(x - spacing * 0.48), round(stem_y + spacing * 3)),
                    fill=ink,
                    width=max(1, line_width),
                )
            else:
                stem_y = min(ys)
                draw.line(
                    (round(x + spacing * 0.48), round(stem_y), round(x + spacing * 0.48), round(stem_y - spacing * 3)),
                    fill=ink,
                    width=max(1, line_width),
                )
    if rng.random() < 0.75:
        image = image.rotate(rng.uniform(-0.7, 0.7), resample=Image.Resampling.BILINEAR, fillcolor=255)
    if rng.random() < 0.5:
        image = image.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.15, 0.65)))
    values = (255.0 - np.asarray(image, dtype=np.float32)) / 255.0
    noise = np.random.default_rng(rng.randrange(2**32)).normal(
        0.0, rng.uniform(0.002, 0.025), values.shape
    )
    return np.clip(values + noise, 0.0, 1.0)[None, :, :].astype(np.float32)


def _torch_model(torch: Any, *, hidden_size: int) -> Any:
    nn = torch.nn

    class FullLineCTC(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(1, 32, 3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2),
                nn.Conv2d(32, 64, 3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2),
                nn.Conv2d(64, 128, 3, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(inplace=True),
                nn.MaxPool2d((2, 1), (2, 1)),
            )
            self.sequence = nn.GRU(
                128,
                hidden_size,
                num_layers=2,
                bidirectional=True,
                dropout=0.15,
            )
            self.classifier = nn.Linear(hidden_size * 2, VOCABULARY_SIZE)
            # CTC's blank class dominates an untrained long sequence.  A small
            # negative blank prior gives pitch/group tokens gradient signal
            # without encoding any musical answer into the model.
            with torch.no_grad():
                self.classifier.bias.zero_()
                self.classifier.bias[BLANK_TOKEN] = -1.5

        def forward(self, values: Any) -> Any:
            features = self.features(values)
            features = features.mean(dim=2).permute(2, 0, 1)
            sequence, _state = self.sequence(features)
            return self.classifier(sequence).log_softmax(dim=2)

    return FullLineCTC()


def _collate(torch: Any, samples: Sequence[tuple[np.ndarray, list[int]]]) -> tuple[Any, ...]:
    max_width = max(sample[0].shape[2] for sample in samples)
    height = samples[0][0].shape[1]
    images = torch.zeros((len(samples), 1, height, max_width), dtype=torch.float32)
    input_lengths: list[int] = []
    targets: list[int] = []
    target_lengths: list[int] = []
    for index, (image, target) in enumerate(samples):
        width = image.shape[2]
        images[index, :, :, :width] = torch.from_numpy(image)
        input_lengths.append(width // 4)
        targets.extend(target)
        target_lengths.append(len(target))
    return (
        images,
        torch.tensor(targets, dtype=torch.long),
        torch.tensor(input_lengths, dtype=torch.long),
        torch.tensor(target_lengths, dtype=torch.long),
    )


def _predict_cases(
    torch: Any,
    model: Any,
    cases: Sequence[Mapping[str, Any]],
    *,
    output_root: Path,
    image_height: int,
    batch_size: int,
) -> tuple[list[list[list[int]]], list[bool], list[dict[str, Any]]]:
    model.eval()
    predictions: list[list[list[int]]] = []
    completeness: list[bool] = []
    details: list[dict[str, Any]] = []
    with torch.no_grad():
        for offset in range(0, len(cases), batch_size):
            batch = cases[offset : offset + batch_size]
            samples = [
                (
                    _prepare_image(
                        output_root / str(case["image"]["relativePath"]),
                        height=image_height,
                        augment=False,
                        rng=random.Random(0),
                    ),
                    encode_pitch_groups(_target_groups(case)),
                )
                for case in batch
            ]
            images, _targets, input_lengths, _target_lengths = _collate(torch, samples)
            logits = model(images)
            paths = logits.argmax(dim=2).permute(1, 0)
            for case, path, length in zip(batch, paths, input_lengths, strict=True):
                collapsed = collapse_ctc_path(path[: int(length)].tolist())
                groups, well_formed = decode_pitch_tokens(collapsed)
                predictions.append(groups)
                completeness.append(well_formed)
                details.append(
                    {
                        "caseId": str(case["caseId"]),
                        "predictedAttackCount": len(groups),
                        "wellFormed": well_formed,
                        "prediction": groups,
                    }
                )
    return predictions, completeness, details


def _train_epoch(
    torch: Any,
    model: Any,
    optimizer: Any,
    cases: Sequence[Mapping[str, Any]],
    *,
    output_root: Path,
    image_height: int,
    batch_size: int,
    seed: int,
    synthetic_only: bool = False,
) -> float:
    model.train()
    order = list(range(len(cases)))
    rng = random.Random(seed)
    rng.shuffle(order)
    loss_function = torch.nn.CTCLoss(blank=BLANK_TOKEN, zero_infinity=True)
    losses: list[float] = []
    for offset in range(0, len(order), batch_size):
        batch = [cases[index] for index in order[offset : offset + batch_size]]
        samples = []
        for index, case in enumerate(batch):
            sample_rng = random.Random(seed * 1009 + index)
            image = (
                _synthetic_score_image(case, height=image_height, rng=sample_rng)
                if synthetic_only
                else _prepare_image(
                    output_root / str(case["image"]["relativePath"]),
                    height=image_height,
                    augment=True,
                    rng=sample_rng,
                )
            )
            samples.append((image, encode_pitch_groups(_target_groups(case))))
        images, targets, input_lengths, target_lengths = _collate(torch, samples)
        optimizer.zero_grad(set_to_none=True)
        logits = model(images)
        loss = loss_function(logits, targets, input_lengths, target_lengths)
        if not bool(torch.isfinite(loss)):
            raise ScoreSequenceTrainingError("CTC training produced a non-finite loss.")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()
        losses.append(float(loss.detach()))
    return sum(losses) / len(losses)


def train_discovery_score_sequence_challenger(
    *,
    output_root: Path,
    dependency_root: Path,
    seed: int = 1729,
    maximum_epochs: int = 80,
) -> dict[str, Any]:
    """Train on development, freeze, then score opened discovery shadow once."""

    output_root = output_root.expanduser().resolve()
    automation_root = output_root / "review" / "automation"
    dataset_root = automation_root / "reviewed-score-sequence-dataset-v1"
    manifest_path, manifest = _load_manifest(dataset_root)
    cases = list(manifest.get("cases") or [])
    development = [case for case in cases if case.get("subset") == "development"]
    shadow = [case for case in cases if case.get("subset") == "shadow"]
    if len(development) != 27 or len(shadow) != 12:
        raise ScoreSequenceTrainingError(
            "The frozen 27-development/12-shadow sequence contract changed."
        )
    for case in cases:
        image_path = output_root / str(case["image"]["relativePath"])
        if _sha256_file(image_path) != str(case["image"]["sha256"]):
            raise ScoreSequenceTrainingError("A digest-pinned score crop changed.")

    baseline_path, baseline = _load_semantic_baseline(
        automation_root, str(manifest["benchmarkManifestDigest"])
    )
    baseline_by_case = {
        str(result["caseId"]): result for result in baseline.get("results") or []
    }
    if set(baseline_by_case) != {str(case["caseId"]) for case in cases}:
        raise ScoreSequenceTrainingError("The baseline and sequence dataset differ.")

    torch = _private_torch(dependency_root)
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)

    config = {
        "version": SCORE_SEQUENCE_CHALLENGER_VERSION,
        "seed": seed,
        "imageHeight": 96,
        "hiddenSize": 128,
        "batchSize": 3,
        "maximumCalibrationEpochs": maximum_epochs,
        "learningRate": 0.001,
        "weightDecay": 0.0001,
        "syntheticPretrainingEpochs": 30,
        "syntheticRenderer": "scan-style-staff-from-approved-development-labels-v1",
        "patience": 25,
        "minimumEpochs": 25,
        "vocabulary": {
            "blankToken": BLANK_TOKEN,
            "groupEndToken": GROUP_END_TOKEN,
            "pitchTokenOffset": PITCH_TOKEN_OFFSET,
            "minimumPitch": MIN_PITCH,
            "maximumPitch": MAX_PITCH,
            "size": VOCABULARY_SIZE,
        },
        "targetScope": ["attack_order", "simultaneous_pitch_group", "scientific_pitch"],
        "excludedTargets": ["duration", "rhythm", "tie", "tablature", "source_text"],
        "device": "cpu",
    }
    train_ids, calibration_ids = grouped_development_split(development)
    train_set = [case for case in development if case["caseId"] in train_ids]
    calibration_set = [case for case in development if case["caseId"] in calibration_ids]

    model = _torch_model(torch, hidden_size=config["hiddenSize"])
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config["learningRate"],
        weight_decay=config["weightDecay"],
    )
    best_state: dict[str, Any] | None = None
    best_key: tuple[float, int, int] | None = None
    best_epoch = 0
    patience = 0
    calibration_history: list[dict[str, Any]] = []
    targets = [_target_groups(case) for case in calibration_set]
    for epoch in range(1, config["syntheticPretrainingEpochs"] + 1):
        _train_epoch(
            torch,
            model,
            optimizer,
            train_set,
            output_root=output_root,
            image_height=config["imageHeight"],
            batch_size=config["batchSize"],
            seed=seed + 5000 + epoch,
            synthetic_only=True,
        )
    for epoch in range(1, maximum_epochs + 1):
        loss = _train_epoch(
            torch,
            model,
            optimizer,
            train_set,
            output_root=output_root,
            image_height=config["imageHeight"],
            batch_size=config["batchSize"],
            seed=seed + epoch,
        )
        predictions, completeness, _details = _predict_cases(
            torch,
            model,
            calibration_set,
            output_root=output_root,
            image_height=config["imageHeight"],
            batch_size=config["batchSize"],
        )
        metrics = sequence_metrics(targets, predictions, well_formed=completeness)
        key = (
            float(metrics["tokenErrorRate"]),
            -int(metrics["sequenceExactLineCount"]),
            -int(metrics["attackCountExactLineCount"]),
        )
        calibration_history.append(
            {"epoch": epoch, "trainingLoss": round(loss, 6), "metrics": metrics}
        )
        eligible_for_selection = epoch >= config["minimumEpochs"]
        if eligible_for_selection and (best_key is None or key < best_key):
            best_key = key
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            patience = 0
        elif eligible_for_selection:
            patience += 1
        if eligible_for_selection and patience >= config["patience"]:
            break
    if best_state is None or best_epoch < 1:
        raise ScoreSequenceTrainingError("Calibration did not produce a candidate.")

    # The calibration-selected epoch is now frozen.  Reinitialize and train the
    # final candidate on all development cases without reading shadow metrics.
    torch.manual_seed(seed)
    final_model = _torch_model(torch, hidden_size=config["hiddenSize"])
    final_optimizer = torch.optim.AdamW(
        final_model.parameters(),
        lr=config["learningRate"],
        weight_decay=config["weightDecay"],
    )
    final_losses: list[float] = []
    for epoch in range(1, config["syntheticPretrainingEpochs"] + 1):
        _train_epoch(
            torch,
            final_model,
            final_optimizer,
            development,
            output_root=output_root,
            image_height=config["imageHeight"],
            batch_size=config["batchSize"],
            seed=seed + 15000 + epoch,
            synthetic_only=True,
        )
    for epoch in range(1, best_epoch + 1):
        final_losses.append(
            _train_epoch(
                torch,
                final_model,
                final_optimizer,
                development,
                output_root=output_root,
                image_height=config["imageHeight"],
                batch_size=config["batchSize"],
                seed=seed + 10000 + epoch,
            )
        )

    candidate_root = dataset_root / "challengers"
    candidate_root.mkdir(parents=True, exist_ok=True)
    os.chmod(candidate_root, 0o700)
    temporary_weights = candidate_root / ".candidate-weights.pt"
    torch.save(final_model.state_dict(), temporary_weights)
    os.chmod(temporary_weights, 0o600)
    weights_digest = _sha256_file(temporary_weights)
    contract_core = {
        "schemaVersion": SCORE_SEQUENCE_CHALLENGER_SCHEMA_VERSION,
        "candidateVersion": SCORE_SEQUENCE_CHALLENGER_VERSION,
        "datasetManifestDigest": str(manifest["manifestDigest"]),
        "benchmarkManifestDigest": str(manifest["benchmarkManifestDigest"]),
        "semanticBaselineDigest": str(baseline["reportDigest"]),
        "developmentCaseIds": sorted(str(case["caseId"]) for case in development),
        "developmentContentUnitIds": sorted(
            {str(case["contentUnitId"]) for case in development}
        ),
        "calibrationTrainingCaseIds": train_ids,
        "calibrationCaseIds": calibration_ids,
        "selectedEpochCount": best_epoch,
        "configuration": config,
        "weightsSha256": weights_digest,
        "shadowMetricsReadDuringSelection": False,
        "validationAccessed": False,
        "sealedTestAccessed": False,
        "promotionEligible": False,
    }
    contract_digest = _sha256_json(contract_core)
    model_id = f"score-ctc-{contract_digest[:16]}"
    model_root = candidate_root / model_id
    if model_root.exists():
        temporary_weights.unlink(missing_ok=True)
        raise ScoreSequenceTrainingError("This immutable sequence candidate already exists.")
    model_root.mkdir(mode=0o700)
    weights_path = model_root / "weights.pt"
    os.replace(temporary_weights, weights_path)
    contract = {**contract_core, "modelId": model_id, "contractDigest": contract_digest}
    contract_path = model_root / "contract.json"
    _write_json(contract_path, contract)

    # Opened discovery shadow is evaluated only after the exact weights and
    # configuration are frozen above.  It is regression evidence, never a
    # promotion-quality holdout.
    shadow_predictions, shadow_complete, shadow_details = _predict_cases(
        torch,
        final_model,
        shadow,
        output_root=output_root,
        image_height=config["imageHeight"],
        batch_size=config["batchSize"],
    )
    shadow_targets = [_target_groups(case) for case in shadow]
    challenger_metrics = sequence_metrics(
        shadow_targets, shadow_predictions, well_formed=shadow_complete
    )
    baseline_predictions = [
        _baseline_groups(baseline_by_case[str(case["caseId"])]) for case in shadow
    ]
    baseline_metrics = sequence_metrics(shadow_targets, baseline_predictions)
    gates = {
        "allOutputsWellFormed": (
            challenger_metrics["wellFormedLineCount"] == len(shadow)
        ),
        "noBlankOutputs": challenger_metrics["blankLineCount"] == 0,
        "moreExactSequencesThanBaseline": (
            challenger_metrics["sequenceExactLineCount"]
            > baseline_metrics["sequenceExactLineCount"]
        ),
        "noWorseAttackCountAccuracy": (
            challenger_metrics["attackCountExactLineCount"]
            >= baseline_metrics["attackCountExactLineCount"]
        ),
        "lowerTokenErrorThanBaseline": (
            challenger_metrics["tokenErrorRate"] < baseline_metrics["tokenErrorRate"]
        ),
        "moreExactAttackGroupsThanBaseline": (
            challenger_metrics["exactAttackGroupCount"]
            > baseline_metrics["exactAttackGroupCount"]
        ),
    }
    unified_review_gate_passed = all(gates.values())
    report_core = {
        "schemaVersion": SCORE_SEQUENCE_CHALLENGER_SCHEMA_VERSION,
        "modelId": model_id,
        "contractDigest": contract_digest,
        "weightsSha256": weights_digest,
        "datasetManifestDigest": str(manifest["manifestDigest"]),
        "datasetManifestPath": str(manifest_path.relative_to(output_root)),
        "semanticBaselineDigest": str(baseline["reportDigest"]),
        "semanticBaselinePath": str(baseline_path.relative_to(output_root)),
        "evaluationClass": "opened_discovery_shadow_regression",
        "selectedEpochCount": best_epoch,
        "calibrationBestMetrics": calibration_history[best_epoch - 1]["metrics"],
        "calibrationHistory": calibration_history,
        "finalTrainingLosses": [round(value, 6) for value in final_losses],
        "baselineShadowMetrics": baseline_metrics,
        "challengerShadowMetrics": challenger_metrics,
        "shadowResults": shadow_details,
        "gates": gates,
        "unifiedReviewGatePassed": unified_review_gate_passed,
        "reviewPacketCreated": False,
        "currentPageRecordsModified": False,
        "trainingStarted": True,
        "promotionEligible": False,
        "validationAccessed": False,
        "sealedTestAccessed": False,
    }
    report_digest = _sha256_json(report_core)
    report = {**report_core, "reportDigest": report_digest}
    report_path = model_root / "shadow-report.json"
    _write_json(report_path, report)
    return {
        "schemaVersion": SCORE_SEQUENCE_CHALLENGER_SCHEMA_VERSION,
        "modelId": model_id,
        "contractDigest": contract_digest,
        "weightsSha256": weights_digest,
        "datasetManifestDigest": str(manifest["manifestDigest"]),
        "selectedEpochCount": best_epoch,
        "developmentCaseCount": len(development),
        "shadowCaseCount": len(shadow),
        "baselineShadowMetrics": baseline_metrics,
        "challengerShadowMetrics": challenger_metrics,
        "gates": gates,
        "unifiedReviewGatePassed": unified_review_gate_passed,
        "reportDigest": report_digest,
        "reportPath": str(report_path.relative_to(output_root)),
        "reviewPacketCreated": False,
        "promotionEligible": False,
        "validationAccessed": False,
        "sealedTestAccessed": False,
    }
