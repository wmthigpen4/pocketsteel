"""Streaming conditional static-file responses for the same-origin app."""

from __future__ import annotations

import mimetypes
import re
import zlib
from datetime import timezone
from email.utils import formatdate, parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator


StartResponse = Callable[[str, list[tuple[str, str]]], None]
CHUNK_SIZE = 64 * 1024
HASHED_ASSET_RE = re.compile(r"(?:^|[.-])[0-9a-f]{10,64}(?:[.-]|$)", re.I)
COMPRESSIBLE_TYPES = {
    "application/javascript",
    "application/json",
    "image/svg+xml",
    "text/css",
    "text/html",
    "text/javascript",
    "text/plain",
}


class GzipFileIterable:
    def __init__(self, file_path: Path) -> None:
        self._file = file_path.open("rb")

    def __iter__(self) -> Iterator[bytes]:
        try:
            compressor = zlib.compressobj(level=6, wbits=16 + zlib.MAX_WBITS)
            while True:
                chunk = self._file.read(CHUNK_SIZE)
                if not chunk:
                    break
                encoded = compressor.compress(chunk)
                if encoded:
                    yield encoded
            tail = compressor.flush()
            if tail:
                yield tail
        finally:
            self.close()

    def close(self) -> None:
        self._file.close()


class FileIterable:
    def __init__(self, file_path: Path) -> None:
        self._file = file_path.open("rb")

    def __iter__(self) -> Iterator[bytes]:
        try:
            while True:
                chunk = self._file.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk
        finally:
            self.close()

    def close(self) -> None:
        self._file.close()


def _content_type(file_path: Path) -> tuple[str, bool]:
    precompressed = file_path.suffix == ".gz"
    source_path = file_path.with_suffix("") if precompressed else file_path
    content_type = mimetypes.guess_type(str(source_path))[0] or "application/octet-stream"
    if content_type.startswith("text/") or content_type in {
        "application/javascript",
        "application/json",
        "image/svg+xml",
    }:
        content_type = f"{content_type}; charset=utf-8"
    return content_type, precompressed


def _not_modified(environ: dict[str, Any], etag: str, modified_seconds: int) -> bool:
    if_none_match = str(environ.get("HTTP_IF_NONE_MATCH") or "").strip()
    if if_none_match:
        return etag in {value.strip() for value in if_none_match.split(",")}
    if_modified_since = str(environ.get("HTTP_IF_MODIFIED_SINCE") or "").strip()
    if not if_modified_since:
        return False
    try:
        parsed = parsedate_to_datetime(if_modified_since)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp()) >= modified_seconds
    except (TypeError, ValueError, OverflowError):
        return False


def _cache_control(file_path: Path, query_string: str) -> str:
    if file_path.name == "manifest.json":
        return "no-cache"
    if file_path.suffix.lower() in {".html", ".htm"}:
        return "no-cache"
    if "v=" in query_string or HASHED_ASSET_RE.search(file_path.name):
        return "public, max-age=31536000, immutable"
    return "public, max-age=3600"


def static_file_response(
    environ: dict[str, Any],
    start_response: StartResponse,
    *,
    file_path: Path,
    root: Path,
    security_headers: tuple[tuple[str, str], ...] = (),
) -> Iterable[bytes]:
    try:
        file_path.relative_to(root)
    except ValueError:
        body = b"forbidden"
        start_response(
            "403 Forbidden",
            [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(body))), *security_headers],
        )
        return [body]
    if not file_path.is_file():
        body = b"not found"
        start_response(
            "404 Not Found",
            [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(body))), *security_headers],
        )
        return [body]

    stat = file_path.stat()
    content_type, precompressed = _content_type(file_path)
    accepts_gzip = "gzip" in str(environ.get("HTTP_ACCEPT_ENCODING") or "").lower()
    base_type = content_type.split(";", 1)[0]
    use_streaming_gzip = accepts_gzip and not precompressed and stat.st_size >= 1024 and base_type in COMPRESSIBLE_TYPES
    encoding = "gzip" if precompressed or use_streaming_gzip else "identity"
    etag = f'W/"{stat.st_mtime_ns:x}-{stat.st_size:x}-{encoding}"'
    modified_seconds = int(stat.st_mtime)
    common_headers = [
        ("ETag", etag),
        ("Last-Modified", formatdate(modified_seconds, usegmt=True)),
        ("Cache-Control", _cache_control(file_path, str(environ.get("QUERY_STRING") or ""))),
        ("Vary", "Accept-Encoding"),
        *security_headers,
    ]
    if _not_modified(environ, etag, modified_seconds):
        start_response("304 Not Modified", common_headers)
        return []

    response_headers = [("Content-Type", content_type), *common_headers]
    if precompressed or use_streaming_gzip:
        response_headers.append(("Content-Encoding", "gzip"))
    if use_streaming_gzip:
        start_response("200 OK", response_headers)
        return GzipFileIterable(file_path)

    response_headers.append(("Content-Length", str(stat.st_size)))
    start_response("200 OK", response_headers)
    file_wrapper = environ.get("wsgi.file_wrapper")
    if callable(file_wrapper):
        file_handle = file_path.open("rb")
        return file_wrapper(file_handle, CHUNK_SIZE)
    return FileIterable(file_path)
