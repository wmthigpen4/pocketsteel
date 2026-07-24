"""Provider-neutral optical music recognition for clean printed notation.

Source bytes and rendered pages remain in memory. Recognition, normalization,
and validation are separate so a managed provider can replace the local reader
without changing the score editor or deterministic pedal-steel arranger.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol, Sequence

from PIL import Image, ImageStat


OMR_RESULT_SCHEMA_VERSION = "score_omr_result_v1"
OMR_INSPECTION_SCHEMA_VERSION = "score_document_inspection_v1"
MAX_PDF_PAGES = 12
MAX_SELECTED_PAGES = 8
MAX_RENDERED_PIXELS = 18_000_000
LOW_CONFIDENCE_THRESHOLD = 0.8


class ScoreOmrError(ValueError):
    """A safe, user-facing OMR error."""


@dataclass(frozen=True)
class ScoreOmrPage:
    page_number: int
    image_bytes: bytes
    mime_type: str = "image/png"


class ScoreOmrProvider(Protocol):
    """Replaceable interface implemented by local or managed score readers."""

    provider_id: str

    def recognize_page(self, page: ScoreOmrPage) -> Mapping[str, Any]:
        """Return provider output for one rendered page."""


class LocalVisionOmrProvider:
    """Adapter around the existing loopback vision reader."""

    provider_id = "local_vision"

    def __init__(self, client: Callable[[str, str], Mapping[str, Any]]) -> None:
        self._client = client

    def recognize_page(self, page: ScoreOmrPage) -> Mapping[str, Any]:
        return self._client(base64.b64encode(page.image_bytes).decode("ascii"), page.mime_type)


def provider_catalog() -> list[dict[str, Any]]:
    """Return benchmark candidates without implying that a provider is enabled."""

    return [
        {
            "id": "local_vision",
            "label": "Local vision / Audiveris pipeline",
            "mode": "local",
            "available": True,
            "trainingUse": False,
        },
        {
            "id": "flat_interactive_omr",
            "label": "Flat Interactive OMR",
            "mode": "managed",
            "available": False,
            "reason": "Requires provider agreement, credentials, privacy review, and a completed benchmark.",
            "beta": True,
        },
    ]


def inspect_pdf(raw: bytes) -> dict[str, Any]:
    """Render small page previews for transient client-side page selection."""

    document = _open_pdf(raw)
    page_count = len(document)
    if page_count < 1:
        raise ScoreOmrError("That PDF does not contain any pages.")
    if page_count > MAX_PDF_PAGES:
        raise ScoreOmrError(
            f"That PDF has {page_count} pages. Choose a PDF with no more than {MAX_PDF_PAGES} pages."
        )
    pages = []
    for page_index in range(page_count):
        image = _render_pdf_page(document, page_index, scale=0.45)
        preview = _encode_image(image, "JPEG", quality=72)
        pages.append(
            {
                "pageNumber": page_index + 1,
                "width": image.width,
                "height": image.height,
                "previewMimeType": "image/jpeg",
                "previewBase64": base64.b64encode(preview).decode("ascii"),
            }
        )
    return {
        "schemaVersion": OMR_INSPECTION_SCHEMA_VERSION,
        "pageCount": page_count,
        "pages": pages,
        "sourceRetained": False,
    }


def recognize_printed_document(
    *,
    raw: bytes,
    source_type: str,
    title: str,
    selected_pages: Sequence[int] | None,
    selected_part: str | None,
    provider: ScoreOmrProvider,
    normalize: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Recognize selected printed pages and return one normalized score draft."""

    if source_type == "pdf":
        document = _open_pdf(raw)
        page_count = len(document)
        page_numbers = _selected_page_numbers(selected_pages, page_count)
        pages = [
            ScoreOmrPage(
                page_number=page_number,
                image_bytes=_encode_image(
                    _render_pdf_page(document, page_number - 1, scale=1.8),
                    "PNG",
                ),
            )
            for page_number in page_numbers
        ]
    else:
        page_count = 1
        page_numbers = [1]
        _validate_raster(raw)
        pages = [ScoreOmrPage(page_number=1, image_bytes=raw, mime_type=source_type)]

    page_drafts: list[dict[str, Any]] = []
    recognized_parts: list[dict[str, Any]] = []
    provider_selected_part = ""
    for page in pages:
        interpreted = provider.recognize_page(page)
        if not recognized_parts and isinstance(interpreted.get("parts"), Sequence):
            recognized_parts = [
                {
                    "id": str(part.get("id") or "")[:80],
                    "name": str(part.get("name") or part.get("label") or "Staff")[:120],
                    "eventCount": _nonnegative_int(part.get("eventCount")),
                }
                for part in interpreted["parts"]
                if isinstance(part, Mapping) and part.get("id")
            ][:16]
            provider_selected_part = str(interpreted.get("selectedPartId") or "")
        assessment = interpreted.get("inputAssessment") if isinstance(interpreted, Mapping) else None
        if isinstance(assessment, Mapping):
            kind = str(assessment.get("kind") or "").strip().lower()
            if kind in {"handwritten", "tablature", "handwritten_chord_chart"}:
                raise ScoreOmrError(
                    "This reader supports clean printed Western notation, not handwriting, chord-chart handwriting, or existing tablature."
                )
            if assessment.get("accepted") is False:
                guidance = str(assessment.get("rescanGuidance") or "").strip()
                raise ScoreOmrError(
                    guidance
                    or "This page is not clear enough to read reliably. Use a sharp, straight image with the full staff visible."
                )
        normalized = normalize(
            interpreted,
            source={
                "type": "pdf" if source_type == "pdf" else "image",
                "title": title,
                "url": None,
                "rightsLabel": "user_authorized",
                "retained": False,
            },
            review_status="needs_review",
        )
        page_drafts.append(normalized)

    combined = _combine_page_drafts(page_drafts, normalize=normalize)
    combined["source"].update(
        {
            "type": "pdf" if source_type == "pdf" else "image",
            "title": title,
            "rightsLabel": "user_authorized",
            "retained": False,
            "private": True,
            "trainingUse": False,
            "retentionPolicy": "request_only",
            "providerId": provider.provider_id,
            "pageCount": page_count,
            "selectedPages": page_numbers,
        }
    )
    if recognized_parts:
        combined["parts"] = recognized_parts
        combined["selectedPartId"] = str(selected_part or provider_selected_part or recognized_parts[0]["id"])
    combined["review"] = structural_diagnostics(combined)
    if selected_part or len(recognized_parts) == 1:
        combined["review"]["confirmationsRequired"] = [
            item for item in combined["review"]["confirmationsRequired"] if item != "melody_part"
        ]
    combined["omr"] = {
        "schemaVersion": OMR_RESULT_SCHEMA_VERSION,
        "providerId": provider.provider_id,
        "pageCount": page_count,
        "selectedPages": page_numbers,
        "selectedPartId": str(selected_part or provider_selected_part or ""),
        "artifacts": {
            "source": "transient",
            "recognizedScore": "provider_output",
            "normalizedEvents": "score_draft_v1",
            "arrangement": "not_started",
        },
    }
    return combined


