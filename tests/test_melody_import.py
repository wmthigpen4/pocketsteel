from __future__ import annotations

import base64
import io
import json
import struct
import zipfile

import pytest
from PIL import Image, ImageDraw

from steel_guitar_rag.melody_import import (
    MelodyImportError,
    import_score_draft,
    normalize_score_draft,
    parse_midi,
    parse_musicxml,
    public_song_catalog,
)
from steel_guitar_rag.score_omr import (
    LocalVisionOmrProvider,
    inspect_pdf,
    provider_catalog,
    recognize_printed_document,
)
from steel_guitar_rag.melody_arranger import (
    arrange_melody_routes,
    parse_melody_inputs,
    resolve_contour,
)


AMAZING_GRACE_PITCHES = ["D4", "G4", "B4", "G4", "B4", "A4", "G4", "E4"]


def _printed_page_bytes(image_format: str = "PNG") -> bytes:
    image = Image.new("RGB", (1200, 800), "white")
    draw = ImageDraw.Draw(image)
    for y in range(220, 271, 12):
        draw.line((100, y, 1100, y), fill="black", width=2)
    draw.ellipse((280, 235, 302, 250), fill="black")
    stream = io.BytesIO()
    image.save(stream, format=image_format)
    return stream.getvalue()


def _three_note_midi() -> bytes:
    track = b"".join(
        (
            b"\x00\x90\x43\x40",
            b"\x83\x60\x80\x43\x00",
            b"\x00\x90\x45\x40",
            b"\x83\x60\x80\x45\x00",
            b"\x00\x90\x47\x40",
            b"\x83\x60\x80\x47\x00",
            b"\x00\xff\x2f\x00",
        )
    )
    return (
        b"MThd"
        + struct.pack(">IHHH", 6, 0, 1, 480)
        + b"MTrk"
        + struct.pack(">I", len(track))
        + track
    )


def test_structured_input_paths_share_exact_normalized_pitch_events() -> None:
    expected = [67, 69, 71]
    manual = normalize_score_draft(
        {
            "source": {"type": "composed_in_studio"},
            "score": {
                "sourceKey": "G",
                "arrangementKey": "G",
                "melody": [
                    {"pitchValue": pitch, "measure": 1, "beat": index}
                    for index, pitch in enumerate(expected, start=1)
                ],
            },
        }
    )
    xml = b"""<score-partwise><part-list><score-part id='P1'><part-name>Melody</part-name></score-part></part-list><part id='P1'><measure number='1'><attributes><divisions>1</divisions><key><fifths>1</fifths></key></attributes><note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration></note><note><pitch><step>A</step><octave>4</octave></pitch><duration>1</duration></note><note><pitch><step>B</step><octave>4</octave></pitch><duration>1</duration></note></measure></part></score-partwise>"""
    musicxml = parse_musicxml(xml)
    midi = parse_midi(_three_note_midi())
    interval_inputs = parse_melody_inputs(["1", "2", "3"], "G")
    typed_note_inputs = parse_melody_inputs(["G", "A", "B"], "G")

    assert [event["pitchValue"] for event in manual["score"]["melody"]] == expected
    assert [event["pitchValue"] for event in musicxml["score"]["melody"]] == expected
    assert [event["pitchValue"] for event in midi["score"]["melody"]] == expected
    assert resolve_contour(interval_inputs, "ascending") == expected
    assert resolve_contour(typed_note_inputs, "ascending") == expected
    assert all(
        draft["review"]["status"] == "needs_review"
        for draft in (musicxml, midi)
    )

    modality_inputs = {
        "typed_notes": ["G", "A", "B"],
        "intervals": ["1", "2", "3"],
        "musicxml": musicxml["score"]["melody"],
        "midi": midi["score"]["melody"],
        "normalized_events": manual["score"]["melody"],
    }

    def arrangement_signature(raw_events: list[object]) -> list[object]:
        routes, resolved = arrange_melody_routes(
            raw_events,
            key="G",
            texture="both",
            route_id_prefix="modality-parity",
            title="Modality parity",
        )
        return [
            [event["pitchValue"] for event in resolved],
            [
                {
                    "harmonyType": route["harmonyType"],
                    "events": [
                        {
                            "pitchValue": event["pitchValue"],
                            "notes": event["notes"],
                            "performanceControls": event["performanceControls"],
                            "patternFamily": event["patternFamily"],
                            "canonicalGrip": event["canonicalGrip"],
                        }
                        for event in route["tabExample"]["events"]
                    ],
                }
                for route in routes
            ],
        ]

    signatures = {
        input_type: arrangement_signature(raw_events)
        for input_type, raw_events in modality_inputs.items()
    }
    assert len(
        {json.dumps(signature, sort_keys=True) for signature in signatures.values()}
    ) == 1


