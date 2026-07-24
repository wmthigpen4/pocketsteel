"""Durable, loopback-only draft capture for private Lane 15 review consoles.

This module deliberately sits outside the frozen Amazing Tablature rules
engine. Drafts are operational recovery data only: they are never submissions,
ground truth, training records, or evaluation results.
"""

from __future__ import annotations

import hashlib
import http.server
import json
import os
import re
import tempfile
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from steel_guitar_rag.amazing_tablature_extraction import (
    ExtractionWorkflowError,
    make_review_http_server,
)

_DRAFT_ENDPOINT = "/__lane15_review_draft"
_DRAFT_SCHEMA = "lane15-durable-review-draft-v1"
_MAX_DRAFT_BYTES = 5_000_000
_ALLOWED_REVIEW_TYPES = frozenset({"combined_score_tab", "validation_line_audit"})
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_HARDENER_MARKER = "lane15-durable-review-draft-v1"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _require_identifier(value: object, *, field: str) -> str:
    text = str(value or "")
    if not _SAFE_ID.fullmatch(text):
        raise ExtractionWorkflowError(f"Review draft {field} is invalid.")
    return text


def _require_digest(value: object) -> str:
    text = str(value or "")
    if not _SHA256.fullmatch(text):
        raise ExtractionWorkflowError("Review draft packetDigest must be a SHA-256 digest.")
    return text


def _draft_identity(payload: Mapping[str, Any]) -> tuple[str, str, str]:
    review_type = str(payload.get("reviewType") or "")
    if review_type not in _ALLOWED_REVIEW_TYPES:
        raise ExtractionWorkflowError("Review draft type is not supported.")
    batch_id = _require_identifier(payload.get("batchId"), field="batchId")
    packet_digest = _require_digest(payload.get("packetDigest"))
    return review_type, batch_id, packet_digest


def _draft_path(
    private_root: Path | str,
    *,
    review_type: str,
    batch_id: str,
    packet_digest: str,
) -> Path:
    identity = f"{review_type}\0{batch_id}\0{packet_digest}".encode()
    identity_digest = hashlib.sha256(identity).hexdigest()
    return (
        Path(private_root).expanduser().resolve()
        / "review-drafts"
        / identity_digest[:2]
        / f"{identity_digest}.json"
    )


def _atomic_private_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_path, 0o600)
    os.replace(temp_path, path)


