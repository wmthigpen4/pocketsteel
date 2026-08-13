#!/usr/bin/env python3
"""Run the frozen 752-question campaign with zero-network Terra/Luna fixtures."""

from __future__ import annotations

import argparse
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.run_answer_eval import load_question_bank
from scripts.run_exploratory_answer_smoke import built_in_questions
from steel_guitar_rag.access_control import DEV_ACCESS_ROLE_ENVIRON
from steel_guitar_rag.api import create_app


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_QUESTIONS = 752


class FixtureSearchIndex:
    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        safe_query = " ".join(query.split())[:500]
        return {
            "results": [{
                "score": 0.95,
                "excerpt": (
                    f"Steel Guitar Forum contributors discussed {safe_query} in pedal-steel "
                    "context, including practical setup and playing details."
                ),
                "source_system": "sgf_phpbb_current",
                "forum_name": "Fixture Steel Guitar Forum",
                "thread_title": safe_query or "Fixture discussion",
                "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=752",
                "chunk_id": "sgf:fixture:752",
                "post_uid": "sgf:post:fixture:752",
            }],
            "warnings": [],
        }


class FixtureTerraLunaFrontier:
    """A contract fixture, not a model or Responses API client."""

    def __init__(self) -> None:
        self.terra_calls = 0
        self.luna_calls = 0

    def readiness(self, *, timeout_seconds: float = 1.0) -> dict[str, Any]:
        del timeout_seconds
        return {"status": "ready", "reason": "fixture_ready", "http_status": 200}

    def answer(
        self,
        question: str,
        *,
        conversation_context: list[str] | None = None,
    ) -> dict[str, Any]:
        del question, conversation_context
        self.terra_calls += 1
        self.luna_calls += 1
        claim = (
            "Fixture Forum Author reported that the cited public SGF passage directly "
            "discusses the requested steel-guitar topic."
        )
        return {
            "schema_version": 1,
            "mode": "complete",
            "answer": claim,
            "claims": [{
                "claim_id": "fixture-c1",
                "text": claim,
                "source_ids": ["steel-passage-v1:fixture-752"],
                "support_mode": "independent_relevance_entailment_verifier",
            }],
            "sources": [{
                "source_id": "steel-passage-v1:fixture-752",
                "chunk_id": "steel-passage-v1:fixture-752",
                "post_uid": "sgf:post:fixture:752",
                "thread_title": "Fixture source-backed answer",
                "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=752",
                "forum_name": "Fixture Steel Guitar Forum",
                "excerpt": "A public SGF fixture passage directly discusses this steel-guitar topic.",
                "score": 0.95,
                "warnings": [],
            }],
            "coverage": [],
            "response_note": "",
            "metadata": {
                "delivery_mode": "verified_synthesis",
                "primary_model": "gpt-5.6-terra-fixture",
                "verifier_model": "gpt-5.6-luna-fixture",
            },
        }


class FixtureRateLimiter:
    def check(self, key: str) -> Any:
        del key
        return type("Decision", (), {
            "allowed": True,
            "error": "",
            "retry_after_seconds": 0,
        })()


def campaign_questions() -> list[dict[str, str]]:
    exploratory = [
        {"id": f"exploratory:{row.id}", "category": row.category, "question": row.question}
        for row in built_in_questions()
    ]
    evaluator = [
        {**row, "id": f"evaluator:{index:03d}:{row['id']}"}
        for index, row in enumerate(
            load_question_bank(ROOT / "tests/fixtures/user_question_bank.json"), 1
        )
    ]
    broad = []
    for line in (ROOT / "tests/answer_eval/question_bank.jsonl").read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        broad.append({
            "id": f"broad:{row['id']}",
            "category": str(row.get("bucket") or "broad_contract"),
            "question": str(row["question"]),
        })
    combined = [*exploratory, *evaluator, *broad]
    if len(exploratory) != 193 or len(evaluator) != 295 or len(broad) != 264:
        raise ValueError("The frozen 193 + 295 + 264 campaign inputs have changed.")
    if len(combined) != EXPECTED_QUESTIONS:
        raise ValueError("The fixture campaign must contain exactly 752 prompts.")
    return combined


def call_answer(app: Any, question: str) -> tuple[int, dict[str, Any]]:
    body = json.dumps({"question": question, "mode": "ask"}).encode("utf-8")
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        del headers
        captured["status"] = int(status.split()[0])

    raw = b"".join(app({
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/api/answer",
        "QUERY_STRING": "",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        DEV_ACCESS_ROLE_ENVIRON: "beta_user",
    }, start_response))
    return int(captured["status"]), json.loads(raw)


def run_campaign() -> dict[str, Any]:
    frontier = FixtureTerraLunaFrontier()
    app = create_app(
        FixtureSearchIndex(),
        answer_auth_mode="local_dev",
        canonical_frontier_enabled=True,
        canonical_frontier_client=frontier,
        melody_exercise_enabled=False,
        melody_import_enabled=False,
        song_practice_enabled=False,
        account_copedents_enabled=False,
        account_usage_enabled=False,
        answer_rate_limiter=FixtureRateLimiter(),
    )
    rows = campaign_questions()
    status_counts: Counter[int] = Counter()
    provenance_counts: Counter[str] = Counter()
    failures: list[dict[str, Any]] = []
    for row in rows:
        status, payload = call_answer(app, row["question"])
        status_counts[status] += 1
        provenance = payload.get("answer_provenance") or {}
        provenance_counts[str(provenance.get("kind") or "none")] += 1
        if status != 200 or not str(payload.get("answer") or "").strip():
            failures.append({
                "id": row["id"],
                "status": status,
                "error": str(payload.get("error") or "")[:160],
            })
    if frontier.terra_calls != frontier.luna_calls:
        failures.append({"id": "fixture-boundary", "error": "Terra/Luna call counts differ"})
    return {
        "schema_version": 1,
        "campaign": "steel-rag-qna-752-fixture-v1",
        "questions": len(rows),
        "network_openai_requests": 0,
        "fixture_terra_calls": frontier.terra_calls,
        "fixture_luna_calls": frontier.luna_calls,
        "status_counts": dict(sorted(status_counts.items())),
        "provenance_counts": dict(sorted(provenance_counts.items())),
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=Path("/tmp/steel-rag-qna-752-fixture.json"))
    args = parser.parse_args()
    result = run_campaign()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
