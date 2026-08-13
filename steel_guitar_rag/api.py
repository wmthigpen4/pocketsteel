"""Tiny local retrieval API for Steel Guitar RAG."""

from __future__ import annotations

import hashlib
import logging
import json
import os
import re
import subprocess
import threading
from collections import deque
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urlsplit

from steel_guitar_rag.answering import (
    AnswerProvider,
    DeterministicAnswerProvider,
    answer_is_no_source,
    apply_private_profile_wording,
    bc_pedal_exercise_answer,
    build_sections,
    concise_source_cards,
    configured_answer_provider,
    final_answer_quality_gate,
    filter_sources_for_question,
    normalize_answer_list_markers,
    parse_answer_request,
    private_profile_answer,
)
from steel_guitar_rag.access_control import (
    AnswerAuthMode,
    AuthProvider,
    authorize_answer_request,
    authorize_local_dev_request,
    configured_answer_auth_mode,
    normalize_answer_auth_mode,
    resolve_auth_provider,
)
from steel_guitar_rag.answer_usage import InMemoryAnswerRateLimiter, answer_rate_limit_key
from steel_guitar_rag.account_usage import (
    AccountUsageRepository,
    AccountUsageUnavailableError,
    PUBLIC_ACTIVITY_EVENT_TYPES,
    configured_account_usage_enabled,
    configured_account_usage_path,
)
from steel_guitar_rag.account_copedents import (
    AccountCopedentError,
    AccountCopedentRepository,
    AccountConfigurationError,
    AccountProfileConflictError,
    AccountProfileNotFoundError,
    EntitlementRequiredError,
    account_access_for_decision,
    configured_account_copedents_enabled,
    configured_account_copedents_path,
)
from steel_guitar_rag.answer_tab_examples import (
    answer_body_for_tab_example,
    fretboard_payload_for_tab_example,
    static_answer_body_for_question,
    static_fretboard_payload_for_question,
    tab_example_payload_for_question,
)
from steel_guitar_rag.api_contract import AnswerResponse
from steel_guitar_rag.answer_contracts import enforce_answer_contract, infer_contract_intent
from steel_guitar_rag.answer_intent_classifier import classify_answer_request
from steel_guitar_rag.answer_routing import (
    AnswerRouteTrace,
    contextual_entity_probe_question,
    corpus_promoted_decision,
    deterministic_subquestion_for_hybrid,
    evaluate_corpus_entity_evidence,
    hybrid_promoted_decision,
    is_corpus_entity_candidate,
    select_answer_route,
)
from steel_guitar_rag.amazing_tablature_model import RuntimeRankerPolicy
from steel_guitar_rag.amazing_tablature_runtime import (
    configured_private_ranker_policy,
    private_beta_enabled,
)
from steel_guitar_rag.chroma_search import (
    ChromaSearchIndex,
    SearchResponse,
)
from steel_guitar_rag.canonical_frontier_client import (
    CanonicalFrontierClient,
    CanonicalFrontierUnavailable,
    configured_canonical_frontier_enabled,
)
from steel_guitar_rag.degraded_answer import compose_extractive_degraded_answer
from steel_guitar_rag.curated_answers import (
    CURATED_FACT_WEAK_WARNING,
    WEAK_RETRIEVAL_WARNING,
    generic_sgf_quarantine_fallback_answer,
    intent_mode_curated_answer,
    is_source_provenance_followup,
    lookup_curated_answer,
    retrieval_looks_weak_for_curated,
    sgf_answer_body_needs_quarantine,
    sgf_quarantine_teacher_answer,
    source_provenance_followup_answer,
    unsupported_chord_position_curated_answer,
    visual_fretboard_curated_answer,
)
from steel_guitar_rag.curated_guidance_retriever import (
    ENABLE_CURATED_GUIDANCE_ENV,
    is_teaching_style_query,
    search_curated_guidance,
)
from steel_guitar_rag.curated_source_registry import slide_bar_vendor_source_cards
from steel_guitar_rag.fretboard_examples import (
    classic_country_move_payload_for_question,
    fretboard_payload_for_question,
)
from steel_guitar_rag.progression_guide import progression_guide_for_question
from steel_guitar_rag.copedent_transfer import (
    copedent_context_metadata,
    custom_e9_profile_from_payload,
    profile_control_answer,
    retarget_fretboard_payload,
    retarget_tab_example_payload,
    resolve_copedent_context,
)
from steel_guitar_rag.e9_copedents import DEFAULT_COPEDENT_ID, E9CopedentProfile, available_e9_copedents
from steel_guitar_rag.fretboard_explorer import build_explorer_payload_for_profile
from steel_guitar_rag.melody_assistant import (
    MelodyExerciseError,
    configured_melody_exercise_enabled,
    melody_exercise_response,
)
from steel_guitar_rag.melody_import import (
    MAX_IMPORT_BODY_BYTES,
    MelodyImportError,
    MelodyImportTooLargeError,
    configured_melody_import_enabled,
    import_score_draft,
    public_song_catalog,
)
from steel_guitar_rag.score_import_jobs import ScoreImportJobManager
from steel_guitar_rag.lesson_studio import LessonStudioError, build_lesson_response, lesson_catalog
from steel_guitar_rag.song_practice import (
    SongPracticeError,
    arrange_song_practice,
    build_play_along_melody_lessons,
    configured_song_practice_enabled,
    song_practice_catalog,
)
from steel_guitar_rag.rag_guardrails import (
    safe_http_url,
    sanitize_retrieved_sources,
    sanitize_source_text,
)
from steel_guitar_rag.rag_guardrails import is_injection_like
from steel_guitar_rag.private_source_search import PrivateSourceSearchIndex
from steel_guitar_rag.retrieval_modes import (
    RetrievalMode,
    RetrievalModeConfig,
    configured_retrieval_mode_config,
    private_sources_allowed,
    retrieval_plan_for_role,
)
from steel_guitar_rag.runtime_server import bounded_env_int
from steel_guitar_rag.runtime_dependencies import BoundedDependencyRunner, bounded_env_float
from steel_guitar_rag.tab_engine import render_tab_from_payload

LOGGER = logging.getLogger(__name__)

ENABLE_PRIVATE_REVIEW_SOURCES_ENV = "ENABLE_PRIVATE_REVIEW_SOURCES"
ENABLE_CURATED_GUIDANCE_IN_ANSWER_ENV = "ENABLE_CURATED_GUIDANCE_IN_ANSWER"
CURATED_GUIDANCE_ADMIN_ROLES = {"admin", "dev", "developer", "backstage"}
CURATED_GUIDANCE_FORUM_WISDOM_RE = re.compile(
    r"\b(?:what\s+do\s+(?:players|people|forum|steelers)|players?\s+(?:say|think|report)|"
    r"forum\s+(?:players|wisdom|opinions?)|owner\s+reports?|public\s+forum)\b",
    re.I,
)
CONTEXTUAL_FOLLOWUP_RE = re.compile(
    r"\b(?:he|him|his|she|her|hers|they|them|their|it|its|that|those|this|these|"
    r"the\s+(?:answer|player|course|product|song|grip|position|recommendation))\b",
    re.I,
)
MAX_JSON_BODY_BYTES = 1_048_576
MAX_CSP_REPORT_BYTES = 65_536
MAX_SECURITY_EVENT_LOG = 256
CONTENT_CONCURRENCY_ENV = "STEEL_RAG_CONTENT_CONCURRENCY"
DEFAULT_CONTENT_CONCURRENCY = 4
RETRIEVAL_WALL_TIMEOUT_ENV = "STEEL_RAG_RETRIEVAL_WALL_TIMEOUT_SECONDS"
ANSWER_WALL_TIMEOUT_ENV = "STEEL_RAG_ANSWER_WALL_TIMEOUT_SECONDS"
DEFAULT_RETRIEVAL_WALL_TIMEOUT_SECONDS = 20.0
DEFAULT_ANSWER_WALL_TIMEOUT_SECONDS = 25.0
CONTENT_BEARING_PATHS = frozenset(
    {
        "/api/search",
        "/api/tab",
        "/api/answer",
        "/api/melody",
        "/api/amazing-tablature/arrange",
    }
)
SECURITY_RESPONSE_HEADERS: tuple[tuple[str, str], ...] = (
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
    ("Permissions-Policy", "camera=(), geolocation=(), microphone=()"),
    ("Cross-Origin-Opener-Policy", "same-origin"),
    (
        "Content-Security-Policy-Report-Only",
        "default-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; "
        "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; media-src 'self' blob:; font-src 'self' data:; "
        "connect-src 'self'; object-src 'none'; "
        "report-uri /api/security/csp-report",
    ),
)


class JsonRequestError(ValueError):
    pass


class JsonRequestTooLargeError(JsonRequestError):
    pass


def _question_mentions_slide_bar_item(question: str) -> bool:
    lowered = (question or "").lower()
    return "slide bar" in lowered or "steel bar" in lowered or "tone bar" in lowered


def _curated_answer_should_be_source_free(intent: str) -> bool:
    return intent in {
        "factual_biography",
        "sensitive_identity",
        "sensitive_personal_attribute",
        "style_how_to",
        "safety_adjacent",
        "teach_me_something",
        "position_strategy",
        "movement_request",
        "progression_intro_request",
        "pocket_request",
        "lick_request",
        "vague_learning_request",
        "frustrated_learning_request",
        "everyday_context",
    }


def _answer_intent_guardrail_answer(domain: str) -> str:
    if domain == "unsafe_or_impossible":
        return (
            "This app is focused on pedal steel guitar. That request is outside Steel Guitar RAG’s scope, "
            "and it may be unsafe or too large to display usefully. "
            "Try asking about E9 positions, grips, pedals/levers, tone, gear, blocking, bar movement, practice plans, "
            "or steel-guitar forum wisdom."
        )
    return (
        "This app is focused on pedal steel guitar. That request is outside Steel Guitar RAG’s scope. "
        "Try asking about E9 positions, grips, pedals/levers, tone, gear, blocking, bar movement, practice plans, "
        "or steel-guitar forum wisdom."
    )


def _should_gate_answer_intent(decision: dict[str, Any]) -> bool:
    if decision.get("domain") == "unsafe_or_impossible":
        return True
    # The classifier intentionally labels many underspecified prompts as
    # off-domain/unknown.  Those still need the local clarifier, curated
    # teaching, or entity-probe routes below.  Only definite small talk is a
    # safe off-domain refusal at this point in the router.
    return decision.get("domain") == "off_domain" and decision.get("intent") == "small_talk"


def _answer_provenance(kind: str, title: str, summary: str) -> dict[str, str]:
    """Build the stable, user-facing provenance envelope used by the existing UI."""

    return {"kind": kind, "title": title, "summary": summary}


def _prior_user_question(conversation_context: tuple[str, ...]) -> str | None:
    for item in reversed(conversation_context):
        normalized = " ".join(str(item or "").split())
        if normalized.casefold().startswith("user:"):
            question = normalized.split(":", 1)[1].strip()
            return question or None
    return None


DETERMINISTIC_E9_PROVENANCE = _answer_provenance(
    "deterministic_e9_rules",
    "Deterministic E9 rules",
    (
        "Calculated locally from the selected E9 copedent, pitch spelling, grips, "
        "pedal and lever changes, and answer-contract rules. No forum passage or "
        "language model is required for this result."
    ),
)
POSITION_STRATEGY_PROVENANCE = _answer_provenance(
    "deterministic_e9_rules",
    "Deterministic E9 rules",
    (
        "Calculated from standard E9 tuning, the A+B pedal changes, and the resulting "
        "notes on strings 4-5-6 at the 3rd and 8th frets."
    ),
)
VERIFIED_SYNTHESIS_PROVENANCE = _answer_provenance(
    "verified_sgf_synthesis",
    "Verified SGF synthesis",
    (
        "Local lexical and BGE retrieval ranked the public SGF evidence; Terra wrote "
        "passage-linked claims and Luna verified relevance and citation support before "
        "deterministic formatting."
    ),
)
EXTRACTIVE_DEGRADED_PROVENANCE = _answer_provenance(
    "sgf_extractive_degraded",
    "Extractive degraded evidence",
    (
        "Terra/Luna synthesis is temporarily unavailable. This response uses only "
        "bounded sentences selected locally from the displayed public SGF source cards."
    ),
)


SOURCE_BACKED_PARENT_PROVENANCE_KINDS = frozenset({
    "verified_sgf_synthesis",
    "sgf_extractive_degraded",
})


