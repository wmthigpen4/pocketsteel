"""Short-lived in-memory jobs for page-by-page printed-score recognition."""

from __future__ import annotations

import secrets
import threading
import time
from typing import Any, Callable, Mapping


JOB_SCHEMA_VERSION = "score_import_job_v1"
JOB_TTL_SECONDS = 10 * 60


class ScoreImportJobManager:
    """Run OMR outside the request thread without persisting source bytes."""

    def __init__(
        self,
        *,
        importer: Callable[..., dict[str, Any]],
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._importer = importer
        self._clock = clock
        self._lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}

    def start(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        self._cleanup()
        job_id = secrets.token_urlsafe(24)
        selected_pages = [
            int(page) for page in payload.get("selectedPages", []) if str(page).isdigit()
        ]
        page_count = len(selected_pages) or 1
        now = self._clock()
        with self._lock:
            self._jobs[job_id] = {
                "schemaVersion": JOB_SCHEMA_VERSION,
                "jobId": job_id,
                "status": "queued",
                "pageCount": page_count,
                "completedPages": 0,
                "currentPage": None,
                "createdAt": now,
                "updatedAt": now,
            }
        source_payload = dict(payload)
        worker = threading.Thread(
            target=self._run,
            args=(job_id, source_payload),
            name=f"score-import-{job_id[:8]}",
            daemon=True,
        )
        worker.start()
        return self.snapshot(job_id) or {}

    def snapshot(self, job_id: str) -> dict[str, Any] | None:
        self._cleanup()
        with self._lock:
            job = self._jobs.get(str(job_id))
            if job is None:
                return None
            return {
                key: value
                for key, value in job.items()
                if key not in {"createdAt", "updatedAt"}
            }

    def _run(self, job_id: str, payload: dict[str, Any]) -> None:
        self._update(job_id, status="running")

        def progress(page_number: int, completed_pages: int, page_count: int) -> None:
            self._update(
                job_id,
                status="running",
                currentPage=page_number,
                completedPages=completed_pages,
                pageCount=page_count,
            )

        try:
            result = self._importer(payload, progress_callback=progress)
        except Exception as exc:
            safe_error = (
                str(exc)[:500]
                if exc.__class__.__name__ in {"MelodyImportError", "MelodyImportTooLargeError", "ScoreOmrError"}
                else "Score recognition failed before a reviewable draft was produced."
            )
            self._update(job_id, status="failed", error=safe_error)
        else:
            selected_pages = result.get("source", {}).get("selectedPages", [])
            completed_pages = len(selected_pages) or 1
            self._update(
                job_id,
                status="complete",
                completedPages=completed_pages,
                pageCount=completed_pages,
                currentPage=None,
                result=result,
            )
        finally:
            payload.clear()

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.update(changes)
            job["updatedAt"] = self._clock()

    def _cleanup(self) -> None:
        cutoff = self._clock() - JOB_TTL_SECONDS
        with self._lock:
            expired = [
                job_id
                for job_id, job in self._jobs.items()
                if job["updatedAt"] < cutoff and job["status"] in {"complete", "failed"}
            ]
            for job_id in expired:
                del self._jobs[job_id]
