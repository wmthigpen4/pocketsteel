#!/usr/bin/env python3
"""Render the Howdy notation-plus-E9-tab handout from canonical events."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from partner_companions.travis_howdy.release import DEFAULT_COMPANION, generate_tablature_pdf


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--companion", type=Path, default=DEFAULT_COMPANION)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.companion.read_text(encoding="utf-8"))
    output = generate_tablature_pdf(data, args.output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
