#!/usr/bin/env python3
"""Run a private printed-score canary without persisting source or provider output."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from steel_guitar_rag.melody_arranger import arrange_melody_routes
from steel_guitar_rag.melody_import import SCORE_OMR_PROVIDER_ENV, import_score_draft


EVENT_FIELDS = ("measure", "beat", "durationBeats", "pitch", "pitchValue", "rest", "tie")


def _canonical_event(event: Mapping[str, Any]) -> dict[str, Any]:
    return {field: event[field] for field in EVENT_FIELDS if field in event}


def _attack_pitches(events: list[Mapping[str, Any]]) -> list[str]:
    return [
        str(event["pitch"])
        for event in events
        if not event.get("rest") and event.get("tie") != "stop"
    ]


def _performance_events(events: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for raw in events:
        event = dict(raw)
        previous = result[-1] if result else None
        if (
            event.get("tie") == "stop"
            and previous
            and previous.get("tie") == "start"
            and previous.get("pitchValue") == event.get("pitchValue")
        ):
            previous["durationBeats"] = float(previous["durationBeats"]) + float(
                event["durationBeats"]
            )
            previous["tie"] = ""
            previous["sustainedFromTie"] = True
            continue
        result.append(event)
    return result


def run_canary(source_path: Path, reference_path: Path, *, provider: str) -> dict[str, Any]:
    source_bytes = source_path.read_bytes()
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    if source_digest != reference["sourceSha256"]:
        raise AssertionError(
            f"Source digest mismatch: expected {reference['sourceSha256']}, received {source_digest}"
        )

    os.environ[SCORE_OMR_PROVIDER_ENV] = provider
    payload = {
        "sourceType": "image",
        "mimeType": "image/png",
        "contentBase64": base64.b64encode(source_bytes).decode("ascii"),
        "filename": source_path.name,
        "rightsAcknowledged": True,
        "partId": reference["selectedPartId"],
    }
    draft = import_score_draft(payload)
    score = draft["score"]
    actual_events = [_canonical_event(event) for event in score["melody"]]
    expected_events = [_canonical_event(event) for event in reference["events"]]
    checks = {
        "sourceDigest": source_digest == reference["sourceSha256"],
        "key": score["sourceKey"] == reference["sourceKey"],
        "meter": score["meter"] == reference["meter"],
        "staffSelection": draft.get("selectedPartId") == reference["selectedPartId"],
        "selectionResolved": not bool(draft.get("selectionRequired")),
        "exactTimeline": actual_events == expected_events,
        "exactAttackPitches": _attack_pitches(score["melody"]) == reference["attackPitches"],
        "noBassContamination": all(
            str(event.get("staff") or "") == "1" for event in score["melody"]
        ),
        "honestConfidence": all(
            float(event.get("confidence") or 0) < 1
            and event.get("confidenceBasis")
            == "provider_not_reported_structural_review_required"
            for event in score["melody"]
        ),
        "structureValid": bool(draft["review"]["summary"]["canArrange"])
        and draft["review"]["summary"]["errorCount"] == 0,
    }

    performance_events = _performance_events(score["melody"])
    arrangement_events = [
        {
            "token": event["pitch"],
            "pitch": event["pitch"],
            "pitchValue": event["pitchValue"],
            "measure": event["measure"],
            "beat": event["beat"],
            "durationBeats": event["durationBeats"],
            "tie": event.get("tie", ""),
            "origin": event.get("origin", "recognized"),
        }
        for event in performance_events
        if not event.get("rest")
    ]
    routes, resolved = arrange_melody_routes(
        arrangement_events,
        key=score["arrangementKey"],
        texture="both",
        route_id_prefix="private-score-canary",
        title="Private printed-score canary",
        meter=score["meter"],
        pickup_beats=score.get("pickupBeats", 0),
    )
    expected_sounding = [
        int(event["pitchValue"]) for event in performance_events if not event.get("rest")
    ]
    checks["arrangerPitchParity"] = [
        int(event["pitchValue"]) for event in resolved
    ] == expected_sounding
    checks["routePitchParity"] = all(
        [int(event["pitchValue"]) for event in route["events"]] == expected_sounding
        for route in routes
    )
    checks["mechanicalValidity"] = bool(routes) and all(
        route["tabExample"]["validation"]["ok"]
        and len(route["fretboard"]["positions"]) == len(expected_sounding)
        for route in routes
    )

    failures = [name for name, passed in checks.items() if not passed]
    return {
        "schemaVersion": "private_score_canary_result_v1",
        "providerId": draft["source"]["providerId"],
        "eventCount": len(score["melody"]),
        "attackCount": len(reference["attackPitches"]),
        "routeCount": len(routes),
        "checks": checks,
        "passed": not failures,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--provider", default="homr")
    args = parser.parse_args()
    result = run_canary(args.source, args.reference, provider=args.provider)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
