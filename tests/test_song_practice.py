from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from steel_guitar_rag.copedent_transfer import absolute_pitch_for_profile
from steel_guitar_rag.e9_copedents import CANONICAL_NOTES, NOTE_TO_SEMITONE, get_e9_copedent_profile
from steel_guitar_rag.song_practice import (
    ENABLE_SONG_PRACTICE_ENV,
    SongPracticeError,
    arrange_song_practice,
    configured_song_practice_enabled,
    parse_chord_symbol,
    get_curated_practice_project,
    list_curated_lessons,
    song_practice_catalog,
)


def request_for(chords: list[str]) -> dict[str, object]:
    return {
        "schemaVersion": "song_practice_request_v1",
        "level": "chord_karaoke",
        "key": "G",
        "meter": "4/4",
        "style": "classic_country",
        "events": [
            {
                "id": f"event-{index}",
                "measureId": f"measure-{index}",
                "sectionId": "verse-1",
                "chord": chord,
                "startMs": (index - 1) * 1000,
                "endMs": index * 1000,
                "role": "comp",
            }
            for index, chord in enumerate(chords, start=1)
        ],
    }


def test_song_practice_launches_by_default_and_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENABLE_SONG_PRACTICE_ENV, raising=False)
    assert configured_song_practice_enabled() is True
    monkeypatch.setenv(ENABLE_SONG_PRACTICE_ENV, "false")
    assert configured_song_practice_enabled() is False
    monkeypatch.setenv(ENABLE_SONG_PRACTICE_ENV, "true")
    assert configured_song_practice_enabled() is True


@pytest.mark.parametrize(
    ("symbol", "quality", "bass"),
    [
        ("G", "major", ""),
        ("Bb", "major", ""),
        ("F#m", "minor", ""),
        ("D7", "dominant7", ""),
        ("Am7", "minor7", ""),
        ("G/B", "major", "B"),
    ],
)
def test_chord_parser_discloses_supported_quality_and_slash_bass(symbol: str, quality: str, bass: str) -> None:
    parsed = parse_chord_symbol(symbol)
    assert parsed is not None
    assert parsed.quality == quality
    assert parsed.bass == bass


@pytest.mark.parametrize("symbol", ["H", "Gmaj7", "Cdim", "Dsus4", "G13", ""])
def test_chord_parser_leaves_unsupported_quality_for_manual_review(symbol: str) -> None:
    assert parse_chord_symbol(symbol) is None


@pytest.mark.parametrize("profile_id", ["emmons-e9-basic", "day-e9-basic"])
def test_arranger_validates_all_chromatic_major_roots_minor_and_dominant(profile_id: str) -> None:
    chords = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B", "Am", "D7", "Em7"]
    profile = get_e9_copedent_profile(profile_id)
    result = arrange_song_practice(request_for(chords), copedent_profile=profile, copedent_revision=1)

    assert result["schemaVersion"] == "song_practice_plan_v1"
    assert result["targetCopedentId"] == profile_id
    assert result["route"]["coherentAcrossChart"] is True
    assert result["provenance"] == {
        "kind": "deterministic_e9_chord_route",
        "audioReceived": False,
        "lyricsReceived": False,
        "ragUsed": False,
        "stage": 1,
    }
    for event in result["events"]:
        assert event["status"] == "ready"
        position = event["position"]
        assert position["validation"] == ["absolute_pitch", "chord_tones", "mechanical_controls"]
        for note in position["notes"]:
            assert note["pitch"] == absolute_pitch_for_profile(
                profile,
                note["string"],
                note["fret"],
                position["controls"],
            )
            assert note["note"] == CANONICAL_NOTES[note["pitch"] % 12]


def test_arranger_is_deterministic_uses_familiar_route_and_never_invents_unsupported_grip() -> None:
    profile = get_e9_copedent_profile()
    request = request_for(["G", "C", "D7", "Gmaj7", "G/B"])
    first = arrange_song_practice(request, copedent_profile=profile, copedent_revision=1)
    second = arrange_song_practice(request, copedent_profile=profile, copedent_revision=1)

    assert first == second
    assert first["events"][0]["position"]["controls"] == []
    assert first["events"][3]["status"] == "manual_position_needed"
    assert first["events"][3]["position"] is None
    assert "manual" in first["events"][3]["warning"]
    assert first["events"][4]["status"] == "ready"
    assert "Slash bass B" in first["events"][4]["disclosure"]
    assert all(
        len(event["position"]["strings"]) == 3
        for event in first["events"]
        if event["status"] == "ready"
    )
    assert first["events"][0]["position"]["strings"] == [4, 5, 6]
    assert "transitions" not in first
    assert "solo" not in first
    assert "melody" not in first


@pytest.mark.parametrize("forbidden", ["audio", "audioBytes", "filename", "songTitle", "artist", "cueText", "lyrics"])
def test_arranger_rejects_private_media_and_identifying_fields(forbidden: str) -> None:
    request = request_for(["G"])
    request[forbidden] = "must not cross the boundary"
    with pytest.raises(SongPracticeError, match="not allowed"):
        arrange_song_practice(request, copedent_profile=get_e9_copedent_profile(), copedent_revision=1)


