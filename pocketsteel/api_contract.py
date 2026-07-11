"""Shared API response shapes for retrieval and answer endpoints."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

try:
    from typing import NotRequired
except ImportError:  # Python 3.9 compatibility.
    from typing_extensions import NotRequired


AnswerMode = Literal["ask", "gear", "copedent", "tab", "practice"]


class SearchResult(TypedDict):
    score: float
    excerpt: str
    source_system: str
    forum_name: str
    thread_title: str
    thread_url: str
    chunk_id: str
    post_uid: str
    source_kind: str
    forum_id: str
    legacy_forum_number: str
    thread_id: str
    legacy_thread_uid: str
    thread_category: str
    thread_quality_score: Any
    chunk_index: Any
    warnings: list[str]
    chunk_role: NotRequired[str]
    quality_score: NotRequired[Any]
    noise_score: NotRequired[Any]
    source_metadata_complete: NotRequired[Any]
    cleanup_flags: NotRequired[list[str]]
    post_uids: NotRequired[list[str]]
    post_role_summary: NotRequired[Any]


class SourceCitation(TypedDict):
    title: str
    forumName: str
    url: str
    excerpt: str
    score: float
    chunkId: str
    postUid: str | None
    source_system: NotRequired[str]
    visibility: NotRequired[str]
    source_id: NotRequired[str]
    source_path: NotRequired[str]
    provenance_status: NotRequired[str]
    answer_quote_allowed: NotRequired[str]


class AnswerSection(TypedDict):
    title: str
    body: str
    style: NotRequired[str]


class FretboardHighlight(TypedDict):
    id: str
    label: str
    fret: int
    strings: list[int]
    pedals: list[str]
    levers: list[str]
    role: str


class FretboardPosition(TypedDict):
    id: str
    label: str
    root: str
    quality: str
    positionKind: str
    fret: int
    strings: list[int]
    grip: str
    pedals: list[str]
    levers: list[str]
    color: str
    role: NotRequired[str]
    function: str
    keyContext: str
    family: str
    tier: str
    colorRole: str
    visibleByDefault: bool
    sortOrder: int
    notes: dict[str, str]
    intervals: dict[str, str]
    omittedIntervals: list[str]
    addedIntervals: list[str]
    isFullChord: bool
    isPartial: bool
    isRootless: bool
    whyUseIt: str
    caveats: list[str]
    validationStatus: str
    explanation: str
    tierReason: str
    whenToUse: str
    soundCharacter: str
    movementUse: str
    resolutionUse: str
    forumEvidence: list[str]
    forumEvidenceStatus: str
    explanationShort: str
    explanationLong: str


class FretboardPayload(TypedDict):
    type: NotRequired[str]
    title: str
    subtitle: NotRequired[str]
    description: NotRequired[str]
    tuning: NotRequired[str]
    copedent: NotRequired[dict[str, str]]
    key: NotRequired[str]
    strings: NotRequired[dict[str, Any]]
    positions: NotRequired[list[FretboardPosition]]
    highlights: list[FretboardHighlight]
    legend: NotRequired[list[dict[str, Any]]]
    notes: NotRequired[list[str]]
    warnings: NotRequired[list[str]]
    sourceContext: NotRequired[list[dict[str, Any]]]


class TabExampleValidation(TypedDict):
    ok: bool
    issues: list[dict[str, Any]]
    profile: str
    eventCount: int


class TabExamplePayload(TypedDict):
    id: str
    title: str
    context: dict[str, Any]
    rendered_tab: str
    validation: TabExampleValidation
    explanation: str
    intervals: list[dict[str, Any]]
    events: list[dict[str, Any]]


class MelodyExercisePayload(TypedDict):
    schemaVersion: str
    id: str
    status: str
    kind: str
    title: str
    material: dict[str, str]
    renderingMode: str
    accuracy: dict[str, Any]
    section: dict[str, Any]
    events: list[dict[str, Any]]
    validation: dict[str, Any]


class ScoreDraftSource(TypedDict):
    type: str
    title: str
    url: str | None
    rightsLabel: str
    retained: bool


class ScoreDraftPayload(TypedDict):
    schemaVersion: str
    source: ScoreDraftSource
    score: dict[str, Any]
    review: dict[str, Any]


class AnswerResponse(TypedDict):
    answer: str
    mode: AnswerMode
    sources: list[SourceCitation]
    warnings: list[str]
    sections: list[AnswerSection]
    fretboard: NotRequired[FretboardPayload]
    tab_example: NotRequired[TabExamplePayload]
    progression_guide: NotRequired[dict[str, Any]]
    melody_exercise: NotRequired[MelodyExercisePayload]
