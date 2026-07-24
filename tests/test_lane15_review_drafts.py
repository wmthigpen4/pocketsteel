from __future__ import annotations

import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from pocketsteel.amazing_tablature_extraction import ExtractionWorkflowError
from pocketsteel.lane15_review_drafts import (
    harden_review_console,
    load_review_draft,
    make_durable_review_http_server,
    store_review_draft,
)


PACKET_DIGEST = "a" * 64
BATCH_ID = "lane15-sealed-ground-truth-test-main"


def _payload() -> dict[str, object]:
    return {
        "reviewType": "combined_score_tab",
        "batchId": BATCH_ID,
        "partition": "discovery",
        "packetDigest": PACKET_DIGEST,
        "decisions": {
            "input-0001:score-system-1": {
                "status": "tab_pitch_hypothesis_matches",
                "comment": None,
                "tabConfirmed": True,
            }
        },
    }


def test_review_draft_round_trips_as_non_ground_truth(tmp_path: Path) -> None:
    result = store_review_draft(tmp_path, _payload())

    assert result["status"] == "draft_saved"
    assert result["decisionCount"] == 1
    stored = load_review_draft(
        tmp_path,
        review_type="combined_score_tab",
        batch_id=BATCH_ID,
        packet_digest=PACKET_DIGEST,
    )
    assert stored is not None
    assert stored["status"] == "draft_not_submitted"
    assert stored["trainingEligible"] is False
    assert stored["evaluationEligible"] is False
    assert stored["decisions"] == _payload()["decisions"]
    draft_files = list((tmp_path / "review-drafts").rglob("*.json"))
    assert len(draft_files) == 1
    assert draft_files[0].stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("batchId", "../escape"),
        ("packetDigest", "not-a-digest"),
        ("reviewType", "unknown_review"),
        ("partition", "sealed-test"),
    ],
)
def test_review_draft_rejects_invalid_identity(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    payload = _payload()
    payload[field] = value
    with pytest.raises(ExtractionWorkflowError):
        store_review_draft(tmp_path, payload)


def test_harden_review_console_is_idempotent(tmp_path: Path) -> None:
    console = tmp_path / "review.html"
    console.write_text(
        "<!doctype html><body><script>const key='x';</script></body></html>",
        encoding="utf-8",
    )

    assert harden_review_console(console) is True
    assert harden_review_console(console) is False
    html = console.read_text(encoding="utf-8")
    assert html.count("data-lane15-durable-review-draft") == 1
    assert "/__lane15_review_draft" in html


def test_durable_server_stores_and_restores_exact_draft(tmp_path: Path) -> None:
    (tmp_path / "batches").mkdir()
    server = make_durable_review_http_server(tmp_path, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    encoded = json.dumps(_payload()).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/__lane15_review_draft",
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            saved = json.load(response)
        assert response.status == 201
        assert saved["decisionCount"] == 1

        query = urllib.parse.urlencode(
            {
                "reviewType": "combined_score_tab",
                "batchId": BATCH_ID,
                "packetDigest": PACKET_DIGEST,
            }
        )
        with urllib.request.urlopen(f"{base}/__lane15_review_draft?{query}") as response:
            restored = json.load(response)
        assert response.status == 200
        assert restored["decisions"] == _payload()["decisions"]

        missing_query = urllib.parse.urlencode(
            {
                "reviewType": "combined_score_tab",
                "batchId": BATCH_ID,
                "packetDigest": "b" * 64,
            }
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"{base}/__lane15_review_draft?{missing_query}")
        assert exc_info.value.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
