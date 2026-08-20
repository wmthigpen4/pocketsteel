from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock

import numpy as np

from steel_guitar_rag.chord_reader import dasheng


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _fake_snapshot(root: Path) -> Path:
    revision = "1" * 40
    files = {
        "config.json": json.dumps(
            {
                "architectures": ["DashengModel"],
                "encoder_kwargs": {
                    "depth": 12,
                    "embed_dim": 768,
                    "num_heads": 12,
                    "patch_size": [64, 4],
                    "patch_stride": [64, 4],
                    "target_length": 1008,
                },
                "loss": "BCELoss",
                "model_type": "dasheng",
                "name": "dasheng-base",
            },
            sort_keys=True,
        ).encode(),
        "configuration_dasheng.py": b"class DashengConfig: pass\n",
        "feature_extraction_dasheng.py": b"class DashengFeatureExtractor: pass\n",
        "modeling_dasheng.py": b"class DashengModel: pass\n",
        "preprocessor_config.json": json.dumps(
            {"feature_size": 64, "hop_size": 160, "sampling_rate": 16000},
            sort_keys=True,
        ).encode(),
        "model.safetensors": b"sealed-test-checkpoint",
    }
    for relative, payload in files.items():
        (root / relative).write_bytes(payload)
    contract = {
        "schemaVersion": "chord_reader_dasheng_snapshot_v1",
        "featureKind": "dasheng_base_v1",
        "modelId": "mispeech/dasheng-base",
        "revision": revision,
        "license": {
            "spdx": "Apache-2.0",
            "modelCardUrl": "https://example.test/model-card",
            "upstreamLicenseUrl": "https://example.test/license",
        },
        "sampleRate": 16000,
        "nativeFrameSeconds": 0.04,
        "frameSeconds": 0.1,
        "featureCount": 768,
        "pooling": "interval_overlap_mean_v1",
        "timestampConvention": "left_edge_seconds_v1",
        "files": [
            {
                "path": relative,
                "bytes": len(payload),
                "sha256": _sha256(payload),
                "sourceUrl": (
                    f"https://huggingface.co/mispeech/dasheng-base/resolve/{revision}/{relative}"
                ),
            }
            for relative, payload in sorted(files.items())
        ],
    }
    contract_path = root.parent / "dasheng-test-contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    return contract_path


