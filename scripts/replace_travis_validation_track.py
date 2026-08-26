#!/usr/bin/env python3
"""Replace one ignored Travis validation track with a one-track proof bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--replacement-proof", type=Path, required=True)
    parser.add_argument("--remove-id", required=True)
    parser.add_argument("--audio-source", type=Path, required=True)
    parser.add_argument("--audio-destination", type=Path, required=True)
    parser.add_argument("--removed-audio", type=Path, required=True)
    args = parser.parse_args()

    proof = json.loads(args.proof.read_text(encoding="utf-8"))
    replacement_payload = json.loads(args.replacement_proof.read_text(encoding="utf-8"))
    replacement = replacement_payload["tracks"][0]
    matches = [index for index, item in enumerate(proof["tracks"]) if item["track"]["id"] == args.remove_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {args.remove_id!r} track, found {len(matches)}.")

    args.audio_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.audio_source, args.audio_destination)
    replacement["track"]["audioUrl"] = (
        "/ui/chord-reader-travis-validation/local-data/audio/" + args.audio_destination.name
    )
    proof["tracks"][matches[0]] = replacement
    proof["generatedAt"] = replacement_payload["generatedAt"]
    if args.removed_audio.exists():
        args.removed_audio.unlink()
    temporary = args.proof.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(args.proof)
    print(json.dumps({"removed": args.remove_id, "added": replacement["track"]["id"], "order": matches[0] + 1}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