def test_amazing_grace_catalog_record_is_reviewed_and_checksummed() -> None:
    cards = public_song_catalog()
    assert len(cards) == 12
    assert cards[0]["id"] == "amazing-grace-new-britain"
    assert cards[0]["title"] == "Amazing Grace"
    assert cards[0]["subtitle"] == "Complete verse melody · NEW BRITAIN, 1829"
    assert cards[0]["rightsLabel"] == "public_domain"
    assert cards[0]["key"] == "G"
    assert cards[0]["meter"] == "3/4"
    assert cards[0]["sourceUrl"] == "https://library.timelesstruths.org/music/Amazing_Grace/midi/"
    assert {card["key"] for card in cards} == {"G", "C"}
    assert {card["difficulty"] for card in cards} == {"starter", "easy"}
    assert all(card["eventCount"] >= 25 for card in cards)
    assert all(card["measureCount"] >= 8 for card in cards)
    assert all(card["sectionCount"] >= 2 for card in cards)
    assert any(card["sectionCount"] > 4 for card in cards)
    assert all(card["formLabel"] for card in cards)
    assert all(card["attribution"] for card in cards)
    draft = import_score_draft({"sourceType": "catalog", "catalogId": cards[0]["id"]})
    assert draft["schemaVersion"] == "score_draft_v1"
    assert draft["source"]["retained"] is False
    assert draft["source"]["rightsLabel"] == "public_domain"
    assert draft["source"]["sourceChecksum"].startswith("sha256:")
    assert [event["pitch"] for event in draft["score"]["melody"][:8]] == AMAZING_GRACE_PITCHES
    assert len(draft["score"]["melody"]) == 35
    assert len(draft["score"]["sections"]) == 4
    assert draft["score"]["sections"][0]["label"] == "Amazing grace"


def test_starter_songbook_drafts_are_reviewed_sourced_and_arranger_ready() -> None:
    cards = public_song_catalog()
    expected_ids = {
        "amazing-grace-new-britain", "oh-susanna", "aura-lee", "buffalo-gals",
        "skip-to-my-lou", "shell-be-coming-round-the-mountain", "when-the-saints",
        "red-river-valley", "shenandoah", "my-bonnie", "yankee-doodle", "camptown-races",
    }
    assert {card["id"] for card in cards} == expected_ids
    for card in cards:
        draft = import_score_draft({"sourceType": "catalog", "catalogId": card["id"]})
        assert draft["review"]["status"] == "confirmed"
        assert draft["source"]["rightsLabel"] == "public_domain"
        assert draft["source"]["sourceChecksum"].startswith("sha256:")
        assert draft["source"]["url"].startswith("https://")
        assert draft["score"]["arrangementKey"] in {"G", "C"}
        assert len([event for event in draft["score"]["melody"] if not event.get("rest")]) == card["eventCount"]
        assert draft["score"]["harmony"]
        assert draft["score"]["sections"]


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
        "contentBase64": base64.b64encode(_printed_page_bytes()).decode("ascii"),
        "title": "Page one",
        "rightsAcknowledged": True,
    }
    draft = import_score_draft(
        payload,
        vision_client=lambda _image, _mime: {
            "score": {"sourceKey": "G", "arrangementKey": "G", "meter": "3/4", "melody": [{"pitch": "D4", "durationBeats": 1}]}
        },
    )
    assert draft["source"]["type"] == "image"
    assert draft["source"]["title"] == "Page one"
    assert draft["source"]["rightsLabel"] == "user_authorized"
    assert draft["source"]["retained"] is False
    assert draft["source"]["private"] is True
    assert draft["source"]["trainingUse"] is False
    assert draft["source"]["retentionPolicy"] == "request_only"
    assert draft["source"]["providerId"] == "local_vision"
    assert draft["review"]["status"] == "needs_review"
    assert draft["review"]["confirmationsRequired"] == ["key_signature", "time_signature", "melody_part"]
    with pytest.raises(MelodyImportError):
        import_score_draft(payload, vision_client=lambda _image, _mime: {"score": {"melody": "bad"}})