class DashengSnapshotTests(unittest.TestCase):
    def test_checked_in_contract_is_immutable_and_commercially_permissive(self) -> None:
        contract = dasheng.load_dasheng_contract()
        self.assertEqual(contract["revision"], "d29a721c75b996ffa49e2a1f985349d191a4ae5e")
        self.assertEqual(contract["license"]["spdx"], "Apache-2.0")
        self.assertEqual({item["path"] for item in contract["files"]}, dasheng.DASHENG_REQUIRED_FILES)
        for item in contract["files"]:
            self.assertEqual(len(item["sha256"]), 64)
            self.assertIn(f"/resolve/{contract['revision']}/", item["sourceUrl"])
        checkpoint = next(item for item in contract["files"] if item["path"] == "model.safetensors")
        self.assertEqual(checkpoint["bytes"], 341_807_392)
        self.assertEqual(
            checkpoint["sha256"],
            "adaa439ebec13933501242364a29b7912c2695d0354061b278c873438b2736c3",
        )

    def test_snapshot_verification_retains_only_hash_verified_code_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "snapshot"
            root.mkdir()
            contract_path = _fake_snapshot(root)
            verified = dasheng.verify_dasheng_snapshot(root, contract_path)
            self.assertEqual(verified.root, root.resolve())
            self.assertEqual(
                set(verified.file_bytes),
                {
                    "config.json",
                    "configuration_dasheng.py",
                    "feature_extraction_dasheng.py",
                    "modeling_dasheng.py",
                    "preprocessor_config.json",
                },
            )
            self.assertNotIn("model.safetensors", verified.file_bytes)

    def test_snapshot_verification_rejects_tampering_before_runtime_load(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "snapshot"
            root.mkdir()
            contract_path = _fake_snapshot(root)
            (root / "modeling_dasheng.py").write_bytes(b"print('tampered')\n")
            with mock.patch.object(dasheng, "_load_verified_runtime") as runtime_loader:
                with self.assertRaisesRegex(dasheng.DashengSnapshotError, "size mismatch|SHA-256 mismatch"):
                    dasheng.DashengBaseFeatureExtractor(root, contract_path=contract_path)
            runtime_loader.assert_not_called()

    def test_snapshot_verification_rejects_unallowlisted_active_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "snapshot"
            root.mkdir()
            contract_path = _fake_snapshot(root)
            (root / "surprise.py").write_text("raise RuntimeError\n", encoding="utf-8")
            with self.assertRaisesRegex(dasheng.DashengSnapshotError, "Unallowlisted"):
                dasheng.verify_dasheng_snapshot(root, contract_path)

    def test_offline_loader_blocks_sockets_and_restores_environment(self) -> None:
        previous = os.environ.get("HF_HUB_OFFLINE")
        with dasheng._network_disabled():
            self.assertEqual(os.environ["HF_HUB_OFFLINE"], "1")
            sock = socket.socket()
            try:
                with self.assertRaisesRegex(RuntimeError, "Network access is disabled"):
                    sock.connect(("127.0.0.1", 9))
            finally:
                sock.close()
        self.assertEqual(os.environ.get("HF_HUB_OFFLINE"), previous)


class DashengGridTests(unittest.TestCase):
    def test_overlap_pooling_has_exact_values_timestamps_and_frame_count(self) -> None:
        native = np.repeat(np.arange(7, dtype=np.float32)[:, None], 768, axis=1)
        features, timestamps = dasheng.pool_dasheng_embeddings(native, 0.26)
        self.assertEqual(features.shape, (3, 768))
        np.testing.assert_array_equal(timestamps, np.array([0.0, 0.1, 0.2]))
        np.testing.assert_allclose(features[:, 0], np.array([0.8, 3.2, 16 / 3]), rtol=0, atol=1e-6)

    def test_grid_uses_existing_ceil_duration_contract(self) -> None:
        native = np.zeros((26, 768), dtype=np.float32)
        features, timestamps = dasheng.pool_dasheng_embeddings(native, 1.01)
        self.assertEqual(features.shape, (11, 768))
        self.assertEqual(timestamps[-1], 1.0)

    def test_pooling_is_byte_deterministic(self) -> None:
        random = np.random.default_rng(991)
        native = random.standard_normal((31, 768), dtype=np.float32)
        first_features, first_times = dasheng.pool_dasheng_embeddings(native, 1.21)
        second_features, second_times = dasheng.pool_dasheng_embeddings(native.copy(), 1.21)
        self.assertEqual(first_features.tobytes(), second_features.tobytes())
        self.assertEqual(first_times.tobytes(), second_times.tobytes())

    def test_provenance_hash_is_stable_and_covers_all_snapshot_hashes(self) -> None:
        contract = dasheng.load_dasheng_contract()
        first = dasheng.dasheng_feature_provenance(contract)
        second = dasheng.dasheng_feature_provenance(contract)
        self.assertEqual(first, second)
        self.assertEqual(len(first["provenanceSha256"]), 64)
        self.assertEqual(set(first["fileSha256"]), dasheng.DASHENG_REQUIRED_FILES)


class _FakeExtractor:
    def __init__(self) -> None:
        self.provenance = dasheng.dasheng_feature_provenance(dasheng.load_dasheng_contract())

    def extract(self, audio: Path) -> dasheng.DashengFeatureBatch:
        marker = int(audio.stem.rsplit("-", 1)[-1]) if "-" in audio.stem else 0
        features = np.full((3, 768), marker, dtype=np.float32)
        return dasheng.DashengFeatureBatch(
            features=features,
            timestamps_seconds=np.array([0.0, 0.1, 0.2]),
            duration_seconds=0.25,
            provenance=self.provenance,
        )


class DashengPilotTests(unittest.TestCase):
    def test_one_and_ten_track_pilots_are_bounded_and_hash_features(self) -> None:
        tracks = [{"id": f"track-{index}", "audioPath": f"/tmp/audio-{index}.wav"} for index in range(10)]
        extractor = _FakeExtractor()
        one = dasheng.run_dasheng_one_track_pilot(tracks, extractor=extractor)
        ten = dasheng.run_dasheng_ten_track_pilot(tracks, extractor=extractor)
        self.assertEqual(one["processedTracks"], 1)
        self.assertEqual(ten["processedTracks"], 10)
        self.assertEqual(ten["totalAudioSeconds"], 2.5)
        self.assertEqual(ten["tracks"][0]["frames"], 3)
        self.assertEqual(ten["tracks"][0]["featureCount"], 768)
        expected = dasheng.DashengFeatureBatch(
            features=np.zeros((3, 768), dtype=np.float32),
            timestamps_seconds=np.array([0.0, 0.1, 0.2]),
            duration_seconds=0.25,
            provenance=extractor.provenance,
        ).feature_sha256
        self.assertEqual(ten["tracks"][0]["featureSha256"], expected)

    def test_pilot_refuses_any_limit_that_could_start_a_corpus_run(self) -> None:
        tracks = [{"id": "one", "audioPath": "/tmp/one.wav"}]
        with self.assertRaisesRegex(ValueError, "exactly 1 or 10"):
            dasheng.run_dasheng_pilot(tracks, limit=11, extractor=_FakeExtractor())
        with self.assertRaisesRegex(ValueError, "received only"):
            dasheng.run_dasheng_ten_track_pilot(tracks, extractor=_FakeExtractor())


@unittest.skipUnless(os.environ.get("DASHENG_SNAPSHOT_ROOT"), "set DASHENG_SNAPSHOT_ROOT for sealed integration")
class DashengSnapshotIntegrationTests(unittest.TestCase):
    def test_real_checkpoint_is_deterministic_on_a_synthetic_song_excerpt(self) -> None:
        sample_rate = dasheng.DASHENG_SAMPLE_RATE
        timestamps = np.arange(round(0.41 * sample_rate), dtype=np.float32) / sample_rate
        waveform = (
            0.2 * np.sin(2 * np.pi * 220 * timestamps)
            + 0.15 * np.sin(2 * np.pi * 277.1826 * timestamps)
            + 0.1 * np.sin(2 * np.pi * 329.6276 * timestamps)
        ).astype(np.float32)
        extractor = dasheng.DashengBaseFeatureExtractor(Path(os.environ["DASHENG_SNAPSHOT_ROOT"]))
        first = extractor.extract_waveform(waveform)
        second = extractor.extract_waveform(waveform)
        self.assertEqual(first.features.shape, (5, 768))
        np.testing.assert_array_equal(first.timestamps_seconds, np.arange(5) * 0.1)
        self.assertEqual(first.features.tobytes(), second.features.tobytes())
        self.assertEqual(first.feature_sha256, second.feature_sha256)


if __name__ == "__main__":
    unittest.main()