def store_review_draft(
    private_root: Path | str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and atomically store one partial browser review draft."""

    review_type, batch_id, packet_digest = _draft_identity(payload)
    partition = str(payload.get("partition") or "")
    if partition not in {"discovery", "validation"}:
        raise ExtractionWorkflowError("Review draft partition is invalid.")
    decisions = payload.get("decisions")
    if not isinstance(decisions, Mapping):
        raise ExtractionWorkflowError("Review draft decisions must be a JSON object.")
    if len(decisions) > 5_000:
        raise ExtractionWorkflowError("Review draft contains too many decisions.")
    for key, decision in decisions.items():
        if not isinstance(key, str) or not key or len(key) > 500:
            raise ExtractionWorkflowError("Review draft contains an invalid decision key.")
        if not isinstance(decision, Mapping):
            raise ExtractionWorkflowError("Every review draft decision must be an object.")

    updated_at = _utc_now()
    record = {
        "schemaVersion": _DRAFT_SCHEMA,
        "reviewType": review_type,
        "batchId": batch_id,
        "partition": partition,
        "packetDigest": packet_digest,
        "updatedAt": updated_at,
        "decisionCount": len(decisions),
        "decisions": dict(decisions),
        "status": "draft_not_submitted",
        "trainingEligible": False,
        "evaluationEligible": False,
    }
    path = _draft_path(
        private_root,
        review_type=review_type,
        batch_id=batch_id,
        packet_digest=packet_digest,
    )
    _atomic_private_json(path, record)
    return {
        "schemaVersion": _DRAFT_SCHEMA,
        "packetDigest": packet_digest,
        "decisionCount": len(decisions),
        "updatedAt": updated_at,
        "status": "draft_saved",
    }


def load_review_draft(
    private_root: Path | str,
    *,
    review_type: str,
    batch_id: str,
    packet_digest: str,
) -> dict[str, Any] | None:
    """Load the exact matching draft, if one exists."""

    review_type, batch_id, packet_digest = _draft_identity(
        {
            "reviewType": review_type,
            "batchId": batch_id,
            "packetDigest": packet_digest,
        }
    )
    path = _draft_path(
        private_root,
        review_type=review_type,
        batch_id=batch_id,
        packet_digest=packet_digest,
    )
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExtractionWorkflowError("Saved review draft is not a JSON object.")
    expected = (review_type, batch_id, packet_digest)
    actual = (
        str(value.get("reviewType") or ""),
        str(value.get("batchId") or ""),
        str(value.get("packetDigest") or ""),
    )
    if actual != expected:
        raise ExtractionWorkflowError("Saved review draft identity does not match its path.")
    return value


def make_durable_review_http_server(
    private_root: Path | str,
    *,
    host: str = "127.0.0.1",
    port: int = 8766,
) -> http.server.ThreadingHTTPServer:
    """Extend the frozen private review server with draft GET/POST endpoints."""

    if host not in {"127.0.0.1", "localhost"}:
        raise ExtractionWorkflowError("The private review server may bind only to loopback.")
    root = Path(private_root).expanduser().resolve()

    # Reuse the frozen server's exact static-file and final-submission behavior.
    template_server = make_review_http_server(root, host=host, port=0)
    base_handler = template_server.RequestHandlerClass
    template_server.server_close()

    class DurableReviewHandler(base_handler):  # type: ignore[misc, valid-type]
        server_version = "Lane15DurableReview/1"

        def do_GET(self) -> None:  # noqa: N802 - inherited HTTP verb naming
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path != _DRAFT_ENDPOINT:
                super().do_GET()
                return
            if self.client_address[0] not in {"127.0.0.1", "::1"}:
                self._json_response(403, {"error": "loopback_only"})
                return
            query = urllib.parse.parse_qs(parsed.query)
            try:
                draft = load_review_draft(
                    root,
                    review_type=(query.get("reviewType") or [""])[0],
                    batch_id=(query.get("batchId") or [""])[0],
                    packet_digest=(query.get("packetDigest") or [""])[0],
                )
            except (ExtractionWorkflowError, json.JSONDecodeError) as exc:
                self._json_response(
                    400,
                    {"error": "invalid_review_draft", "message": str(exc)},
                )
                return
            if draft is None:
                self._json_response(404, {"error": "review_draft_not_found"})
                return
            self._json_response(200, draft)

        def do_POST(self) -> None:  # noqa: N802 - inherited HTTP verb naming
            if urllib.parse.urlsplit(self.path).path != _DRAFT_ENDPOINT:
                super().do_POST()
                return
            if self.client_address[0] not in {"127.0.0.1", "::1"}:
                self._json_response(403, {"error": "loopback_only"})
                return
            try:
                content_length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                content_length = 0
            if content_length < 2 or content_length > _MAX_DRAFT_BYTES:
                self._json_response(413, {"error": "invalid_draft_size"})
                return
            try:
                payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
                if not isinstance(payload, Mapping):
                    raise ExtractionWorkflowError(
                        "Review draft body must be a JSON object."
                    )
                result = store_review_draft(root, payload)
            except (ExtractionWorkflowError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                self._json_response(
                    400,
                    {"error": "invalid_review_draft", "message": str(exc)},
                )
                return
            self._json_response(201, result)

    return http.server.ThreadingHTTPServer((host, port), DurableReviewHandler)


_DURABLE_CAPTURE_SCRIPT = r"""
<script data-lane15-durable-review-draft="v1">
(() => {
  const DRAFT_MARKER = 'lane15-durable-review-draft-v1';
  const RESTORED_KEY = `${DRAFT_MARKER}:${location.pathname}`;
  let captureTimer = null;
  let packetWaitCount = 0;

  function readLocalDecisions() {
    try {
      const value = JSON.parse(localStorage.getItem(key) || '{}');
      return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
    } catch (_error) {
      return {};
    }
  }

  function draftUrl() {
    const params = new URLSearchParams({
      reviewType: REVIEW_TYPE,
      batchId: packet.batchId,
      packetDigest: packet.packetDigest,
    });
    return `/__lane15_review_draft?${params.toString()}`;
  }

  function captureNow() {
    if (!packet) return;
    const local = readLocalDecisions();
    fetch('/__lane15_review_draft', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      keepalive: true,
      body: JSON.stringify({
        reviewType: REVIEW_TYPE,
        batchId: packet.batchId,
        partition: packet.partition,
        packetDigest: packet.packetDigest,
        decisions: local,
      }),
    }).catch(() => {});
  }

  function queueCapture() {
    clearTimeout(captureTimer);
    captureTimer = setTimeout(captureNow, 120);
  }

  async function initializeDurableCapture() {
    if (!packet) {
      if (packetWaitCount++ < 200) setTimeout(initializeDurableCapture, 50);
      return;
    }
    const local = readLocalDecisions();
    if (Object.keys(local).length) {
      captureNow();
      return;
    }
    try {
      const response = await fetch(draftUrl(), {cache: 'no-store'});
      if (!response.ok) return;
      const draft = await response.json();
      if (!draft.decisions || !Object.keys(draft.decisions).length) return;
      localStorage.setItem(key, JSON.stringify(draft.decisions));
      if (sessionStorage.getItem(RESTORED_KEY) !== packet.packetDigest) {
        sessionStorage.setItem(RESTORED_KEY, packet.packetDigest);
        location.reload();
      }
    } catch (_error) {}
  }

  document.addEventListener('change', queueCapture, true);
  document.addEventListener('input', queueCapture, true);
  window.addEventListener('pagehide', captureNow);
  initializeDurableCapture();
})();
</script>
"""


def harden_review_console(path: Path | str) -> bool:
    """Inject durable draft capture into one generated private review console."""

    console_path = Path(path).expanduser().resolve()
    html = console_path.read_text(encoding="utf-8")
    if _HARDENER_MARKER in html:
        return False
    if "</body>" not in html:
        raise ExtractionWorkflowError("Review console has no closing body element.")
    hardened = html.replace("</body>", f"{_DURABLE_CAPTURE_SCRIPT}</body>", 1)
    console_path.write_text(hardened, encoding="utf-8")
    return True
