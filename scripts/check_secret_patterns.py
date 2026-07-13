from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys


MAX_SCANNED_FILE_SIZE = 2 * 1024 * 1024
PATTERNS = {
    "private key": re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "OpenAI-style key": re.compile(rb"\bsk-[A-Za-z0-9_-]{32,}\b"),
    "GitHub token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "Cloudflare token assignment": re.compile(
        rb"\b(?:CF_API_TOKEN|CLOUDFLARE_API_TOKEN)\s*[:=]\s*['\"]?[A-Za-z0-9_-]{20,}"
    ),
}


def tracked_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files", "-z"])
    return [Path(item.decode("utf-8")) for item in output.split(b"\0") if item]


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        if not path.is_file() or path.stat().st_size > MAX_SCANNED_FILE_SIZE:
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(data):
                findings.append(f"{path}: {label}")

    if findings:
        print("Secret-pattern scan failed:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print("Secret-pattern scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
