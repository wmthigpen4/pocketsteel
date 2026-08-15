"""Validate and package deterministic TTT Practice Guide pilots.

Private transcripts and comments are authoring inputs only.  The emitted bundle
contains four reviewed guide artifacts, safe lesson metadata, short excerpts,
and one-page PDFs.  It contains no model client or private-source body.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Mapping, Sequence

from steel_guitar_rag.ttt_concept_graph import (
    TranscriptCue,
    parse_timestamped_transcript,
    validate_catalog,
    validate_taxonomy,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
CONTENT_ROOT = PACKAGE_ROOT / "content"
SITE_ROOT = PACKAGE_ROOT / "site"
TEMPLATE_ROOT = PACKAGE_ROOT / "templates"
DEFAULT_COLLECTION = CONTENT_ROOT / "pilot-guides.draft.json"
DEFAULT_CATALOG = CONTENT_ROOT / "lesson-catalog.json"
DEFAULT_TAXONOMY = CONTENT_ROOT / "concept-taxonomy.json"

FORMULA_SEMITONES = {
    "1": 0,
    "b3": 3,
    "3": 4,
    "5": 7,
    "6": 9,
    "b7": 10,
    "7": 11,
    "b9": 13,
}
EXPECTED_FORMULAS = {
    "major_triad": (0, 4, 7),
    "minor_triad": (0, 3, 7),
    "dominant_7": (0, 4, 7, 10),
    "major_7": (0, 4, 7, 11),
    "dominant_7_flat_9": (0, 4, 7, 10, 13),
}
EXPECTED_GUIDE_BLOCKS = (
    "point",
    "moments",
    "practice",
    "diagnostics",
    "conceptTrails",
    "visualization",
    "nextLessons",
)
FORBIDDEN_BUNDLE_TEXT = (
    "raw_vtt",
    ".timestamped.txt",
    "corpus-private",
    "/users/cory",
    "openai.com/v1",
    "anthropic.com",
    "ollama",
    "chroma",
    "/api/answer",
    "/api/search",
    "sourceMappingURL",
)


class PracticeGuideReleaseError(ValueError):
    """Raised when a guide cannot be source-validated or safely packaged."""


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PracticeGuideReleaseError(f"Cannot read JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise PracticeGuideReleaseError(f"Expected a JSON object in {path}")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
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


def _normalize_text(value: object) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).split())


def _format_time(milliseconds: int) -> str:
    seconds = max(0, int(milliseconds) // 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"


def _ascii(value: object) -> str:
    replacements = {"—": "-", "–": "-", "’": "'", "“": '"', "”": '"', "→": "->", "♭": "b", "♯": "#"}
    text = str(value or "")
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text.encode("ascii", "replace").decode("ascii")


def _wrap_words(text: str, maximum: int) -> list[str]:
    words = _ascii(text).split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if current and len(candidate) > maximum:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def _formula_semitones(formula: str) -> tuple[int, ...]:
    tokens = re.split(r"[-–]", formula.replace("♭", "b").replace("♯", "#"))
    try:
        return tuple(FORMULA_SEMITONES[token] for token in tokens)
    except KeyError as error:
        raise PracticeGuideReleaseError(f"Unsupported deterministic interval token: {error.args[0]}") from error


def validate_collection(collection: Mapping[str, Any], taxonomy: Mapping[str, Any], catalog: Mapping[str, Any]) -> None:
    validate_taxonomy(taxonomy)
    validate_catalog(catalog)
    if collection.get("schemaVersion") != "practice_guide_collection_v1":
        raise PracticeGuideReleaseError("Unsupported practice guide collection schema")
    if collection.get("runtimeMode") != "published_deterministic" or collection.get("modelCallsAllowed") is not False:
        raise PracticeGuideReleaseError("Learner runtime must be deterministic with model calls disabled")
    source_policy = collection.get("sourcePolicy") or {}
    forbidden_source_flags = ("rawTranscriptsIncluded", "rawCommentsIncluded", "memberIdentitiesIncluded", "uncertainRecommendationsPublished", "learnerRuntimeUsesModels")
    if any(source_policy.get(flag) is not False for flag in forbidden_source_flags):
        raise PracticeGuideReleaseError("The static collection contains an unsafe source-policy flag")

    concept_by_id = {str(item["id"]): item for item in taxonomy["concepts"]}
    lesson_by_id = {str(item["id"]): item for item in catalog["lessons"]}
    for concept_id, expected in EXPECTED_FORMULAS.items():
        concept = concept_by_id.get(concept_id)
        if not concept or _formula_semitones(str(concept.get("formula"))) != expected:
            raise PracticeGuideReleaseError(f"Deterministic theory validation failed for {concept_id}")

    guides = collection.get("guides")
    if not isinstance(guides, list) or len(guides) != 4:
        raise PracticeGuideReleaseError("The pilot must contain exactly four guides")
    ids = [str(item.get("companionId") or "") for item in guides]
    slugs = [str(item.get("slug") or "") for item in guides]
    if "" in ids or len(ids) != len(set(ids)) or "" in slugs or len(slugs) != len(set(slugs)):
        raise PracticeGuideReleaseError("Guide IDs and slugs must be present and unique")

    for guide in guides:
        if guide.get("schemaVersion") != "lesson_companion_v2":
            raise PracticeGuideReleaseError(f"Guide {guide.get('companionId')} must use lesson_companion_v2")
        runtime = guide.get("runtime") or {}
        if runtime.get("mode") != "published_deterministic" or runtime.get("modelCallsAllowed") is not False:
            raise PracticeGuideReleaseError(f"Guide {guide.get('companionId')} requires a deterministic static runtime")
        if tuple(guide.get("orderedGuideBlocks") or ()) != EXPECTED_GUIDE_BLOCKS:
            raise PracticeGuideReleaseError(f"Guide {guide.get('companionId')} has an invalid ordered block contract")
        if guide.get("lessonId") not in lesson_by_id:
            raise PracticeGuideReleaseError(f"Guide {guide.get('companionId')} references an unknown lesson")
        if guide.get("type") not in {"technique_coach", "pedal_theory_lab", "fretboard_path_guide", "application_guide"}:
            raise PracticeGuideReleaseError(f"Guide {guide.get('companionId')} has an unknown type")
        claims = guide.get("claims") or []
        if not claims:
            raise PracticeGuideReleaseError(f"Guide {guide.get('companionId')} requires claim provenance")
        for claim in claims:
            if claim.get("provenance") not in {"transcript", "deterministic_rule", "editorial", "human_transcription"}:
                raise PracticeGuideReleaseError(f"Claim {claim.get('id')} has an unknown provenance")
            if not str(claim.get("reviewStatus") or "").strip() or not str(claim.get("text") or "").strip():
                raise PracticeGuideReleaseError(f"Claim {claim.get('id')} requires text and review status")
        moments = guide.get("moments") or []
        if not 3 <= len(moments) <= 7:
            raise PracticeGuideReleaseError(f"Guide {guide.get('companionId')} requires three to seven moments")
        moment_ids = {str(item.get("id") or "") for item in moments}
        if "" in moment_ids or len(moment_ids) != len(moments):
            raise PracticeGuideReleaseError(f"Guide {guide.get('companionId')} has invalid moment IDs")
        for moment in moments:
            if moment.get("quoteKind") != "verbatim_excerpt" or not str(moment.get("excerpt") or "").strip():
                raise PracticeGuideReleaseError(f"Moment {moment.get('id')} requires a short verbatim excerpt")
            if len(str(moment["excerpt"]).split()) > 22:
                raise PracticeGuideReleaseError(f"Moment {moment.get('id')} exceeds the short-excerpt limit")
            if int(moment.get("startMs", -1)) < 0 or int(moment.get("endMs", -1)) < int(moment.get("startMs", -1)):
                raise PracticeGuideReleaseError(f"Moment {moment.get('id')} has invalid timing")
            if any(concept_id not in concept_by_id for concept_id in moment.get("conceptIds") or []):
                raise PracticeGuideReleaseError(f"Moment {moment.get('id')} references an unknown concept")
        for diagnostic in guide.get("diagnostics") or []:
            if diagnostic.get("sourceKind") not in {"comment_theme", "editorial"}:
                raise PracticeGuideReleaseError("Diagnostics must distinguish comment themes from editorial guidance")
        for trail in guide.get("conceptTrails") or []:
            if trail.get("conceptId") not in concept_by_id or trail.get("momentId") not in moment_ids:
                raise PracticeGuideReleaseError("Concept Trails must reference known concepts and source moments")
            targets = trail.get("targets") or []
            if not 1 <= len(targets) <= 3:
                raise PracticeGuideReleaseError("Each Concept Trail may publish one to three destinations")
            for target in targets:
                lesson = lesson_by_id.get(str(target.get("lessonId") or ""))
                if not lesson or lesson.get("isZoom") is not False:
                    raise PracticeGuideReleaseError("Every Concept Trail target must be a cataloged non-Zoom lesson")
                if int(target.get("startMs", -1)) < 0 or int(target.get("endMs", -1)) <= int(target.get("startMs", -1)):
                    raise PracticeGuideReleaseError("Concept Trail target timing is invalid")
                if not str(target.get("reason") or "").strip() or not str(target.get("estimatedDetour") or "").strip():
                    raise PracticeGuideReleaseError("Concept Trail targets require a reason and detour estimate")
                evidence_excerpt = str(target.get("evidenceExcerpt") or "").strip()
                if not evidence_excerpt or len(evidence_excerpt.split()) > 22:
                    raise PracticeGuideReleaseError("Concept Trail targets require a short verbatim evidence excerpt")
        if len(guide.get("nextLessons") or []) not in {2, 3}:
            raise PracticeGuideReleaseError("Keep Going must contain two or three lessons")
        if any(item not in lesson_by_id for item in guide.get("nextLessons") or []):
            raise PracticeGuideReleaseError("Keep Going contains an unknown lesson")


def _transcript_for_lesson(transcript_root: Path, lesson: Mapping[str, Any]) -> Path:
    matches = list(Path(transcript_root).expanduser().resolve().rglob(f"{lesson['sourceSlug']}.timestamped.txt"))
    matches = [path for path in matches if not re.search(r"zoom|ttt members|sunday night steel", path.as_posix(), re.I)]
    if len(matches) != 1:
        raise PracticeGuideReleaseError(f"Expected one non-Zoom transcript for {lesson['id']}; found {len(matches)}")
    return matches[0]


def _selected_cues(cues: Sequence[TranscriptCue], start_ms: int, end_ms: int) -> list[TranscriptCue]:
    return [cue for cue in cues if cue.start_ms >= start_ms and cue.end_ms <= end_ms]


def _validate_cue_range(cues: Sequence[TranscriptCue], start_ms: int, end_ms: int, label: str) -> list[TranscriptCue]:
    starts = {cue.start_ms for cue in cues}
    ends = {cue.end_ms for cue in cues}
    if start_ms not in starts or end_ms not in ends:
        raise PracticeGuideReleaseError(f"{label} does not begin and end on exact VTT cue boundaries")
    selected = _selected_cues(cues, start_ms, end_ms)
    if not selected:
        raise PracticeGuideReleaseError(f"{label} does not select any complete VTT cues")
    return selected


def verify_private_sources(
    collection: Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    transcript_root: Path,
    howdy_evidence_path: Path,
) -> dict[str, Any]:
    """Verify every published excerpt and detour against private source boundaries."""

    lesson_by_id = {str(item["id"]): item for item in catalog["lessons"]}
    cues_by_lesson: dict[str, list[TranscriptCue]] = {}
    verified_moments = 0
    verified_targets: set[tuple[str, int, int]] = set()
    howdy_evidence = _json(howdy_evidence_path)
    howdy_moments = {
        (int(item.get("lessonTimeMs", -1)), _normalize_text(item.get("excerpt"))): item
        for item in howdy_evidence.get("lessonMoments") or []
    }

    def cues_for(lesson_id: str) -> list[TranscriptCue]:
        if lesson_id not in cues_by_lesson:
            cues_by_lesson[lesson_id] = parse_timestamped_transcript(_transcript_for_lesson(transcript_root, lesson_by_id[lesson_id]))
        return cues_by_lesson[lesson_id]

    for guide in collection["guides"]:
        if guide["lessonId"] == "howdy-solo":
            for moment in guide["moments"]:
                key = (int(moment["startMs"]), _normalize_text(moment["excerpt"]))
                if key not in howdy_moments or moment.get("evidenceRef") != howdy_evidence.get("revision"):
                    raise PracticeGuideReleaseError(f"Howdy moment {moment['id']} is absent from the approved private index")
                verified_moments += 1
        else:
            cues = cues_for(str(guide["lessonId"]))
            for moment in guide["moments"]:
                selected = _validate_cue_range(cues, int(moment["startMs"]), int(moment["endMs"]), f"Moment {moment['id']}")
                evidence = _normalize_text(" ".join(cue.text for cue in selected))
                if _normalize_text(moment["excerpt"]) not in evidence:
                    raise PracticeGuideReleaseError(f"Moment {moment['id']} excerpt is not present in its exact cue window")
                verified_moments += 1
        for trail in guide["conceptTrails"]:
            for target in trail["targets"]:
                key = (str(target["lessonId"]), int(target["startMs"]), int(target["endMs"]))
                if key in verified_targets:
                    continue
                target_cues = cues_for(key[0])
                selected = _validate_cue_range(
                    target_cues,
                    key[1],
                    key[2],
                    f"Concept Trail {key[0]} {key[1]}-{key[2]}",
                )
                evidence = _normalize_text(" ".join(cue.text for cue in selected))
                if _normalize_text(target["evidenceExcerpt"]) not in evidence:
                    raise PracticeGuideReleaseError(
                        f"Concept Trail target excerpt is not present in its exact cue window for {key[0]}"
                    )
                if key[2] > int(lesson_by_id[key[0]]["durationMs"]):
                    raise PracticeGuideReleaseError(f"Concept Trail target exceeds catalog duration for {key[0]}")
                verified_targets.add(key)
    return {
        "schemaVersion": "ttt_source_verification_v1",
        "verifiedMoments": verified_moments,
        "verifiedConceptTrailTargets": len(verified_targets),
        "nonZoomOnly": True,
        "rawSourcesDeployable": False,
        "howdyEvidenceRevision": howdy_evidence.get("revision"),
    }


def _public_collection(
    collection: Mapping[str, Any],
    taxonomy: Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    asset_root_url: str,
) -> dict[str, Any]:
    public = copy.deepcopy(dict(collection))
    public["artifactSha256"] = ""
    public["buildSha"] = _git_sha()
    public["concepts"] = [
        {key: item[key] for key in ("id", "label", "definition", "formula", "prerequisiteConceptIds", "deeperConceptIds", "confusionConceptIds") if key in item}
        for item in taxonomy["concepts"]
    ]
    public["lessonCatalog"] = [
        {key: item[key] for key in ("id", "title", "url", "durationMs", "depth", "isZoom")}
        for item in catalog["lessons"]
    ]
    for guide in public["guides"]:
        guide["print"]["pdfUrl"] = f"{asset_root_url}/{guide['slug']}-practice-card.pdf"
    public["artifactSha256"] = _sha256_bytes(_canonical_json_bytes(public))
    return public


def generate_practice_card_pdf(guide: Mapping[str, Any], collection_revision: str, output_path: Path) -> Path:
    """Render one deterministic one-page practice card from the v2 guide."""

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as error:
        raise PracticeGuideReleaseError("PDF generation requires reportlab") from error

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = letter
    page = canvas.Canvas(str(output_path), pagesize=letter, pageCompression=1, invariant=1)
    page.setTitle(_ascii(guide["print"]["title"]))
    page.setAuthor("Travis Toy Tutorials / Steel Guitar RAG")
    page.setSubject("Deterministic lesson practice card")
    teal = colors.HexColor("#134361")
    coral = colors.HexColor("#ff3f20")
    ink = colors.HexColor("#13222c")
    muted = colors.HexColor("#66747d")
    line = colors.HexColor("#dce3e7")
    soft = colors.HexColor("#f4f6f7")

    page.setFillColor(teal)
    page.rect(0, height - 104, width, 104, stroke=0, fill=1)
    page.setFillColor(colors.white)
    page.setFont("Helvetica-Bold", 9)
    page.drawString(42, height - 28, "TRAVIS TOY TUTORIALS - PRACTICE GUIDE")
    page.setFont("Helvetica-Bold", 20)
    page.drawString(42, height - 57, _ascii(guide["print"]["title"]))
    page.setFont("Helvetica", 8)
    page.drawString(42, height - 76, _ascii(guide["print"]["subtitle"]))
    page.drawRightString(width - 42, height - 28, _ascii(collection_revision))
    page.drawRightString(width - 42, height - 42, "Page 1 of 1")

    y = height - 132

    def heading(label: str) -> None:
        nonlocal y
        page.setFillColor(coral)
        page.setFont("Helvetica-Bold", 8)
        page.drawString(42, y, label.upper())
        y -= 16

    def paragraph(text: str, *, size: float = 9, leading: float = 13, indent: float = 0) -> None:
        nonlocal y
        page.setFillColor(ink)
        page.setFont("Helvetica", size)
        for line_text in _wrap_words(text, 96 if not indent else 88):
            page.drawString(42 + indent, y, line_text)
            y -= leading
        y -= 4

    heading("The point")
    paragraph(str(guide["point"]["outcome"]), size=11, leading=15)
    session = next((item for item in guide["point"]["sessions"] if int(item["minutes"]) == 5), guide["point"]["sessions"][0])
    page.setFillColor(soft)
    page.roundRect(42, y - 38, width - 84, 46, 6, stroke=0, fill=1)
    page.setFillColor(teal)
    page.setFont("Helvetica-Bold", 9)
    page.drawString(54, y - 8, _ascii(f"{session['minutes']}-MINUTE SESSION - {session['label']}"))
    page.setFillColor(ink)
    page.setFont("Helvetica", 8)
    session_lines = _wrap_words(str(session["instruction"]), 88)[:2]
    for index, line_text in enumerate(session_lines):
        page.drawString(54, y - 23 - index * 11, line_text)
    y -= 58

    heading("Try this now")
    page.setFillColor(muted)
    page.setFont("Helvetica", 7.5)
    page.drawString(42, y, _ascii(f"{guide['practice']['tempo']}  |  {guide['practice']['repetitions']}"))
    y -= 18
    for index, step in enumerate(guide["practice"]["steps"], start=1):
        page.setFillColor(coral)
        page.setFont("Helvetica-Bold", 8)
        page.drawString(44, y, f"{index}.")
        paragraph(str(step), size=8.5, leading=11, indent=18)

    y -= 2
    heading("Self-check")
    for item in guide["practice"]["hearSeeFeel"]:
        page.setStrokeColor(teal)
        page.rect(44, y - 2, 7, 7, stroke=1, fill=0)
        page.setFillColor(ink)
        page.setFont("Helvetica", 8.2)
        for line_index, line_text in enumerate(_wrap_words(str(item), 83)):
            page.drawString(60, y - line_index * 10, line_text)
        y -= 12 * max(1, len(_wrap_words(str(item), 83)))
    y -= 4

    page.setFillColor(colors.HexColor("#e6f3ee"))
    success_lines = _wrap_words(str(guide["practice"]["success"]), 84)
    box_height = 24 + 11 * len(success_lines)
    page.roundRect(42, y - box_height + 8, width - 84, box_height, 6, stroke=0, fill=1)
    page.setFillColor(colors.HexColor("#195b49"))
    page.setFont("Helvetica-Bold", 8)
    page.drawString(54, y - 6, "SUCCESS CONDITION")
    page.setFont("Helvetica", 8)
    for index, line_text in enumerate(success_lines):
        page.drawString(54, y - 19 - index * 11, line_text)
    y -= box_height + 8

    if y > 118:
        heading("Adjust the difficulty")
        page.setFillColor(teal)
        page.setFont("Helvetica-Bold", 8)
        page.drawString(42, y, "MAKE IT EASIER")
        page.drawString(width / 2 + 8, y, "NEXT CHALLENGE")
        y -= 13
        page.setFillColor(ink)
        page.setFont("Helvetica", 7.5)
        easier = _wrap_words(str(guide["practice"]["easier"]), 42)[:3]
        challenge = _wrap_words(str(guide["practice"]["challenge"]), 42)[:3]
        for index in range(max(len(easier), len(challenge))):
            if index < len(easier):
                page.drawString(42, y - index * 10, easier[index])
            if index < len(challenge):
                page.drawString(width / 2 + 8, y - index * 10, challenge[index])

    page.setStrokeColor(line)
    page.line(42, 46, width - 42, 46)
    page.setFillColor(muted)
    page.setFont("Helvetica", 6.8)
    page.drawString(42, 32, _ascii(f"Key/context: {guide['setup']['key']}"))
    page.drawString(42, 20, "Member-use owner preview - source-backed guidance - no raw comments or transcript included")
    page.drawRightString(width - 42, 20, "Powered by Steel Guitar RAG")
    page.showPage()
    page.save()
    return output_path


def _render_template(path: Path, replacements: Mapping[str, str]) -> str:
    value = Path(path).read_text(encoding="utf-8")
    for key, replacement in replacements.items():
        value = value.replace(f"__{key}__", replacement)
    unresolved = re.findall(r"__[A-Z_]+__", value)
    if unresolved:
        raise PracticeGuideReleaseError(f"Unresolved template tokens in {path.name}: {', '.join(unresolved)}")
    return value


def _scan_bundle(bundle_root: Path, asset_token: str, guide_slugs: Sequence[str]) -> None:
    allowed = {
        "index.html",
        "404.html",
        "_headers",
        "_redirects",
        "release-manifest.json",
        "practice-guide/index.html",
        "practice-guide/jump/index.html",
        *{f"practice-guide/{slug}/index.html" for slug in guide_slugs},
    }
    asset_prefix = f"assets/{asset_token}/"
    asset_names = {"practice-guide.css", "practice-guide.js", "practice-guides.json", *{f"{slug}-practice-card.pdf" for slug in guide_slugs}}
    for path in bundle_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(bundle_root).as_posix()
        if relative not in allowed and not (relative.startswith(asset_prefix) and relative.removeprefix(asset_prefix) in asset_names):
            raise PracticeGuideReleaseError(f"Generated file is not allowlisted: {relative}")
        if path.suffix.lower() in {".vtt", ".srt", ".map"} or "transcript" in path.name.lower() or "comment" in path.name.lower():
            raise PracticeGuideReleaseError(f"Private source material leaked into the bundle: {relative}")
        if path.suffix.lower() in {".html", ".css", ".js", ".json", ""}:
            lowered = path.read_text(encoding="utf-8").lower()
            for forbidden in FORBIDDEN_BUNDLE_TEXT:
                present = (
                    bool(re.search(rf"\b{re.escape(forbidden.lower())}\b", lowered))
                    if forbidden in {"chroma", "ollama"}
                    else forbidden.lower() in lowered
                )
                if present:
                    raise PracticeGuideReleaseError(f"Forbidden runtime/source reference {forbidden!r} in {relative}")


def build_practice_guide_bundle(
    output_dir: Path,
    *,
    collection_path: Path = DEFAULT_COLLECTION,
    taxonomy_path: Path = DEFAULT_TAXONOMY,
    catalog_path: Path = DEFAULT_CATALOG,
    transcript_root: Path | None = None,
    howdy_evidence_path: Path | None = None,
    printable_output_dir: Path | None = None,
) -> dict[str, Any]:
    """Build an isolated, allowlisted local preview bundle."""

    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise PracticeGuideReleaseError(f"Output directory already exists: {output_dir}")
    if len(output_dir.parts) < 4:
        raise PracticeGuideReleaseError("Refusing to package into a broad filesystem path")

    collection = _json(collection_path)
    taxonomy = _json(taxonomy_path)
    catalog = _json(catalog_path)
    validate_collection(collection, taxonomy, catalog)
    source_verification: dict[str, Any] = {"status": "not_requested"}
    if transcript_root is not None or howdy_evidence_path is not None:
        if transcript_root is None or howdy_evidence_path is None:
            raise PracticeGuideReleaseError("Private-source verification requires both transcript root and Howdy evidence")
        source_verification = verify_private_sources(
            collection,
            catalog,
            transcript_root=transcript_root,
            howdy_evidence_path=howdy_evidence_path,
        )

    source_seed = _git_sha().encode("ascii") + b"".join(
        Path(path).read_bytes()
        for path in (collection_path, taxonomy_path, catalog_path, SITE_ROOT / "practice-guide.css", SITE_ROOT / "practice-guide.js")
    )
    asset_token = _sha256_bytes(source_seed)[:20]
    asset_root_url = f"/assets/{asset_token}"
    public_collection = _public_collection(collection, taxonomy, catalog, asset_root_url=asset_root_url)
    guide_slugs = [str(item["slug"]) for item in public_collection["guides"]]

    stage_parent = output_dir.parent
    stage_parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=stage_parent))
    try:
        assets = stage / "assets" / asset_token
        assets.mkdir(parents=True)
        (stage / "practice-guide" / "jump").mkdir(parents=True)
        shutil.copyfile(SITE_ROOT / "practice-guide.css", assets / "practice-guide.css")
        shutil.copyfile(SITE_ROOT / "practice-guide.js", assets / "practice-guide.js")
        (assets / "practice-guides.json").write_bytes(_canonical_json_bytes(public_collection))

        pdf_hashes: dict[str, str] = {}
        for guide in public_collection["guides"]:
            slug = str(guide["slug"])
            pdf = generate_practice_card_pdf(guide, str(public_collection["revision"]), assets / f"{slug}-practice-card.pdf")
            pdf_hashes[slug] = _sha256_file(pdf)
            if printable_output_dir is not None:
                final_root = Path(printable_output_dir).expanduser().resolve()
                final_root.mkdir(parents=True, exist_ok=True)
                revision_token = re.sub(r"[^a-z0-9.-]+", "-", str(public_collection["revision"]).lower()).strip("-")
                final_path = final_root / f"{slug}-practice-card-{revision_token}.pdf"
                if final_path.exists():
                    raise PracticeGuideReleaseError(f"Printable output already exists: {final_path}")
                shutil.copyfile(pdf, final_path)

        replacements = {
            "STYLE_URL": f"{asset_root_url}/practice-guide.css",
            "SCRIPT_URL": f"{asset_root_url}/practice-guide.js",
            "COLLECTION_URL": f"{asset_root_url}/practice-guides.json",
        }
        (stage / "practice-guide" / "index.html").write_text(_render_template(TEMPLATE_ROOT / "index.html", replacements), encoding="utf-8")
        (stage / "practice-guide" / "jump" / "index.html").write_text(_render_template(TEMPLATE_ROOT / "jump.html", replacements), encoding="utf-8")
        for guide in public_collection["guides"]:
            guide_dir = stage / "practice-guide" / str(guide["slug"])
            guide_dir.mkdir(parents=True)
            guide_replacements = {**replacements, "GUIDE_SLUG": str(guide["slug"]), "GUIDE_TITLE": _ascii(guide["title"])}
            (guide_dir / "index.html").write_text(_render_template(TEMPLATE_ROOT / "guide.html", guide_replacements), encoding="utf-8")
        (stage / "404.html").write_text(_render_template(TEMPLATE_ROOT / "404.html", replacements), encoding="utf-8")
        (stage / "index.html").write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow,noarchive"><meta http-equiv="refresh" content="0;url=/practice-guide/"><title>TTT Practice Guide</title></head><body><a href="/practice-guide/">Open the practice guides</a></body></html>\n',
            encoding="utf-8",
        )
        (stage / "_redirects").write_text("/ /practice-guide/ 302\n", encoding="utf-8")
        (stage / "_headers").write_text(
            "/*\n  X-Robots-Tag: noindex, nofollow, noarchive\n  Referrer-Policy: no-referrer\n  X-Content-Type-Options: nosniff\n  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()\n  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'none'; connect-src 'self'; object-src 'none'; form-action 'none'; frame-ancestors 'self'\n  Cache-Control: no-store\n\n/assets/*\n  Cache-Control: private, max-age=31536000, immutable\n",
            encoding="utf-8",
        )

        manifest = {
            "schemaVersion": "ttt_practice_guide_release_manifest_v1",
            "gitSha": _git_sha(),
            "revision": public_collection["revision"],
            "artifactSha256": public_collection["artifactSha256"],
            "assetToken": asset_token,
            "assetHashes": {
                "practice-guide.css": _sha256_file(assets / "practice-guide.css"),
                "practice-guide.js": _sha256_file(assets / "practice-guide.js"),
                "practice-guides.json": _sha256_file(assets / "practice-guides.json"),
                **{f"{slug}-practice-card.pdf": value for slug, value in pdf_hashes.items()},
            },
            "sourceVerification": source_verification,
            "routes": ["/practice-guide/", "/practice-guide/jump/", *[f"/practice-guide/{slug}/" for slug in guide_slugs]],
            "deployment": "not_performed_local_ungated",
        }
        (stage / "release-manifest.json").write_bytes(_canonical_json_bytes(manifest))
        _scan_bundle(stage, asset_token, guide_slugs)
        shutil.move(str(stage), str(output_dir))
        return manifest
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
