#!/usr/bin/env python3
"""Assemble an allowlisted Travis companion Pages directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from partner_companions.travis_howdy.release import DEFAULT_COMPANION, build_companion_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Temporary Pages Direct Upload directory.")
    parser.add_argument("--companion", type=Path, default=DEFAULT_COMPANION, help="Canonical companion JSON.")
    parser.add_argument("--release", action="store_true", help="Require complete approvals and private assets.")
    parser.add_argument("--release-config", type=Path, help="Ignored private release configuration.")
    parser.add_argument("--manifest", type=Path, help="Internal manifest path outside the upload directory.")
    parser.add_argument("--source-date-epoch", type=int, help="Deterministic manifest timestamp.")
    parser.add_argument("--draft-pdf", type=Path, help="Use an already rendered draft PDF.")
    parser.add_argument(
        "--draft-audio",
        type=Path,
        help="Use a private hash-pinned audio file for a local draft bundle.",
    )
    args = parser.parse_args()
    manifest = build_companion_bundle(
        args.output,
        companion_path=args.companion,
        release=args.release,
        release_config_path=args.release_config,
        manifest_path=args.manifest,
        source_date_epoch=args.source_date_epoch,
        draft_pdf_path=args.draft_pdf,
        draft_audio_path=args.draft_audio,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
