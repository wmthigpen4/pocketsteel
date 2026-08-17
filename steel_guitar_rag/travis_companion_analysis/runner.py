"""Outbound-only leased-job client for the private Travis analysis machine."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .analysis import AnalysisError, analyze_project


RUNNER_TOKEN_ENV = "TRAVIS_COMPANION_RUNNER_TOKEN"


class RunnerClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _request(
        self,
        path: str,
        *,
        method: str = "GET",
        body: bytes | None = None,
        content_type: str = "application/json",
        lease_token: str | None = None,
    ) -> bytes:
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": content_type}
        if lease_token:
            headers["X-Job-Lease"] = lease_token
        request = Request(
            f"{self.base_url}{path}",
            method=method,
            data=body,
            headers=headers,
        )
        with urlopen(request, timeout=120) as response:
            return response.read()

    def claim(self) -> dict[str, Any] | None:
        try:
            response = self._request("/api/runner/jobs/claim", method="POST")
        except HTTPError as exc:
            if exc.code == 204:
                return None
            raise
        if not response:
            return None
        payload = json.loads(response)
        return payload.get("job")

    def fetch_json(self, path: str, *, lease_token: str) -> dict[str, Any]:
        return json.loads(self._request(path, lease_token=lease_token))

    def download(self, path: str, destination: Path, *, lease_token: str) -> str:
        payload = self._request(path, lease_token=lease_token)
        destination.write_bytes(payload)
        return hashlib.sha256(payload).hexdigest()

    def upload_artifact(self, job_id: str, name: str, payload: bytes, *, lease_token: str) -> dict[str, Any]:
        return json.loads(
            self._request(
                f"/api/runner/jobs/{job_id}/artifacts/{name}",
                method="PUT",
                body=payload,
                content_type="application/json",
                lease_token=lease_token,
            )
        )

    def renew(self, job_id: str, *, lease_token: str) -> None:
        self._request(f"/api/runner/jobs/{job_id}/renew", method="POST", body=b"{}", lease_token=lease_token)

    def progress(self, job_id: str, progress: float, message: str, *, lease_token: str) -> None:
        body = json.dumps({"progress": progress, "message": message}).encode()
        self._request(f"/api/runner/jobs/{job_id}/progress", method="POST", body=body, lease_token=lease_token)

    def complete(self, job_id: str, result_key: str, source_hashes: dict[str, str], *, lease_token: str) -> None:
        body = json.dumps({"resultKey": result_key, "sourceHashes": source_hashes}).encode()
        self._request(f"/api/runner/jobs/{job_id}/complete", method="POST", body=body, lease_token=lease_token)

    def fail(self, job_id: str, message: str, *, retryable: bool, lease_token: str) -> None:
        body = json.dumps({"error": message[:500], "retryable": retryable}).encode()
        self._request(f"/api/runner/jobs/{job_id}/fail", method="POST", body=body, lease_token=lease_token)


def run_once(client: RunnerClient) -> bool:
    job = client.claim()
    if not job:
        return False
    job_id = str(job["id"])
    lease_token = str(job["leaseToken"])
    stop_renewal = threading.Event()

    def renew_lease() -> None:
        while not stop_renewal.wait(120):
            try:
                client.renew(job_id, lease_token=lease_token)
            except Exception:
                return

    renewal = threading.Thread(target=renew_lease, name=f"travis-lease-{job_id[:8]}", daemon=True)
    renewal.start()
    try:
        client.progress(job_id, 0.05, "Claimed private analysis job.", lease_token=lease_token)
        draft = client.fetch_json(f"/api/runner/jobs/{job_id}/draft", lease_token=lease_token)
        with tempfile.TemporaryDirectory(prefix=f"travis-job-{job_id[:8]}-") as temp_dir:
            root = Path(temp_dir)
            video = root / "lesson-video"
            primary = root / "primary-track.mp3"
            hashes = {
                "lessonVideo": client.download(f"/api/runner/jobs/{job_id}/assets/{job['videoAssetId']}", video, lease_token=lease_token),
                "primaryTrack": client.download(f"/api/runner/jobs/{job_id}/assets/{job['primaryTrackAssetId']}", primary, lease_token=lease_token),
            }
            client.progress(job_id, 0.2, "Decoded and fingerprinted source media.", lease_token=lease_token)
            result = analyze_project(draft, video_path=video, primary_track_path=primary)
            result["analysis"]["sourceHashes"] = hashes
            waveform = result.pop("_derivedWaveform")
            waveform_artifact = client.upload_artifact(
                job_id,
                "primary-waveform.json",
                (json.dumps(waveform, separators=(",", ":")) + "\n").encode(),
                lease_token=lease_token,
            )
            result["analysis"]["derivedArtifacts"] = {"primaryWaveform": waveform_artifact["key"]}
            artifact = client.upload_artifact(
                job_id,
                "review-draft.json",
                (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode(),
                lease_token=lease_token,
            )
            client.progress(job_id, 0.95, "Uploaded review draft.", lease_token=lease_token)
            client.complete(job_id, str(artifact["key"]), hashes, lease_token=lease_token)
    except (AnalysisError, ValueError) as exc:
        client.fail(job_id, str(exc), retryable=False, lease_token=lease_token)
    except Exception:
        client.fail(job_id, "The private analysis runner failed before producing a review draft.", retryable=True, lease_token=lease_token)
    finally:
        stop_renewal.set()
        renewal.join(timeout=1)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=10.0)
    args = parser.parse_args()
    token = os.environ.get(RUNNER_TOKEN_ENV, "").strip()
    if not token:
        raise SystemExit(f"Set {RUNNER_TOKEN_ENV} in the private runner environment.")
    client = RunnerClient(args.base_url, token)
    while True:
        worked = run_once(client)
        if args.once:
            return 0
        if not worked:
            time.sleep(max(1.0, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