def test_arranger_rejects_future_levels_and_invalid_timing() -> None:
    request = request_for(["G"])
    request["level"] = "chord_moves"
    with pytest.raises(SongPracticeError, match="Stage 1"):
        arrange_song_practice(request, copedent_profile=get_e9_copedent_profile(), copedent_revision=1)

    request = request_for(["G"])
    request["events"][0]["endMs"] = 0  # type: ignore[index]
    with pytest.raises(SongPracticeError, match="invalid time range"):
        arrange_song_practice(request, copedent_profile=get_e9_copedent_profile(), copedent_revision=1)


def test_pilot_catalog_passes_rights_checksum_no_steel_and_asset_budget_gates() -> None:
    catalog = song_practice_catalog()
    assert catalog["schemaVersion"] == "song_practice_catalog_v1"
    assert [track["title"] for track in catalog["tracks"]] == [
        "Amazing Grace",
        "When the Saints Go Marching In",
        "Hard Times Come Again No More",
    ]
    for track in catalog["tracks"][:2]:
        asset = Path(track["audioUrl"].lstrip("/"))
        assert track["noSteel"] is True
        assert track["melodyLead"] is True
        assert track["learnerReady"] is True
        assert track["publicationState"] == "private_preview"
        assert asset.stat().st_size < 2 * 1024 * 1024
        assert hashlib.sha256(asset.read_bytes()).hexdigest()
        assert track["barStartsMs"][0] > 0
        assert track["durationMs"] > track["barStartsMs"][-1]

    amazing_grace = catalog["tracks"][0]
    assert amazing_grace["id"] == "amazing-grace-kevin-macleod-lesson-v1"
    assert amazing_grace["performer"] == "Kevin MacLeod · Steel Guitar RAG lesson edit"
    assert amazing_grace["tempo"] == 76
    assert amazing_grace["countInBars"] == 2
    assert amazing_grace["durationMs"] == 42947
    assert amazing_grace["audioUrl"].endswith("amazing-grace-2011-guide.mp3")
    assert hashlib.sha256(Path(amazing_grace["audioUrl"].lstrip("/")).read_bytes()).hexdigest() == (
        "c0126a24458b913168ee5f3f58a0a54f75a32a6dfcd8fa1e23d80ffe8a91e417"
    )
    assert amazing_grace["recordingCredit"].startswith("“Amazing Grace 2011” Kevin MacLeod")
    assert amazing_grace["license"] == "CC BY 3.0"
    assert amazing_grace["rightsUrl"].startswith("https://commons.wikimedia.org/")
    assert amazing_grace["rightsDocumentUrl"].endswith("amazing-grace-2011-guide.RIGHTS.md")
    assert hashlib.sha256(Path(amazing_grace["rightsDocumentUrl"].lstrip("/")).read_bytes()).hexdigest() == (
        "c7b8b8a4e4c5fd7f0d8c4eb0813d9cf814e34e9d39a19eee9e0ad8fc4df31d7e"
    )
    assert amazing_grace["beatTimesMs"][6] == amazing_grace["barStartsMs"][0] == 4737
    assert len(amazing_grace["beatTimesMs"]) == 55
    assert amazing_grace["chart"] == (
        "[Opening] | G | G | C | G | [Middle] G | G | D7 | D7 | G | G | C | G | "
        "[Ending] Em | D7 | G | G |"
    )
    assert [cue["text"] for cue in amazing_grace["lyricCues"]] == [
        "Amazing grace, how sweet the sound",
        "That saved a wretch like me",
        "I once was lost, but now am found",
        "Was blind, but now I see",
    ]
    assert [cue["startMs"] for cue in amazing_grace["lyricCues"]] == [3947, 13421, 22895, 32368]
    assert amazing_grace["lyricCues"][0]["startMs"] == amazing_grace["beatTimesMs"][5]
    assert amazing_grace["lyricCues"][0]["startMs"] < amazing_grace["barStartsMs"][0]
    assert catalog["tracks"][1]["countInBars"] == 1
    assert catalog["tracks"][2]["publicationState"] == "coming_soon"
    assert catalog["tracks"][2]["recordingCredit"] == "Grant Raymond Barrett · CC BY 3.0"


def test_curated_registry_exposes_playable_projects_and_withholds_unreviewed_track() -> None:
    lessons = list_curated_lessons()
    assert [lesson["projectId"] for lesson in lessons] == [
        "amazing-grace-guided",
        "when-the-saints-guided",
        "hard-times-guided",
    ]
    amazing_grace = get_curated_practice_project("amazing-grace-guided")
    assert amazing_grace is not None
    assert amazing_grace["lyricCues"][0]["text"].startswith("Amazing grace")
    assert amazing_grace["practiceProject"]["timeline"]["beatTimesMs"] == amazing_grace["beatTimesMs"]
    assert get_curated_practice_project("hard-times-guided") is None
