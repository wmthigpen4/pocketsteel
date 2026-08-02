#!/usr/bin/env python3
"""Validate and report the private Play Songs candidate pipeline."""

from __future__ import annotations

import argparse
import json

from steel_guitar_rag.song_catalog_pipeline import build_curation_report, format_curation_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--check", action="store_true", help="Exit nonzero only when the registries violate their schemas or gates.")
    args = parser.parse_args()
    report = build_curation_report()
    print(json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else format_curation_report(report))
    return 1 if args.check and not report["valid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
