from __future__ import annotations

import io
import json
from typing import Any

from pocketsteel.api import create_app
from pocketsteel.answer_tab_examples import (
    answer_body_for_tab_example,
    fretboard_payload_for_tab_example,
    static_answer_body_for_question,
    static_fretboard_payload_for_question,
    tab_example_payload_for_question,
)
from pocketsteel.tab_engine import (
    TabEvent,
    TabNote,
    default_e9_copedent_profile,
    render_example,
    render_tab,
    tab_examples,
    validate_events,
)


def _row(tab: str, label: str) -> str:
    for line in tab.splitlines():
        if line.startswith(label):
            return line
    raise AssertionError(f"Missing row {label!r} in:\n{tab}")


def _issue_codes(events: tuple[TabEvent, ...]) -> set[str]:
    return {issue.code for issue in validate_events(events)}


def test_renderer_always_outputs_ten_string_rows() -> None:
    result = render_tab((TabEvent(notes=(TabNote(4, 3), TabNote(5, 3), TabNote(6, 3))),))

    assert result.ok
    string_rows = [line for line in result.tab.splitlines() if line[:3].strip().isdigit()]
    assert len(string_rows) == 10
    assert string_rows[0].startswith(" 1 |")
    assert string_rows[-1].startswith("10 |")
    assert "-" not in result.tab


def test_simultaneous_notes_align_in_same_event_column() -> None:
    result = render_tab((TabEvent(notes=(TabNote(4, 3), TabNote(5, 3), TabNote(6, 3))),))

    assert result.ok
    assert _row(result.tab, " 4 |").index("3") == _row(result.tab, " 5 |").index("3")
    assert _row(result.tab, " 5 |").index("3") == _row(result.tab, " 6 |").index("3")


def test_rejects_more_than_three_notes() -> None:
    events = (TabEvent(notes=(TabNote(3, 3), TabNote(4, 3), TabNote(5, 3), TabNote(6, 3))),)

    assert "too_many_notes" in _issue_codes(events)


def test_rejects_invalid_string_numbers() -> None:
    events = (TabEvent(notes=(TabNote(11, 3),)),)

    assert "invalid_string" in _issue_codes(events)


def test_rejects_unrecognized_change() -> None:
    events = (TabEvent(notes=(TabNote(5, 3, ("Z",)),)),)

    assert "unknown_change" in _issue_codes(events)


def test_rejects_a_pedal_on_string_four() -> None:
    events = (TabEvent(notes=(TabNote(4, 3, ("A",)),)),)

    assert "unaffected_string_change" in _issue_codes(events)


def test_permits_known_string_specific_changes() -> None:
    events = (
        TabEvent(
            notes=(
                TabNote(5, 3, ("A",)),
                TabNote(6, 3, ("B",)),
                TabNote(4, 3, ("F",)),
            )
        ),
    )

    assert validate_events(events) == ()


def test_unaffected_string_does_not_display_change() -> None:
    result = render_tab(
        (TabEvent(notes=(TabNote(4, 3), TabNote(5, 3, ("A",)), TabNote(6, 3, ("B",)))),)
    )

    assert result.ok
    assert "3A" not in _row(result.tab, " 4 |")
    assert "3A" in _row(result.tab, " 5 |")
    assert "3B" in _row(result.tab, " 6 |")


def test_lyrics_and_chords_align_to_event_start_column() -> None:
    result = render_tab(
        (
            TabEvent(
                chord="G",
                lyric="pick",
                notes=(TabNote(4, 3), TabNote(5, 3), TabNote(6, 3)),
            ),
            TabEvent(
                chord="C",
                lyric="press",
                notes=(TabNote(5, 3, ("A",)), TabNote(6, 3, ("B",)), TabNote(8, 3)),
            ),
        )
    )

    assert result.ok
    first_column = _row(result.tab, " 4 |").index("3")
    second_column = _row(result.tab, " 5 |").index("3A")
    assert _row(result.tab, "Ch |").index("G") == first_column
    assert _row(result.tab, "Ly |").index("pick") == first_column
    assert _row(result.tab, "Ch |").index("C", 4) == second_column
    assert _row(result.tab, "Ly |").index("press") == second_column


