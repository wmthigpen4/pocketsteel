#!/usr/bin/env python3
"""Run the private localhost drop page for the current chord-reader engine."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from threading import Lock
from typing import Any, Mapping
from urllib.parse import unquote, urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_local_chord_reader_test import (
    MODEL_PATHS,
    _recognizer,
    _sha256,
    _summary,
)


PAGE_ROOT = REPO_ROOT / "ui/chord-reader-owner-test"
OUTPUT_ROOT = PAGE_ROOT / "local-data"
MANIFEST_PATH = OUTPUT_ROOT / "tracks.json"
STATIC_PATHS = {
    "/ui/chord-reader-owner-test/",
    "/ui/chord-reader-owner-test/index.html",
    "/ui/chord-reader-owner-test/owner-test.css",
    "/ui/chord-reader-owner-test/owner-test.js",
    "/ui/chord-reader-owner-test/timing.js",
}
MAX_UPLOAD_BYTES = 750 * 1024 * 1024
ENGINE_LABEL = "Current Travis-validation ensemble with phase-safe timing"
ANALYSIS_LOCK = Lock()


def _ensure_analysis_runtime() -> None:
    if importlib.util.find_spec("onnxruntime") is not None:
        return
    configured = os.environ.get("POCKET_STEEL_CHORD_PYTHON")
    candidates = [
        Path(configured).expanduser() if configured else None,
        REPO_ROOT.parent / "play-along-route-fix/.venv/bin/python",
        REPO_ROOT.parent / "tmp/chord-reader-v4/.venv/bin/python",
    ]
    for candidate in candidates:
        if candidate and candidate.is_file() and os.access(candidate, os.X_OK):
            os.execv(
                str(candidate),
                [str(candidate), str(Path(__file__).resolve()), *sys.argv[1:]],
            )
    raise RuntimeError(
        "ONNX Runtime is unavailable. Set POCKET_STEEL_CHORD_PYTHON to the chord-reader Python interpreter."
    )


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:72] or "song"


def _clean_title(value: str, fallback: str) -> str:
    title = re.sub(r"\s+", " ", value).strip()
    if not title:
        title = Path(fallback).stem
    return title[:160]


def _run(command: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        check=True,
    )


def _transcode(source: Path, wav_path: Path, browser_audio: Path) -> None:
    _run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "22050",
            "-c:a",
            "pcm_s16le",
            str(wav_path),
        ]
    )
    browser_audio.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-vn",
            "-ac",
            "2",
            "-ar",
            "44100",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(browser_audio),
        ]
    )


def _rhythm(audio: Path) -> dict[str, Any]:
    completed = _run(["node", "scripts/chord_reader_v2.js", "--audio", str(audio)])
    return json.loads(completed.stdout)


def _display_bars(
    prediction: Mapping[str, Any], rhythm: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    meter = str(rhythm.get("meter") or "4/4")
    try:
        beats_per_bar = max(1, int(meter.split("/", 1)[0]))
    except ValueError:
        beats_per_bar = 4
    request = {
        "tracks": [
            {
                "id": prediction["id"],
                "durationSeconds": prediction["durationSeconds"],
                "segments": prediction["segments"],
                "beatTimesSeconds": rhythm.get("beatTimesSeconds") or [],
                "beatsPerBar": beats_per_bar,
            }
        ]
    }
    completed = _run(
        ["node", "scripts/build_current_chord_reader_bars.js"],
        input_text=json.dumps(request),
    )
    result = json.loads(completed.stdout)["tracks"][0]
    bars = [{"bar": index + 1, **bar} for index, bar in enumerate(result.get("currentBars") or [])]
    return bars, {
        "status": result["phase"]["status"],
        "confidence": result["phase"]["confidence"],
        "downbeatOffsetBeats": result["appliedPhase"],
    }


def _read_manifest(output_root: Path = OUTPUT_ROOT) -> dict[str, Any]:
    path = output_root / "tracks.json"
    if not path.is_file():
        return {"schemaVersion": "owner_chord_reader_library_v1", "tracks": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(manifest: Mapping[str, Any], output_root: Path = OUTPUT_ROOT) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    destination = output_root / "tracks.json"
    temporary = output_root / "tracks.json.tmp"
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)


def analyze_file(
    source: Path,
    *,
    title: str = "",
    source_name: str | None = None,
    output_root: Path = OUTPUT_ROOT,
) -> dict[str, Any]:
    source = source.resolve(strict=True)
    source_name = source_name or source.name
    display_title = _clean_title(title, source_name)
    source_hash = _sha256(source)
    identifier = f"{_slug(display_title)}-{source_hash[:10]}"
    browser_audio = output_root / "audio" / f"{identifier}.mp3"
    with tempfile.TemporaryDirectory(prefix="owner-chord-reader-") as temporary:
        wav_path = Path(temporary) / "analysis.wav"
        _transcode(source, wav_path, browser_audio)
        prediction = _recognizer().predict(wav_path, prediction_id=identifier)
        rhythm = _rhythm(wav_path)
    bars, phase = _display_bars(prediction, rhythm)
    timing_mode = "beat-aligned-bars" if phase["status"] == "anchored" else "exact-model-transitions"
    item = {
        "schemaVersion": "owner_chord_reader_track_v1",
        "id": identifier,
        "title": display_title,
        "sourceFileName": Path(source_name).name,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "audioUrl": f"/ui/chord-reader-owner-test/local-data/audio/{browser_audio.name}",
        "audioSha256": source_hash,
        "durationSeconds": prediction["durationSeconds"],
        "engine": {
            "label": ENGINE_LABEL,
            "prediction": "frozen-domain-gated-v8",
            "display": "travis-phase-safe-timing-v2",
            "modelSha256": {path.name: _sha256(path) for path in MODEL_PATHS},
        },
        "rhythm": {
            "key": rhythm.get("key"),
            "keyMode": rhythm.get("keyMode"),
            "meter": rhythm.get("meter"),
            "tempoBpm": rhythm.get("tempo"),
            "beatTimesSeconds": rhythm.get("beatTimesSeconds") or [],
            "phase": phase,
        },
        "summary": {
            **_summary(prediction),
            "barCount": len(bars),
            "displayItemCount": len(bars) if timing_mode == "beat-aligned-bars" else len(prediction["segments"]),
        },
        "timingMode": timing_mode,
        "segments": prediction["segments"],
        "bars": bars,
        "disclosure": (
            "This is an unscored listening test. Confidence is the engine's own "
            "probability, not measured chord accuracy."
        ),
    }
    manifest = _read_manifest(output_root)
    tracks = [track for track in manifest["tracks"] if track.get("id") != identifier]
    tracks.insert(0, item)
    manifest = {
        "schemaVersion": "owner_chord_reader_library_v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "tracks": tracks,
    }
    _write_manifest(manifest, output_root)
    return item


class OwnerChordReaderHandler(SimpleHTTPRequestHandler):
    server_version = "OwnerChordReader/1"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _serve_seekable_audio(self, pathname: str) -> bool:
        prefix = "/ui/chord-reader-owner-test/local-data/audio/"
        if not pathname.startswith(prefix):
            return False
        audio_root = (OUTPUT_ROOT / "audio").resolve()
        requested = (audio_root / unquote(pathname[len(prefix) :])).resolve()
        if requested.parent != audio_root or not requested.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return True
        size = requested.stat().st_size
        start = 0
        end = size - 1
        status = HTTPStatus.OK
        range_header = self.headers.get("Range")
        if range_header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
            if not match or (not match.group(1) and not match.group(2)):
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return True
            if match.group(1):
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else end
            else:
                suffix_length = int(match.group(2))
                start = max(0, size - suffix_length)
            if start >= size or end < start:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return True
            end = min(end, size - 1)
            status = HTTPStatus.PARTIAL_CONTENT
        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        with requested.open("rb") as source:
            source.seek(start)
            remaining = length
            while remaining:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)
        return True

    def do_GET(self) -> None:  # noqa: N802
        pathname = urlsplit(self.path).path
        if pathname == "/":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/ui/chord-reader-owner-test/")
            self.end_headers()
            return
        if pathname == "/api/owner-chord-test/tracks":
            self._json(_read_manifest())
            return
        if self._serve_seekable_audio(pathname):
            return
        if pathname in STATIC_PATHS:
            super().do_GET()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_HEAD(self) -> None:  # noqa: N802
        pathname = urlsplit(self.path).path
        if pathname == "/":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/ui/chord-reader-owner-test/")
            self.end_headers()
            return
        if pathname in STATIC_PATHS:
            super().do_HEAD()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != "/api/owner-chord-test/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
            if length <= 0:
                raise ValueError("Choose an audio or video file first.")
            if length > MAX_UPLOAD_BYTES:
                raise ValueError("That file is larger than the 750 MB local limit.")
            source_name = unquote(self.headers.get("X-File-Name") or "song.audio")
            title = unquote(self.headers.get("X-Song-Title") or "")
            suffix = Path(source_name).suffix[:12] or ".audio"
            with tempfile.TemporaryDirectory(prefix="owner-chord-upload-") as temporary:
                source = Path(temporary) / f"upload{suffix}"
                remaining = length
                with source.open("wb") as output:
                    while remaining:
                        chunk = self.rfile.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise ValueError("The upload ended before the file was complete.")
                        output.write(chunk)
                        remaining -= len(chunk)
                if not ANALYSIS_LOCK.acquire(blocking=False):
                    self._json(
                        {"error": "Another song is already being analyzed."},
                        HTTPStatus.CONFLICT,
                    )
                    return
                try:
                    result = analyze_file(source, title=title, source_name=source_name)
                finally:
                    ANALYSIS_LOCK.release()
            self._json(result, HTTPStatus.CREATED)
        except (ValueError, subprocess.CalledProcessError) as error:
            detail = (
                error.stderr.strip()
                if isinstance(error, subprocess.CalledProcessError) and error.stderr
                else str(error)
            )
            self._json(
                {"error": detail or "The song could not be analyzed."},
                HTTPStatus.BAD_REQUEST,
            )
        except Exception as error:  # pragma: no cover - last-resort local guard
            self.log_error("analysis failed: %s", error)
            self._json(
                {"error": "The local chord-reader analysis failed."},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )


def main() -> int:
    _ensure_analysis_runtime()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8899)
    parser.add_argument("--seed-audio", action="append", type=Path, default=[])
    parser.add_argument("--seed-title", default="")
    parser.add_argument("--analyze-only", action="store_true")
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("This private test server may bind only to localhost.")
    for source in args.seed_audio:
        result = analyze_file(source, title=args.seed_title)
        print(json.dumps({"id": result["id"], "title": result["title"], "bars": len(result["bars"])}))
    if args.analyze_only:
        return 0
    server = ThreadingHTTPServer((args.host, args.port), OwnerChordReaderHandler)
    print(f"Owner chord-reader page: http://{args.host}:{args.port}/ui/chord-reader-owner-test/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
