#!/usr/bin/env python3
"""Verify route isolation, headers, hashes, and forbidden references in a built bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from partner_companions.travis_howdy.release import CompanionReleaseError, FORBIDDEN_TEXT, validate_companion


REQUIRED_FILES = (
    "index.html",
    "404.html",
    "_headers",
    "_redirects",
    "howdy/index.html",
    "howdy/embed-demo/index.html",
)
BLOCKED_ROUTES = (
    "/api/answer",
    "/api/search",
    "/ui/example",
    "/chat",
    "/melody",
    "/lessons",
    "/assets/../howdy",
    "/%2e%2e/%2e%2e/etc/passwd",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(bundle: Path, manifest_path: Path) -> dict[str, object]:
    bundle = bundle.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for relative in REQUIRED_FILES:
        if not (bundle / relative).is_file():
            raise CompanionReleaseError(f"Missing required bundle file: {relative}")
    pdf_paths = list(bundle.glob("assets/*/howdy-tablature.pdf"))
    if len(pdf_paths) != 1:
        raise CompanionReleaseError("Expected exactly one canonical printable PDF.")
    pdf_route = "/" + pdf_paths[0].relative_to(bundle).as_posix()
    redirects = (bundle / "_redirects").read_text(encoding="utf-8")
    expected_redirects = (
        "/ /howdy 302",
        "/howdy /howdy/index.html 200",
        "/howdy/embed-demo /howdy/embed-demo/index.html 200",
        f"/howdy/print {pdf_route} 302",
        f"/howdy/print/ {pdf_route} 302",
    )
    local_alias_redirects = (
        "/practice-guide/howdy /practice-guide/howdy/index.html 200",
        "/practice-guide/howdy/ /practice-guide/howdy/index.html 200",
    )
    actual_redirects = tuple(line for line in redirects.splitlines() if line.strip())
    local_alias_allowed = (
        manifest.get("releaseMode") == "draft"
        and "/practice-guide/howdy" in (manifest.get("allowedRoutes") or [])
        and (bundle / "practice-guide" / "howdy" / "index.html").is_file()
    )
    permitted_redirects = expected_redirects + local_alias_redirects if local_alias_allowed else expected_redirects
    if actual_redirects != permitted_redirects:
        raise CompanionReleaseError("The route allowlist differs from the reviewed companion map.")
    headers = (bundle / "_headers").read_text(encoding="utf-8")
    required_headers = (
        "Content-Security-Policy:",
        "connect-src 'self'",
        "object-src 'none'",
        "form-action 'none'",
        "frame-ancestors 'none'",
        "X-Robots-Tag: noindex, nofollow, noarchive",
        "Referrer-Policy: no-referrer",
        "X-Content-Type-Options: nosniff",
        "Cache-Control: private, max-age=31536000, immutable",
    )
    missing_headers = [value for value in required_headers if value not in headers]
    if missing_headers:
        raise CompanionReleaseError(f"Missing required security headers: {', '.join(missing_headers)}")
    artifact_paths = list(bundle.glob("assets/*/lesson-companion.json"))
    if len(artifact_paths) != 1:
        raise CompanionReleaseError("Expected exactly one canonical companion artifact.")
    data = json.loads(artifact_paths[0].read_text(encoding="utf-8"))
    validate_companion(data, release=manifest.get("releaseMode") == "release")
    release_data = data.get("release", {})
    if manifest.get("reviewPhase") != release_data.get("reviewPhase"):
        raise CompanionReleaseError("The release manifest review phase differs from the canonical companion.")
    if manifest.get("accessTesterCount") != int(release_data.get("testerEmailCount", 0)):
        raise CompanionReleaseError("The release manifest tester count differs from the canonical companion.")
    actual_hashes = {
        path.relative_to(bundle).as_posix(): sha256(path)
        for path in sorted(bundle.rglob("*"))
        if path.is_file()
    }
    if actual_hashes != manifest.get("assetHashes"):
        raise CompanionReleaseError("The bundle no longer matches its immutable release manifest.")
    for path in bundle.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".css", ".js", ".json", ""}:
            continue
        lowered = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_TEXT:
            if forbidden.lower() in lowered:
                raise CompanionReleaseError(f"Forbidden reference {forbidden!r} in {path.relative_to(bundle)}")
    routes = [line.split()[0] for line in redirects.splitlines() if line]
    escaped = [route for route in BLOCKED_ROUTES if route in routes]
    if escaped:
        raise CompanionReleaseError(f"Blocked routes unexpectedly appear in the allowlist: {escaped}")
    if re.search(r"\.(?:vtt|srt|map)(?:$|\?)", "\n".join(actual_hashes), re.IGNORECASE):
        raise CompanionReleaseError("Raw transcript or source-map extension found in bundle.")
    return {
        "result": "pass",
        "files": len(actual_hashes),
        "companionRevision": data["revision"],
        "artifactSha256": data["artifactSha256"],
        "blockedRoutes": list(BLOCKED_ROUTES),
        "networkPolicy": "same-origin-only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.bundle, args.manifest), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