def test_spacing_stays_stable_with_different_token_lengths() -> None:
    result = render_tab(
        (
            TabEvent(notes=(TabNote(4, 3, ("F",)), TabNote(5, 3, ("A",)), TabNote(6, 3, ("B",)))),
            TabEvent(notes=(TabNote(4, 10), TabNote(5, 10, ("A",)), TabNote(6, 10, ("B",)))),
        )
    )

    assert result.ok
    first_column = _row(result.tab, " 4 |").index("3F")
    second_column = _row(result.tab, " 4 |").index("10")
    assert _row(result.tab, " 5 |").index("3A") == first_column
    assert _row(result.tab, " 6 |").index("3B") == first_column
    assert _row(result.tab, " 5 |").index("10A") == second_column
    assert _row(result.tab, " 6 |").index("10B") == second_column


def test_examples_all_validate() -> None:
    examples = tab_examples()

    assert {"g_major_open", "g_to_c", "ab_major", "e_lower_color", "beginner_lick"} <= set(examples)
    for name in examples:
        result = render_example(name)
        assert result.ok, name
        assert result.issues == ()


def test_static_g_major_grip_uses_fretboard_without_tab_payload() -> None:
    assert tab_example_payload_for_question("Show me a G major grip.") is None
    assert static_answer_body_for_question("Show me a G major grip.").startswith("Here is a simple G major grip on E9.")

    fretboard = static_fretboard_payload_for_question("Show me a G major grip.")
    assert fretboard is not None
    assert fretboard["sourceContext"][0]["sourceId"] == "pocketsteel.answer_tab_examples.static_grip"
    assert fretboard["positions"][0]["positionKind"] == "full_chord_position"
    assert fretboard["positions"][0]["family"] == "open_no_pedals"
    assert fretboard["positions"][0]["strings"] == [4, 5, 6]
    assert fretboard["positions"][0]["notes"] == {"4": "G", "5": "D", "6": "B"}


def test_static_four_five_six_grip_uses_fretboard_without_tab_payload() -> None:
    assert tab_example_payload_for_question("Show me a 4-5-6 grip.") is None
    fretboard = static_fretboard_payload_for_question("Show me a 4-5-6 grip.")

    assert fretboard is not None
    assert fretboard["positions"][0]["grip"] == "4-5-6"


def test_answer_tab_example_selector_supports_safe_first_examples() -> None:
    cases = [
        ("Show me a G to C move.", "movement-g-i-iv-v1"),
        ("How do I use A+B pedals?", "a-b-pedal-major-position"),
        ("Show me an E-lower move.", "e-lower-color-move"),
        ("Give me a beginner lick in G.", "beginner-g-two-event-lick"),
    ]

    for question, expected_id in cases:
        payload = tab_example_payload_for_question(question)
        assert payload is not None, question
        assert payload["id"] == expected_id
        assert payload["rendered_tab"]
        assert payload["validation"]["ok"] is True
        assert payload["validation"]["issues"] == []
        assert fretboard_payload_for_tab_example(payload) is not None


def test_parameterized_chord_movement_selector_supports_major_key_progressions() -> None:
    cases = [
        ("Show me a I to IV move in G.", "movement-g-i-iv-v1", "I-IV", ["G", "C"], ["I", "IV"]),
        ("Show me a G to C move.", "movement-g-i-iv-v1", "I-IV", ["G", "C"], ["I", "IV"]),
        ("Show me a I to V move in G.", "movement-g-i-v-v1", "I-V", ["G", "D"], ["I", "V"]),
        ("Show me a G to D move.", "movement-g-i-v-v1", "I-V", ["G", "D"], ["I", "V"]),
        (
            "Show me a G C D G movement.",
            "movement-g-i-iv-v-i-v1",
            "I-IV-V-I",
            ["G", "C", "D", "G"],
            ["I", "IV", "V", "I"],
        ),
        (
            "Show me a 1 4 5 1 move in G.",
            "movement-g-i-iv-v-i-v1",
            "I-IV-V-I",
            ["G", "C", "D", "G"],
            ["I", "IV", "V", "I"],
        ),
        ("Give me a simple I-IV move in A.", "movement-a-i-iv-v1", "I-IV", ["A", "D"], ["I", "IV"]),
    ]

    for question, expected_id, progression, chords, functions in cases:
        payload = tab_example_payload_for_question(question)
        assert payload is not None, question
        assert payload["id"] == expected_id
        assert payload["kind"] == "parameterized_chord_movement"
        assert payload["display_tab"] is True
        assert payload["preferred_display"] == "tab_and_fretboard"
        assert payload["context"]["progression"] == progression
        assert payload["context"]["chords"] == chords
        assert payload["context"]["rightsStatus"] == "original_educational_example"
        assert payload["context"]["provenanceType"] == "deterministic_exercise"
        assert payload["context"]["sourcePolicy"] == "no_external_song_source"
        assert payload["context"]["generator"] == "parameterized_e9_chord_movement_v1"
        assert [event["function"] for event in payload["events"]] == functions
        assert payload["validation"]["ok"] is True
        assert payload["validation"]["eventCount"] == len(payload["events"])
        assert answer_body_for_tab_example(payload).startswith("Here is a short original")
        assert fretboard_payload_for_tab_example(payload) is not None


