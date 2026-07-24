from __future__ import annotations

import threading
import time
from typing import Any

from steel_guitar_rag.score_import_jobs import JOB_SCHEMA_VERSION, ScoreImportJobManager


def _wait_for_terminal(manager: ScoreImportJobManager, job_id: str) -> dict[str, Any]:
    for _ in range(100):
        job = manager.snapshot(job_id)
        if job and job["status"] in {"complete", "failed"}:
            return job
        time.sleep(0.005)
    raise AssertionError("job did not finish")


def test_score_import_job_reports_real_page_progress_without_exposing_source() -> None:
    release_second_page = threading.Event()
    first_page_complete = threading.Event()

    def importer(payload: dict[str, Any], *, progress_callback: Any) -> dict[str, Any]:
        assert payload["contentBase64"] == "private-source-bytes"
        progress_callback(2, 1, 2)
        first_page_complete.set()
        assert release_second_page.wait(timeout=1)
        progress_callback(4, 2, 2)
        return {
            "source": {"selectedPages": [2, 4], "retained": False},
            "score": {"melody": [{"pitch": "G4"}]},
        }

    manager = ScoreImportJobManager(importer=importer)
    started = manager.start(
        {
            "sourceType": "pdf",
            "selectedPages": [2, 4],
            "contentBase64": "private-source-bytes",
        }
    )
    assert started["schemaVersion"] == JOB_SCHEMA_VERSION
    assert "contentBase64" not in started
    assert first_page_complete.wait(timeout=1)
    running = manager.snapshot(started["jobId"])
    assert running is not None
    assert running["status"] == "running"
    assert running["completedPages"] == 1
    assert running["currentPage"] == 2
    assert "contentBase64" not in running

    release_second_page.set()
    complete = _wait_for_terminal(manager, started["jobId"])
    assert complete["status"] == "complete"
    assert complete["completedPages"] == 2
    assert complete["result"]["source"]["retained"] is False
    assert "contentBase64" not in complete["result"]


def test_score_import_job_hides_unexpected_internal_errors() -> None:
    def importer(_payload: dict[str, Any], *, progress_callback: Any) -> dict[str, Any]:
        del progress_callback
        raise RuntimeError("secret backend detail")

    manager = ScoreImportJobManager(importer=importer)
    started = manager.start({"sourceType": "image", "contentBase64": "private"})
    failed = _wait_for_terminal(manager, started["jobId"])
    assert failed["status"] == "failed"
    assert failed["error"] == "Score recognition failed before a reviewable draft was produced."
