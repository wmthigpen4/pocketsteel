from __future__ import annotations

from pathlib import Path
import urllib.error

import pytest

import scripts.run_semantic_answer_preview_smoke as preview_smoke
from scripts.run_semantic_answer_preview_smoke import (
    DEFAULT_BANK,
    _headers,
    load_cases,
    main,
    score_case,
)


def passing_payload(case: dict[str, object]) -> dict[str, object]:
    answer = " ".join(str(term) for term in case["required_terms"])
    answer = (answer + " " + "Useful pedal steel teaching and verification. " * 20).strip()
    if case.get("answer_must_end_with_question"):
        answer = answer.rstrip(". ") + "?"
    payload: dict[str, object] = {"answer": answer, "sources": [], "warnings": []}
    if case["expect_sources"] == "present":
        payload["sources"] = [{"title": "Supported discussion", "url": "https://example.test/source"}]
    if case["expect_fretboard"] == "present":
        payload["fretboard"] = {"positions": [{"fret": 3}]}
    return payload


def test_preview_bank_covers_all_authorities_and_required_followups() -> None:
    cases = load_cases(DEFAULT_BANK)
    assert len(cases) == 10
    assert {case["authority"] for case in cases} == {
        "deterministic",
        "semantic_teacher",
        "source_backed_rag",
        "hybrid",
        "clarify",
        "guardrail",
    }
    assert sum(bool(case.get("conversation_context")) for case in cases) >= 2


@pytest.mark.parametrize("case", load_cases(DEFAULT_BANK), ids=lambda case: str(case["id"]))
def test_preview_case_scorer_accepts_contract_conforming_payload(case: dict[str, object]) -> None:
    assert score_case(case, 200, passing_payload(case)) == []


def test_preview_case_scorer_rejects_authority_shape_leakage() -> None:
    case = next(case for case in load_cases(DEFAULT_BANK) if case["authority"] == "semantic_teacher")
    payload = passing_payload(case)
    payload["sources"] = [{"title": "unexpected"}]
    payload["fretboard"] = {"positions": [{"fret": 3}]}
    failures = score_case(case, 200, payload)
    assert "unexpected source cards" in failures
    assert "unexpected fretboard payload" in failures


def test_access_header_reads_token_from_named_environment_without_cli_value() -> None:
    headers = _headers(
        auth_mode="access-jwt",
        access_jwt_env="TEST_PREVIEW_JWT",
        env={"TEST_PREVIEW_JWT": "test-secret-token"},
    )
    assert headers["Cf-Access-Jwt-Assertion"] == "test-secret-token"


def test_preview_runner_validates_bank_without_network(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "across all six authorities" in capsys.readouterr().out


def test_preview_runner_requires_exact_request_authorization() -> None:
    with pytest.raises(ValueError, match="exact authorization for 10 answer requests"):
        main(["--base-url", "http://127.0.0.1:8770", "--auth-mode", "dev"])


def test_preview_smoke_fails_before_answer_calls_when_activation_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def request_json(url: str, **_kwargs: object) -> tuple[int, dict[str, object], str, int]:
        calls.append(url)
        return 200, {"features": {}}, "", 1

    monkeypatch.setattr(preview_smoke, "_request_json", request_json)
    cases = load_cases(DEFAULT_BANK)
    report = preview_smoke.run_smoke(
        base_url="http://127.0.0.1:8770",
        cases=cases,
        headers={"X-Steel-Rag-Dev-Access-Role": "admin"},
        timeout=1,
    )
    assert calls == ["http://127.0.0.1:8770/api/session"]
    assert report["activation"]["status"] == "fail"
    assert report["requested_case_count"] == len(cases)
    assert report["case_count"] == 0


@pytest.mark.parametrize(
    "base_url",
    [
        "http://example.test",
        "https://user:password@example.test",
        "https://example.test/path",
        "https://example.test?redirect=evil",
    ],
)
def test_preview_smoke_rejects_unsafe_base_url_before_network(base_url: str) -> None:
    with pytest.raises(ValueError, match="base URL"):
        preview_smoke.run_smoke(
            base_url=base_url,
            cases=load_cases(DEFAULT_BANK),
            headers={"Cf-Access-Jwt-Assertion": "test"},
            timeout=1,
        )


def test_preview_request_converts_network_failure_to_scoreable_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def urlopen(*_args: object, **_kwargs: object) -> object:
        raise urllib.error.URLError("test outage")

    monkeypatch.setattr(preview_smoke.urllib.request, "urlopen", urlopen)
    status, payload, trace_id, latency_ms = preview_smoke._request_json(
        "http://127.0.0.1:8770/api/session",
        headers={},
        timeout=1,
    )
    assert status == 0
    assert payload == {"error": "request failed: URLError"}
    assert trace_id == ""
    assert latency_ms >= 0


def test_invalid_bank_is_rejected(tmp_path: Path) -> None:
    bank = tmp_path / "invalid.yaml"
    bank.write_text("version: 1\ncases: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="at least eight"):
        load_cases(bank)