def test_parameterized_chord_movement_defaults_numeral_only_requests_to_g() -> None:
    payload = tab_example_payload_for_question("How do I move from the I chord to the IV chord on E9?")

    assert payload is not None
    assert payload["id"] == "movement-g-i-iv-v1"
    assert payload["context"]["defaultedKey"] is True
    assert "defaulting to G" in answer_body_for_tab_example(payload)


def test_parameterized_chord_movement_defaults_no_pedals_to_ab_to_g_i_iv() -> None:
    payload = tab_example_payload_for_question("How do I connect no-pedals to A+B positions?")

    assert payload is not None
    assert payload["id"] == "movement-g-i-iv-v1"
    assert payload["context"]["progression"] == "I-IV"
    assert payload["context"]["chords"] == ["G", "C"]
    assert payload["context"]["defaultedKey"] is True
    assert [event["function"] for event in payload["events"]] == ["I", "IV"]
    assert answer_body_for_tab_example(payload).startswith("Here is a short original G I-IV movement on E9.")
    assert fretboard_payload_for_tab_example(payload) is not None


def test_beginner_g_lick_press_event_only_contains_changed_a_b_strings() -> None:
    payload = tab_example_payload_for_question("Give me a beginner lick in G.")

    assert payload is not None
    press_event = payload["events"][1]
    assert press_event["lyric"] == "press"
    assert press_event["chord"] == "C partial"
    assert press_event["notes"] == [
        {"string": 5, "fret": 3, "changes": ["A"]},
        {"string": 6, "fret": 3, "changes": ["B"]},
    ]
    assert "string 8" not in payload["explanation"].lower()
    assert "strings 5 and 6" in answer_body_for_tab_example(payload)


def test_a_b_tab_example_is_pitch_consistent_g_major_grip() -> None:
    payload = tab_example_payload_for_question("Show me an A+B example.")

    assert payload is not None
    event = payload["events"][0]
    assert event["notes"] == [
        {"string": 3, "fret": 10, "changes": ["B"]},
        {"string": 4, "fret": 10, "changes": []},
        {"string": 5, "fret": 10, "changes": ["A"]},
    ]
    fretboard = fretboard_payload_for_tab_example(payload)
    assert fretboard is not None
    position = fretboard["positions"][0]
    assert position["notes"] == {"3": "G", "4": "D", "5": "B"}
    assert position["intervals"] == {"3": "1", "4": "5", "5": "3"}


def test_answer_tab_example_selector_blocks_unsafe_or_unsupported_requests() -> None:
    assert tab_example_payload_for_question("Where can I buy a slide bar?") is None
    assert tab_example_payload_for_question("Tab the whole solo from Together Again.") is None
    assert tab_example_payload_for_question("Transcribe this recording into tab.") is None
    assert tab_example_payload_for_question("Give me a minor I-IV-V move in G.") is None
    assert tab_example_payload_for_question("Show a blues I7-IV7-V7 turnaround.") is None
    assert tab_example_payload_for_question("Use my custom copedent for a I-IV move.") is None