def structural_diagnostics(draft: Mapping[str, Any]) -> dict[str, Any]:
    """Identify uncertain events and score-structure inconsistencies."""

    score = draft.get("score") if isinstance(draft.get("score"), Mapping) else {}
    events = score.get("melody") if isinstance(score.get("melody"), Sequence) else []
    issues: list[dict[str, Any]] = []
    flagged_ids: list[str] = []
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            continue
        confidence = float(event.get("confidence") or 0)
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            event_id = str(event.get("id") or f"m{index + 1}")
            flagged_ids.append(event_id)
            issues.append(
                {
                    "code": "low_event_confidence",
                    "severity": "warning",
                    "eventIds": [event_id],
                    "message": f"Check note {index + 1}: pitch or rhythm confidence is {round(confidence * 100)}%.",
                }
            )

    meter = str(score.get("meter") or "")
    beats = 3.0 if meter == "3/4" else 4.0 if meter == "4/4" else 0.0
    totals: dict[int, float] = {}
    for event in events:
        if not isinstance(event, Mapping):
            continue
        measure = int(event.get("measure") or 1)
        totals[measure] = totals.get(measure, 0.0) + float(event.get("durationBeats") or 0)
    pickup = float(score.get("pickupBeats") or 0)
    last_measure = max(totals, default=1)
    if beats:
        for measure, total in sorted(totals.items()):
            capacity = pickup if measure == 1 and pickup else beats
            if total > capacity + 0.001:
                related = [
                    str(event.get("id"))
                    for event in events
                    if isinstance(event, Mapping) and int(event.get("measure") or 1) == measure
                ]
                flagged_ids.extend(related)
                issues.append(
                    {
                        "code": "measure_overfull",
                        "severity": "error",
                        "eventIds": related,
                        "message": f"Measure {measure} totals {total:g} beats but {meter} allows {capacity:g}.",
                    }
                )
            elif measure != last_measure and total < capacity - 0.001:
                issues.append(
                    {
                        "code": "measure_underfull",
                        "severity": "warning",
                        "eventIds": [],
                        "message": f"Measure {measure} totals {total:g} beats; check for a missing rest, note, or voice.",
                    }
                )

    existing_review = draft.get("review") if isinstance(draft.get("review"), Mapping) else {}
    warnings = [str(item)[:240] for item in existing_review.get("warnings", [])][:12]
    warnings.extend(issue["message"] for issue in issues if issue["severity"] == "error")
    return {
        "status": "needs_review",
        "warnings": list(dict.fromkeys(warnings))[:12],
        "issues": issues[:64],
        "flaggedEventIds": list(dict.fromkeys(flagged_ids)),
        "confirmationsRequired": ["key_signature", "time_signature", "melody_part"],
        "summary": {
            "eventCount": len(events),
            "flaggedEventCount": len(set(flagged_ids)),
            "errorCount": sum(issue["severity"] == "error" for issue in issues),
            "warningCount": sum(issue["severity"] == "warning" for issue in issues),
        },
    }


