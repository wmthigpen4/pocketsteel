#!/usr/bin/env python3
"""Direct Upload an already approved Travis companion bundle to Cloudflare Pages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from partner_companions.travis_howdy.release import CompanionReleaseError, HOSTNAME, PROJECT_NAME
from scripts.verify_travis_companion import verify


def wrangler_binary() -> Path:
    candidate = ROOT / "node_modules" / ".bin" / "wrangler"
    if not candidate.is_file():
        raise CompanionReleaseError("Install the repository's pinned dependencies with npm ci before publishing.")
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--deploy-reviewed-bundle",
        action="store_true",
        help="Required acknowledgement that Access, custom domain, rights, brand, music, and print approvals passed.",
    )
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = verify(args.bundle, manifest_path)
    if manifest.get("releaseMode") != "release":
        raise CompanionReleaseError("Draft bundles cannot be uploaded.")
    if manifest.get("intendedCloudflareProject") != PROJECT_NAME or manifest.get("intendedHostname") != HOSTNAME:
        raise CompanionReleaseError("Manifest target differs from the isolated Travis preview target.")
    if manifest.get("accessTesterCount") != 2:
        raise CompanionReleaseError("The Access allowlist must contain exactly two reviewed identities.")
    if not args.deploy_reviewed_bundle:
        print(json.dumps({"result": "validated-not-deployed", "verification": report}, indent=2, sort_keys=True))
        return 0
    command = [
        str(wrangler_binary()),
        "pages",
        "deploy",
        str(args.bundle.resolve()),
        "--project-name",
        PROJECT_NAME,
        "--branch",
        "main",
        "--commit-hash",
        str(manifest["gitSha"]),
        "--commit-message",
        f"Howdy companion {manifest['companionRevision']}",
        "--commit-dirty=false",
        "--no-bundle",
    ]
    result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    combined = result.stdout + "\n" + result.stderr
    urls = re.findall(r"https://[a-zA-Z0-9.-]+\.pages\.dev", combined)
    immutable = next((url for url in urls if url != f"https://{PROJECT_NAME}.pages.dev"), None)
    if not immutable:
        raise CompanionReleaseError("Wrangler completed but did not return an immutable deployment URL.")
    manifest["immutablePagesDeploymentUrl"] = immutable
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "result": "deployed",
                "customUrl": f"https://{HOSTNAME}/howdy",
                "immutablePagesDeploymentUrlRecorded": True,
                "companionRevision": manifest["companionRevision"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
