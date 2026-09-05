from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "deploy/macos/install-private-preview-launchagent.sh"


def _run(command: str, **overrides: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "STEEL_RAG_REPO_DIR": str(ROOT),
            "STEEL_RAG_DATA_DIR": str(ROOT),
            "STEEL_RAG_ENV_FILE": str(ROOT / "tests/fixtures/private-preview.env"),
            **overrides,
        }
    )
    return subprocess.run(
        [str(INSTALLER), command],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def test_rendered_launchagent_is_user_domain_and_loopback_only(tmp_path: Path) -> None:
    env_file = tmp_path / "private-preview.env"
    env_file.write_text("STEEL_RAG_TEST=1\n", encoding="utf-8")
    result = _run("render", STEEL_RAG_ENV_FILE=str(env_file))

    assert result.returncode == 0, result.stderr
    payload = plistlib.loads(result.stdout.encode())
    assert payload["Label"] == "com.steelguitarrag.private-preview"
    assert payload["RunAtLoad"] is True
    assert payload["KeepAlive"] is True
    assert "UserName" not in payload
    assert "GroupName" not in payload
    assert payload["EnvironmentVariables"]["STEEL_RAG_HOST"] == "127.0.0.1"
    assert payload["EnvironmentVariables"]["STEEL_RAG_PORT"] == "8770"
    assert payload["EnvironmentVariables"]["STEEL_RAG_REPO_DIR"] == str(ROOT)


def test_launchagent_installer_never_invokes_sudo() -> None:
    body = INSTALLER.read_text(encoding="utf-8")

    assert "sudo " not in body
    assert 'STEEL_RAG_DOMAIN="${STEEL_RAG_DOMAIN:-gui/$(id -u)}"' in body
    assert 'bootstrap "$STEEL_RAG_DOMAIN"' in body
    assert 'kickstart -k "$STEEL_RAG_DOMAIN/$STEEL_RAG_LABEL"' in body


def test_preflight_requires_an_exact_expected_release(tmp_path: Path) -> None:
    env_file = tmp_path / "private-preview.env"
    env_file.write_text("STEEL_RAG_TEST=1\n", encoding="utf-8")
    result = _run(
        "preflight",
        STEEL_RAG_ENV_FILE=str(env_file),
        STEEL_RAG_EXPECTED_GIT_SHA="",
    )

    assert result.returncode != 0
    assert "STEEL_RAG_EXPECTED_GIT_SHA is required" in result.stderr


def test_preflight_rejects_a_branch_checkout(tmp_path: Path) -> None:
    env_file = tmp_path / "private-preview.env"
    env_file.write_text("STEEL_RAG_TEST=1\n", encoding="utf-8")
    fake_home = tmp_path / "home"
    release = fake_home / ".steel-rag/releases/branch-checkout"
    release.mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "test-branch"], cwd=release, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "CI Test"], cwd=release, check=True)
    subprocess.run(["git", "config", "user.email", "ci-test@example.invalid"], cwd=release, check=True)
    (release / "tracked.txt").write_text("branch checkout\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=release, check=True)
    subprocess.run(["git", "commit", "-m", "test branch checkout"], cwd=release, check=True, capture_output=True)
    python_path = release / ".venv/bin/python"
    python_path.parent.mkdir(parents=True)
    python_path.symlink_to(sys.executable)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=release, text=True).strip()
    result = _run(
        "preflight",
        HOME=str(fake_home),
        STEEL_RAG_REPO_DIR=str(release),
        STEEL_RAG_ENV_FILE=str(env_file),
        STEEL_RAG_EXPECTED_GIT_SHA=sha,
    )

    assert result.returncode != 0
    assert "release must be an exact detached checkout" in result.stderr
