from __future__ import annotations

import hashlib
import json
import os
import plistlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.verify_canonical_frontier_service import verify_bundle


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "deploy/macos/run-canonical-frontier-service.sh"
PLIST = ROOT / "deploy/macos/com.steelguitarrag.canonical-frontier.plist.template"
INSTALLER = ROOT / "deploy/macos/install-canonical-frontier-launchdaemon.sh"
USER_PLIST = ROOT / "deploy/macos/com.steelguitarrag.canonical-frontier.launchagent.plist.template"
USER_INSTALLER = ROOT / "deploy/macos/install-canonical-frontier-launchagent.sh"
REAL_SERVICE_ROOT = Path(
    os.environ.get(
        "STEEL_RAG_TEST_CANONICAL_FRONTIER_SERVICE_ROOT",
        Path.home() / ".steel-rag/services/canonical-frontier-v1034-fallback-20260806",
    )
).expanduser()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CanonicalFrontierServiceBundleTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        candidate_path = root / "rag-evaluation/audit/canonical-frontier-implementation-ready-v931.json"
        index_root = root / "rag-evaluation/index/steel-forum-passages-v1-hybrid-v1"
        tiered_path = root / "rag-evaluation/training/canonical-tiered-reranker-grid-policy-v856.json"
        lexical = index_root / "lexical.sqlite3"
        vector = index_root / "vector"
        group = index_root / "group-expansion-v1.sqlite3"
        for directory in (candidate_path.parent, index_root, tiered_path.parent, vector):
            directory.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(json.dumps({
            "status": "owner_corrected_default_off_candidate_implementation_ready",
            "protected_holdout_cases_used": 0,
            "runtime_activation_authorized": False,
            "deployment_authorized": False,
            "confirmed_corrected_answer": {"checks": {"owner_correction": True}},
        }), encoding="utf-8")
        lexical.write_bytes(b"sqlite")
        group.write_bytes(b"sqlite")
        (index_root / "manifest.json").write_text(json.dumps({
            "status": "ready",
            "corpus_version": "steel-forum-passages-v1",
            "source_id_scheme": "steel-passage-v1",
            "protected_holdout_used": False,
            "lexical": {"count": 1, "database": str(lexical)},
            "vector": {"count": 1, "path": str(vector)},
        }), encoding="utf-8")
        (index_root / "vector-embedding-progress.json").write_text(json.dumps({
            "expected_passages": 1,
            "processed_passages": 1,
            "collection_count": 1,
            "protected_holdout_cases_used": 0,
        }), encoding="utf-8")
        tiered_path.write_text(json.dumps({
            "group_expansion_index": str(group),
        }), encoding="utf-8")
        entrypoint = root / "canonical_frontier_http_api_v2.py"
        entrypoint.write_text("# fixture\n", encoding="utf-8")
        required_paths = [
            candidate_path,
            index_root / "manifest.json",
            index_root / "vector-embedding-progress.json",
            tiered_path,
            entrypoint,
        ]
        for index in range(45):
            path = root / f"module_{index:02d}.py"
            path.write_text(f"# {index}\n", encoding="utf-8")
            required_paths.append(path)
        manifest = root / "bundle.json"
        manifest.write_text(json.dumps({
            "schema_version": 1,
            "bundle_version": "canonical-frontier-service-bundle-v1034",
            "service_entrypoint": "canonical_frontier_http_api_v2.py",
            "candidate": str(candidate_path.relative_to(root)),
            "expected_index_passages": 1,
            "required_files": {
                str(path.relative_to(root)): digest(path) for path in required_paths
            },
        }), encoding="utf-8")
        return manifest

    def test_complete_bundle_verifies_without_activation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = verify_bundle(root, self.fixture(root))
            self.assertEqual(result["status"], "canonical_frontier_service_bundle_verified")
            self.assertEqual(result["verified_files"], 50)
            self.assertFalse(result["runtime_activation_authorized"])

    def test_modified_runtime_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.fixture(root)
            (root / "module_00.py").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                verify_bundle(root, manifest)

    def test_path_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = self.fixture(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["required_files"]["../outside.py"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsafe bundle path"):
                verify_bundle(root, manifest_path)


class CanonicalFrontierLaunchFilesTests(unittest.TestCase):
    def test_wrapper_has_valid_shell_syntax(self) -> None:
        for path in (WRAPPER, INSTALLER, USER_INSTALLER):
            result = subprocess.run(
                ["bash", "-n", str(path)], capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrapper_verifies_before_start_and_rejects_non_loopback(self) -> None:
        source = WRAPPER.read_text(encoding="utf-8")
        self.assertIn('== "127.0.0.1"', source)
        self.assertLess(source.index("--service-root"), source.index("exec \"$STEEL_RAG_CANONICAL_FRONTIER_PYTHON\""))
        self.assertNotIn("echo $STEEL_RAG_CANONICAL_FRONTIER_TOKEN", source)
        self.assertIn('HF_HUB_OFFLINE="1"', source)
        self.assertIn('TRANSFORMERS_OFFLINE="1"', source)
        self.assertIn('STEEL_RAG_CANONICAL_FRONTIER_RUNTIME_VERSION="v1034"', source)
        self.assertIn('STEEL_RAG_CANONICAL_FRONTIER_WARMUP_ROUNDS="2"', source)

    def test_plist_contains_no_secret_values_or_public_binding(self) -> None:
        for path in (PLIST, USER_PLIST):
            raw = path.read_bytes()
            value = plistlib.loads(raw)
            environment = value["EnvironmentVariables"]
            self.assertEqual(environment["STEEL_RAG_CANONICAL_FRONTIER_HOST"], "127.0.0.1")
            self.assertNotIn("STEEL_RAG_CANONICAL_FRONTIER_TOKEN", environment)
            self.assertNotIn("OPENAI_API_KEY", environment)

    def test_user_launchagent_documents_keychain_boundary(self) -> None:
        source = USER_INSTALLER.read_text(encoding="utf-8")
        self.assertIn("login Keychain", source)
        self.assertIn('gui/$(id -u)', source)
        self.assertNotIn("sudo ", source)

    def installer_env(self, temporary: Path) -> dict[str, str]:
        env_file = temporary / "private-preview.env"
        env_file.write_text(
            "STEEL_RAG_CANONICAL_FRONTIER_TOKEN=test-only-token\n",
            encoding="utf-8",
        )
        return {
            **os.environ,
            "STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT": str(REAL_SERVICE_ROOT),
            "STEEL_RAG_CANONICAL_FRONTIER_PYTHON": "/usr/bin/python3",
            "STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE": str(env_file),
            "STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR": str(temporary / "logs"),
            "STEEL_RAG_CANONICAL_FRONTIER_INSTALL_DIR": str(temporary / "installed"),
            "STEEL_RAG_CANONICAL_FRONTIER_PLIST_PATH": str(temporary / "service.plist"),
        }

    @unittest.skipUnless(REAL_SERVICE_ROOT.is_dir(), "local frozen service bundle is unavailable")
    def test_installer_render_and_preflight_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            env = self.installer_env(temporary)
            rendered = subprocess.run(
                [str(INSTALLER), "render"], env=env,
                capture_output=True, text=True,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            plist = plistlib.loads(rendered.stdout.encode("utf-8"))
            self.assertEqual(plist["EnvironmentVariables"]["STEEL_RAG_CANONICAL_FRONTIER_HOST"], "127.0.0.1")
            self.assertNotIn("__STEEL_RAG_", rendered.stdout)
            preflight = subprocess.run(
                [str(INSTALLER), "preflight"], env=env,
                capture_output=True, text=True,
            )
            self.assertEqual(preflight.returncode, 0, preflight.stderr)
            self.assertIn("no state changed", preflight.stdout)
            self.assertFalse((temporary / "service.plist").exists())

    @unittest.skipUnless(REAL_SERVICE_ROOT.is_dir(), "local frozen service bundle is unavailable")
    def test_installer_rejects_non_loopback_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env = self.installer_env(Path(directory))
            env["STEEL_RAG_CANONICAL_FRONTIER_HOST"] = "0.0.0.0"
            result = subprocess.run(
                [str(INSTALLER), "preflight"], env=env,
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-loopback", result.stderr)


if __name__ == "__main__":
    unittest.main()