def _bounded_parent_text(value: Any, *, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _normalized_parent_answer_context(value: Any) -> dict[str, Any] | None:
    """Validate the immediately preceding UI answer without trusting browser state."""

    if not isinstance(value, dict):
        return None
    raw_provenance = value.get("answerProvenance", value.get("answer_provenance"))
    provenance: dict[str, str] = {}
    if isinstance(raw_provenance, dict):
        kind = _bounded_parent_text(raw_provenance.get("kind"), limit=64)
        if kind in {
            "deterministic_e9_rules",
            "curated_local_guidance",
            *SOURCE_BACKED_PARENT_PROVENANCE_KINDS,
        }:
            provenance = {
                "kind": kind,
                "title": _bounded_parent_text(raw_provenance.get("title"), limit=120),
                "summary": _bounded_parent_text(raw_provenance.get("summary"), limit=600),
            }

    cards = []
    raw_sources = value.get("sources")
    if isinstance(raw_sources, list):
        for raw_source in raw_sources[:10]:
            if not isinstance(raw_source, dict):
                continue
            excerpt, _, drop = sanitize_source_text(
                _bounded_parent_text(raw_source.get("excerpt"), limit=1_200)
            )
            if drop or not excerpt:
                continue
            title = _bounded_parent_text(raw_source.get("title"), limit=240)
            if not title:
                continue
            cards.append({
                "title": title,
                "forumName": _bounded_parent_text(
                    raw_source.get("forumName", raw_source.get("forum")),
                    limit=120,
                ) or "Steel Guitar Forum",
                "url": safe_http_url(raw_source.get("url")),
                "excerpt": excerpt[:420],
                "score": 0.0,
                "chunkId": "",
                "postUid": None,
            })

    parent = {
        "question": _bounded_parent_text(value.get("question"), limit=2_000),
        "answer": _bounded_parent_text(value.get("answer"), limit=8_000),
        "sources": cards,
        "answer_provenance": provenance,
    }
    if not any((parent["question"], parent["answer"], cards, provenance)):
        return None
    return parent


def _attach_tab_example_if_available(
    payload: AnswerResponse,
    question: str,
    *,
    answer_intent_decision: dict[str, Any] | None = None,
) -> None:
    static_fretboard = static_fretboard_payload_for_question(question)
    if static_fretboard is not None:
        if "fretboard" not in payload:
            payload["fretboard"] = static_fretboard
        if _answer_is_generic_tab_fallback(payload.get("answer", "")):
            replacement = static_answer_body_for_question(question)
            if replacement:
                payload["answer"] = replacement
                payload["sections"] = build_sections(replacement)
        return

    tab_example = tab_example_payload_for_question(question, answer_intent=answer_intent_decision)
    if tab_example is not None:
        payload["tab_example"] = tab_example
        if tab_example.get("kind") == "parameterized_chord_movement":
            payload["sources"] = []
            payload["warnings"] = []
            fretboard = fretboard_payload_for_tab_example(tab_example)
            if fretboard is not None:
                payload["fretboard"] = fretboard
        elif "fretboard" not in payload:
            fretboard = fretboard_payload_for_tab_example(tab_example)
            if fretboard is not None:
                payload["fretboard"] = fretboard
        if tab_example.get("kind") == "parameterized_chord_movement" or _answer_is_generic_tab_fallback(
            payload.get("answer", "")
        ):
            replacement = answer_body_for_tab_example(tab_example)
            if replacement:
                payload["answer"] = replacement
                payload["sections"] = build_sections(replacement)


def _personalize_answer_payload(
    payload: AnswerResponse,
    profile: E9CopedentProfile,
    revision: int,
) -> None:
    """Retarget deterministic answer visuals and attach explicit profile identity."""

    metadata = copedent_context_metadata(profile, revision)
    payload.update(metadata)
    warnings = list(payload.get("warnings") or [])
    if payload.get("fretboard") is not None:
        fretboard = retarget_fretboard_payload(payload.get("fretboard"), profile)
        if fretboard is None:
            payload.pop("fretboard", None)
            warnings.append(f"No mechanically equivalent fretboard position was available on {profile.label}.")
        else:
            fretboard.update(metadata)
            payload["fretboard"] = fretboard
    if payload.get("tab_example") is not None:
        tab_example = retarget_tab_example_payload(payload.get("tab_example"), profile)
        if tab_example is None:
            payload.pop("tab_example", None)
            warnings.append(f"The tab example could not be reproduced exactly on {profile.label}.")
        else:
            tab_example.update(metadata)
            payload["tab_example"] = tab_example
    payload["warnings"] = list(dict.fromkeys(warnings))


def _answer_is_generic_tab_fallback(answer: str) -> bool:
    return _answer_is_generic_specificity_fallback(answer)


def _answer_is_generic_specificity_fallback(answer: str) -> bool:
    lowered = str(answer or "").lower()
    return any(
        marker in lowered
        for marker in (
            "i need a more specific steel-guitar question",
            "i don't have enough reliable information",
            "i don’t have enough reliable information",
            "available matches are too thin",
        )
    )


def _env_flag(name: str, env: dict[str, str] | None = None) -> bool:
    value = (env or os.environ).get(name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _curated_guidance_answer_flags_enabled(env: dict[str, str] | None = None) -> bool:
    return (
        _env_flag(ENABLE_PRIVATE_REVIEW_SOURCES_ENV, env)
        and _env_flag(ENABLE_CURATED_GUIDANCE_ENV, env)
        and _env_flag(ENABLE_CURATED_GUIDANCE_IN_ANSWER_ENV, env)
    )


def _curated_guidance_role_allowed(role: str | None) -> bool:
    return str(role or "").strip().lower() in CURATED_GUIDANCE_ADMIN_ROLES


def _curated_guidance_query_eligible(question: str, decision: dict[str, Any]) -> bool:
    if decision.get("domain") != "steel_guitar":
        return False
    if decision.get("needs_fretboard"):
        return False
    if decision.get("allowed_answer_shape") == "guardrail_refusal":
        return False
    if CURATED_GUIDANCE_FORUM_WISDOM_RE.search(question or ""):
        return False
    return is_teaching_style_query(question or "")


class RetrievalApi:
    def __init__(
        self,
        search_index: Any,
        answer_provider: AnswerProvider | None = None,
        *,
        answer_auth_mode: AnswerAuthMode | None = None,
        auth_provider: AuthProvider | None = None,
        cloudflare_verifier: Any = None,
        answer_rate_limiter: InMemoryAnswerRateLimiter | None = None,
        private_search_index: Any | None = None,
        retrieval_config: RetrievalModeConfig | None = None,
        curated_guidance_search: Callable[..., list[dict[str, object]]] | None = None,
        melody_exercise_enabled: bool | None = None,
        melody_import_enabled: bool | None = None,
        song_practice_enabled: bool | None = None,
        account_copedents_enabled: bool | None = None,
        account_copedent_repository: AccountCopedentRepository | None = None,
        account_usage_enabled: bool | None = None,
        account_usage_repository: AccountUsageRepository | None = None,
        amazing_tablature_policy: RuntimeRankerPolicy | None = None,
        canonical_frontier_enabled: bool | None = None,
        canonical_frontier_client: Any | None = None,
    ) -> None:
        self.search_index = search_index
        self.private_search_index = private_search_index
        self.curated_guidance_search = curated_guidance_search or search_curated_guidance
        self.answer_provider = configured_answer_provider(answer_provider)
        self.canonical_frontier_enabled = (
            configured_canonical_frontier_enabled()
            if canonical_frontier_enabled is None
            else bool(canonical_frontier_enabled)
        )
        self.canonical_frontier_client = (
            canonical_frontier_client
            if canonical_frontier_client is not None
            else CanonicalFrontierClient.from_env()
            if self.canonical_frontier_enabled
            else None
        )
        self.answer_auth_mode = normalize_answer_auth_mode(answer_auth_mode or configured_answer_auth_mode())
        self.auth_provider = resolve_auth_provider(self.answer_auth_mode, auth_provider)
        self.cloudflare_verifier = cloudflare_verifier
        self.answer_rate_limiter = answer_rate_limiter or InMemoryAnswerRateLimiter.from_env()
        self.answer_request_log: deque[dict[str, Any]] = deque(maxlen=MAX_SECURITY_EVENT_LOG)
        self.csp_report_log: deque[dict[str, str]] = deque(maxlen=MAX_SECURITY_EVENT_LOG)
        self.retrieval_config = retrieval_config or configured_retrieval_mode_config()
        self.melody_exercise_enabled = (
            configured_melody_exercise_enabled()
            if melody_exercise_enabled is None
            else bool(melody_exercise_enabled)
        )
        self.amazing_tablature_policy = (
            configured_private_ranker_policy()
            if amazing_tablature_policy is None
            else amazing_tablature_policy
        )
        self.melody_import_enabled = (
            configured_melody_import_enabled()
            if melody_import_enabled is None
            else bool(melody_import_enabled)
        )
        self.score_import_jobs = ScoreImportJobManager(importer=import_score_draft)
        self.song_practice_enabled = (
            configured_song_practice_enabled()
            if song_practice_enabled is None
            else bool(song_practice_enabled)
        )
        self.account_copedents_enabled = (
            configured_account_copedents_enabled()
            if account_copedents_enabled is None
            else bool(account_copedents_enabled)
        )
        if self.account_copedents_enabled:
            self.account_copedent_repository = account_copedent_repository or AccountCopedentRepository(
                configured_account_copedents_path()
            )
        else:
            self.account_copedent_repository = None
        self.account_usage_enabled = (
            configured_account_usage_enabled()
            if account_usage_enabled is None
            else bool(account_usage_enabled)
        )
        if self.account_usage_enabled:
            self.account_usage_repository = account_usage_repository or AccountUsageRepository(
                configured_account_usage_path()
            )
        else:
            self.account_usage_repository = None
        self.git_sha = self._git_value("rev-parse", "--short", "HEAD")
        self.git_branch = self._git_value("branch", "--show-current")
        self.server_started_at = datetime.now(timezone.utc).isoformat()
        self._content_slots = threading.BoundedSemaphore(
            bounded_env_int(
                CONTENT_CONCURRENCY_ENV,
                DEFAULT_CONTENT_CONCURRENCY,
                minimum=1,
                maximum=16,
            )
        )
        dependency_workers = bounded_env_int(
            CONTENT_CONCURRENCY_ENV,
            DEFAULT_CONTENT_CONCURRENCY,
            minimum=1,
            maximum=16,
        )
        self._retrieval_dependencies = BoundedDependencyRunner(dependency_workers)
        self._answer_dependencies = BoundedDependencyRunner(dependency_workers)
        self._retrieval_wall_timeout = bounded_env_float(
            RETRIEVAL_WALL_TIMEOUT_ENV,
            DEFAULT_RETRIEVAL_WALL_TIMEOUT_SECONDS,
            minimum=0.01,
            maximum=35.0,
        )
        self._answer_wall_timeout = bounded_env_float(
            ANSWER_WALL_TIMEOUT_ENV,
            DEFAULT_ANSWER_WALL_TIMEOUT_SECONDS,
            minimum=0.01,
            maximum=120.0,
        )

    def __call__(self, environ: dict[str, Any], start_response: Any) -> Iterable[bytes]:
        path = str(environ.get("PATH_INFO") or "")
        is_content_work = (
            path in CONTENT_BEARING_PATHS
            or path.startswith("/api/melody/")
            or path.startswith("/api/lessons/")
            or path.startswith("/api/song-practice/")
        )
        if not is_content_work:
            return self._dispatch(environ, start_response)
        if not self._content_slots.acquire(blocking=False):
            return self._json_response(
                start_response,
                "503 Service Unavailable",
                {"error": "content service is busy"},
                extra_headers=(("Retry-After", "2"),),
            )
        try:
            return self._dispatch(environ, start_response)
        finally:
            self._content_slots.release()

    def _dispatch(self, environ: dict[str, Any], start_response: Any) -> Iterable[bytes]:
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "")

        if path == "/health/live":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            return self._json_response(
                start_response,
                "200 OK",
                {"status": "live"},
                extra_headers=(("Cache-Control", "no-store"),),
            )

        if path == "/health/ready":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            if not self.canonical_frontier_enabled:
                return self._json_response(
                    start_response,
                    "200 OK",
                    {"status": "ready"},
                    extra_headers=(("Cache-Control", "no-store"),),
                )
            if self.canonical_frontier_enabled:
                try:
                    frontier_client = self.canonical_frontier_client
                    if frontier_client is None:
                        raise CanonicalFrontierUnavailable(
                            "Canonical frontier client is not configured.",
                            error_code="frontier_not_configured",
                            retryable=False,
                        )
                    frontier_health = frontier_client.readiness(timeout_seconds=1.0)
                except (CanonicalFrontierUnavailable, RuntimeError) as exc:
                    return self._json_response(
                        start_response,
                        "200 OK",
                        {
                            "status": "degraded",
                            "dependencies": {
                                "local_answer_paths": "ready",
                                "canonical_frontier": "not_ready",
                            },
                            "reason": getattr(exc, "error_code", "frontier_health_unavailable"),
                        },
                        extra_headers=(("Cache-Control", "no-store"),),
                    )
                if (
                    frontier_health.get("status") != "ready"
                    or int(frontier_health.get("http_status") or 0) != 200
                ):
                    return self._json_response(
                        start_response,
                        "200 OK",
                        {
                            "status": "degraded",
                            "dependencies": {
                                "local_answer_paths": "ready",
                                "canonical_frontier": "not_ready",
                            },
                            "reason": str(frontier_health.get("reason") or "frontier_not_ready"),
                        },
                        extra_headers=(("Cache-Control", "no-store"),),
                    )
            return self._json_response(
                start_response,
                "200 OK",
                {
                    "status": "ready",
                    "dependencies": {
                        "local_answer_paths": "ready",
                        "canonical_frontier": "ready",
                    },
                },
                extra_headers=(("Cache-Control", "no-store"),),
            )

        if path == "/api/version":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            return self._json_response(start_response, "200 OK", self._version_payload())

        if path == "/api/security/csp-report":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            try:
                report_payload = self._read_json_body(environ, max_bytes=MAX_CSP_REPORT_BYTES)
            except JsonRequestTooLargeError as exc:
                return self._json_response(start_response, "413 Payload Too Large", {"error": str(exc)})
            except JsonRequestError as exc:
                return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})
            self.csp_report_log.append(self._csp_report_summary(report_payload))
            return self._empty_response(start_response, "204 No Content")

        if path == "/api/search":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})

            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})

            params = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
            query = params.get("q", [""])[0]
            search_response, debug_metadata = self._search_for_api(query, role=access.role)
            sanitized_search = sanitize_retrieved_sources(search_response.results)
            payload = {
                "query": query,
                "results": sanitized_search.sources,
                "warnings": [*search_response.warnings, *sanitized_search.warnings],
            }
            if debug_metadata:
                payload["retrieval"] = debug_metadata
            return self._json_response(start_response, "200 OK", payload)

        if path == "/api/session":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})

            params = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
            access = authorize_local_dev_request(
                environ,
                self.answer_auth_mode,
                self.auth_provider,
                self.cloudflare_verifier,
            )
            auth_provider = "cloudflare_access" if self.auth_provider == "cloudflare_access" and self.answer_auth_mode != "local_dev" else "local_dev"
            payload = {
                "authenticated": access.allowed,
                "role": access.role if access.allowed else "anonymous",
                "authProvider": auth_provider,
            }
            features: dict[str, bool] = {}
            if self.melody_exercise_enabled:
                features["melodyExercise"] = True
                features["melodyCatalog"] = True
            if private_beta_enabled(self.amazing_tablature_policy):
                features["amazingTablaturePrivateBeta"] = True
            if self.melody_import_enabled:
                features["melodyImport"] = True
            if self.song_practice_enabled:
                features["songPractice"] = True
            if self.account_copedents_enabled:
                features["accountCopedents"] = True
            if self.account_usage_enabled:
                features["accountUsage"] = True
            if features:
                payload["features"] = features
            if self.account_copedents_enabled and access.allowed:
                account_access = account_access_for_decision(access)
                if account_access is None or self.account_copedent_repository is None:
                    return self._json_response(
                        start_response,
                        "503 Service Unavailable",
                        {"error": "account copedent service is unavailable"},
                    )
                bundle = self.account_copedent_repository.account_bundle(account_access)
                payload["account"] = bundle["account"]
                payload["entitlements"] = bundle["entitlements"]
            if params.get("debug") == ["auth"]:
                payload["accessDebug"] = {
                    "authProvider": auth_provider,
                    "answerAuthMode": self.answer_auth_mode,
                    **access.diagnostics,
                }
            return self._json_response(start_response, "200 OK", payload)

        if path == "/api/account/usage":
            if method != "GET":
                return self._json_response(
                    start_response,
                    "405 Method Not Allowed",
                    {"error": "method not allowed"},
                    extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                )
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(
                    start_response,
                    access.status,
                    {"error": access.error},
                    extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                )
            if not self.account_usage_enabled or self.account_usage_repository is None:
                return self._json_response(
                    start_response,
                    "503 Service Unavailable",
                    {"error": "account usage is unavailable"},
                    extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                )
            account_access = None if self.answer_auth_mode == "local_dev" else account_access_for_decision(access)
            if account_access is None:
                return self._json_response(
                    start_response,
                    "401 Unauthorized",
                    {"error": "verified account identity is required"},
                    extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                )
            try:
                usage = self.account_usage_repository.current_usage(account_access.identity)
            except AccountUsageUnavailableError:
                LOGGER.exception("account usage read failed")
                return self._json_response(
                    start_response,
                    "503 Service Unavailable",
                    {"error": "account usage is temporarily unavailable"},
                    extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                )
            return self._json_response(
                start_response,
                "200 OK",
                usage.to_dict(),
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/account/activity":
            no_store_headers = (("Cache-Control", "no-store"), ("Pragma", "no-cache"))
            if method != "POST":
                return self._json_response(
                    start_response,
                    "405 Method Not Allowed",
                    {"error": "method not allowed"},
                    extra_headers=no_store_headers,
                )
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(
                    start_response,
                    access.status,
                    {"error": access.error},
                    extra_headers=no_store_headers,
                )
            if not self.account_usage_enabled or self.account_usage_repository is None:
                return self._json_response(
                    start_response,
                    "503 Service Unavailable",
                    {"error": "account activity is unavailable"},
                    extra_headers=no_store_headers,
                )
            account_access = None if self.answer_auth_mode == "local_dev" else account_access_for_decision(access)
            if account_access is None:
                return self._json_response(
                    start_response,
                    "401 Unauthorized",
                    {"error": "verified account identity is required"},
                    extra_headers=no_store_headers,
                )
            try:
                activity_payload = self._read_json_body(environ, max_bytes=2048)
            except JsonRequestTooLargeError as exc:
                return self._json_response(
                    start_response,
                    "413 Payload Too Large",
                    {"error": str(exc)},
                    extra_headers=no_store_headers,
                )
            except JsonRequestError as exc:
                return self._json_response(
                    start_response,
                    "400 Bad Request",
                    {"error": str(exc)},
                    extra_headers=no_store_headers,
                )
            event_type = str(activity_payload.get("eventType") or "").strip()
            event_id = str(activity_payload.get("eventId") or "").strip()
            dedupe_key = str(activity_payload.get("dedupeKey") or event_type).strip()
            if event_type not in PUBLIC_ACTIVITY_EVENT_TYPES:
                return self._json_response(
                    start_response,
                    "400 Bad Request",
                    {"error": "unsupported account activity event"},
                    extra_headers=no_store_headers,
                )
            if not (8 <= len(event_id) <= 100) or not re.fullmatch(r"[A-Za-z0-9._:-]+", event_id):
                return self._json_response(
                    start_response,
                    "400 Bad Request",
                    {"error": "eventId is invalid"},
                    extra_headers=no_store_headers,
                )
            if not (1 <= len(dedupe_key) <= 160) or any(ord(char) < 32 for char in dedupe_key):
                return self._json_response(
                    start_response,
                    "400 Bad Request",
                    {"error": "dedupeKey is invalid"},
                    extra_headers=no_store_headers,
                )
            try:
                result = self.account_usage_repository.record_activity(
                    account_access.identity,
                    event_type=event_type,
                    event_id=event_id,
                    dedupe_key=dedupe_key,
                )
            except AccountUsageUnavailableError:
                LOGGER.exception("account activity write failed")
                return self._json_response(
                    start_response,
                    "503 Service Unavailable",
                    {"error": "account activity is temporarily unavailable"},
                    extra_headers=no_store_headers,
                )
            return self._json_response(
                start_response,
                "200 OK",
                {
                    "schemaVersion": "account_activity_event_v1",
                    "eventType": result.event_type,
                    "recorded": result.recorded,
                },
                extra_headers=no_store_headers,
            )

        if path == "/api/account/copedents" or path == "/api/account/copedents/import":
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            account_access = account_access_for_decision(access)
            if not self.account_copedents_enabled or account_access is None or self.account_copedent_repository is None:
                return self._json_response(start_response, "404 Not Found", {"error": "account copedents are not enabled"})
            if method == "GET" and path == "/api/account/copedents":
                return self._json_response(
                    start_response,
                    "200 OK",
                    self.account_copedent_repository.account_bundle(account_access),
                    extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                )
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            try:
                request_payload = self._read_json_body(environ)
                snapshot = request_payload.get("profile") or request_payload.get("profileSnapshot")
                if not isinstance(snapshot, dict):
                    raise ValueError("profile must be an object")
                profile = self.account_copedent_repository.create_profile(account_access, snapshot)
            except EntitlementRequiredError as exc:
                return self._entitlement_response(start_response, exc)
            except JsonRequestTooLargeError as exc:
                return self._json_response(start_response, "413 Payload Too Large", {"error": str(exc)})
            except (JsonRequestError, ValueError, TypeError) as exc:
                return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})
            return self._json_response(
                start_response,
                "201 Created",
                {
                    "profile": profile,
                    "accountCopedents": self.account_copedent_repository.account_bundle(account_access),
                    "imported": path.endswith("/import"),
                },
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/account/copedents/active":
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            account_access = account_access_for_decision(access)
            if not self.account_copedents_enabled or account_access is None or self.account_copedent_repository is None:
                return self._json_response(start_response, "404 Not Found", {"error": "account copedents are not enabled"})
            if method != "PUT":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            try:
                request_payload = self._read_json_body(environ)
                bundle = self.account_copedent_repository.set_active(
                    account_access,
                    str(request_payload.get("profileId") or request_payload.get("profile_id") or ""),
                )
            except EntitlementRequiredError as exc:
                return self._entitlement_response(start_response, exc)
            except AccountProfileNotFoundError as exc:
                return self._json_response(start_response, "404 Not Found", {"error": str(exc)})
            except (JsonRequestError, AccountCopedentError, ValueError, TypeError) as exc:
                return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})
            return self._json_response(
                start_response,
                "200 OK",
                bundle,
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path.startswith("/api/account/copedents/"):
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            account_access = account_access_for_decision(access)
            if not self.account_copedents_enabled or account_access is None or self.account_copedent_repository is None:
                return self._json_response(start_response, "404 Not Found", {"error": "account copedents are not enabled"})
            profile_id = unquote(path.removeprefix("/api/account/copedents/"))
            try:
                if method == "PUT":
                    request_payload = self._read_json_body(environ)
                    snapshot = request_payload.get("profile") or request_payload.get("profileSnapshot")
                    if not isinstance(snapshot, dict):
                        raise ValueError("profile must be an object")
                    expected_revision = int(
                        request_payload.get("expectedRevision")
                        or request_payload.get("expected_revision")
                        or 0
                    )
                    profile = self.account_copedent_repository.update_profile(
                        account_access,
                        profile_id,
                        snapshot,
                        expected_revision=expected_revision,
                    )
                    return self._json_response(
                        start_response,
                        "200 OK",
                        {
                            "profile": profile,
                            "accountCopedents": self.account_copedent_repository.account_bundle(account_access),
                        },
                        extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                    )
                if method == "DELETE":
                    self.account_copedent_repository.delete_profile(account_access, profile_id)
                    return self._json_response(
                        start_response,
                        "200 OK",
                        self.account_copedent_repository.account_bundle(account_access),
                        extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                    )
            except EntitlementRequiredError as exc:
                return self._entitlement_response(start_response, exc)
            except AccountProfileConflictError as exc:
                return self._json_response(start_response, "409 Conflict", {"error": str(exc), "code": "revision_conflict"})
            except AccountProfileNotFoundError as exc:
                return self._json_response(start_response, "404 Not Found", {"error": str(exc)})
            except JsonRequestTooLargeError as exc:
                return self._json_response(start_response, "413 Payload Too Large", {"error": str(exc)})
            except (JsonRequestError, AccountCopedentError, ValueError, TypeError) as exc:
                return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})
            return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})

        if path == "/api/copedents/e9":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            return self._json_response(
                start_response,
                "200 OK",
                {
                    "schemaVersion": "e9_copedent_library_v2",
                    "defaultProfileId": DEFAULT_COPEDENT_ID,
                    "profiles": [profile.to_dict(include_options=False) for profile in available_e9_copedents()],
                },
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/copedents/validate":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            if self.account_copedents_enabled:
                account_access = account_access_for_decision(access)
                if account_access is None or not account_access.allows("copedent.custom.manage"):
                    return self._entitlement_response(
                        start_response,
                        EntitlementRequiredError("Session Pass is required to validate a custom copedent."),
                    )
            try:
                request_payload = self._read_json_body(environ)
                snapshot = request_payload.get("profileSnapshot") or request_payload.get("profile") or request_payload
                if not isinstance(snapshot, dict):
                    raise ValueError("profile must be an object")
                profile = custom_e9_profile_from_payload(snapshot)
            except (JsonRequestError, ValueError, TypeError) as exc:
                status = "413 Payload Too Large" if isinstance(exc, JsonRequestTooLargeError) else "400 Bad Request"
                return self._json_response(start_response, status, {"error": str(exc)})
            return self._json_response(
                start_response,
                "200 OK",
                {
                    "schemaVersion": "e9_copedent_validation_v2",
                    "valid": True,
                    "profile": profile.to_dict(include_options=False),
                    "copedentContext": {
                        "profileId": profile.id,
                        "profileRevision": profile.revision,
                        "profileSnapshot": snapshot,
                    },
                },
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/explorer/e9":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            try:
                request_payload = self._read_json_body(environ)
                context = request_payload.get("copedentContext") or request_payload.get("copedent_context")
                if context is not None and not isinstance(context, dict):
                    raise ValueError("copedentContext must be an object")
                profile, revision = self._resolve_request_copedent(access, context)
                explorer = build_explorer_payload_for_profile(str(request_payload.get("key") or "G"), profile)
                explorer.update(copedent_context_metadata(profile, revision))
            except EntitlementRequiredError as exc:
                return self._entitlement_response(start_response, exc)
            except AccountProfileNotFoundError as exc:
                return self._json_response(start_response, "404 Not Found", {"error": str(exc)})
            except AccountConfigurationError:
                return self._json_response(start_response, "503 Service Unavailable", {"error": "account copedent service is unavailable"})
            except (JsonRequestError, ValueError, TypeError) as exc:
                status = "413 Payload Too Large" if isinstance(exc, JsonRequestTooLargeError) else "400 Bad Request"
                return self._json_response(start_response, status, {"error": str(exc)})
            return self._json_response(
                start_response,
                "200 OK",
                explorer,
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/amazing-tablature/arrange":
            if method != "POST":
                return self._json_response(
                    start_response,
                    "405 Method Not Allowed",
                    {"error": "method not allowed"},
                )
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            if not self.melody_exercise_enabled:
                return self._json_response(
                    start_response,
                    "404 Not Found",
                    {"error": "Amazing Tablature is not enabled"},
                )
            try:
                request_payload = self._read_json_body(environ)
                arrangement_request = dict(request_payload)
                response_mode = str(
                    arrangement_request.pop(
                        "responseMode",
                        arrangement_request.pop("response_mode", "full"),
                    )
                    or "full"
                )
                if response_mode not in {"full", "play_along_lessons"}:
                    raise MelodyExerciseError("responseMode must be full or play_along_lessons")
                play_along_timeline = arrangement_request.pop(
                    "playAlongTimeline",
                    arrangement_request.pop("play_along_timeline", None),
                )
                opening_chord_melody_events = arrangement_request.pop(
                    "playAlongOpeningChordMelodyEvents",
                    arrangement_request.pop("play_along_opening_chord_melody_events", 0),
                )
                if play_along_timeline is not None and not isinstance(play_along_timeline, list):
                    raise MelodyExerciseError("playAlongTimeline must be an array")
                if not arrangement_request.get("melody") and isinstance(
                    arrangement_request.get("events"), list
                ):
                    arrangement_request["melody"] = list(arrangement_request["events"])
                context = arrangement_request.pop(
                    "copedentContext",
                    arrangement_request.pop("copedent_context", None),
                )
                if context is not None and not isinstance(context, dict):
                    raise MelodyExerciseError("copedentContext must be an object")
                profile, revision = self._resolve_request_copedent(access, context)
                arrangement_request.setdefault("targetCopedentId", profile.id)
                if profile.id.startswith("saved:") and not arrangement_request.get("targetCopedent"):
                    snapshot = self._account_snapshot_for_profile(access, profile)
                    if snapshot:
                        arrangement_request["targetCopedent"] = snapshot
                result = melody_exercise_response(
                    "Arrange this normalized melody for E9.",
                    arrangement_request,
                    ranker_policy=self.amazing_tablature_policy,
                )
                if result is None or result["melody_exercise"]["status"] != "ready":
                    raise MelodyExerciseError(
                        "Amazing Tablature needs at least one normalized note or interval event."
                    )
            except EntitlementRequiredError as exc:
                return self._entitlement_response(start_response, exc)
            except AccountProfileNotFoundError as exc:
                return self._json_response(start_response, "404 Not Found", {"error": str(exc)})
            except AccountConfigurationError:
                return self._json_response(
                    start_response,
                    "503 Service Unavailable",
                    {"error": "account copedent service is unavailable"},
                )
            except (JsonRequestError, MelodyExerciseError, ValueError, TypeError) as exc:
                status = (
                    "413 Payload Too Large"
                    if isinstance(exc, JsonRequestTooLargeError)
                    else "400 Bad Request"
                )
                return self._json_response(start_response, status, {"error": str(exc)})
            exercise = result["melody_exercise"]
            play_along_lessons = None
            if play_along_timeline is not None:
                try:
                    play_along_lessons = build_play_along_melody_lessons(
                        exercise,
                        play_along_timeline,
                        opening_chord_melody_events=int(opening_chord_melody_events),
                    )
                except (SongPracticeError, ValueError, TypeError) as exc:
                    return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})
            if response_mode == "play_along_lessons":
                if play_along_lessons is None:
                    return self._json_response(
                        start_response,
                        "400 Bad Request",
                        {"error": "playAlongTimeline is required for play_along_lessons"},
                    )
                response = {
                    "schemaVersion": "play_along_response_v1",
                    "playAlongLessons": play_along_lessons,
                }
            else:
                selected_route = next(
                    route
                    for route in exercise["routes"]
                    if route["id"] == exercise["selectedRouteId"]
                )
                response = {
                    "schemaVersion": exercise["arrangementContract"]["schemaVersion"],
                    "arrangement": exercise["arrangementContract"],
                    "melodyExercise": exercise,
                    "tabs": list(result.get("tabs") or ()),
                    "tabExample": selected_route["tabExample"],
                    "fretboard": selected_route["fretboard"],
                }
                if play_along_lessons is not None:
                    response["playAlongLessons"] = play_along_lessons
            response.update(copedent_context_metadata(profile, revision))
            return self._json_response(
                start_response,
                "200 OK",
                response,
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/melody/catalog":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"}, extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")))
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error}, extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")))
            if not self.melody_exercise_enabled:
                return self._json_response(start_response, "404 Not Found", {"error": "melody catalog is not enabled"}, extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")))
            return self._json_response(
                start_response,
                "200 OK",
                {"schemaVersion": "score_catalog_v1", "songs": public_song_catalog()},
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        score_job_prefix = "/api/melody/import/jobs/"
        if path.startswith(score_job_prefix):
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"}, extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")))
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error}, extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")))
            if not self.melody_import_enabled:
                return self._json_response(start_response, "404 Not Found", {"error": "melody import is not enabled"}, extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")))
            job = self.score_import_jobs.snapshot(path.removeprefix(score_job_prefix))
            if job is None:
                return self._json_response(start_response, "404 Not Found", {"error": "score import job not found"}, extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")))
            return self._json_response(
                start_response,
                "200 OK",
                job,
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/melody/import":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"}, extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")))
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error}, extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")))
            try:
                request_payload = self._read_bounded_json_body(environ, MAX_IMPORT_BODY_BYTES)
                source_type = str(request_payload.get("sourceType") or request_payload.get("source_type") or "").strip().lower()
                catalog_allowed = source_type == "catalog" and self.melody_exercise_enabled
                if not self.melody_import_enabled and not catalog_allowed:
                    return self._json_response(start_response, "404 Not Found", {"error": "melody import is not enabled"}, extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")))
                if request_payload.get("async") is True and source_type in {"image", "pdf"}:
                    job = self.score_import_jobs.start(request_payload)
                    return self._json_response(
                        start_response,
                        "202 Accepted",
                        job,
                        extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                    )
                draft = import_score_draft(request_payload)
            except MelodyImportTooLargeError as exc:
                return self._json_response(
                    start_response,
                    "413 Payload Too Large",
                    {"error": str(exc)},
                    extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                )
            except MelodyImportError as exc:
                return self._json_response(
                    start_response,
                    "400 Bad Request",
                    {"error": str(exc)},
                    extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
                )
            return self._json_response(
                start_response,
                "200 OK",
                draft,
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/song-practice/catalog":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            if not self.song_practice_enabled:
                return self._json_response(start_response, "404 Not Found", {"error": "song practice is not enabled"})
            try:
                catalog = song_practice_catalog()
            except SongPracticeError as exc:
                return self._json_response(start_response, "503 Service Unavailable", {"error": str(exc)})
            return self._json_response(
                start_response,
                "200 OK",
                catalog,
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/song-practice/arrange":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            if not self.song_practice_enabled:
                return self._json_response(start_response, "404 Not Found", {"error": "song practice is not enabled"})
            try:
                song_request = self._read_json_body(environ)
                context = song_request.get("copedentContext") or song_request.get("copedent_context")
                if context is not None and not isinstance(context, dict):
                    raise SongPracticeError("copedentContext must be an object")
                profile, revision = self._resolve_request_copedent(access, context)
                plan = arrange_song_practice(
                    song_request,
                    copedent_profile=profile,
                    copedent_revision=revision,
                )
            except EntitlementRequiredError as exc:
                return self._entitlement_response(start_response, exc)
            except AccountProfileNotFoundError as exc:
                return self._json_response(start_response, "404 Not Found", {"error": str(exc)})
            except AccountConfigurationError:
                return self._json_response(start_response, "503 Service Unavailable", {"error": "account copedent service is unavailable"})
            except (JsonRequestError, SongPracticeError, ValueError, TypeError) as exc:
                status = "413 Payload Too Large" if isinstance(exc, JsonRequestTooLargeError) else "400 Bad Request"
                return self._json_response(start_response, status, {"error": str(exc)})
            return self._json_response(
                start_response,
                "200 OK",
                plan,
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/lessons/catalog":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            return self._json_response(
                start_response,
                "200 OK",
                lesson_catalog(),
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/lessons/build":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            try:
                lesson_request = self._read_json_body(environ)
                context = lesson_request.get("copedentContext") or lesson_request.get("copedent_context")
                if context is not None and not isinstance(context, dict):
                    raise LessonStudioError("copedentContext must be an object")
                lesson_profile, lesson_revision = self._resolve_request_copedent(access, context)
                result = build_lesson_response(
                    lesson_request,
                    copedent_profile=lesson_profile,
                    copedent_revision=lesson_revision,
                )
                if result.get("status") == "ready":
                    source_results: list[dict[str, Any]] = []
                    query = str((result.get("lesson") or {}).get("topic") or lesson_request.get("topic") or "")
                    if query and callable(getattr(self.search_index, "search", None)):
                        try:
                            public_sources = self._retrieval_dependencies.run(
                                lambda: self._search(query, limit=3),
                                timeout_seconds=self._retrieval_wall_timeout,
                            )
                        except RuntimeError:
                            LOGGER.warning("lesson_source_retrieval_unavailable deterministic_curriculum=true")
                        else:
                            source_results = public_sources.results
                    result = build_lesson_response(
                        lesson_request,
                        source_results=source_results,
                        copedent_profile=lesson_profile,
                        copedent_revision=lesson_revision,
                    )
            except JsonRequestTooLargeError as exc:
                return self._json_response(start_response, "413 Payload Too Large", {"error": str(exc)})
            except JsonRequestError as exc:
                return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})
            except EntitlementRequiredError as exc:
                return self._entitlement_response(start_response, exc)
            except AccountProfileNotFoundError as exc:
                return self._json_response(start_response, "404 Not Found", {"error": str(exc)})
            except AccountConfigurationError:
                return self._json_response(start_response, "503 Service Unavailable", {"error": "account copedent service is unavailable"})
            except LessonStudioError as exc:
                return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})
            return self._json_response(
                start_response,
                "200 OK",
                result,
                extra_headers=(("Cache-Control", "no-store"), ("Pragma", "no-cache")),
            )

        if path == "/api/tab/render":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            access = self._authorize_content_request(environ)
            if not access.allowed:
                return self._json_response(start_response, access.status, {"error": access.error})
            try:
                request_payload = self._read_json_body(environ)
            except JsonRequestTooLargeError as exc:
                return self._json_response(start_response, "413 Payload Too Large", {"error": str(exc)})
            except JsonRequestError as exc:
                return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})
            return self._json_response(start_response, "200 OK", render_tab_from_payload(request_payload).to_dict())

        if path == "/api/answer":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})

            access = self._authorize_content_request(environ)
            if not access.allowed:
                self._log_answer_attempt(
                    {},
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="blocked",
                    authorized=False,
                    error_status=access.status,
                )
                return self._json_response(start_response, access.status, {"error": access.error})

            try:
                request_payload = self._read_json_body(environ)
            except JsonRequestTooLargeError as exc:
                return self._json_response(start_response, "413 Payload Too Large", {"error": str(exc)})
            except JsonRequestError as exc:
                return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})

            identity_key = self._identity_key(access.identity_email)
            rate_key = answer_rate_limit_key(environ, access.role, identity_key=identity_key)
            rate_limit = self.answer_rate_limiter.check(rate_key)
            if not rate_limit.allowed:
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="rate_limited",
                    authorized=True,
                    error_status="429 Too Many Requests",
                )
                return self._json_response(
                    start_response,
                    "429 Too Many Requests",
                    {"error": rate_limit.error, "retryAfterSeconds": rate_limit.retry_after_seconds},
                )

            answer_request, error = parse_answer_request(request_payload)
            if error or answer_request is None:
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    error_status="400 Bad Request",
                )
                return self._json_response(start_response, "400 Bad Request", {"error": error or "invalid request"})

            copedent_context = request_payload.get("copedentContext") or request_payload.get("copedent_context")
            if copedent_context is not None and not isinstance(copedent_context, dict):
                return self._json_response(start_response, "400 Bad Request", {"error": "copedentContext must be an object"})
            try:
                target_profile, target_revision = self._resolve_request_copedent(access, copedent_context)
            except EntitlementRequiredError as exc:
                return self._entitlement_response(start_response, exc)
            except AccountProfileNotFoundError as exc:
                return self._json_response(start_response, "404 Not Found", {"error": str(exc)})
            except AccountConfigurationError:
                return self._json_response(start_response, "503 Service Unavailable", {"error": "account copedent service is unavailable"})
            except (ValueError, TypeError) as exc:
                return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})

            profile_personalization_requested = bool(
                copedent_context is not None or self.account_copedents_enabled
            )

            direct_profile_answer = (
                profile_control_answer(answer_request.question, target_profile)
                if profile_personalization_requested
                else None
            )
            if direct_profile_answer is not None:
                direct_profile_answer = normalize_answer_list_markers(direct_profile_answer)
                payload: AnswerResponse = {
                    "answer": direct_profile_answer,
                    "mode": answer_request.mode,
                    "sources": [],
                    "warnings": [],
                    "sections": build_sections(direct_profile_answer),
                    "answer_provenance": DETERMINISTIC_E9_PROVENANCE,
                }
                payload.update(copedent_context_metadata(target_profile, target_revision))
                return self._answer_success_response(
                    start_response, payload, access, request_payload=request_payload
                )

            answer_intent_decision: dict[str, Any] = dict(
                classify_answer_request(
                    answer_request.question,
                    answer_request.mode,
                )
            )
            route_trace = AnswerRouteTrace(
                classification=(
                    f"{answer_intent_decision.get('domain', 'unknown')}:"
                    f"{answer_intent_decision.get('intent', 'unknown')}"
                )
            )
            parent_answer_context = _normalized_parent_answer_context(
                request_payload.get("parentAnswerContext")
            )
            parent_answer_kind = (
                parent_answer_context["answer_provenance"].get("kind", "")
                if parent_answer_context is not None
                else ""
            )
            provenance_followup = (
                None
                if parent_answer_kind in SOURCE_BACKED_PARENT_PROVENANCE_KINDS
                else source_provenance_followup_answer(
                    answer_request.question,
                    answer_request.conversation_context,
                )
            )
            if provenance_followup is not None:
                final_answer = final_answer_quality_gate(
                    provenance_followup.answer,
                    answer_request.question,
                )
                contract_validation = enforce_answer_contract(
                    final_answer,
                    provenance_followup.intent,
                )
                final_answer = normalize_answer_list_markers(contract_validation.answer)
                payload: AnswerResponse = {
                    "answer": final_answer,
                    "mode": answer_request.mode,
                    "sources": [],
                    "warnings": [],
                    "sections": build_sections(final_answer),
                    "answer_provenance": (
                        POSITION_STRATEGY_PROVENANCE
                        if provenance_followup.intent == "position_strategy"
                        else DETERMINISTIC_E9_PROVENANCE
                    ),
                }
                if copedent_context is not None:
                    _personalize_answer_payload(payload, target_profile, target_revision)
                route_trace.classification = "steel_guitar:source_provenance_followup"
                route_trace.route = "deterministic"
                route_trace.retrieval = "not_needed"
                route_trace.evidence = "deterministic_e9_pitch_calculation"
                route_trace.synthesis = "contextual_provenance_explanation"
                route_trace.verification = "answer_contract"
                route_trace.displayed_answer = "answer_with_provenance"
                self._log_route_trace(route_trace)
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    source_count=0,
                    warning_count=0,
                )
                return self._answer_success_response(
                    start_response,
                    payload,
                    access,
                    request_payload=request_payload,
                )

            if (
                request_payload.get("isFollowup") is True
                and is_source_provenance_followup(answer_request.question)
                and parent_answer_context is not None
            ):
                parent_provenance = parent_answer_context["answer_provenance"]
                parent_kind = parent_provenance.get("kind", "")
                if parent_kind in SOURCE_BACKED_PARENT_PROVENANCE_KINDS:
                    parent_sources = parent_answer_context["sources"]
                    if parent_sources:
                        source_lines = [
                            f"{index}. [{index}] {source['forumName']} — {source['title']}"
                            for index, source in enumerate(parent_sources, start=1)
                        ]
                        if parent_kind == "sgf_extractive_degraded":
                            provenance_intro = (
                                "The preceding answer used extractive degraded SGF evidence. It was assembled "
                                "locally from the same displayed passages below; no generative model was used."
                            )
                            answer_provenance = EXTRACTIVE_DEGRADED_PROVENANCE
                        else:
                            provenance_intro = (
                                "The preceding answer used the same displayed Steel Guitar Forum evidence below. "
                                "Local lexical and BGE retrieval ranked those passages, Terra wrote passage-linked "
                                "claims, and Luna verified their relevance and citation support."
                            )
                            answer_provenance = VERIFIED_SYNTHESIS_PROVENANCE
                        final_answer = (
                            f"{provenance_intro}\n\n"
                            "This follow-up reused the preceding answer’s verified source cards; it did not run "
                            "another retrieval or model request.\n\n"
                            "Sources from the preceding answer:\n"
                            + "\n".join(source_lines)
                        )
                        warnings: list[str] = []
                    else:
                        final_answer = (
                            "The preceding response did not contain a claim with a displayable supporting source "
                            "card. It was an abstention or unavailable-evidence response, so there is no source "
                            "passage I can honestly attribute to it. This follow-up did not run another retrieval "
                            "or model request."
                        )
                        warnings = ["prior answer contained no displayable source cards"]
                        answer_provenance = (
                            EXTRACTIVE_DEGRADED_PROVENANCE
                            if parent_kind == "sgf_extractive_degraded"
                            else VERIFIED_SYNTHESIS_PROVENANCE
                        )
                    payload = {
                        "answer": final_answer,
                        "mode": answer_request.mode,
                        "sources": parent_sources,
                        "warnings": warnings,
                        "sections": build_sections(final_answer),
                        "answer_provenance": answer_provenance,
                    }
                    route_trace.classification = "steel_guitar:source_provenance_followup"
                    route_trace.route = "deterministic"
                    route_trace.retrieval = "reused_prior_source_cards"
                    route_trace.evidence = f"{len(parent_sources)}_prior_source_cards"
                    route_trace.synthesis = "not_run_contextual_provenance"
                    route_trace.verification = "validated_parent_answer_envelope"
                    route_trace.displayed_answer = "prior_answer_provenance"
                    self._log_route_trace(route_trace)
                    self._log_answer_attempt(
                        request_payload,
                        role=access.role,
                        identity_email=access.identity_email,
                        access_status="authorized",
                        authorized=True,
                        source_count=len(parent_sources),
                        warning_count=len(warnings),
                    )
                    return self._answer_success_response(
                        start_response,
                        payload,
                        access,
                        request_payload=request_payload,
                    )

            if (
                request_payload.get("isFollowup") is True
                and is_source_provenance_followup(answer_request.question)
                and not answer_request.conversation_context
            ):
                final_answer = (
                    "I can answer that provenance question, but the earlier question and answer were not "
                    "included with this follow-up request. Please return to the original answer and use its "
                    "follow-up box again, or paste the claim you want sourced; I will identify whether it came "
                    "from deterministic E9 rules, curated guidance, or retrieved source cards."
                )
                payload = {
                    "answer": final_answer,
                    "mode": answer_request.mode,
                    "sources": [],
                    "warnings": ["prior conversation context was unavailable"],
                    "sections": build_sections(final_answer),
                }
                route_trace.classification = "source_provenance_followup:context_missing"
                route_trace.route = "guardrail"
                route_trace.retrieval = "not_run"
                route_trace.evidence = "prior_turn_missing"
                route_trace.synthesis = "context_recovery_clarifier"
                route_trace.verification = "context_required"
                route_trace.displayed_answer = "context_recovery_clarifier"
                self._log_route_trace(route_trace)
                return self._answer_success_response(
                    start_response,
                    payload,
                    access,
                    request_payload=request_payload,
                )

            prior_context_question = _prior_user_question(
                answer_request.conversation_context
            )
            if (
                answer_intent_decision.get("domain") == "off_domain"
                and answer_intent_decision.get("intent") == "unknown"
                and prior_context_question
                and CONTEXTUAL_FOLLOWUP_RE.search(answer_request.question)
            ):
                prior_decision = classify_answer_request(
                    prior_context_question,
                    answer_request.mode,
                )
                if prior_decision.get("domain") == "steel_guitar":
                    answer_intent_decision = corpus_promoted_decision(
                        answer_request.question
                    )
                    route_trace.classification = "contextual_steel_followup:source_backed"

            corpus_probe_response: SearchResponse | None = None
            corpus_promoted = False
            contextual_probe_question = contextual_entity_probe_question(
                answer_request.question,
                answer_request.conversation_context,
            )
            entity_probe_question = (
                contextual_probe_question
                or (
                    answer_request.question
                    if is_corpus_entity_candidate(answer_request.question, answer_intent_decision)
                    else None
                )
            )
            if entity_probe_question is not None:
                route_trace.corpus_probe = "checking_public_sgf"
                try:
                    corpus_probe_response = self._retrieval_dependencies.run(
                        lambda: self._search(entity_probe_question, limit=4),
                        timeout_seconds=self._retrieval_wall_timeout,
                    )
                except RuntimeError:
                    route_trace.corpus_probe = "unavailable"
                else:
                    entity_evidence = evaluate_corpus_entity_evidence(
                        entity_probe_question,
                        corpus_probe_response.results,
                    )
                    route_trace.corpus_probe = entity_evidence.reason
                    if entity_evidence.strong:
                        answer_intent_decision = corpus_promoted_decision(answer_request.question)
                        corpus_promoted = True
                        route_trace.classification = (
                            f"corpus_promoted:{answer_intent_decision['intent']}"
                        )

            deterministic_question = (
                deterministic_subquestion_for_hybrid(answer_request.question)
                or answer_request.question
            )
            if deterministic_question != answer_request.question:
                answer_intent_decision = hybrid_promoted_decision(answer_intent_decision)
                route_trace.classification = (
                    f"hybrid_requested:{answer_intent_decision.get('intent', 'unknown')}"
                )
            deterministic_chord_answer = visual_fretboard_curated_answer(
                deterministic_question
            )
            if deterministic_chord_answer is None:
                deterministic_chord_answer = unsupported_chord_position_curated_answer(
                    deterministic_question
                )
            deterministic_fretboard_payload = fretboard_payload_for_question(
                deterministic_question
            )
            answer_route = select_answer_route(
                answer_intent_decision,
                deterministic_available=deterministic_chord_answer is not None,
            )
            if (
                deterministic_chord_answer is not None
                and deterministic_question == answer_request.question
                and not corpus_promoted
            ):
                answer_route = "deterministic"
            route_trace.route = answer_route
            curated_guidance_status: str | None = None
            curated_guidance_count: int | None = None

            melody_request = request_payload.get("melodyRequest") or request_payload.get("melody_request")
            if melody_request is not None and not isinstance(melody_request, dict):
                return self._json_response(
                    start_response,
                    "400 Bad Request",
                    {"error": "melodyRequest must be an object"},
                )
            if melody_request is not None and profile_personalization_requested:
                melody_request = dict(melody_request)
                if not melody_request.get("targetCopedent") and not melody_request.get("target_copedent"):
                    snapshot = (copedent_context or {}).get("profileSnapshot") or (copedent_context or {}).get("profile_snapshot")
                    if not snapshot:
                        snapshot = self._account_snapshot_for_profile(access, target_profile)
                    if snapshot:
                        melody_request["targetCopedent"] = snapshot
                if not melody_request.get("targetCopedentId") and not melody_request.get("target_copedent_id"):
                    melody_request["targetCopedentId"] = target_profile.id
            if self.melody_exercise_enabled:
                try:
                    melody_result = melody_exercise_response(
                        answer_request.question,
                        melody_request,
                        ranker_policy=self.amazing_tablature_policy,
                    )
                except MelodyExerciseError as exc:
                    self._log_answer_attempt(
                        request_payload,
                        role=access.role,
                        identity_email=access.identity_email,
                        access_status="authorized",
                        authorized=True,
                        error_status="400 Bad Request",
                    )
                    return self._json_response(start_response, "400 Bad Request", {"error": str(exc)})
            else:
                melody_result = None
            if melody_result is not None:
                final_answer = normalize_answer_list_markers(str(melody_result["answer"]))
                selected_melody_route = next(
                    (
                        route
                        for route in melody_result["melody_exercise"].get("routes") or ()
                        if route.get("id")
                        == melody_result["melody_exercise"].get("selectedRouteId")
                    ),
                    None,
                )
                payload: AnswerResponse = {
                    "answer": final_answer,
                    "mode": answer_request.mode,
                    "sources": list(melody_result.get("sources") or []),
                    "warnings": list(melody_result.get("warnings") or []),
                    "sections": build_sections(final_answer),
                    "melody_exercise": melody_result["melody_exercise"],
                }
                selected_tab_example = (
                    selected_melody_route.get("tabExample")
                    if selected_melody_route is not None
                    else melody_result.get("tab_example")
                )
                selected_fretboard = (
                    selected_melody_route.get("fretboard")
                    if selected_melody_route is not None
                    else melody_result.get("fretboard")
                )
                if selected_tab_example is not None:
                    payload["tab_example"] = selected_tab_example
                if melody_result.get("tabs") is not None:
                    payload["tabs"] = list(melody_result["tabs"])
                if selected_fretboard is not None:
                    payload["fretboard"] = selected_fretboard
                payload.update(copedent_context_metadata(target_profile, target_revision))
                route_trace.route = "deterministic"
                route_trace.retrieval = "not_needed"
                route_trace.evidence = "deterministic_melody_model"
                route_trace.synthesis = "melody_exercise"
                route_trace.verification = "deterministic_contract"
                route_trace.displayed_answer = "answer_with_melody_exercise"
                self._log_route_trace(route_trace)
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    source_count=len(payload["sources"]),
                    warning_count=len(payload["warnings"]),
                )
                return self._answer_success_response(
                    start_response, payload, access, request_payload=request_payload
                )

            progression_guide_answer = progression_guide_for_question(answer_request.question)
            if (
                progression_guide_answer is not None
                and answer_intent_decision.get("domain") != "unsafe_or_impossible"
            ):
                final_answer = final_answer_quality_gate(
                    str(progression_guide_answer["answer"]),
                    answer_request.question,
                )
                contract_validation = enforce_answer_contract(final_answer, "copedent_fretboard")
                final_answer = normalize_answer_list_markers(contract_validation.answer)
                payload: AnswerResponse = {
                    "answer": final_answer,
                    "mode": answer_request.mode,
                    "sources": [],
                    "warnings": [],
                    "sections": build_sections(final_answer),
                    "progression_guide": progression_guide_answer["progression_guide"],
                    "fretboard": progression_guide_answer["fretboard"],
                    "answer_provenance": DETERMINISTIC_E9_PROVENANCE,
                }
                if copedent_context is not None:
                    _personalize_answer_payload(payload, target_profile, target_revision)
                route_trace.route = "deterministic"
                route_trace.retrieval = "not_needed"
                route_trace.evidence = "deterministic_progression_rules"
                route_trace.synthesis = "progression_guide"
                route_trace.verification = "answer_contract"
                route_trace.displayed_answer = "answer_with_progression_guide"
                self._log_route_trace(route_trace)
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    source_count=0,
                    warning_count=0,
                )
                return self._answer_success_response(
                    start_response, payload, access, request_payload=request_payload
                )

            if (
                deterministic_chord_answer is not None
                and answer_intent_decision.get("domain") != "unsafe_or_impossible"
                and answer_route != "hybrid"
            ):
                final_answer = final_answer_quality_gate(deterministic_chord_answer.answer, answer_request.question)
                contract_validation = enforce_answer_contract(final_answer, deterministic_chord_answer.intent)
                final_answer = contract_validation.answer
                final_answer = normalize_answer_list_markers(final_answer)
                fretboard_payload = deterministic_fretboard_payload
                curated_sources = concise_source_cards(list(deterministic_chord_answer.source_cards))
                payload: AnswerResponse = {
                    "answer": final_answer,
                    "mode": answer_request.mode,
                    "sources": curated_sources,
                    "warnings": [],
                    "sections": build_sections(final_answer),
                    "answer_provenance": DETERMINISTIC_E9_PROVENANCE,
                }
                if fretboard_payload is not None:
                    payload["fretboard"] = fretboard_payload
                _attach_tab_example_if_available(
                    payload,
                    answer_request.question,
                    answer_intent_decision=answer_intent_decision,
                )
                if copedent_context is not None:
                    _personalize_answer_payload(payload, target_profile, target_revision)
                route_trace.route = "deterministic"
                route_trace.retrieval = "not_needed"
                route_trace.evidence = "deterministic_copedent_rules"
                route_trace.synthesis = "deterministic_chord_answer"
                route_trace.verification = "answer_contract"
                route_trace.displayed_answer = "answer_with_optional_fretboard"
                self._log_route_trace(route_trace)
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    source_count=len(curated_sources),
                    warning_count=0,
                )
                return self._answer_success_response(
                    start_response, payload, access, request_payload=request_payload
                )

            if (
                _should_gate_answer_intent(answer_intent_decision)
            ):
                final_answer = _answer_intent_guardrail_answer(answer_intent_decision["domain"])
                final_answer = normalize_answer_list_markers(final_answer)
                payload: AnswerResponse = {
                    "answer": final_answer,
                    "mode": answer_request.mode,
                    "sources": [],
                    "warnings": [],
                    "sections": build_sections(final_answer),
                }
                if copedent_context is not None:
                    _personalize_answer_payload(payload, target_profile, target_revision)
                route_trace.route = "guardrail"
                route_trace.retrieval = "not_allowed"
                route_trace.evidence = "not_applicable"
                route_trace.synthesis = "guardrail_copy"
                route_trace.verification = "guardrail_contract"
                route_trace.displayed_answer = "guardrail"
                self._log_route_trace(route_trace)
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    source_count=0,
                    warning_count=0,
                )
                # Scope/copyright guardrails are blocked requests, not successful Ask usage.
                return self._json_response(start_response, "200 OK", payload)

            curated_guidance_results, curated_guidance_status = self._curated_guidance_for_answer(
                answer_request.question,
                role=access.role,
                answer_intent_decision=answer_intent_decision,
                limit=answer_request.top_k,
            )
            curated_guidance_count = len(curated_guidance_results)

            practical_intent_answer = (
                intent_mode_curated_answer(answer_request.question)
                if answer_route == "deterministic"
                else None
            )
            if practical_intent_answer is not None:
                final_answer = final_answer_quality_gate(practical_intent_answer.answer, answer_request.question)
                contract_validation = enforce_answer_contract(final_answer, practical_intent_answer.intent)
                final_answer = contract_validation.answer
                final_answer = normalize_answer_list_markers(final_answer)
                payload: AnswerResponse = {
                    "answer": final_answer,
                    "mode": answer_request.mode,
                    "sources": [],
                    "warnings": [],
                    "sections": build_sections(final_answer),
                    "answer_provenance": _answer_provenance(
                        "curated_local_guidance",
                        "Curated local guidance",
                        "Selected from reviewed Steel Guitar RAG teaching rules; no retrieved quotation or language model was used.",
                    ),
                }
                _attach_tab_example_if_available(
                    payload,
                    answer_request.question,
                    answer_intent_decision=answer_intent_decision,
                )
                classic_country_move_payload = classic_country_move_payload_for_question(answer_request.question)
                if classic_country_move_payload is not None:
                    payload["fretboard"] = classic_country_move_payload
                if copedent_context is not None:
                    _personalize_answer_payload(payload, target_profile, target_revision)
                route_trace.route = "deterministic"
                route_trace.retrieval = "not_needed"
                route_trace.evidence = "curated_rules"
                route_trace.synthesis = "curated_practical_answer"
                route_trace.verification = "answer_contract"
                route_trace.displayed_answer = "answer_with_optional_tab"
                self._log_route_trace(route_trace)
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    source_count=0,
                    warning_count=0,
                    curated_guidance_count=curated_guidance_count,
                    curated_guidance_status=curated_guidance_status,
                )
                return self._answer_success_response(
                    start_response, payload, access, request_payload=request_payload
                )

            if (
                answer_route == "deterministic"
                and answer_intent_decision["domain"] == "steel_guitar"
                and answer_intent_decision["allowed_answer_shape"] != "guardrail_refusal"
            ):
                answer_route = "source_backed_rag"
                route_trace.route = answer_route
                route_trace.fallback = "deterministic_miss_to_source_backed"

            if self.canonical_frontier_enabled and answer_route in {
                "source_backed_rag",
                "hybrid",
            }:
                frontier_error: Exception | None = None
                try:
                    frontier_client = self.canonical_frontier_client
                    if frontier_client is None:
                        raise CanonicalFrontierUnavailable(
                            "canonical frontier client is not configured"
                        )
                    frontier_result = self._answer_dependencies.run(
                        lambda: frontier_client.answer(
                            answer_request.question,
                            conversation_context=list(answer_request.conversation_context),
                        ),
                        timeout_seconds=self._answer_wall_timeout,
                    )
                except (CanonicalFrontierUnavailable, RuntimeError) as exc:
                    frontier_error = exc
                else:
                    frontier_metadata = frontier_result.get("metadata") or {}
                    frontier_delivery_mode = (
                        str(frontier_metadata.get("delivery_mode") or "")
                        if isinstance(frontier_metadata, dict)
                        else ""
                    )
                    frontier_degraded = frontier_delivery_mode == "sgf_extractive_degraded"
                    route_trace.retrieval = (
                        "canonical_frontier_local_extractive"
                        if frontier_degraded
                        else "canonical_frontier_complete"
                    )
                    frontier_mode = str(frontier_result.get("mode") or "complete")
                    frontier_answer = normalize_answer_list_markers(
                        str(frontier_result["answer"])
                    )
                    frontier_sources = concise_source_cards(list(frontier_result["sources"]))
                    route_trace.evidence = f"{len(frontier_sources)}_source_cards"
                    route_trace.synthesis = (
                        "not_run_extractive_degraded"
                        if frontier_degraded
                        else f"terra_{frontier_mode}"
                    )
                    route_trace.verification = (
                        "deterministic_sentence_support"
                        if frontier_degraded
                        else "luna_claim_entailment"
                    )
                    final_answer = frontier_answer
                    if answer_route == "hybrid" and deterministic_chord_answer is not None:
                        deterministic_answer = final_answer_quality_gate(
                            deterministic_chord_answer.answer,
                            answer_request.question,
                        )
                        deterministic_contract = enforce_answer_contract(
                            deterministic_answer,
                            deterministic_chord_answer.intent,
                        )
                        final_answer = normalize_answer_list_markers(
                            f"Deterministic E9 result:\n\n{deterministic_contract.answer}"
                            f"\n\nSource-backed forum context:\n\n{frontier_answer}"
                        )
                        route_trace.synthesis = f"deterministic_plus_frontier_{frontier_mode}"
                    payload: AnswerResponse = {
                        "answer": final_answer,
                        "mode": answer_request.mode,
                        "sources": frontier_sources,
                        "warnings": (
                            ["verified synthesis is unavailable; showing extractive SGF evidence"]
                            if frontier_degraded
                            else []
                        ),
                        "sections": build_sections(final_answer),
                        "answer_provenance": (
                            EXTRACTIVE_DEGRADED_PROVENANCE
                            if frontier_degraded
                            else VERIFIED_SYNTHESIS_PROVENANCE
                        ),
                    }
                    if answer_route == "hybrid" and deterministic_fretboard_payload is not None:
                        payload["fretboard"] = deterministic_fretboard_payload
                        _attach_tab_example_if_available(
                            payload,
                            answer_request.question,
                            answer_intent_decision=answer_intent_decision,
                        )
                    if profile_personalization_requested:
                        _personalize_answer_payload(payload, target_profile, target_revision)
                    route_trace.displayed_answer = "answer_with_sources"
                    self._log_route_trace(route_trace)
                    self._log_answer_attempt(
                        request_payload,
                        role=access.role,
                        identity_email=access.identity_email,
                        access_status="authorized",
                        authorized=True,
                        source_count=len(frontier_sources),
                        warning_count=len(payload["warnings"]),
                    )
                    return self._answer_success_response(
                        start_response,
                        payload,
                        access,
                        request_payload=request_payload,
                        ai_assisted=not frontier_degraded,
                    )

                if frontier_error is not None:
                    cause = frontier_error.__cause__
                    frontier_error_code = getattr(
                        frontier_error,
                        "error_code",
                        "canonical_frontier_unavailable",
                    )
                    LOGGER.warning(
                        "canonical_frontier_unavailable honest_failure=true error_type=%s cause_type=%s error_code=%s trace_id=%s",
                        type(frontier_error).__name__,
                        type(cause).__name__ if cause is not None else "none",
                        frontier_error_code,
                        route_trace.trace_id,
                    )
                    route_trace.retrieval = "canonical_frontier_unavailable"
                    route_trace.evidence = "unavailable"
                    route_trace.synthesis = "not_run"
                    route_trace.verification = "not_run"
                    route_trace.fallback = "bounded_local_extractive"
                    degraded_result = None
                    try:
                        local_response = self._retrieval_dependencies.run(
                            lambda: self._search(answer_request.question, limit=10),
                            timeout_seconds=self._retrieval_wall_timeout,
                        )
                    except RuntimeError:
                        route_trace.fallback = "local_retrieval_unavailable"
                    else:
                        degraded_result = compose_extractive_degraded_answer(
                            answer_request.question,
                            local_response.results,
                        )
                    if degraded_result is not None:
                        degraded_answer = degraded_result.answer
                        if answer_route == "hybrid" and deterministic_chord_answer is not None:
                            deterministic_answer = final_answer_quality_gate(
                                deterministic_chord_answer.answer,
                                answer_request.question,
                            )
                            deterministic_contract = enforce_answer_contract(
                                deterministic_answer,
                                deterministic_chord_answer.intent,
                            )
                            degraded_answer = normalize_answer_list_markers(
                                f"Deterministic E9 result:\n\n{deterministic_contract.answer}"
                                f"\n\nExtractive SGF evidence:\n\n{degraded_answer}"
                            )
                        payload = {
                            "answer": degraded_answer,
                            "mode": answer_request.mode,
                            "sources": degraded_result.sources,
                            "warnings": [
                                "verified synthesis is unavailable; showing extractive SGF evidence"
                            ],
                            "sections": build_sections(degraded_answer),
                            "answer_provenance": EXTRACTIVE_DEGRADED_PROVENANCE,
                        }
                        if answer_route == "hybrid" and deterministic_fretboard_payload is not None:
                            payload["fretboard"] = deterministic_fretboard_payload
                        if profile_personalization_requested:
                            _personalize_answer_payload(payload, target_profile, target_revision)
                        route_trace.retrieval = "local_public_sgf_degraded"
                        route_trace.evidence = f"{len(degraded_result.sources)}_source_cards"
                        route_trace.synthesis = "not_run_extractive_degraded"
                        route_trace.verification = "deterministic_sentence_support"
                        route_trace.displayed_answer = (
                            "extractive_cards_only"
                            if degraded_result.cards_only
                            else "extractive_answer_with_sources"
                        )
                        self._log_route_trace(route_trace)
                        self._log_answer_attempt(
                            request_payload,
                            role=access.role,
                            identity_email=access.identity_email,
                            access_status="authorized",
                            authorized=True,
                            source_count=len(degraded_result.sources),
                            warning_count=1,
                        )
                        return self._answer_success_response(
                            start_response,
                            payload,
                            access,
                            request_payload=request_payload,
                            ai_assisted=False,
                        )

                    if answer_route == "hybrid" and deterministic_chord_answer is not None:
                        deterministic_answer = final_answer_quality_gate(
                            deterministic_chord_answer.answer,
                            answer_request.question,
                        )
                        deterministic_contract = enforce_answer_contract(
                            deterministic_answer,
                            deterministic_chord_answer.intent,
                        )
                        final_answer = normalize_answer_list_markers(
                            f"{deterministic_contract.answer}\n\n"
                            "The deterministic E9 result is available, but the source-backed "
                            "forum context could not be completed right now. No forum summary "
                            "was substituted."
                        )
                        payload = {
                            "answer": final_answer,
                            "mode": answer_request.mode,
                            "sources": [],
                            "warnings": ["source-backed forum context is temporarily unavailable"],
                            "sections": build_sections(final_answer),
                            "answer_provenance": DETERMINISTIC_E9_PROVENANCE,
                        }
                        if deterministic_fretboard_payload is not None:
                            payload["fretboard"] = deterministic_fretboard_payload
                        _attach_tab_example_if_available(
                            payload,
                            answer_request.question,
                            answer_intent_decision=answer_intent_decision,
                        )
                        if profile_personalization_requested:
                            _personalize_answer_payload(payload, target_profile, target_revision)
                        route_trace.displayed_answer = "deterministic_partial_with_honest_warning"
                        self._log_route_trace(route_trace)
                        return self._answer_success_response(
                            start_response,
                            payload,
                            access,
                            request_payload=request_payload,
                            ai_assisted=False,
                        )

                    route_trace.displayed_answer = "source_service_unavailable"
                    self._log_route_trace(route_trace)
                    self._log_answer_attempt(
                        request_payload,
                        role=access.role,
                        identity_email=access.identity_email,
                        access_status="authorized",
                        authorized=True,
                        source_count=0,
                        warning_count=1,
                        error_status="503 Service Unavailable",
                    )
                    return self._json_response(
                        start_response,
                        "503 Service Unavailable",
                        {
                            "error": (
                                "The source-backed steel-guitar knowledge service could not "
                                "complete this answer. No generic answer was substituted. "
                                "Please try again."
                            )
                        },
                        extra_headers=(("X-Steel-Rag-Trace-Id", route_trace.trace_id),),
                    )

            source_system = self._optional_string(request_payload.get("sourceSystem") or request_payload.get("source_system"))
            forum_name = self._optional_string(request_payload.get("forumName") or request_payload.get("forum_name"))
            ai_assisted = False
            if corpus_probe_response is not None and source_system is None and forum_name is None:
                search_response = corpus_probe_response
            else:
                search_response = self._search_for_answer(
                    answer_request.question,
                    role=access.role,
                    limit=answer_request.top_k,
                    source_system=source_system,
                    forum_name=forum_name,
                )
            warnings = list(search_response.warnings)
            user_prompt_injection = is_injection_like(answer_request.question)
            if user_prompt_injection:
                warnings.append("prompt-injection-like text ignored")
            strong_sources = [source for source in search_response.results if float(source.get("score") or 0.0) > 0.0]
            sanitized = sanitize_retrieved_sources(strong_sources)
            warnings.extend(sanitized.warnings)
            strong_sources = sanitized.sources
            contract_intent = infer_contract_intent(answer_request.question, answer_request.mode)
            exercise_answer = bc_pedal_exercise_answer(answer_request.question, strong_sources)
            if exercise_answer is not None:
                answer = exercise_answer
                contract_intent = "practice_plan"
                sources = concise_source_cards(strong_sources)
            else:
                profile_answer = private_profile_answer(answer_request.question, strong_sources)
                if profile_answer is not None:
                    answer = profile_answer
                    contract_intent = "copedent_fretboard"
                    sources = concise_source_cards(strong_sources)
                else:
                    direct_curated_answer = intent_mode_curated_answer(
                        answer_request.question
                    )
                    curated_answer = lookup_curated_answer(answer_request.question, strong_sources)
                if profile_answer is not None:
                    pass
                elif curated_answer is not None:
                    answer = curated_answer.answer
                    contract_intent = curated_answer.intent
                    clean_telonics_slide_check = (
                        curated_answer.intent == "curated_fact_source_check"
                        and "telonics" in answer_request.question.lower()
                        and _question_mentions_slide_bar_item(answer_request.question)
                    )
                    if curated_answer.intent == "curated_fact_source_check" and not clean_telonics_slide_check:
                        warnings.append(CURATED_FACT_WEAK_WARNING)
                    if curated_answer.intent == "curated_fact_source_check" and not clean_telonics_slide_check and retrieval_looks_weak_for_curated(
                        answer_request.question, curated_answer, strong_sources
                    ):
                        warnings.append(WEAK_RETRIEVAL_WARNING)
                    if (
                        _curated_answer_should_be_source_free(curated_answer.intent)
                        or (
                            direct_curated_answer is not None
                            and direct_curated_answer.answer == curated_answer.answer
                        )
                    ):
                        sources = []
                    elif curated_answer.source_cards:
                        sources = concise_source_cards(list(curated_answer.source_cards))
                    elif answer_is_no_source(answer):
                        sources = []
                        warnings.append("no strong source match")
                    elif curated_answer.intent == "vendor_buying_guidance" and _question_mentions_slide_bar_item(
                        answer_request.question
                    ):
                        sources = concise_source_cards(slide_bar_vendor_source_cards())
                    else:
                        sources = concise_source_cards(strong_sources)
                elif user_prompt_injection:
                    answer = (
                        "I can’t follow prompt-injection instructions. "
                        "Ask a steel-guitar question and I’ll answer from the available sources."
                    )
                    sources = concise_source_cards(strong_sources)
                elif not strong_sources:
                    answer = "No strong source match found for that question."
                    sources: list[dict[str, Any]] = []
                    warnings.append("no strong source match")
                else:
                    try:
                        answer = self._answer_dependencies.run(
                            lambda: self.answer_provider.answer(answer_request, strong_sources),
                            timeout_seconds=self._answer_wall_timeout,
                        )
                        ai_assisted = bool(getattr(self.answer_provider, "is_ai_backed", False))
                    except RuntimeError:
                        LOGGER.warning("answer_provider_unavailable deterministic_fallback=true")
                        answer = DeterministicAnswerProvider().answer(answer_request, strong_sources)
                        warnings.append("live answer provider unavailable; deterministic guidance returned")
                    if answer_is_no_source(answer):
                        sources = []
                        warnings.append("no strong source match")
                    else:
                        sources = concise_source_cards(strong_sources)
            answer = apply_private_profile_wording(answer, answer_request.question, strong_sources)
            raw_answer_needed_quarantine = sgf_answer_body_needs_quarantine(answer)
            final_answer = final_answer_quality_gate(answer, answer_request.question)
            if raw_answer_needed_quarantine or sgf_answer_body_needs_quarantine(final_answer):
                quarantine_answer = sgf_quarantine_teacher_answer(answer_request.question)
                if quarantine_answer is not None:
                    route_trace.fallback = "sgf_quarantine_teacher_answer"
                else:
                    quarantine_answer = generic_sgf_quarantine_fallback_answer(
                        answer_request.question
                    )
                    route_trace.fallback = "sgf_quarantine_specificity_fallback"
                final_answer = final_answer_quality_gate(quarantine_answer.answer, answer_request.question)
                contract_intent = quarantine_answer.intent
                sources = []
                warnings = []
            contract_validation = enforce_answer_contract(final_answer, contract_intent)
            if contract_validation.violations and contract_validation.answer != final_answer:
                warnings.append(f"answer contract enforced: {contract_validation.intent}")
            final_answer = contract_validation.answer
            final_answer = normalize_answer_list_markers(final_answer)
            fretboard_payload = fretboard_payload_for_question(answer_request.question)
            if fretboard_payload is not None:
                visual_answer = visual_fretboard_curated_answer(answer_request.question)
                if visual_answer is not None and _answer_is_generic_specificity_fallback(final_answer):
                    final_answer = final_answer_quality_gate(visual_answer.answer, answer_request.question)
                    contract_validation = enforce_answer_contract(final_answer, visual_answer.intent)
                    final_answer = normalize_answer_list_markers(contract_validation.answer)
                sources = []
                warnings = []
            payload: AnswerResponse = {
                "answer": final_answer,
                "mode": answer_request.mode,
                "sources": sources,
                "warnings": warnings,
                "sections": build_sections(final_answer),
            }
            if fretboard_payload is not None:
                payload["fretboard"] = fretboard_payload
            _attach_tab_example_if_available(
                payload,
                answer_request.question,
                answer_intent_decision=answer_intent_decision,
            )
            if profile_personalization_requested:
                _personalize_answer_payload(payload, target_profile, target_revision)
            route_trace.retrieval = (
                "corpus_probe_reused"
                if corpus_probe_response is not None
                else "legacy_local_retrieval"
            )
            route_trace.evidence = f"{len(sources)}_source_cards"
            route_trace.synthesis = (
                "legacy_ai_provider" if ai_assisted else "deterministic_or_curated_legacy"
            )
            route_trace.verification = "answer_contract"
            route_trace.displayed_answer = "answer_with_optional_sources"
            if "live answer provider unavailable; deterministic guidance returned" in warnings:
                route_trace.fallback = "explicit_legacy_provider_warning"
            self._log_route_trace(route_trace)
            self._log_answer_attempt(
                request_payload,
                role=access.role,
                identity_email=access.identity_email,
                access_status="authorized",
                authorized=True,
                source_count=len(sources),
                warning_count=len(warnings),
                curated_guidance_count=curated_guidance_count,
                curated_guidance_status=curated_guidance_status,
            )
            return self._answer_success_response(
                start_response,
                payload,
                access,
                request_payload=request_payload,
                ai_assisted=ai_assisted,
            )

        else:
            return self._json_response(start_response, "404 Not Found", {"error": "not found"})

    def _search(
        self,
        query: str,
        *,
        limit: int = 5,
        source_system: str | None = None,
        forum_name: str | None = None,
    ) -> SearchResponse:
        try:
            response = self.search_index.search(
                query,
                limit=limit,
                source_system=source_system,
                forum_name=forum_name,
            )
        except TypeError:
            response = self.search_index.search(query)
        if isinstance(response, SearchResponse):
            return response
        if isinstance(response, dict):
            return SearchResponse(
                results=list(response.get("results") or []),
                warnings=list(response.get("warnings") or []),
            )
        return SearchResponse(results=list(response or []), warnings=[])

    def _search_for_answer(
        self,
        query: str,
        *,
        role: str,
        limit: int = 5,
        source_system: str | None = None,
        forum_name: str | None = None,
    ) -> SearchResponse:
        response, _plan = self._search_with_retrieval_plan(
            query,
            role=role,
            limit=limit,
            source_system=source_system,
            forum_name=forum_name,
        )
        return response

    def _search_for_api(
        self,
        query: str,
        *,
        role: str,
        limit: int = 5,
        source_system: str | None = None,
        forum_name: str | None = None,
    ) -> tuple[SearchResponse, dict[str, Any]]:
        search_response, plan = self._search_with_retrieval_plan(
            query,
            role=role,
            limit=limit,
            source_system=source_system,
            forum_name=forum_name,
        )

        debug_metadata: dict[str, Any] = {}
        if self._may_expose_retrieval_debug(role, plan.expose_debug_metadata):
            debug_metadata = {
                "requestedMode": self.retrieval_config.requested_mode.value,
                "selectedMode": plan.selected_mode.value,
                "sourceOrder": list(plan.source_order),
                "useSgf": plan.use_sgf,
                "usePrivate": plan.use_private,
                "privateSourcesEnabled": self.retrieval_config.private_sources_enabled,
                "privateSourcesAllowed": private_sources_allowed(role, self.retrieval_config),
                "role": role,
            }

        return search_response, debug_metadata

    def _search_with_retrieval_plan(
        self,
        query: str,
        *,
        role: str,
        limit: int = 5,
        source_system: str | None = None,
        forum_name: str | None = None,
    ) -> tuple[SearchResponse, Any]:
        plan = retrieval_plan_for_role(role, config=self.retrieval_config)
        warnings = list(plan.warnings)
        results_by_source: dict[str, list[dict[str, Any]]] = {}

        if plan.use_sgf:
            try:
                sgf_response = self._retrieval_dependencies.run(
                    lambda: self._search(
                        query,
                        limit=limit,
                        source_system=source_system,
                        forum_name=forum_name,
                    ),
                    timeout_seconds=self._retrieval_wall_timeout,
                )
            except RuntimeError:
                LOGGER.warning("sgf_retrieval_unavailable deterministic_fallback=true")
                warnings.append("source retrieval temporarily unavailable; using deterministic guidance")
            else:
                results_by_source["sgf_v2"] = sgf_response.results
                warnings.extend(sgf_response.warnings)

        if plan.use_private:
            if self.private_search_index is None:
                warnings.append("private retrieval requested but private search index is not configured")
            else:
                try:
                    private_response = self._retrieval_dependencies.run(
                        lambda: self._search_private(
                            query,
                            limit=limit,
                            source_system=source_system,
                            forum_name=forum_name,
                        ),
                        timeout_seconds=self._retrieval_wall_timeout,
                    )
                except RuntimeError:
                    LOGGER.warning("private_retrieval_unavailable deterministic_fallback=true")
                    warnings.append("private retrieval temporarily unavailable")
                else:
                    results_by_source["private_sources"] = private_response.results
                    warnings.extend(private_response.warnings)

        merged: list[dict[str, Any]] = []
        for source_name in plan.source_order:
            merged.extend(filter_sources_for_question(query, results_by_source.get(source_name, [])))
        merged = merged[:limit]

        return SearchResponse(results=merged, warnings=warnings), plan

    def _search_private(
        self,
        query: str,
        *,
        limit: int,
        source_system: str | None,
        forum_name: str | None,
    ) -> SearchResponse:
        try:
            response = self.private_search_index.search(
                query,
                limit=limit,
                source_system=source_system,
                forum_name=forum_name,
            )
        except TypeError:
            response = self.private_search_index.search(query)
        if isinstance(response, SearchResponse):
            return response
        if isinstance(response, dict):
            return SearchResponse(
                results=list(response.get("results") or []),
                warnings=list(response.get("warnings") or []),
            )
        return SearchResponse(results=list(response or []), warnings=[])

    def _curated_guidance_for_answer(
        self,
        question: str,
        *,
        role: str,
        answer_intent_decision: dict[str, Any],
        limit: int,
    ) -> tuple[list[dict[str, object]], str]:
        if not _curated_guidance_answer_flags_enabled():
            return [], "disabled"
        if not _curated_guidance_role_allowed(role):
            return [], "role_blocked"
        if not _curated_guidance_query_eligible(question, answer_intent_decision):
            return [], "ineligible"
        try:
            results = self.curated_guidance_search(question, top_k=min(max(limit, 1), 5))
        except Exception:
            LOGGER.exception("curated guidance retrieval failed")
            return [], "error"
        return list(results), "retrieved" if results else "empty"

    def _authorize_content_request(self, environ: dict[str, Any]) -> Any:
        return authorize_answer_request(
            environ,
            self.answer_auth_mode,
            self.auth_provider,
            self.cloudflare_verifier,
        )

    def _resolve_request_copedent(
        self,
        access_decision: Any,
        context: dict[str, Any] | None,
    ) -> tuple[E9CopedentProfile, int]:
        if not self.account_copedents_enabled:
            return resolve_copedent_context(context)
        account_access = account_access_for_decision(access_decision)
        repository = self.account_copedent_repository
        if account_access is None or repository is None:
            raise AccountConfigurationError("account copedent identity is unavailable")
        snapshot = (context or {}).get("profileSnapshot") or (context or {}).get("profile_snapshot")
        if snapshot is not None:
            if self.answer_auth_mode != "local_dev":
                raise AccountCopedentError(
                    "Import this custom copedent into the account before using it for personalized results."
                )
            if not account_access.allows("copedent.custom.use"):
                raise EntitlementRequiredError(
                    "Session Pass is required to use a custom copedent.",
                    "copedent.custom.use",
                )
            return resolve_copedent_context(context)
        profile_id = str(
            (context or {}).get("profileId")
            or (context or {}).get("profile_id")
            or repository.effective_active_profile(account_access)
        ).strip()
        if profile_id in {DEFAULT_COPEDENT_ID, "day-e9-basic"}:
            return resolve_copedent_context({"profileId": profile_id})
        stored = repository.owned_profile(account_access, profile_id)
        profile = custom_e9_profile_from_payload(stored)
        return profile, int(stored.get("revision") or profile.revision)

    def _account_snapshot_for_profile(
        self,
        access_decision: Any,
        profile: E9CopedentProfile,
    ) -> dict[str, object] | None:
        if not self.account_copedents_enabled or not profile.id.startswith("saved:"):
            return None
        account_access = account_access_for_decision(access_decision)
        if account_access is None or self.account_copedent_repository is None:
            return None
        return self.account_copedent_repository.owned_profile(account_access, profile.id)

    @staticmethod
    def _entitlement_response(start_response: Any, error: EntitlementRequiredError) -> list[bytes]:
        return RetrievalApi._json_response(
            start_response,
            "403 Forbidden",
            {
                "error": str(error),
                "code": "entitlement_required",
                "requiredEntitlement": error.required_entitlement,
                "upgradePath": "/ui/steel-guitar-rag-mock.html#backstage-pass",
            },
            extra_headers=(("Cache-Control", "no-store"),),
        )

    @staticmethod
    def _may_expose_retrieval_debug(role: str, enabled: bool) -> bool:
        return enabled and role in {"admin", "dev", "developer"}

    @staticmethod
    def _read_json_body(
        environ: dict[str, Any],
        *,
        max_bytes: int = MAX_JSON_BODY_BYTES,
    ) -> dict[str, Any]:
        try:
            content_length = int(environ.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError) as exc:
            raise JsonRequestError("request has an invalid content length") from exc
        if content_length <= 0:
            return {}
        if content_length > max_bytes:
            raise JsonRequestTooLargeError("request body exceeds the 1 MiB JSON limit")

        raw_body = environ["wsgi.input"].read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise JsonRequestError("request body is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise JsonRequestError("request body must be a JSON object")
        return payload

    @staticmethod
    def _read_bounded_json_body(environ: dict[str, Any], max_bytes: int) -> dict[str, Any]:
        try:
            content_length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError as exc:
            raise MelodyImportError("The import request has an invalid content length.") from exc
        if content_length <= 0:
            raise MelodyImportError("The import request is empty.")
        if content_length > max_bytes:
            raise MelodyImportTooLargeError("The import request is larger than the Melody Studio limit.")
        raw_body = environ["wsgi.input"].read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise MelodyImportError("The import request is not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise MelodyImportError("The import request must be a JSON object.")
        return payload

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None

    def _answer_success_response(
        self,
        start_response: Any,
        payload: AnswerResponse,
        access_decision: Any,
        *,
        request_payload: dict[str, Any] | None = None,
        ai_assisted: bool = False,
    ) -> list[bytes]:
        """Record one successful Ask response without making usage a response dependency."""

        if (
            self.answer_auth_mode != "local_dev"
            and self.account_usage_enabled
            and self.account_usage_repository is not None
        ):
            account_access = account_access_for_decision(access_decision)
            if account_access is not None:
                try:
                    self.account_usage_repository.record_success(
                        account_access.identity,
                        is_followup=bool((request_payload or {}).get("isFollowup")),
                        ai_assisted=ai_assisted,
                    )
                except Exception:
                    LOGGER.exception("account usage write failed")
        return self._json_response(start_response, "200 OK", payload)

    def _log_answer_attempt(
        self,
        request_payload: dict[str, Any],
        *,
        role: str,
        identity_email: str = "",
        access_status: str,
        authorized: bool,
        source_count: int | None = None,
        warning_count: int = 0,
        error_status: str = "",
        curated_guidance_count: int | None = None,
        curated_guidance_status: str | None = None,
    ) -> None:
        question = str(request_payload.get("question") or "")
        mode = str(request_payload.get("mode") or "ask")
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "identityKey": self._identity_key(identity_email),
            "accessStatus": access_status,
            "authorized": authorized,
            "blocked": not authorized or bool(error_status),
            "questionLength": len(question),
            "mode": mode,
            "sourceCount": source_count,
            "warningCount": warning_count,
            "errorStatus": error_status,
        }
        if curated_guidance_status is not None:
            event["curatedGuidanceStatus"] = curated_guidance_status
            event["curatedGuidanceCount"] = int(curated_guidance_count or 0)
        self.answer_request_log.append(event)
        LOGGER.info("answer request event: %s", json.dumps(event, sort_keys=True))

    @staticmethod
    def _log_route_trace(trace: AnswerRouteTrace) -> None:
        LOGGER.info("answer route event: %s", json.dumps(trace.event(), sort_keys=True))

    @staticmethod
    def _identity_key(identity_email: str = "") -> str:
        normalized = str(identity_email or "").strip().lower()
        if not normalized:
            return ""
        digest = hashlib.sha256(f"steel-rag-access:{normalized}".encode("utf-8")).hexdigest()
        return f"email_sha256:{digest}"

    def _version_payload(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "git_sha": self.git_sha,
            "server_started_at": self.server_started_at,
        }

    @staticmethod
    def _csp_report_summary(payload: dict[str, Any]) -> dict[str, str]:
        report = payload.get("csp-report") or payload.get("body") or payload
        if not isinstance(report, dict):
            return {"directive": "unknown", "blockedHost": ""}
        blocked_uri = str(report.get("blocked-uri") or report.get("blockedURL") or "")
        try:
            blocked_host = urlsplit(blocked_uri).hostname or ""
        except ValueError:
            blocked_host = ""
        return {
            "directive": str(
                report.get("effective-directive")
                or report.get("violated-directive")
                or report.get("effectiveDirective")
                or "unknown"
            )[:160],
            "blockedHost": blocked_host[:253],
        }

    @staticmethod
    def _git_value(*args: str) -> str:
        try:
            result = subprocess.run(
                ("git", *args),
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            )
        except Exception:
            return "unknown"
        return result.stdout.strip() or "unknown"

    @staticmethod
    def _json_response(
        start_response: Any,
        status: str,
        payload: dict[str, Any],
        *,
        extra_headers: tuple[tuple[str, str], ...] = (),
    ) -> list[bytes]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        start_response(
            status,
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
                *SECURITY_RESPONSE_HEADERS,
                *extra_headers,
            ],
        )
        return [body]

    @staticmethod
    def _empty_response(start_response: Any, status: str) -> list[bytes]:
        start_response(
            status,
            [
                ("Content-Length", "0"),
                *SECURITY_RESPONSE_HEADERS,
            ],
        )
        return []


