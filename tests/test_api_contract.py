from __future__ import annotations

import json
from pathlib import Path

from pocketsteel.answering import VALID_MODES


FIXTURE = Path("tests/fixtures/api_contract_mock_response.json")


def test_api_contract_fixture_matches_required_shapes() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    search = payload["searchResponse"]
    answer = payload["answerResponse"]

    assert set(search) == {"query", "results", "warnings"}
    assert set(search["results"][0]) == {
        "score",
        "excerpt",
        "source_system",
        "forum_name",
        "thread_title",
        "thread_url",
        "chunk_id",
        "post_uid",
        "source_kind",
        "forum_id",
        "legacy_forum_number",
        "thread_id",
        "legacy_thread_uid",
        "thread_category",
        "thread_quality_score",
        "chunk_index",
        "warnings",
    }

    assert answer["mode"] in VALID_MODES
    assert set(answer) == {"answer", "mode", "sources", "warnings", "sections"}
    assert set(answer["sources"][0]) == {"title", "forumName", "url", "excerpt", "score", "chunkId", "postUid"}
    assert set(answer["sections"][0]) == {"title", "style", "body"}
