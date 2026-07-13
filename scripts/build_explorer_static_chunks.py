#!/usr/bin/env python3
"""Split the legacy Explorer fixture into deterministic lazy-loaded chunks."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path("ui/e9-fretboard-explorer-data.js")
DEFAULT_OUTPUT = Path("ui/explorer-data-v1")
PAYLOADS_MARKER = "window.STEEL_RAG_E9_EXPLORER_PAYLOADS = "
COPEDENTS_MARKER = "window.STEEL_RAG_E9_EXPLORER_PAYLOADS_BY_COPEDENT = "
FALLBACK_MARKER = "window.STEEL_RAG_E9_EXPLORER_PAYLOAD = "


def _extract_json(text: str, start_marker: str, end_marker: str) -> dict[str, Any]:
    try:
        body = text.split(start_marker, 1)[1].split(f";\n{end_marker}", 1)[0]
    except IndexError as exc:
        raise ValueError(f"could not find Explorer assignment: {start_marker}") from exc
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError(f"Explorer assignment is not an object: {start_marker}")
    return payload


def _slug(value: str) -> str:
    aliases = {"#": "-sharp", "♯": "-sharp", "♭": "-flat"}
    rendered = "".join(aliases.get(character, character) for character in value).lower()
    return re.sub(r"[^a-z0-9]+", "-", rendered).strip("-") or "value"


def build_chunks(source: Path, output: Path) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8")
    default_payloads = _extract_json(text, PAYLOADS_MARKER, COPEDENTS_MARKER)
    by_copedent = _extract_json(text, COPEDENTS_MARKER, FALLBACK_MARKER)
    output.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "schemaVersion": "explorer_static_manifest_v1",
        "defaultCopedentId": "emmons-e9-basic",
        "defaultKey": "G",
        "copedents": {},
    }
    for copedent_id, payloads in sorted(by_copedent.items()):
        if not isinstance(payloads, dict) or not payloads:
            continue
        first_payload = next(iter(payloads.values()))
        selected_copedent = first_payload.get("selected_copedent") or {}
        copedent_record: dict[str, Any] = {
            "label": selected_copedent.get("label") or copedent_id,
            "keys": sorted(payloads),
            "chunks": {},
        }
        for key, payload in sorted(payloads.items()):
            raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            filename = f"{_slug(copedent_id)}.{_slug(key)}.{digest[:16]}.json.gz"
            compressed = gzip.compress(raw, compresslevel=9, mtime=0)
            (output / filename).write_bytes(compressed)
            copedent_record["chunks"][key] = {
                "path": f"/ui/{output.name}/{filename}",
                "sha256": digest,
                "bytes": len(raw),
                "compressedBytes": len(compressed),
            }
        manifest["copedents"][copedent_id] = copedent_record

    default_keys = set(default_payloads)
    manifest_keys = set(manifest["copedents"][manifest["defaultCopedentId"]]["keys"])
    if default_keys != manifest_keys:
        raise ValueError("default Explorer payload keys do not match the default copedent chunks")
    manifest_body = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    manifest["version"] = hashlib.sha256(manifest_body.encode("utf-8")).hexdigest()[:16]
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = build_chunks(args.source, args.output)
    chunk_count = sum(len(item["chunks"]) for item in manifest["copedents"].values())
    print(f"Wrote Explorer manifest {manifest['version']} with {chunk_count} compressed chunks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
