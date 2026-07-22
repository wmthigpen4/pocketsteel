from __future__ import annotations

from pathlib import Path
import re
import sys


LOCK_DIR = Path("requirements")
EXPECTED_LOCKS = (
    "runtime.lock",
    "rag.lock",
    "training.lock",
    "test.lock",
    "deployment.lock",
)
PIN_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+==[^\s\\;]+")


def main() -> int:
    failures: list[str] = []
    for filename in EXPECTED_LOCKS:
        path = LOCK_DIR / filename
        if not path.is_file():
            failures.append(f"{path}: missing")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        pins = [index for index, line in enumerate(lines) if PIN_PATTERN.match(line)]
        if not pins:
            failures.append(f"{path}: no exact pins")
            continue
        for position, index in enumerate(pins):
            end = pins[position + 1] if position + 1 < len(pins) else len(lines)
            block = lines[index:end]
            if not any("--hash=sha256:" in line for line in block):
                failures.append(f"{path}:{index + 1}: pin has no SHA-256 hash")

    if failures:
        print("Dependency lock check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"Dependency lock check passed for {len(EXPECTED_LOCKS)} environments.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
