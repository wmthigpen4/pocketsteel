from __future__ import annotations

import json
import os
import plistlib
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "deploy/macos/install-private-preview-launchdaemon.sh"


def _run_installer(command: str, **overrides: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(overrides)
    return subprocess.run(
        [str(INSTALLER), command],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def test_rendered_launchdaemon_always_keeps_origin_alive() -> None:
    result = _run_installer("render")

    assert result.returncode == 0, result.stderr
    payload = plistlib.loads(result.stdout.encode())
    assert payload["RunAtLoad"] is True
    assert payload["KeepAlive"] is True
    assert payload["EnvironmentVariables"]["STEEL_RAG_DATA_DIR"] == str(REPO_ROOT)
    assert payload["EnvironmentVariables"]["STEEL_RAG_REPO_DIR"] == str(REPO_ROOT)


def test_restart_refuses_to_run_without_an_exact_release() -> None:
    result = _run_installer("restart", STEEL_RAG_EXPECTED_GIT_SHA="")

    assert result.returncode != 0
    assert "STEEL_RAG_EXPECTED_GIT_SHA is required" in result.stderr
    assert "sudo" not in result.stderr.lower()


def test_preflight_rejects_a_branch_checkout() -> None:
    result = _run_installer(
        "preflight",
        STEEL_RAG_EXPECTED_GIT_SHA=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip(),
    )

    assert result.returncode != 0


def test_verify_health_checks_live_ready_and_exact_version() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            payload = {
                "/health/live": {"status": "live"},
                "/health/ready": {"status": "ready"},
                "/api/version": {"status": "ok", "git_sha": "abc1234"},
            }.get(self.path)
            if payload is None:
                self.send_response(404)
                self.end_headers()
                return
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = _run_installer(
            "verify",
            STEEL_RAG_HOST="127.0.0.1",
            STEEL_RAG_PORT=str(server.server_address[1]),
            STEEL_RAG_EXPECTED_GIT_SHA="abc1234",
            STEEL_RAG_HEALTH_TIMEOUT_SECONDS="2",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["git_sha"] == "abc1234"


def test_verify_rejects_invalid_timeout_without_waiting() -> None:
    result = _run_installer(
        "verify",
        STEEL_RAG_HEALTH_TIMEOUT_SECONDS="not-a-number",
    )

    assert result.returncode != 0
    assert "must be a positive integer" in result.stderr


def test_activate_refuses_an_invalid_replacement_pid_before_sudo() -> None:
    result = _run_installer(
        "activate",
        STEEL_RAG_EXPECTED_GIT_SHA="not-a-commit",
        STEEL_RAG_REPLACE_PID="not-a-pid",
    )

    assert result.returncode != 0
    assert "Expected release is not available" in result.stderr
