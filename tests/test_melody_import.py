from __future__ import annotations

import base64
import io
import zipfile

import pytest

from pocketsteel.melody_import import (
    MelodyImportError,
    import_score_draft,
    parse_musicxml,
    public_song_catalog,
)


AMAZING_GRACE_PITCHES = ["D4", "G4", "B4", "G4", "B4", "A4", "G4", "E4"]


def test_amazing_grace_catalog_record_is_reviewed_and_checksummed() -> None:
    cards = public_song_catalog()
    assert cards == [
        {
            "id": "amazing-grace-new-britain",
            "title": "Amazing Grace",
            "subtitle": "NEW BRITAIN · 1829 setting",
            "rightsLabel": "public_domain",
            "key": "G",
            "meter": "3/4",
            "sourceUrl": "https://library.timelesstruths.org/music/Amazing_Grace/midi/",
        }
    ]
    draft = import_score_draft({"sourceType": "catalog", "catalogId": cards[0]["id"]})
    assert draft["schemaVersion"] == "score_draft_v1"
    assert draft["source"]["retained"] is False
    assert draft["source"]["rightsLabel"] == "public_domain"
    assert draft["source"]["sourceChecksum"] == "sha256:4cd985b4dd4993f317269509af06b71ad082c1643dd0f191433fcf0a040459bf"
    assert [event["pitch"] for event in draft["score"]["melody"]] == AMAZING_GRACE_PITCHES
    assert [item["symbol"] for item in draft["score"]["harmony"]] == ["G", "G", "G", "D7", "Em", "C"]


def test_musicxml_import_preserves_rhythm_chords_and_selects_melody_part() -> None:
    xml = b"""<?xml version='1.0'?>
    <score-partwise version='4.0'>
      <work><work-title>Small tune</work-title></work>
      <part-list>
        <score-part id='P1'><part-name>Melody</part-name></score-part>
        <score-part id='P2'><part-name>Bass</part-name></score-part>
      </part-list>
      <part id='P1'><measure number='1'>
        <attributes><divisions>2</divisions><key><fifths>1</fifths></key><time><beats>3</beats><beat-type>4</beat-type></time></attributes>
        <harmony><root><root-step>G</root-step></root><kind text=''>major</kind></harmony>
        <note><pitch><step>D</step><octave>4</octave></pitch><duration>2</duration><lyric><text>A</text></lyric></note>
        <note><pitch><step>G</step><octave>4</octave></pitch><duration>4</duration></note>
      </measure></part>
      <part id='P2'><measure number='1'><attributes><divisions>2</divisions></attributes>
        <note><pitch><step>G</step><octave>2</octave></pitch><duration>6</duration></note>
      </measure></part>
    </score-partwise>"""
    draft = parse_musicxml(xml, selected_part="P1")
    assert draft["score"]["meter"] == "3/4"
    assert [event["pitch"] for event in draft["score"]["melody"]] == ["D4", "G4"]
    assert [event["durationBeats"] for event in draft["score"]["melody"]] == [1.0, 2.0]
    assert draft["score"]["harmony"][0]["symbol"] == "G"
    assert draft["review"]["status"] == "needs_review"


def test_mxl_is_decompressed_in_memory_and_rejects_unsafe_archive() -> None:
    xml = b"""<score-partwise><part-list><score-part id='P1'><part-name>Melody</part-name></score-part></part-list><part id='P1'><measure number='1'><note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration></note></measure></part></score-partwise>"""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("score.musicxml", xml)
    payload = base64.b64encode(stream.getvalue()).decode("ascii")
    draft = import_score_draft({"sourceType": "mxl", "contentBase64": payload})
    assert draft["score"]["melody"][0]["pitch"] == "G4"

    unsafe = io.BytesIO()
    with zipfile.ZipFile(unsafe, "w") as archive:
        archive.writestr("../score.musicxml", xml)
    with pytest.raises(MelodyImportError):
        import_score_draft({"sourceType": "mxl", "contentBase64": base64.b64encode(unsafe.getvalue()).decode("ascii")})


def test_musicxml_derives_chord_only_when_explicit_symbol_is_absent() -> None:
    xml = b"""<score-partwise><part-list><score-part id='P1'><part-name>Voices</part-name></score-part></part-list>
    <part id='P1'><measure number='1'><attributes><divisions>1</divisions></attributes>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>1</duration></note>
      <note><chord/><pitch><step>B</step><octave>3</octave></pitch><duration>1</duration></note>
      <note><chord/><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration></note>
    </measure></part></score-partwise>"""
    draft = parse_musicxml(xml)
    assert draft["score"]["melody"][0]["pitch"] == "D4"
    assert draft["score"]["harmony"] == [
        {"measure": 1, "beat": 1.0, "symbol": "G", "basis": "derived", "confidence": 0.7}
    ]


def test_image_recognition_is_review_gated_and_malformed_output_is_rejected() -> None:
    payload = {
        "sourceType": "image",
        "mimeType": "image/png",
        "contentBase64": base64.b64encode(b"not persisted").decode("ascii"),
        "title": "Page one",
    }
    draft = import_score_draft(
        payload,
        vision_client=lambda _image, _mime: {
            "score": {"sourceKey": "G", "arrangementKey": "G", "meter": "3/4", "melody": [{"pitch": "D4", "durationBeats": 1}]}
        },
    )
    assert draft["source"] == {"type": "image", "title": "Page one", "url": None, "rightsLabel": "unreviewed", "retained": False}
    assert draft["review"]["status"] == "needs_review"
    with pytest.raises(MelodyImportError):
        import_score_draft(payload, vision_client=lambda _image, _mime: {"score": {"melody": "bad"}})


def test_non_g_or_c_import_requires_explicit_arrangement_choice() -> None:
    draft = import_score_draft(
        {
            "sourceType": "pasted",
            "score": {"sourceKey": "D", "arrangementKey": "D", "melody": [{"pitch": "D4"}]},
        }
    )
    assert draft["score"]["arrangementKey"] == "D"
    assert "Choose G or C" in draft["review"]["warnings"][0]
