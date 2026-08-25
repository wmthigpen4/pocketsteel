#!/usr/bin/env python3
"""Attach a local BTC third opinion and three-system review queue to a proof bundle."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.add_chordify_crosscheck import _compare, _product  # noqa: E402
from steel_guitar_rag.chord_reader.btc import BTCRecognizer  # noqa: E402


DEFAULT_PROOF = REPO_ROOT / "ui/chord-reader-proof/local-tests/proof.json"
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
CATEGORY_PRIORITY = {
    "all_disagree": 0,
    "our_engine_outlier": 1,
    "chordify_outlier": 2,
    "btc_outlier": 3,
}


def _display_product(value: str | None) -> str | None:
    product = _product(value)
    if product is None:
        return None
    root, family = product
    return NOTE_NAMES[root] + ("m" if family == "minor" else "")


def _label_at(segments: Sequence[Mapping[str, Any]], time_seconds: float) -> str | None:
    for segment in segments:
        if float(segment["start"]) <= time_seconds < float(segment["end"]):
            return _display_product(str(segment.get("productLabel") or segment.get("label") or ""))
    return None


def _category(ours: str, chordify: str, btc: str) -> str:
    if ours == chordify == btc:
        return "all_agree"
    if chordify == btc:
        return "our_engine_outlier"
    if ours == btc:
        return "chordify_outlier"
    if ours == chordify:
        return "btc_outlier"
    return "all_disagree"


def build_consensus(
    ours: Sequence[Mapping[str, Any]],
    chordify: Sequence[Mapping[str, Any]],
    btc: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    boundaries = sorted(
        {float(segment[edge]) for source in (ours, chordify, btc) for segment in source for edge in ("start", "end")}
    )
    windows: list[dict[str, Any]] = []
    by_category: dict[str, float] = {}
    covered = 0.0
    ours_supported = 0.0
    for start, end in zip(boundaries, boundaries[1:]):
        if end <= start:
            continue
        midpoint = (start + end) / 2
        labels = (_label_at(ours, midpoint), _label_at(chordify, midpoint), _label_at(btc, midpoint))
        if any(label is None for label in labels):
            continue
        our_label, chordify_label, btc_label = labels
        assert our_label is not None and chordify_label is not None and btc_label is not None
        category = _category(our_label, chordify_label, btc_label)
        seconds = end - start
        covered += seconds
        by_category[category] = by_category.get(category, 0.0) + seconds
        if our_label in {chordify_label, btc_label}:
            ours_supported += seconds
        row = {
            "start": start,
            "end": end,
            "seconds": seconds,
            "ourChord": our_label,
            "chordifyChord": chordify_label,
            "btcChord": btc_label,
            "category": category,
        }
        if (
            windows
            and abs(windows[-1]["end"] - start) <= 1e-6
            and all(windows[-1][key] == row[key] for key in ("ourChord", "chordifyChord", "btcChord", "category"))
        ):
            windows[-1]["end"] = end
            windows[-1]["seconds"] += seconds
        else:
            windows.append(row)

    review_windows = [window for window in windows if window["category"] != "all_agree"]
    review_windows.sort(
        key=lambda window: (
            CATEGORY_PRIORITY[window["category"]],
            -window["seconds"],
            window["start"],
        )
    )
    all_agree = by_category.get("all_agree", 0.0)
    priority_review = by_category.get("all_disagree", 0.0) + by_category.get("our_engine_outlier", 0.0)
    chordify_disagreement = (
        by_category.get("all_disagree", 0.0)
        + by_category.get("our_engine_outlier", 0.0)
        + by_category.get("chordify_outlier", 0.0)
    )
    pair_votes: dict[tuple[str, str], dict[str, Any]] = {}
    for window in windows:
        if window["ourChord"] == window["chordifyChord"]:
            continue
        key = (window["ourChord"], window["chordifyChord"])
        summary = pair_votes.setdefault(
            key,
            {
                "ourChord": key[0],
                "chordifyChord": key[1],
                "windowCount": 0,
                "seconds": 0.0,
                "btcSupportsOurSeconds": 0.0,
                "btcSupportsChordifySeconds": 0.0,
                "btcSupportsNeitherSeconds": 0.0,
            },
        )
        summary["windowCount"] += 1
        summary["seconds"] += window["seconds"]
        if window["category"] == "chordify_outlier":
            summary["btcSupportsOurSeconds"] += window["seconds"]
        elif window["category"] == "our_engine_outlier":
            summary["btcSupportsChordifySeconds"] += window["seconds"]
        else:
            summary["btcSupportsNeitherSeconds"] += window["seconds"]
    return {
        "coveredSeconds": covered,
        "allAgreeFraction": all_agree / covered if covered else 0.0,
        "ourSupportedFraction": ours_supported / covered if covered else 0.0,
        "priorityReviewSeconds": priority_review,
        "chordifyDisagreementSeconds": chordify_disagreement,
        "btcSupportsOurFraction": (
            by_category.get("chordify_outlier", 0.0) / chordify_disagreement if chordify_disagreement else 0.0
        ),
        "btcSupportsChordifyFraction": (
            by_category.get("our_engine_outlier", 0.0) / chordify_disagreement if chordify_disagreement else 0.0
        ),
        "btcSupportsNeitherFraction": (
            by_category.get("all_disagree", 0.0) / chordify_disagreement if chordify_disagreement else 0.0
        ),
        "secondsByCategory": {key: by_category.get(key, 0.0) for key in (*CATEGORY_PRIORITY, "all_agree")},
        "pairVotes": sorted(pair_votes.values(), key=lambda item: (-item["seconds"], item["ourChord"]))[:16],
        "reviewWindows": review_windows[:18],
        "categorySemantics": {
            "all_agree": "All three systems report the same product chord.",
            "our_engine_outlier": "Chordify and BTC agree against our engine; review first.",
            "chordify_outlier": "Our engine and BTC agree against Chordify.",
            "btc_outlier": "Our engine and Chordify agree against BTC.",
            "all_disagree": "All three systems report different product chords; review first.",
        },
    }


def _audio_path(track: Mapping[str, Any], proof_path: Path) -> Path:
    audio_url = str(track["track"]["audioUrl"])
    expected_prefix = "/ui/chord-reader-proof/local-tests/"
    if not audio_url.startswith(expected_prefix):
        raise ValueError(f"Local proof audio URL must start with {expected_prefix!r}.")
    relative = Path(audio_url.removeprefix(expected_prefix))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Unsafe local proof audio path.")
    path = proof_path.parent / relative
    return path.resolve(strict=True)


def add_open_source_consensus(
    payload: dict[str, Any],
    proof_path: Path,
    recognizer: BTCRecognizer | None,
) -> dict[str, Any]:
    for item in payload["tracks"]:
        cross_check = item.get("crossCheck")
        if not cross_check:
            raise ValueError("Run add_chordify_crosscheck.py before adding three-system consensus.")
        existing = item.get("openSourceCrossCheck")
        if recognizer is None:
            if not existing or not existing.get("prediction"):
                raise ValueError("No existing BTC prediction is available to reuse.")
            prediction = existing["prediction"]
            license_name = existing["license"]
            model_revision = existing["modelRevision"]
        else:
            audio = _audio_path(item, proof_path)
            prediction = recognizer.predict(
                audio,
                prediction_id=f"{item['track']['id']}-btc-open-source",
                product_viterbi=True,
            )
            license_name = recognizer.registry["upstream"]["license"]
            model_revision = recognizer.registry["upstream"]["revision"]
        consensus = build_consensus(
            item["prediction"]["segments"],
            cross_check["segments"],
            prediction["segments"],
        )
        item["openSourceCrossCheck"] = {
            "provider": "BTC ISMIR 2019",
            "sourceKind": "local pinned open-source pretrained model",
            "license": license_name,
            "modelRevision": model_revision,
            "prediction": prediction,
            "ourVsBtc": _compare(item["prediction"]["segments"], prediction["segments"]),
            "chordifyVsBtc": _compare(cross_check["segments"], prediction["segments"]),
            "consensus": consensus,
            "disclosure": (
                "BTC is an independent open-source model, not ground truth. Three-system agreement helps order "
                "human review; it does not turn agreement into measured accuracy."
            ),
        }

    payload["openSourceMethodology"] = {
        "title": "What we borrowed from the open-source projects",
        "summary": (
            "Swaram publicly identifies BTC as its recognizer and applies harmonic CQT features plus a fixed, "
            "probability-aware sequence smoother. This proof now runs our already pinned BTC checkpoint locally, "
            "collapses its 170 labels to the same product vocabulary, and uses its full probabilities in one fixed "
            "Viterbi pass. The chord-extractor project confirms Chordino/NNLS-chroma as a valuable, fundamentally "
            "different future baseline; its GPL/native-plugin path remains isolated rather than copied into the app."
        ),
        "sources": [
            {"label": "Swaram chord finder", "url": "https://ecoliving-tips.github.io/chord-finder.html"},
            {
                "label": "Swaram public BTC backend",
                "url": "https://huggingface.co/spaces/vineethwilson/swaram-chord-service",
            },
            {"label": "BTC ISMIR 2019 source", "url": "https://github.com/jayg996/BTC-ISMIR19"},
            {"label": "chord-extractor wrapper", "url": "https://github.com/ohollo/chord-extractor"},
            {"label": "Chordino / NNLS Chroma", "url": "https://code.soundsoftware.ac.uk/projects/nnls-chroma"},
        ],
    }
    payload["openSourceCrossCheckGeneratedAt"] = datetime.now(timezone.utc).isoformat()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof", type=Path, default=DEFAULT_PROOF)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--reuse-existing", action="store_true", help="Recompute consensus without model inference")
    args = parser.parse_args()
    proof_path = args.proof.expanduser().resolve(strict=True)
    payload = json.loads(proof_path.read_text(encoding="utf-8"))
    recognizer = None
    if not args.reuse_existing:
        recognizer = BTCRecognizer(
            device=args.device,
            cache_dir=args.cache_dir,
            local_files_only=args.local_files_only,
        )
    add_open_source_consensus(payload, proof_path, recognizer)
    proof_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "proof": str(proof_path),
                "modelRevision": payload["tracks"][0]["openSourceCrossCheck"]["modelRevision"],
                "decoder": "btc-product-probability-viterbi-v1",
                "tracks": [
                    {
                        "trackId": item["track"]["id"],
                        "ourVsBtcAgreement": item["openSourceCrossCheck"]["ourVsBtc"]["exactAgreementFraction"],
                        "allAgreeFraction": item["openSourceCrossCheck"]["consensus"]["allAgreeFraction"],
                        "ourSupportedFraction": item["openSourceCrossCheck"]["consensus"]["ourSupportedFraction"],
                        "btcSupportsOurFraction": item["openSourceCrossCheck"]["consensus"]["btcSupportsOurFraction"],
                        "btcSupportsChordifyFraction": item["openSourceCrossCheck"]["consensus"][
                            "btcSupportsChordifyFraction"
                        ],
                        "priorityReviewSeconds": item["openSourceCrossCheck"]["consensus"]["priorityReviewSeconds"],
                    }
                    for item in payload["tracks"]
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