def test_printed_import_requires_rights_acknowledgement() -> None:
    with pytest.raises(MelodyImportError, match="right to process"):
        import_score_draft(
            {
                "sourceType": "image",
                "mimeType": "image/png",
                "contentBase64": base64.b64encode(_printed_page_bytes()).decode("ascii"),
            },
            vision_client=lambda _image, _mime: {"score": {"melody": [{"pitch": "G4"}]}},
        )


def test_pdf_inspection_and_selected_page_recognition_are_transient() -> None:
    pdf_bytes = _printed_page_bytes("PDF")
    inspection = inspect_pdf(pdf_bytes)
    assert inspection["schemaVersion"] == "score_document_inspection_v1"
    assert inspection["pageCount"] == 1
    assert inspection["sourceRetained"] is False
    assert inspection["pages"][0]["previewMimeType"] == "image/jpeg"
    assert len(base64.b64decode(inspection["pages"][0]["previewBase64"])) > 100

    provider = LocalVisionOmrProvider(
        lambda _image, mime: {
            "inputAssessment": {"kind": "printed_notation", "accepted": True},
            "score": {
                "sourceKey": "G",
                "arrangementKey": "G",
                "meter": "4/4",
                "melody": [
                    {"id": "n1", "measure": 1, "beat": 1, "durationBeats": 1, "pitch": "G4", "confidence": 0.72},
                    {"id": "n2", "measure": 1, "beat": 2, "durationBeats": 3, "pitch": "B4", "confidence": 0.99},
                ],
            },
        }
    )
    draft = recognize_printed_document(
        raw=pdf_bytes,
        source_type="pdf",
        title="One-page score",
        selected_pages=[1],
        selected_part=None,
        provider=provider,
        normalize=normalize_score_draft,
    )
    assert draft["source"]["retained"] is False
    assert draft["source"]["selectedPages"] == [1]
    assert draft["omr"]["artifacts"]["source"] == "transient"
    assert draft["omr"]["artifacts"]["arrangement"] == "not_started"
    assert draft["review"]["summary"]["flaggedEventCount"] == 1
    assert draft["review"]["flaggedEventIds"] == ["p1-n1"]


def test_handwriting_and_existing_tablature_are_rejected_explicitly() -> None:
    provider = LocalVisionOmrProvider(
        lambda _image, _mime: {
            "inputAssessment": {"kind": "handwritten", "accepted": False},
            "score": {"melody": [{"pitch": "G4"}]},
        }
    )
    with pytest.raises(MelodyImportError, match="not handwriting"):
        import_score_draft(
            {
                "sourceType": "image",
                "mimeType": "image/png",
                "contentBase64": base64.b64encode(_printed_page_bytes()).decode("ascii"),
                "rightsAcknowledged": True,
            },
            vision_client=provider._client,
        )


def test_ambiguous_staffs_are_exposed_and_explicit_selection_clears_part_confirmation() -> None:
    draft = import_score_draft(
        {
            "sourceType": "image",
            "mimeType": "image/png",
            "contentBase64": base64.b64encode(_printed_page_bytes()).decode("ascii"),
            "rightsAcknowledged": True,
            "partId": "staff-2",
        },
        vision_client=lambda _image, _mime: {
            "inputAssessment": {"kind": "printed_notation", "accepted": True},
            "parts": [
                {"id": "staff-1", "name": "Piano", "eventCount": 8},
                {"id": "staff-2", "name": "Vocal", "eventCount": 6},
            ],
            "selectedPartId": "staff-2",
            "score": {"sourceKey": "G", "meter": "4/4", "melody": [{"pitch": "G4"}]},
        },
    )
    assert draft["parts"][1] == {"id": "staff-2", "name": "Vocal", "eventCount": 6}
    assert draft["selectedPartId"] == "staff-2"
    assert "melody_part" not in draft["review"]["confirmationsRequired"]


def test_provider_catalog_keeps_managed_omr_fail_closed() -> None:
    candidates = {item["id"]: item for item in provider_catalog()}
    assert candidates["local_vision"]["available"] is True
    assert candidates["flat_interactive_omr"]["available"] is False
    assert candidates["flat_interactive_omr"]["beta"] is True


def test_import_preserves_supported_major_arrangement_key() -> None:
    draft = import_score_draft(
        {
            "sourceType": "pasted",
            "score": {"sourceKey": "D", "arrangementKey": "D", "melody": [{"pitch": "D4"}]},
        }
    )
    assert draft["score"]["arrangementKey"] == "D"
    assert draft["review"]["warnings"] == []
