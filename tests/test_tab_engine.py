from __future__ import annotations

import io
import json
from typing import Any

from pocketsteel.api import create_app
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
    assert payload["issues"][0]["code"] == "unaffected_string_change"


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