def test_answer_tab_example_selector_omits_payload_when_validation_fails(monkeypatch) -> None:
    class BrokenRenderResult:
        ok = False
        tab = ""
        metadata = {"profile": "default_e9", "event_count": 0}

    monkeypatch.setattr("pocketsteel.answer_tab_examples.render_example", lambda name: BrokenRenderResult())

    assert tab_example_payload_for_question("Show me a G major grip.") is None


def test_fake_tab_global_ab_changes_are_rejected_but_string_aware_version_passes() -> None:
    invalid = (
        TabEvent(
            notes=(
                TabNote(4, 3, ("A", "B")),
                TabNote(5, 3, ("A", "B")),
                TabNote(6, 3, ("A", "B")),
            )
        ),
    )
    valid = (
        TabEvent(
            notes=(
                TabNote(4, 3),
                TabNote(5, 3, ("A",)),
                TabNote(6, 3, ("B",)),
            )
        ),
    )

    assert "unaffected_string_change" in _issue_codes(invalid)
    assert validate_events(valid) == ()
    rendered = render_tab(valid).tab
    assert "3A" in _row(rendered, " 5 |")
    assert "3B" in _row(rendered, " 6 |")


def test_default_e9_profile_declares_expected_user_facing_labels() -> None:
    profile = default_e9_copedent_profile()

    assert profile.open_strings[9] == "D"
    assert profile.changes["A"].affected_strings == (5, 10)
    assert profile.changes["B"].affected_strings == (3, 6)
    assert profile.changes["F"].affected_strings == (4, 8)
    assert profile.control_labels == {
        "P1": "A",
        "P2": "B",
        "P3": "C",
        "LKL": "F",
        "LKR": "E",
        "LKV": "V",
        "RKL": "G",
        "RKR": "D",
    }


def test_api_tab_render_returns_tab_and_issues() -> None:
    status, payload = _call_tab_api(
        {
            "profile": "default_e9",
            "events": [
                {
                    "chord": "G",
                    "notes": [
                        {"string": 4, "fret": 3},
                        {"string": 5, "fret": 3},
                        {"string": 6, "fret": 3},
                    ],
                }
            ],
        }
    )

    assert status == "200 OK"
    assert payload["ok"] is True
    assert payload["issues"] == []
    assert payload["metadata"] == {"profile": "default_e9", "event_count": 1}
    assert " 4 |3" in payload["tab"]
    assert "10 |" in payload["tab"]


def test_api_tab_render_accepts_string_aware_a_pedal_on_string_five() -> None:
    status, payload = _call_tab_api(
        {
            "events": [
                {
                    "notes": [
                        {"string": 5, "fret": 3, "changes": ["A"]},
                    ],
                }
            ],
        }
    )

    assert status == "200 OK"
    assert payload["ok"] is True
    assert payload["issues"] == []
    assert payload["metadata"] == {"profile": "default_e9", "event_count": 1}
    assert "3A" in _row(payload["tab"], " 5 |")
    assert "3A" not in _row(payload["tab"], " 4 |")


def test_api_tab_render_reports_validation_issues() -> None:
    status, payload = _call_tab_api(
        {
            "events": [
                {
                    "notes": [
                        {"string": 4, "fret": 3, "changes": ["A"]},
                    ],
                }
            ],
        }
    )

    assert status == "200 OK"
    assert payload["ok"] is False
    assert payload["tab"] == ""
    assert payload["metadata"] == {"profile": "default_e9", "event_count": 1}
    assert payload["issues"] == [
        {
            "code": "unaffected_string_change",
            "eventIndex": 0,
            "message": "Change A does not affect string 4.",
            "noteIndex": 0,
        }
    ]


def _call_tab_api(json_body: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    app = create_app(_NoopSearchIndex(), answer_auth_mode="local_dev", auth_provider="scaffold")
    body = json.dumps(json_body).encode("utf-8")
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status

    response_body = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/api/tab/render",
                "QUERY_STRING": "",
                "CONTENT_LENGTH": str(len(body)),
                "wsgi.input": io.BytesIO(body),
            },
            start_response,
        )
    )
    return captured["status"], json.loads(response_body)


class _NoopSearchIndex:
    def search(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return []
