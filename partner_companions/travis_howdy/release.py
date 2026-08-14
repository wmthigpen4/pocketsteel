"""Build the deterministic, allowlisted Travis Howdy companion bundle."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Mapping


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
SITE_ROOT = PACKAGE_ROOT / "site"
TEMPLATE_ROOT = PACKAGE_ROOT / "templates"
DEFAULT_COMPANION = PACKAGE_ROOT / "content" / "howdy.draft.json"
PROJECT_NAME = "steel-guitar-rag-travis-preview"
HOSTNAME = "travis-preview.steelguitarrag.com"
REVIEW_PHASE_TESTER_COUNTS = {
    "owner_only": 1,
    "partner_review": 2,
}
REQUIRED_APPROVALS = (
    "musical",
    "chords",
    "tablature",
    "printLayout",
    "audioRights",
    "brandAssets",
    "accessIdentities",
)
FORBIDDEN_TEXT = (
    "/api/answer",
    "/api/search",
    "/ui/",
    'href="/chat',
    'href="/melody',
    'href="/lessons',
    "teachablecdn.com",
    "localhost:",
    "127.0.0.1:",
    "ollama",
    "chroma",
    "openai.com/v1",
    "anthropic.com",
    "sourceMappingURL",
)
ALLOWED_STATIC_SOURCES = (
    SITE_ROOT / "companion.css",
    SITE_ROOT / "companion.js",
    TEMPLATE_ROOT / "full.html",
    TEMPLATE_ROOT / "embed.html",
    TEMPLATE_ROOT / "print.html",
    TEMPLATE_ROOT / "404.html",
    TEMPLATE_ROOT / "companion.fragment.html",
)


class CompanionReleaseError(ValueError):
    """Raised when a bundle is not safe to package or publish."""


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _source_date(source_date_epoch: int | None = None) -> str:
    raw = source_date_epoch if source_date_epoch is not None else int(os.environ.get("SOURCE_DATE_EPOCH", "0") or "0")
    instant = dt.datetime.fromtimestamp(raw, tz=dt.timezone.utc) if raw else dt.datetime.now(tz=dt.timezone.utc)
    return instant.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CompanionReleaseError(f"Cannot load JSON from {path}: {error}") from error
    if not isinstance(payload, dict):
        raise CompanionReleaseError(f"Expected an object in {path}.")
    return payload


def _assert_hash(path: Path, expected: str, label: str) -> str:
    if not path.is_file():
        raise CompanionReleaseError(f"Missing approved {label}: {path}")
    actual = _sha256_file(path)
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected or "")):
        raise CompanionReleaseError(f"{label} requires an explicit SHA-256.")
    if actual != expected:
        raise CompanionReleaseError(f"{label} hash mismatch: expected {expected}, received {actual}.")
    return actual


def _ensure_static_sources_committed() -> None:
    relative_paths = [str(path.relative_to(REPOSITORY_ROOT)) for path in ALLOWED_STATIC_SOURCES]
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", *relative_paths],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
    )
    if tracked.returncode != 0:
        raise CompanionReleaseError("Release-mode static sources must be committed before packaging.")
    changed = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", *relative_paths],
        cwd=REPOSITORY_ROOT,
    )
    if changed.returncode != 0:
        raise CompanionReleaseError("Release-mode static sources differ from HEAD.")


def _normalized_artifact_hash(data: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(data))
    payload["artifactSha256"] = ""
    payload["buildSha"] = ""
    media = payload.setdefault("media", {})
    media["audioUrl"] = None
    media["soloAudioUrl"] = None
    media["pdfUrl"] = None
    media["brandHeroUrl"] = None
    return _sha256_bytes(_canonical_json_bytes(payload))


def validate_companion(data: Mapping[str, Any], *, release: bool) -> None:
    if data.get("schemaVersion") != "lesson_companion_v1":
        raise CompanionReleaseError("Companion schema must be lesson_companion_v1.")
    if data.get("runtimeMode") != "published_deterministic" or data.get("modelCallsAllowed") is not False:
        raise CompanionReleaseError("The runtime must be deterministic with model calls disabled.")
    if data.get("companionId") != "travis-toy-tutorials-howdy":
        raise CompanionReleaseError("Unexpected companion ID.")
    events = data.get("events")
    phrases = data.get("phrases")
    chords = data.get("chordTimeline")
    if not isinstance(events, list) or not events or not isinstance(phrases, list) or not phrases:
        raise CompanionReleaseError("Events and phrases are required.")
    if not isinstance(chords, list) or not chords:
        raise CompanionReleaseError("A chord timeline is required, even when the draft labels are withheld.")
    event_ids = [str(item.get("id") or "") for item in events]
    if "" in event_ids or len(event_ids) != len(set(event_ids)):
        raise CompanionReleaseError("Event IDs must be present and unique.")
    phrase_ids = {str(item.get("id") or "") for item in phrases}
    chord_ids = {str(item.get("id") or "") for item in chords}
    previous_end = 0
    for event in events:
        start = int(event.get("startMs", -1))
        end = int(event.get("endMs", -1))
        if start < previous_end or end <= start:
            raise CompanionReleaseError(f"Invalid or overlapping event timing for {event.get('id')}.")
        previous_end = end
        if event.get("phraseId") not in phrase_ids or event.get("chordEventId") not in chord_ids:
            raise CompanionReleaseError(f"Event {event.get('id')} has a missing phrase or chord reference.")
        notes = event.get("tabNotes")
        if not isinstance(notes, list) or (not notes and event.get("isRest") is not True):
            raise CompanionReleaseError(f"Event {event.get('id')} has no tablature notes.")
        for note in notes:
            if int(note.get("string", 0)) not in range(1, 11) or int(note.get("fret", -1)) not in range(0, 25):
                raise CompanionReleaseError(f"Event {event.get('id')} has an invalid string or fret.")
            if note.get("toFret") is not None and int(note["toFret"]) not in range(0, 25):
                raise CompanionReleaseError(f"Event {event.get('id')} has an invalid slide destination.")
            fret_path = note.get("fretPath")
            if fret_path is not None and (
                not isinstance(fret_path, list)
                or not fret_path
                or int(fret_path[0]) != int(note["fret"])
                or any(int(fret) not in range(0, 25) for fret in fret_path)
            ):
                raise CompanionReleaseError(f"Event {event.get('id')} has an invalid fret path.")
        coaching_cue = event.get("coachingCue")
        if coaching_cue:
            source_moment = event.get("sourceMoment") or {}
            if (
                source_moment.get("quoteKind") != "verbatim_excerpt"
                or source_moment.get("excerpt") != coaching_cue
                or int(source_moment.get("lessonTimeMs", -1)) < 0
            ):
                raise CompanionReleaseError(
                    f"Event {event.get('id')} coaching cue must be a timestamped verbatim excerpt."
                )
    media = data.get("media", {})
    duration = int(media.get("durationMs", -1))
    authored_duration = duration
    scopes = media.get("scopes")
    if scopes is not None:
        if not isinstance(scopes, dict) or set(scopes) != {"fullSong", "taughtSolo"}:
            raise CompanionReleaseError("Media scopes must define exactly fullSong and taughtSolo.")
        for scope_name in ("fullSong", "taughtSolo"):
            scope = scopes.get(scope_name) or {}
            start = int(scope.get("startMs", -1))
            end = int(scope.get("endMs", -1))
            scope_duration = int(scope.get("durationMs", -1))
            if start < 0 or end <= start or scope_duration != end - start or end > duration:
                raise CompanionReleaseError(f"Media scope {scope_name} has invalid timing.")
        full_song = scopes["fullSong"]
        if int(full_song["startMs"]) != 0 or int(full_song["endMs"]) != duration:
            raise CompanionReleaseError("The fullSong media scope must cover the complete audio asset.")
        authored_duration = int(scopes["taughtSolo"]["durationMs"])
    song_chords = data.get("songChordTimeline")
    if song_chords is not None:
        if not isinstance(song_chords, list):
            raise CompanionReleaseError("The full-song chord timeline must be a list when present.")
        previous_song_chord_end = 0
        for chord in song_chords:
            start = int(chord.get("startMs", -1))
            end = int(chord.get("endMs", -1))
            if (
                start != previous_song_chord_end
                or end <= start
                or not str(chord.get("symbol") or "").strip()
                or not str(chord.get("nns") or "").strip()
            ):
                raise CompanionReleaseError(
                    "The full-song chord timeline must be contiguous and fully labeled."
                )
            previous_song_chord_end = end
        if song_chords and previous_song_chord_end != duration:
            raise CompanionReleaseError("The full-song chord timeline must cover the complete song scope.")
    if previous_end != authored_duration:
        message = (
            "The final event must end at the taught-solo authored duration."
            if scopes is not None
            else "The final event must end at the authored duration."
        )
        raise CompanionReleaseError(message)
    for phrase in phrases:
        ids = phrase.get("eventIds") or []
        if not ids or any(item not in event_ids for item in ids):
            raise CompanionReleaseError(f"Phrase {phrase.get('id')} references an unknown event.")
        phrase_events = [event for event in events if event["id"] in ids]
        if int(phrase.get("startMs", -1)) != phrase_events[0]["startMs"]:
            raise CompanionReleaseError(f"Phrase {phrase.get('id')} start does not match its events.")
        if int(phrase.get("endMs", -1)) != phrase_events[-1]["endMs"]:
            raise CompanionReleaseError(f"Phrase {phrase.get('id')} end does not match its events.")
    for moment in data.get("lessonMoments") or []:
        if moment.get("eventId") not in event_ids or int(moment.get("lessonTimeMs", -1)) < 0:
            raise CompanionReleaseError(f"Lesson moment {moment.get('id')} must point to a timestamped event.")
        if moment.get("quoteKind") == "verbatim_excerpt":
            source_event = next(event for event in events if event["id"] == moment["eventId"])
            if not moment.get("excerpt") or moment.get("excerpt") != source_event.get("coachingCue"):
                raise CompanionReleaseError(
                    f"Lesson moment {moment.get('id')} must reuse the event's sourced verbatim excerpt."
                )
        elif moment.get("excerpt"):
            raise CompanionReleaseError(
                f"Lesson moment {moment.get('id')} cannot label a technical summary as an excerpt."
            )
    for chord in chords:
        covered = [
            event
            for event in events
            if event["chordEventId"] == chord["id"]
            and int(chord["startMs"]) - 50 <= int(event["startMs"])
            and int(event["endMs"]) <= int(chord["endMs"]) + 50
        ]
        expected = [event for event in events if event["chordEventId"] == chord["id"]]
        if len(covered) != len(expected) or not expected:
            raise CompanionReleaseError(f"Chord boundary {chord.get('id')} is not aligned to its events within 50 ms.")
        if chord.get("symbol") and not chord.get("tabNotes"):
            raise CompanionReleaseError(f"Labeled chord {chord.get('id')} requires a fixed fretboard grip.")
    if data.get("sourceEvidence") and data.get("sourceEvidence", {}).get("rawTranscriptIncluded") is not False:
        raise CompanionReleaseError("The deployable artifact must state that the raw transcript is excluded.")
    if data.get("print", {}).get("tabStrings") != 10:
        raise CompanionReleaseError("The print artifact must use ten-string E9 tab.")
    if not release:
        return
    if data.get("contentStatus") != "approved":
        raise CompanionReleaseError("Release mode requires contentStatus=approved.")
    approvals = data.get("approvals") or {}
    missing = [name for name in REQUIRED_APPROVALS if approvals.get(name) is not True]
    if missing:
        raise CompanionReleaseError(f"Release approvals incomplete: {', '.join(missing)}.")
    if data.get("copedent", {}).get("approved") is not True:
        raise CompanionReleaseError("The source copedent must be approved.")
    if data.get("print", {}).get("approved") is not True:
        raise CompanionReleaseError("The print artifact must be approved.")
    if any(item.get("musicalVerified") is not True for item in events):
        raise CompanionReleaseError("Every solo event must be musically verified.")
    if any(item.get("verified") is not True or not item.get("symbol") for item in chords):
        raise CompanionReleaseError("Every chord boundary must be verified and labeled.")
    if song_chords and any(item.get("verified") is not True for item in song_chords):
        raise CompanionReleaseError("Every full-song chord event must be verified before release.")
    if len(data.get("release", {}).get("approvalReferences") or []) < 5:
        raise CompanionReleaseError("Release mode requires approval references for music, rights, brand, and print.")
    release_data = data.get("release", {})
    review_phase = str(release_data.get("reviewPhase") or "")
    expected_testers = REVIEW_PHASE_TESTER_COUNTS.get(review_phase)
    if expected_testers is None:
        raise CompanionReleaseError("Release mode requires a recognized review phase.")
    if int(release_data.get("testerEmailCount", 0)) != expected_testers:
        raise CompanionReleaseError(
            f"Review phase {review_phase!r} requires exactly {expected_testers} Access tester "
            f"{'identity' if expected_testers == 1 else 'identities'}."
        )


def _ascii(value: Any) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2197": "/",
    }
    text = str(value or "")
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text.encode("ascii", "replace").decode("ascii")


def _pitch_staff_step(pitch: str) -> int:
    match = re.fullmatch(r"([A-G])(?:#|b)?(\d)", str(pitch))
    if not match:
        return 6
    letter, octave = match.groups()
    order = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}
    value = int(octave) * 7 + order[letter]
    return value - (4 * 7 + order["E"])


def generate_tablature_pdf(data: Mapping[str, Any], output_path: Path) -> Path:
    """Render deterministic notation-plus-ten-string-tab from companion events."""

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from reportlab.pdfgen import canvas
    except ImportError as error:
        raise CompanionReleaseError("PDF generation requires reportlab.") from error

    validate_companion(data, release=False)
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = letter
    page = canvas.Canvas(str(output_path), pagesize=letter, pageCompression=1, invariant=1)
    page.setTitle(_ascii(data.get("print", {}).get("title")))
    page.setAuthor("Travis Toy Tutorials / Steel Guitar RAG")
    page.setSubject("Deterministic lesson companion notation and E9 tablature")
    teal = colors.HexColor("#134361")
    coral = colors.HexColor("#ff3f20")
    gray = colors.HexColor("#667781")
    light = colors.HexColor("#d8e0e4")
    event_by_id = {event["id"]: event for event in data["events"]}
    chord_by_id = {chord["id"]: chord for chord in data["chordTimeline"]}
    phrases = list(data["phrases"])
    phrases_per_page = 2
    page_count = (len(phrases) + phrases_per_page - 1) // phrases_per_page

    def draw_text_fit(text: str, x: float, y: float, maximum: float, size: float = 8) -> None:
        clean = _ascii(text)
        while size > 5.5 and stringWidth(clean, "Helvetica", size) > maximum:
            size -= 0.25
        page.setFont("Helvetica", size)
        page.drawString(x, y, clean)

    def draw_page_header(page_number: int) -> None:
        page.setFillColor(teal)
        page.rect(0, height - 78, width, 78, stroke=0, fill=1)
        page.setFillColor(colors.white)
        page.setFont("Helvetica-Bold", 9)
        page.drawString(42, height - 28, "TRAVIS TOY TUTORIALS - LESSON COMPANION")
        page.setFont("Helvetica-Bold", 20)
        page.drawString(42, height - 53, _ascii(data["print"]["title"]))
        page.setFont("Helvetica", 7)
        page.drawRightString(width - 42, height - 28, _ascii(data["revision"]))
        page.drawRightString(width - 42, height - 40, f"Page {page_number} of {page_count}")
        tempo = data["display"].get("tempoBpm")
        musical_context = f"Key {data['display']['key']} | {data['display']['meter']}"
        if tempo:
            musical_context += f" | {tempo} BPM"
        page.drawRightString(width - 42, height - 52, _ascii(musical_context))
        if not data.get("approvals", {}).get("printLayout"):
            page.saveState()
            page.setFillColor(colors.HexColor("#fff0ed"))
            page.rect(42, height - 99, width - 84, 15, stroke=0, fill=1)
            page.setFillColor(colors.HexColor("#7a210f"))
            page.setFont("Helvetica-Bold", 7)
            page.drawCentredString(width / 2, height - 94, "DRAFT LAYOUT PROOF - NOT MUSICAL OR PRINT APPROVED")
            page.restoreState()

    def draw_chord_chart(top: float) -> None:
        left = 42
        right = width - 42
        bar_width = (right - left) / int(data["display"]["barCount"])
        page.setFillColor(teal)
        page.setFont("Helvetica-Bold", 8)
        page.drawString(left, top, _ascii(f"CHORD CHART - KEY {data['display']['key']}"))
        page.setFillColor(coral if not data.get("approvals", {}).get("chords") else teal)
        page.setFont("Helvetica-Bold", 5.5)
        chart_status = "AUDIO-DERIVED - TRAVIS REVIEW REQUIRED" if not data.get("approvals", {}).get("chords") else "TRAVIS APPROVED"
        page.drawRightString(right, top, chart_status)
        box_top = top - 8
        box_height = 34
        for bar in range(1, int(data["display"]["barCount"]) + 1):
            x = left + (bar - 1) * bar_width
            page.setStrokeColor(colors.HexColor("#77848a"))
            page.setFillColor(colors.white)
            page.rect(x, box_top - box_height, bar_width, box_height, stroke=1, fill=1)
            page.setFillColor(gray)
            page.setFont("Helvetica", 5)
            page.drawString(x + 4, box_top - 8, f"Bar {bar}")
            chords = [
                chord for chord in data["chordTimeline"]
                if chord.get("symbol") and int(chord["barStart"]) <= bar <= int(chord["barEnd"])
            ]
            labels = [
                chord["symbol"] for index, chord in enumerate(chords)
                if index == 0 or chord["symbol"] != chords[index - 1]["symbol"]
            ]
            page.setFillColor(teal)
            page.setFont("Helvetica-Bold", 9)
            page.drawCentredString(x + bar_width / 2, box_top - 25, _ascii(" > ".join(labels) or "PENDING"))

    def draw_phrase(phrase: Mapping[str, Any], top: float) -> None:
        events = [event_by_id[item] for item in phrase["eventIds"]]
        left = 50
        right = width - 42
        inner_width = right - left
        page.setFillColor(teal)
        page.setFont("Helvetica-Bold", 12)
        page.drawString(left, top, _ascii(f"Bars {phrase['barStart']}-{phrase['barEnd']}  |  {phrase['label']}"))
        page.setFillColor(gray)
        draw_text_fit(phrase["lessonNote"], left, top - 14, inner_width, 7.5)
        staff_top = top - 41
        staff_gap = 6
        page.setStrokeColor(colors.black)
        page.setLineWidth(0.55)
        for line in range(5):
            y = staff_top - line * staff_gap
            page.line(left + 28, y, right, y)
        page.setFont("Helvetica-Bold", 16)
        page.setFillColor(colors.black)
        page.drawString(left + 3, staff_top - 18, "G")
        column_width = (inner_width - 42) / len(events)
        previous_bar = None
        previous_chord_id = None
        for index, event in enumerate(events):
            x = left + 40 + column_width * (index + 0.5)
            if previous_bar is not None and event["bar"] != previous_bar:
                page.setStrokeColor(light)
                page.line(x - column_width / 2, staff_top + 7, x - column_width / 2, staff_top - 31)
            previous_bar = event["bar"]
            chord_id = event.get("chordEventId")
            if chord_id != previous_chord_id:
                chord = chord_by_id.get(chord_id, {})
                chord_label = chord.get("symbol") or "CHORD REVIEW PENDING"
                if chord.get("symbol") and not chord.get("verified"):
                    chord_label += "*"
                page.setFillColor(teal if chord.get("verified") else coral)
                page.setFont("Helvetica-Bold", 5.5)
                page.drawCentredString(x, staff_top + 22, _ascii(chord_label))
            previous_chord_id = chord_id
            if event.get("isRest") is True:
                y = staff_top - 12
                page.setFillColor(colors.black)
                page.rect(x - 3, y - 2, 6, 4, stroke=0, fill=1)
                page.line(x + 2, y - 2, x - 2, y - 10)
                pitch_label = "rest"
            else:
                step = _pitch_staff_step(str(event.get("notationPitch")))
                y = staff_top - 4 * staff_gap + step * (staff_gap / 2)
                y = max(staff_top - 34, min(staff_top + 12, y))
                page.setFillColor(colors.white if event.get("rhythm") in {"half", "whole"} else colors.black)
                page.setStrokeColor(colors.black)
                page.ellipse(x - 3.8, y - 2.4, x + 3.8, y + 2.4, stroke=1, fill=1)
                if event.get("rhythm") != "whole":
                    page.line(x + 3.5, y, x + 3.5, y + 18)
                if event.get("tieToNext") is True and index + 1 < len(events):
                    next_x = left + 40 + column_width * (index + 1.5)
                    page.bezier(x + 4, y - 5, x + 12, y - 11, next_x - 12, y - 11, next_x - 4, y - 5)
                pitch_label = event.get("notationPitch")
            page.setFillColor(colors.black)
            page.setFont("Helvetica", 5.5)
            page.drawCentredString(x, staff_top + 11, _ascii(pitch_label))
            page.drawCentredString(x, staff_top - 32, _ascii(f"{event['bar']}.{event['beat']}"))
        tab_top = staff_top - 57
        tab_gap = 8.3
        page.setStrokeColor(colors.HexColor("#77848a"))
        for string_number in range(1, 11):
            y = tab_top - (string_number - 1) * tab_gap
            page.setFont("Helvetica", 5.5)
            page.setFillColor(gray)
            page.drawRightString(left + 20, y - 1.8, str(string_number))
            page.line(left + 28, y, right, y)
        for index, event in enumerate(events):
            x = left + 40 + column_width * (index + 0.5)
            for note in event["tabNotes"]:
                y = tab_top - (int(note["string"]) - 1) * tab_gap
                if note.get("technique") == "pedal-hammer":
                    token = f"{note['fret']}h{''.join(note.get('toControls') or note.get('controls') or [])}"
                elif note.get("technique") == "sustain" and note.get("tieFromPrevious"):
                    token = "-"
                else:
                    controls = "".join(note.get("controls") or [])
                    destination_controls = "".join(note.get("toControls") or note.get("controls") or [])
                    fret_path = note.get("fretPath") or [note["fret"]]
                    path_tail = [str(fret) for fret in fret_path[1:]]
                    if not path_tail and note.get("toFret") is not None:
                        path_tail = [str(note["toFret"])]
                    destination = (">" + ">".join(path_tail) + destination_controls) if path_tail else ""
                    token = f"{note['fret']}{controls}{destination}"
                page.setFillColor(colors.white)
                token_width = max(11, stringWidth(token, "Helvetica-Bold", 6.5) + 4)
                page.rect(x - token_width / 2, y - 4, token_width, 8, stroke=0, fill=1)
                page.setFillColor(colors.black)
                page.setFont("Helvetica-Bold", 6.5)
                page.drawCentredString(x, y - 2.2, token)
            page.setFillColor(gray)
            page.setFont("Helvetica", 5.2)
            draw_text_fit(event["movement"].replace("-", " "), x - column_width * .45, tab_top - 91, column_width * .9, 5.2)

    for page_index in range(page_count):
        draw_page_header(page_index + 1)
        if page_index == 0 and any(chord.get("symbol") for chord in data["chordTimeline"]):
            draw_chord_chart(height - 113)
        page_phrases = phrases[page_index * phrases_per_page : (page_index + 1) * phrases_per_page]
        for phrase_index, phrase in enumerate(page_phrases):
            first_page_chart_offset = 58 if page_index == 0 and any(chord.get("symbol") for chord in data["chordTimeline"]) else 0
            draw_phrase(phrase, height - 126 - first_page_chart_offset - phrase_index * 300)
        page.setStrokeColor(light)
        page.line(42, 39, width - 42, 39)
        page.setFillColor(gray)
        page.setFont("Helvetica", 5.8)
        controls = ", ".join(
            f"{item['code']}={_ascii(item['label'])} (strings {','.join(map(str, item['strings']))})"
            for item in data["copedent"]["controls"]
        )
        page.drawString(42, 27, _ascii(controls)[:112])
        page.drawString(42, 17, "0hA=pedal hammer; bar stays at open fret. Source E9 copedent: review pending.")
        page.drawRightString(width - 42, 17, "Member-use review draft - Travis Toy Tutorials")
        page.showPage()
    page.save()
    return output_path


def _render_template(path: Path, replacements: Mapping[str, str]) -> str:
    rendered = path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", rendered)
    if leftover:
        raise CompanionReleaseError(f"Unresolved template tokens in {path.name}: {', '.join(leftover)}")
    return rendered


def _copy_private_asset(config: Mapping[str, Any], key: str, destination: Path, label: str) -> str:
    item = config.get(key)
    if not isinstance(item, Mapping):
        raise CompanionReleaseError(f"Release configuration requires {key}.")
    source = Path(str(item.get("path") or "")).expanduser().resolve()
    expected = str(item.get("sha256") or "")
    actual = _assert_hash(source, expected, label)
    shutil.copyfile(source, destination)
    return actual


def _merge_release_config(data: dict[str, Any], config: Mapping[str, Any]) -> None:
    review_phase = str(config.get("reviewPhase") or "").strip()
    expected_testers = REVIEW_PHASE_TESTER_COUNTS.get(review_phase)
    if expected_testers is None:
        allowed = ", ".join(sorted(REVIEW_PHASE_TESTER_COUNTS))
        raise CompanionReleaseError(f"Release configuration reviewPhase must be one of: {allowed}.")
    tester_emails = config.get("testerEmails")
    if not isinstance(tester_emails, list) or len(tester_emails) != expected_testers:
        raise CompanionReleaseError(
            f"Review phase {review_phase!r} requires exactly {expected_testers} tester email"
            f"{'s' if expected_testers != 1 else ''}."
        )
    email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    normalized_emails = {str(email).strip().lower() for email in tester_emails}
    if len(normalized_emails) != expected_testers or any(
        not email_pattern.fullmatch(email) for email in normalized_emails
    ):
        raise CompanionReleaseError("Tester emails must be distinct valid addresses for the selected review phase.")
    feedback_email = str(config.get("feedbackEmail") or "").strip()
    if not email_pattern.fullmatch(feedback_email):
        raise CompanionReleaseError("A valid feedback email is required for release.")
    data.setdefault("release", {})["reviewPhase"] = review_phase
    data["release"]["testerEmailCount"] = expected_testers
    data["release"]["feedbackEmail"] = feedback_email
    data["release"]["approvalReferences"] = list(config.get("approvalReferences") or [])
    data["release"]["previewLabel"] = "PRIVATE PREVIEW"
    data["approvals"] = dict(config.get("approvals") or {})
    access = config.get("access")
    if not isinstance(access, Mapping):
        raise CompanionReleaseError("Release configuration requires Access verification.")
    required_access = (
        "customDomainApplicationId",
        "pagesDevProductionApplicationId",
        "pagesDevPreviewApplicationId",
        "customDomainAnonymousDenied",
        "pagesDevProductionAnonymousDenied",
        "pagesDevPreviewAnonymousDenied",
        "appSteelGuitarRagPolicyUnchanged",
    )
    if any(not access.get(key) for key in required_access):
        raise CompanionReleaseError("All three Access applications and fail-closed checks must be recorded before release.")


def _write_root_redirect(path: Path) -> None:
    path.write_text(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"robots\" content=\"noindex,nofollow,noarchive\">"
        "<meta http-equiv=\"refresh\" content=\"0;url=/howdy\"><title>Howdy companion</title>"
        "</head><body><a href=\"/howdy\">Open the Howdy companion</a></body></html>\n",
        encoding="utf-8",
    )


def _scan_bundle(bundle_root: Path, asset_token: str) -> None:
    allowed_files = {
        "_headers",
        "_redirects",
        "404.html",
        "index.html",
        "howdy/index.html",
        "howdy/embed-demo/index.html",
        "howdy/print/index.html",
    }
    allowed_asset_names = {
        "companion.css",
        "companion.js",
        "lesson-companion.json",
        "howdy-tablature.pdf",
        "howdy-backing-track.mp3",
        "howdy-taught-solo.mp3",
        "travis-hero.jpg",
        "travis-hero.jpeg",
        "travis-hero.png",
        "travis-hero.webp",
        "metropolis.woff2",
    }
    for path in bundle_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(bundle_root).as_posix()
        allowed = relative in allowed_files
        prefix = f"assets/{asset_token}/"
        if relative.startswith(prefix) and relative.removeprefix(prefix) in allowed_asset_names:
            allowed = True
        if not allowed:
            raise CompanionReleaseError(f"Generated file is not allowlisted: {relative}")
        if path.suffix.lower() in {".vtt", ".srt", ".map"} or "transcript" in path.name.lower():
            raise CompanionReleaseError(f"Private or source material leaked into the bundle: {relative}")
        if path.stat().st_size > 25 * 1024 * 1024:
            raise CompanionReleaseError(f"Asset exceeds the Pages 25 MiB limit: {relative}")
        if path.suffix.lower() in {".html", ".css", ".js", ".json", ""}:
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            for forbidden in FORBIDDEN_TEXT:
                if forbidden.lower() in lowered:
                    raise CompanionReleaseError(f"Forbidden application/runtime reference {forbidden!r} in {relative}.")


def build_companion_bundle(
    output_dir: Path,
    *,
    companion_path: Path = DEFAULT_COMPANION,
    release: bool = False,
    release_config_path: Path | None = None,
    manifest_path: Path | None = None,
    source_date_epoch: int | None = None,
    draft_pdf_path: Path | None = None,
    draft_audio_path: Path | None = None,
    draft_solo_audio_path: Path | None = None,
) -> dict[str, Any]:
    """Assemble a complete static bundle from an explicit, reviewed allowlist."""

    output_dir = Path(output_dir).resolve()
    if output_dir == Path(output_dir.anchor) or len(output_dir.parts) < 4:
        raise CompanionReleaseError("Refusing to package into a broad filesystem path.")
    if release:
        if release_config_path is None:
            raise CompanionReleaseError("Release mode requires a private release configuration.")
        _ensure_static_sources_committed()
    data = _json(Path(companion_path).resolve())
    release_config: dict[str, Any] = {}
    if release:
        release_config = _json(Path(release_config_path).resolve())
        _merge_release_config(data, release_config)
    validate_companion(data, release=release)
    build_sha = _git_sha()
    data["buildSha"] = build_sha
    artifact_hash = _normalized_artifact_hash(data)
    data["artifactSha256"] = artifact_hash
    private_content_seed = ""
    if release:
        private_content_seed = "".join(
            str((release_config.get(key) or {}).get("sha256") or "")
            for key in ("audio", "soloAudio", "brandHero", "brandFont")
        )
    static_content_seed = "".join(
        (
            artifact_hash,
            _sha256_file(SITE_ROOT / "companion.css"),
            _sha256_file(SITE_ROOT / "companion.js"),
            private_content_seed,
        )
    )
    approved_content_hash = _sha256_bytes(static_content_seed.encode("ascii"))
    asset_token = approved_content_hash[:20]
    asset_root_url = f"/assets/{asset_token}"
    data.setdefault("media", {})["pdfUrl"] = f"{asset_root_url}/howdy-tablature.pdf"
    hero_html = ""

    stage_parent = output_dir.parent
    stage_parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=stage_parent))
    try:
        assets = stage / "assets" / asset_token
        (stage / "howdy" / "embed-demo").mkdir(parents=True)
        (stage / "howdy" / "print").mkdir(parents=True)
        assets.mkdir(parents=True)
        css_text = (SITE_ROOT / "companion.css").read_text(encoding="utf-8")
        if release:
            css_text = (
                '@font-face { font-family: "Metropolis"; src: url("'
                f'{asset_root_url}/metropolis.woff2") format("woff2"); font-display: swap; '
                'font-style: normal; font-weight: 100 900; }\n' + css_text
            )
        (assets / "companion.css").write_text(css_text, encoding="utf-8")
        shutil.copyfile(SITE_ROOT / "companion.js", assets / "companion.js")
        private_hashes: dict[str, str] = {}
        if release:
            audio_destination = assets / "howdy-backing-track.mp3"
            private_hashes["audio"] = _copy_private_asset(
                release_config,
                "audio",
                audio_destination,
                "backing track",
            )
            data["media"]["audioSha256"] = private_hashes["audio"]
            data["media"]["audioUrl"] = f"{asset_root_url}/{audio_destination.name}"
            if data["media"].get("scopes"):
                solo_audio_destination = assets / "howdy-taught-solo.mp3"
                private_hashes["soloAudio"] = _copy_private_asset(
                    release_config,
                    "soloAudio",
                    solo_audio_destination,
                    "taught solo audio",
                )
                data["media"]["soloAudioSha256"] = private_hashes["soloAudio"]
                data["media"]["soloAudioUrl"] = f"{asset_root_url}/{solo_audio_destination.name}"
            data["media"]["draftClockOnly"] = False
            brand_item = release_config.get("brandHero") or {}
            brand_source = Path(str(brand_item.get("path") or "")).expanduser().resolve()
            extension = brand_source.suffix.lower()
            if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
                raise CompanionReleaseError("Approved hero imagery must be JPG, PNG, or WebP.")
            hero_destination = assets / f"travis-hero{extension}"
            private_hashes["brandHero"] = _copy_private_asset(
                release_config,
                "brandHero",
                hero_destination,
                "Travis hero image",
            )
            data["media"]["brandHeroUrl"] = f"{asset_root_url}/{hero_destination.name}"
            private_hashes["brandFont"] = _copy_private_asset(
                release_config,
                "brandFont",
                assets / "metropolis.woff2",
                "approved Metropolis font",
            )
            hero_html = (
                f'<img class="hero-photo" src="{data["media"]["brandHeroUrl"]}" '
                'alt="Approved black-and-white pedal steel photograph">'
            )
        else:
            data["media"]["brandHeroUrl"] = None
            data["media"]["soloAudioUrl"] = None
            if draft_audio_path is not None:
                audio_source = Path(draft_audio_path).expanduser().resolve()
                expected_audio_hash = str(data["media"].get("audioSha256") or "")
                private_hashes["audio"] = _assert_hash(
                    audio_source,
                    expected_audio_hash,
                    "draft backing track",
                )
                audio_destination = assets / "howdy-backing-track.mp3"
                shutil.copyfile(audio_source, audio_destination)
                data["media"]["audioUrl"] = f"{asset_root_url}/{audio_destination.name}"
                data["media"]["draftClockOnly"] = False
            if data["media"].get("scopes") and draft_audio_path is not None and draft_solo_audio_path is None:
                raise CompanionReleaseError("Scoped draft audio requires a hash-pinned taught solo asset.")
            if draft_solo_audio_path is not None:
                if not data["media"].get("scopes"):
                    raise CompanionReleaseError("A draft taught solo asset requires media scopes.")
                solo_audio_source = Path(draft_solo_audio_path).expanduser().resolve()
                expected_solo_audio_hash = str(data["media"].get("soloAudioSha256") or "")
                private_hashes["soloAudio"] = _assert_hash(
                    solo_audio_source,
                    expected_solo_audio_hash,
                    "draft taught solo audio",
                )
                solo_audio_destination = assets / "howdy-taught-solo.mp3"
                shutil.copyfile(solo_audio_source, solo_audio_destination)
                data["media"]["soloAudioUrl"] = f"{asset_root_url}/{solo_audio_destination.name}"
        pdf_destination = assets / "howdy-tablature.pdf"
        if draft_pdf_path is not None:
            source_pdf = Path(draft_pdf_path).resolve()
            if not source_pdf.is_file():
                raise CompanionReleaseError(f"Draft PDF not found: {source_pdf}")
            shutil.copyfile(source_pdf, pdf_destination)
        else:
            generate_tablature_pdf(data, pdf_destination)
        private_hashes["pdf"] = _sha256_file(pdf_destination)
        (assets / "lesson-companion.json").write_bytes(_canonical_json_bytes(data))

        replacements = {
            "STYLE_URL": f"{asset_root_url}/companion.css",
            "SCRIPT_URL": f"{asset_root_url}/companion.js",
            "COMPANION_URL": f"{asset_root_url}/lesson-companion.json",
            "PDF_URL": f"{asset_root_url}/howdy-tablature.pdf",
            "REVISION": _ascii(data["revision"]),
            "BUILD_SHA": build_sha[:12],
            "HERO_IMAGE": hero_html,
            "COMPANION_MARKUP": (TEMPLATE_ROOT / "companion.fragment.html").read_text(encoding="utf-8"),
        }
        (stage / "howdy" / "index.html").write_text(
            _render_template(TEMPLATE_ROOT / "full.html", replacements), encoding="utf-8"
        )
        (stage / "howdy" / "embed-demo" / "index.html").write_text(
            _render_template(TEMPLATE_ROOT / "embed.html", replacements), encoding="utf-8"
        )
        (stage / "howdy" / "print" / "index.html").write_text(
            _render_template(TEMPLATE_ROOT / "print.html", replacements), encoding="utf-8"
        )
        (stage / "404.html").write_text(
            _render_template(TEMPLATE_ROOT / "404.html", replacements), encoding="utf-8"
        )
        _write_root_redirect(stage / "index.html")
        (stage / "_redirects").write_text(
            "/ /howdy 302\n"
            "/howdy /howdy/index.html 200\n"
            "/howdy/embed-demo /howdy/embed-demo/index.html 200\n"
            "/howdy/print /howdy/print/index.html 200\n",
            encoding="utf-8",
        )
        csp = (
            "default-src 'self'; base-uri 'none'; object-src 'none'; frame-src 'none'; "
            "frame-ancestors 'none'; form-action 'none'; connect-src 'self'; media-src 'self' blob:; "
            "img-src 'self' data:; font-src 'self'; script-src 'self'; style-src 'self'"
        )
        (stage / "_headers").write_text(
            "/*\n"
            f"  Content-Security-Policy: {csp}\n"
            "  X-Robots-Tag: noindex, nofollow, noarchive\n"
            "  Referrer-Policy: no-referrer\n"
            "  X-Content-Type-Options: nosniff\n"
            "  X-Frame-Options: DENY\n"
            "  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()\n"
            "  Cross-Origin-Resource-Policy: same-origin\n"
            "/index.html\n"
            "  Cache-Control: no-store\n"
            "/404.html\n"
            "  Cache-Control: no-store\n"
            "/howdy*\n"
            "  Cache-Control: no-store\n"
            f"/assets/{asset_token}/*\n"
            "  Cache-Control: private, max-age=31536000, immutable\n"
            f"/assets/{asset_token}/lesson-companion.json\n"
            "  ! Cache-Control\n"
            "  Cache-Control: no-store\n",
            encoding="utf-8",
        )
        _scan_bundle(stage, asset_token)
        if output_dir.exists():
            if not output_dir.is_dir():
                raise CompanionReleaseError(f"Output path exists and is not a directory: {output_dir}")
            shutil.rmtree(output_dir)
        stage.rename(output_dir)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    asset_hashes = {
        path.relative_to(output_dir).as_posix(): _sha256_file(path)
        for path in sorted(output_dir.rglob("*"))
        if path.is_file()
    }
    manifest = {
        "schemaVersion": "travis_companion_release_manifest_v1",
        "gitSha": build_sha,
        "companionRevision": data["revision"],
        "artifactSha256": artifact_hash,
        "approvedContentHash": approved_content_hash,
        "artifactHashScope": "canonical companion content excluding build SHA and generated asset URLs",
        "assetHashes": asset_hashes,
        "approvalReferences": list(data["release"].get("approvalReferences") or []),
        "buildTime": _source_date(source_date_epoch),
        "releaseMode": "release" if release else "draft",
        "intendedCloudflareProject": PROJECT_NAME,
        "intendedHostname": HOSTNAME,
        "allowedRoutes": ["/", "/howdy", "/howdy/embed-demo", "/howdy/print", f"/assets/{asset_token}/*"],
        "reviewPhase": data["release"].get("reviewPhase"),
        "accessTesterCount": int(data["release"].get("testerEmailCount", 0)),
        "immutablePagesDeploymentUrl": None,
    }
    target_manifest = Path(manifest_path).resolve() if manifest_path else output_dir.with_suffix(".release-manifest.json")
    target_manifest.parent.mkdir(parents=True, exist_ok=True)
    target_manifest.write_bytes(_canonical_json_bytes(manifest))
    return manifest