def _combine_page_drafts(
    drafts: Sequence[Mapping[str, Any]],
    *,
    normalize: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    if not drafts:
        raise ScoreOmrError("No selected page produced a readable melody.")
    first = drafts[0]
    melody: list[dict[str, Any]] = []
    harmony: list[dict[str, Any]] = []
    measure_offset = 0
    warnings: list[str] = []
    for page_index, draft in enumerate(drafts, start=1):
        score = draft["score"]
        page_events = [dict(event) for event in score.get("melody", [])]
        for event in page_events:
            event["measure"] = int(event.get("measure") or 1) + measure_offset
            event["sourcePage"] = page_index
            event["id"] = f"p{page_index}-{event.get('id') or len(melody) + 1}"
        page_harmony = [dict(event) for event in score.get("harmony", [])]
        for event in page_harmony:
            event["measure"] = int(event.get("measure") or 1) + measure_offset
        melody.extend(page_events)
        harmony.extend(page_harmony)
        measure_offset = max((int(event["measure"]) for event in page_events), default=measure_offset)
        warnings.extend(str(item) for item in draft.get("review", {}).get("warnings", []))
    return normalize(
        {
            "source": first["source"],
            "score": {
                "sourceKey": first["score"]["sourceKey"],
                "arrangementKey": first["score"]["arrangementKey"],
                "meter": first["score"]["meter"],
                "pickupBeats": first["score"].get("pickupBeats", 0),
                "melody": melody,
                "harmony": harmony,
            },
            "review": {"status": "needs_review", "warnings": warnings},
        },
        source=first["source"],
        review_status="needs_review",
    )


def _selected_page_numbers(selected_pages: Sequence[int] | None, page_count: int) -> list[int]:
    if page_count > MAX_PDF_PAGES:
        raise ScoreOmrError(
            f"That PDF has {page_count} pages. Choose a PDF with no more than {MAX_PDF_PAGES} pages."
    )
    requested = list(selected_pages or range(1, page_count + 1))
    normalized_set: set[int] = set()
    for raw_page in requested:
        try:
            page = int(raw_page)
        except (TypeError, ValueError):
            continue
        if 1 <= page <= page_count:
            normalized_set.add(page)
    normalized = sorted(normalized_set)
    if not normalized:
        raise ScoreOmrError("Select at least one PDF page to read.")
    if len(normalized) > MAX_SELECTED_PAGES:
        raise ScoreOmrError(f"Select no more than {MAX_SELECTED_PAGES} pages at a time.")
    return normalized


def _open_pdf(raw: bytes) -> Any:
    if not raw.startswith(b"%PDF"):
        raise ScoreOmrError("That file is not a valid PDF.")
    try:
        import pypdfium2 as pdfium

        return pdfium.PdfDocument(raw)
    except ImportError as exc:
        raise ScoreOmrError("PDF reading is not available on this server.") from exc
    except Exception as exc:
        raise ScoreOmrError("That PDF is damaged, encrypted, or unsupported.") from exc


def _render_pdf_page(document: Any, page_index: int, *, scale: float) -> Image.Image:
    try:
        page = document[page_index]
        width, height = page.get_size()
        pixels = int(width * scale) * int(height * scale)
        if pixels > MAX_RENDERED_PIXELS:
            scale *= (MAX_RENDERED_PIXELS / pixels) ** 0.5
        return page.render(scale=scale).to_pil().convert("RGB")
    except Exception as exc:
        raise ScoreOmrError(
            f"Page {page_index + 1} could not be rendered. Export that page as a clean PNG and try again."
        ) from exc


def _validate_raster(raw: bytes) -> None:
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            width, height = image.size
            if width < 320 or height < 240:
                raise ScoreOmrError(
                    "This image is too small to read reliably. Upload a sharper screenshot or a closer, straight photo."
                )
            gray = image.convert("L")
            contrast = ImageStat.Stat(gray).stddev[0]
            if contrast < 8:
                raise ScoreOmrError(
                    "This image has too little contrast to read reliably. Use even lighting and dark notation on a light page."
                )
    except ScoreOmrError:
        raise
    except Exception as exc:
        raise ScoreOmrError("That image is damaged or uses an unsupported encoding.") from exc


def _encode_image(image: Image.Image, image_format: str, **options: Any) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=image_format, **options)
    return buffer.getvalue()


def _nonnegative_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0
