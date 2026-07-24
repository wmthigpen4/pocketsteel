#!/usr/bin/env python3
"""Serve private reviews with durable draft capture or harden one console."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from pocketsteel.amazing_tablature_training import DEFAULT_PRIVATE_ROOT
from pocketsteel.lane15_review_drafts import (
    harden_review_console,
    make_durable_review_http_server,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_PRIVATE_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8766)

    harden = subparsers.add_parser("harden-console")
    harden.add_argument("path", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "harden-console":
        changed = harden_review_console(args.path)
        print(
            json.dumps(
                {"changed": changed, "path": str(args.path.expanduser().resolve())},
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    server = make_durable_review_http_server(
        args.root,
        host=args.host,
        port=args.port,
    )
    print(
        json.dumps(
            {
                "host": args.host,
                "port": server.server_address[1],
                "root": str(args.root.expanduser().resolve()),
                "status": "serving_private_reviews_with_durable_drafts",
            },
            sort_keys=True,
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
