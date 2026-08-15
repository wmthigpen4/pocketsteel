#!/usr/bin/env python3
"""Build the local, ungated TTT Practice Guide pilot bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from partner_companions.travis_practice_guide.release import build_practice_guide_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory for the static preview bundle")
    parser.add_argument("--transcripts", type=Path, default=Path.home() / "Documents" / "vtt-test" / "Sections")
    parser.add_argument(
        "--howdy-evidence",
        type=Path,
        default=Path.home() / ".steel-rag" / "travis-preview" / "howdy" / "howdy.transcribed-review.json",
    )
    parser.add_argument("--printable-output", type=Path, help="Optional directory for the four standalone PDFs")
    parser.add_argument("--skip-private-source-verification", action="store_true", help="For isolated unit tests only")
    args = parser.parse_args()
    manifest = build_practice_guide_bundle(
        args.output,
        transcript_root=None if args.skip_private_source_verification else args.transcripts,
        howdy_evidence_path=None if args.skip_private_source_verification else args.howdy_evidence,
        printable_output_dir=args.printable_output,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
