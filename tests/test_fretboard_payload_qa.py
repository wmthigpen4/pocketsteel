from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from pocketsteel.answering import DeterministicAnswerProvider
from pocketsteel.api import create_app
from pocketsteel.fretboard_examples import fretboard_payload_for_question, validate_fretboard_payload


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "fretboard_payload_qa_cases.json"


class FakeSearchIndex:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"query": query, **kwargs})
        return {
            "results": [
                {
                    "score": 0.82,
                    "excerpt": "On E9, G major can be found at the 3rd fret open, 6th fret with A+F, and 10th fret with A+B.",
                    "forum_name": "Pedal Steel",
                    "thread_title": "G major positions on E9",
                    "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=qa-g-major",
                    "chunk_id": "qa-g-major-positions",
                    "post_uid": "qa-g-major-post",
                    "source_system": "qa_fixture",
                }
            ],
            "warnings": [],
        }


def load_cases() -> list[dict[str, Any]]:
    return json.loads(FIXTURE_PATH.read_text())


def call_answer(question: str) -> dict[str, Any]:
    app = create_app(
        FakeSearchIndex(),
        answer_provider=DeterministicAnswerProvider(),
        answer_auth_mode="local_dev",
    )
    body = json.dumps({"question": question, "mode": "ask", "topK": 6}).encode("utf-8")
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/api/answer",
        "QUERY_STRING": "",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        "HTTP_X_STEEL_RAG_DEV_ACCESS_ROLE": "beta_user",
    }
    response_body = b"".join(app(environ, start_response))

    assert captured["status"] == "200 OK"
    return json.loads(response_body)


def assert_no_raw_geometry(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = str(key).lower()
            assert normalized_key not in {"x", "y", "cx", "cy"}
            assert "coordinate" not in normalized_key
            assert_no_raw_geometry(child)
    elif isinstance(value, list):
        for item in value:
            assert_no_raw_geometry(item)


def positions_by_id(fretboard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {position["id"]: position for position in fretboard["positions"]}


def assert_contract_shape(fretboard: dict[str, Any]) -> None:
    assert {
        "type",
        "title",
        "subtitle",
        "description",
        "tuning",
        "strings",
        "positions",
        "highlights",
    }.issubset(fretboard)
    assert fretboard["type"] == "e9-fretboard-diagram"
    assert fretboard["tuning"] == "E9"
    assert fretboard["strings"]["count"] == 10
    assert "markerFrets" not in fretboard
    assert "markers" not in fretboard
    assert_no_raw_geometry(fretboard)
    validate_fretboard_payload(fretboard)

    assert [position["id"] for position in fretboard["positions"]] == [
        highlight["id"] for highlight in fretboard["highlights"]
    ]
    for position in fretboard["positions"]:
        assert {
            "id",
            "label",
            "fret",
            "strings",
            "grip",
            "pedals",
            "levers",
            "color",
        }.issubset(position)
        assert isinstance(position["id"], str) and position["id"]
        assert 0 <= position["fret"] <= 24
        assert position["strings"]
        assert all(1 <= string <= 10 for string in position["strings"])
        assert position["grip"] == "-".join(str(string) for string in position["strings"])


def assert_expected_position(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    assert actual["fret"] == expected["fret"]
    assert actual["strings"] == expected["strings"]
    assert actual["pedals"] == expected["pedals"]
    assert actual["levers"] == expected["levers"]


def assert_forbidden_control_locations(fretboard: dict[str, Any], forbidden_locations: list[dict[str, Any]]) -> None:
    for forbidden in forbidden_locations:
        for position in fretboard["positions"]:
            assert not (
                position["fret"] == forbidden["fret"]
                and position["pedals"] == forbidden["pedals"]
                and position["levers"] == forbidden["levers"]
            )


def test_fretboard_payload_qa_fixture_cases_are_stable() -> None:
    cases = load_cases()
    assert [case["id"] for case in cases] == [
        "g-major-positions",
        "g-major-ab",
        "g-major-af",
        "unsupported-full-solo-tab",
    ]


def test_supported_known_position_questions_return_contract_fretboard_payloads() -> None:
    for case in load_cases():
        if case.get("unsupported"):
            continue

        response = call_answer(case["question"])
        assert "fretboard" in response
        fretboard = response["fretboard"]
        assert_contract_shape(fretboard)
        by_id = positions_by_id(fretboard)

        for expected in case["expected_positions"]:
            assert expected["id"] in by_id
            assert_expected_position(by_id[expected["id"]], expected)
        assert_forbidden_control_locations(fretboard, case.get("forbidden_controls_at_frets", []))


def test_g_major_payload_locks_prior_af_ab_swap_regression() -> None:
    response = call_answer("Where can I play a G chord?")
    by_id = positions_by_id(response["fretboard"])

    assert by_id["g-af-6"]["fret"] == 6
    assert by_id["g-af-6"]["pedals"] == ["A"]
    assert by_id["g-af-6"]["levers"] == ["F"]
    assert by_id["g-ab-10"]["fret"] == 10
    assert by_id["g-ab-10"]["pedals"] == ["A", "B"]
    assert by_id["g-ab-10"]["levers"] == []


def test_unsupported_query_does_not_emit_invented_fretboard_payload() -> None:
    unsupported = next(case for case in load_cases() if case.get("unsupported"))

    assert fretboard_payload_for_question(unsupported["question"]) is None
    response = call_answer(unsupported["question"])
    assert "fretboard" not in response