def create_app(
    search_index: Any | None = None,
    answer_provider: AnswerProvider | None = None,
    *,
    answer_auth_mode: AnswerAuthMode | None = None,
    auth_provider: AuthProvider | None = None,
    cloudflare_verifier: Any = None,
    answer_rate_limiter: InMemoryAnswerRateLimiter | None = None,
    private_search_index: Any | None = None,
    retrieval_config: RetrievalModeConfig | None = None,
    curated_guidance_search: Callable[..., list[dict[str, object]]] | None = None,
    melody_exercise_enabled: bool | None = None,
    melody_import_enabled: bool | None = None,
    song_practice_enabled: bool | None = None,
    account_copedents_enabled: bool | None = None,
    account_copedent_repository: AccountCopedentRepository | None = None,
    account_usage_enabled: bool | None = None,
    account_usage_repository: AccountUsageRepository | None = None,
    amazing_tablature_policy: RuntimeRankerPolicy | None = None,
    canonical_frontier_enabled: bool | None = None,
    canonical_frontier_client: Any | None = None,
) -> RetrievalApi:
    retrieval_config = retrieval_config or configured_retrieval_mode_config()
    private_requested = retrieval_config.requested_mode in {
        RetrievalMode.PRIVATE_ONLY,
        RetrievalMode.HYBRID_PRIVATE_FIRST,
        RetrievalMode.HYBRID_SGF_FIRST,
    }
    if private_search_index is None and retrieval_config.private_sources_enabled and private_requested:
        private_search_index = PrivateSourceSearchIndex.from_chroma(
            chroma_path=retrieval_config.private_chroma_path,
            collection_name=retrieval_config.private_collection,
        )
    return RetrievalApi(
        search_index or ChromaSearchIndex.from_chroma(),
        answer_provider=answer_provider,
        answer_auth_mode=answer_auth_mode,
        auth_provider=auth_provider,
        cloudflare_verifier=cloudflare_verifier,
        answer_rate_limiter=answer_rate_limiter,
        private_search_index=private_search_index,
        retrieval_config=retrieval_config,
        curated_guidance_search=curated_guidance_search,
        melody_exercise_enabled=melody_exercise_enabled,
        melody_import_enabled=melody_import_enabled,
        song_practice_enabled=song_practice_enabled,
        account_copedents_enabled=account_copedents_enabled,
        account_copedent_repository=account_copedent_repository,
        account_usage_enabled=account_usage_enabled,
        account_usage_repository=account_usage_repository,
        amazing_tablature_policy=amazing_tablature_policy,
        canonical_frontier_enabled=canonical_frontier_enabled,
        canonical_frontier_client=canonical_frontier_client,
    )


def build_arg_parser() -> Any:
    """Compatibility wrapper for callers that import the parser from this module."""
    from steel_guitar_rag.api_cli import build_arg_parser as cli_build_arg_parser

    return cli_build_arg_parser()


def main(argv: list[str] | None = None) -> int:
    from steel_guitar_rag.api_cli import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
