"""Tiny local retrieval API for Steel Guitar RAG."""

from __future__ import annotations

import argparse
import hashlib
import logging
import json
import subprocess
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from pocketsteel.answering import (
    AnswerProvider,
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
from pocketsteel.access_control import (
    AnswerAuthMode,
    AuthProvider,
    authorize_answer_request,
    authorize_local_dev_request,
    configured_answer_auth_mode,
    configured_auth_provider,
    normalize_answer_auth_mode,
    normalize_auth_provider,
)
from pocketsteel.answer_usage import InMemoryAnswerRateLimiter, answer_rate_limit_key
from pocketsteel.api_contract import AnswerResponse
from pocketsteel.answer_contracts import enforce_answer_contract, infer_contract_intent
from pocketsteel.answer_intent_classifier import classify_answer_request
from pocketsteel.chroma_search import (
    CHROMA_COLLECTION_ENV,
    CHROMA_PATH_ENV,
    DEFAULT_CHROMA_PATH,
    DEFAULT_COLLECTION_NAME,
    ChromaSearchIndex,
    SearchResponse,
)
from pocketsteel.curated_answers import (
    CURATED_FACT_WEAK_WARNING,
    WEAK_RETRIEVAL_WARNING,
    generic_sgf_quarantine_fallback_answer,
    intent_mode_curated_answer,
    lookup_curated_answer,
    retrieval_looks_weak_for_curated,
    sgf_answer_body_needs_quarantine,
    sgf_quarantine_teacher_answer,
    unsupported_chord_position_curated_answer,
    visual_fretboard_curated_answer,
)
from pocketsteel.curated_source_registry import slide_bar_vendor_source_cards
from pocketsteel.fretboard_examples import fretboard_payload_for_question
from pocketsteel.rag_guardrails import sanitize_retrieved_sources
from pocketsteel.rag_guardrails import is_injection_like
from pocketsteel.private_source_search import PrivateSourceSearchIndex
from pocketsteel.retrieval_modes import (
    ENABLE_PRIVATE_SOURCES_ENV,
    PRIVATE_CHROMA_PATH_ENV,
    PRIVATE_COLLECTION_ENV,
    RETRIEVAL_DEBUG_ENV,
    RETRIEVAL_MODE_ENV,
    RetrievalMode,
    RetrievalModeConfig,
    configured_retrieval_mode_config,
    normalize_retrieval_mode,
    private_sources_allowed,
    retrieval_plan_for_role,
)

LOGGER = logging.getLogger(__name__)


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
            "That request is outside Steel Guitar RAG’s scope, and it may be unsafe or too large to display usefully. "
            "Try asking about E9 positions, grips, pedals/levers, tone, gear, blocking, bar movement, practice plans, "
            "or steel-guitar forum wisdom."
        )
    return (
        "That request is outside Steel Guitar RAG’s scope. "
        "Try asking about E9 positions, grips, pedals/levers, tone, gear, blocking, bar movement, practice plans, "
        "or steel-guitar forum wisdom."
    )


def _should_gate_answer_intent(decision: dict[str, Any]) -> bool:
    if decision.get("domain") == "unsafe_or_impossible":
        return True
    return decision.get("domain") == "off_domain" and decision.get("intent") == "small_talk"


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
    ) -> None:
        self.search_index = search_index
        self.private_search_index = private_search_index
        self.answer_provider = configured_answer_provider(answer_provider)
        self.answer_auth_mode = normalize_answer_auth_mode(answer_auth_mode or configured_answer_auth_mode())
        self.auth_provider = normalize_auth_provider(auth_provider or configured_auth_provider())
        self.cloudflare_verifier = cloudflare_verifier
        self.answer_rate_limiter = answer_rate_limiter or InMemoryAnswerRateLimiter.from_env()
        self.answer_request_log: list[dict[str, Any]] = []
        self.retrieval_config = retrieval_config or configured_retrieval_mode_config()

    def __call__(self, environ: dict[str, Any], start_response: Any) -> Iterable[bytes]:
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "")

        if path == "/api/version":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
            return self._json_response(start_response, "200 OK", self._version_payload())

        if path == "/api/search":
            if method != "GET":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})

            params = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
            query = params.get("q", [""])[0]
            search_response, debug_metadata = self._search_for_api(query, environ)
            payload = {
                "query": query,
                "results": search_response.results,
                "warnings": search_response.warnings,
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
            if params.get("debug") == ["auth"]:
                payload["accessDebug"] = {
                    "authProvider": auth_provider,
                    "answerAuthMode": self.answer_auth_mode,
                    **access.diagnostics,
                }
            return self._json_response(start_response, "200 OK", payload)

        if path == "/api/answer":
            if method != "POST":
                return self._json_response(start_response, "405 Method Not Allowed", {"error": "method not allowed"})

            request_payload = self._read_json_body(environ)
            access = authorize_answer_request(
                environ,
                self.answer_auth_mode,
                self.auth_provider,
                self.cloudflare_verifier,
            )
            if not access.allowed:
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="blocked",
                    authorized=False,
                    error_status=access.status,
                )
                return self._json_response(start_response, access.status, {"error": access.error})

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

            answer_intent_decision = classify_answer_request(answer_request.question, answer_request.mode)

            deterministic_chord_answer = visual_fretboard_curated_answer(answer_request.question)
            if deterministic_chord_answer is None:
                deterministic_chord_answer = unsupported_chord_position_curated_answer(answer_request.question)
            if (
                deterministic_chord_answer is not None
                and answer_intent_decision.get("domain") != "unsafe_or_impossible"
            ):
                final_answer = final_answer_quality_gate(deterministic_chord_answer.answer, answer_request.question)
                contract_validation = enforce_answer_contract(final_answer, deterministic_chord_answer.intent)
                final_answer = contract_validation.answer
                final_answer = normalize_answer_list_markers(final_answer)
                fretboard_payload = fretboard_payload_for_question(answer_request.question)
                payload: AnswerResponse = {
                    "answer": final_answer,
                    "mode": answer_request.mode,
                    "sources": [],
                    "warnings": [],
                    "sections": build_sections(final_answer),
                }
                if fretboard_payload is not None:
                    payload["fretboard"] = fretboard_payload
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    source_count=0,
                    warning_count=0,
                )
                return self._json_response(start_response, "200 OK", payload)

            if _should_gate_answer_intent(answer_intent_decision):
                final_answer = _answer_intent_guardrail_answer(answer_intent_decision["domain"])
                final_answer = normalize_answer_list_markers(final_answer)
                payload: AnswerResponse = {
                    "answer": final_answer,
                    "mode": answer_request.mode,
                    "sources": [],
                    "warnings": [],
                    "sections": build_sections(final_answer),
                }
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    source_count=0,
                    warning_count=0,
                )
                return self._json_response(start_response, "200 OK", payload)

            practical_intent_answer = intent_mode_curated_answer(answer_request.question)
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
                }
                self._log_answer_attempt(
                    request_payload,
                    role=access.role,
                    identity_email=access.identity_email,
                    access_status="authorized",
                    authorized=True,
                    source_count=0,
                    warning_count=0,
                )
                return self._json_response(start_response, "200 OK", payload)

            source_system = self._optional_string(request_payload.get("sourceSystem") or request_payload.get("source_system"))
            forum_name = self._optional_string(request_payload.get("forumName") or request_payload.get("forum_name"))
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
                    if _curated_answer_should_be_source_free(curated_answer.intent):
                        sources = []
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
                    answer = self.answer_provider.answer(answer_request, strong_sources)
                    if answer_is_no_source(answer):
                        sources = []
                        warnings.append("no strong source match")
                    else:
                        sources = concise_source_cards(strong_sources)
            answer = apply_private_profile_wording(answer, answer_request.question, strong_sources)
            raw_answer_needed_quarantine = sgf_answer_body_needs_quarantine(answer)
            final_answer = final_answer_quality_gate(answer, answer_request.question)
            if raw_answer_needed_quarantine or sgf_answer_body_needs_quarantine(final_answer):
                quarantine_answer = sgf_quarantine_teacher_answer(
                    answer_request.question
                ) or generic_sgf_quarantine_fallback_answer(answer_request.question)
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
                sources = []
            payload: AnswerResponse = {
                "answer": final_answer,
                "mode": answer_request.mode,
                "sources": sources,
                "warnings": warnings,
                "sections": build_sections(final_answer),
            }
            if fretboard_payload is not None:
                payload["fretboard"] = fretboard_payload
            self._log_answer_attempt(
                request_payload,
                role=access.role,
                identity_email=access.identity_email,
                access_status="authorized",
                authorized=True,
                source_count=len(sources),
                warning_count=len(warnings),
            )
            return self._json_response(start_response, "200 OK", payload)

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
        environ: dict[str, Any],
        *,
        limit: int = 5,
        source_system: str | None = None,
        forum_name: str | None = None,
    ) -> tuple[SearchResponse, dict[str, Any]]:
        role = self._search_role(environ)
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
            sgf_response = self._search(
                query,
                limit=limit,
                source_system=source_system,
                forum_name=forum_name,
            )
            results_by_source["sgf_v2"] = sgf_response.results
            warnings.extend(sgf_response.warnings)

        if plan.use_private:
            if self.private_search_index is None:
                warnings.append("private retrieval requested but private search index is not configured")
            else:
                private_response = self._search_private(
                    query,
                    limit=limit,
                    source_system=source_system,
                    forum_name=forum_name,
                )
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

    def _search_role(self, environ: dict[str, Any]) -> str:
        access = authorize_local_dev_request(
            environ,
            self.answer_auth_mode,
            self.auth_provider,
            self.cloudflare_verifier,
        )
        return access.role if access.allowed else "anonymous"

    @staticmethod
    def _may_expose_retrieval_debug(role: str, enabled: bool) -> bool:
        return enabled and role in {"admin", "dev", "developer"}

    @staticmethod
    def _read_json_body(environ: dict[str, Any]) -> dict[str, Any]:
        try:
            content_length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            content_length = 0
        if content_length <= 0:
            return {}

        raw_body = environ["wsgi.input"].read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None

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
        self.answer_request_log.append(event)
        LOGGER.info("answer request event: %s", json.dumps(event, sort_keys=True))

    @staticmethod
    def _identity_key(identity_email: str = "") -> str:
        normalized = str(identity_email or "").strip().lower()
        if not normalized:
            return ""
        digest = hashlib.sha256(f"steel-rag-access:{normalized}".encode("utf-8")).hexdigest()
        return f"email_sha256:{digest}"

    def _version_payload(self) -> dict[str, Any]:
        return {
            "git_sha": self._git_value("rev-parse", "--short", "HEAD"),
            "git_branch": self._git_value("branch", "--show-current"),
            "server_started_at": datetime.now(timezone.utc).isoformat(),
            "python_module": "pocketsteel.api",
            "retrieval_mode": self.retrieval_config.requested_mode.value,
            "auth_provider": self.auth_provider,
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
    def _json_response(start_response: Any, status: str, payload: dict[str, Any]) -> list[bytes]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        start_response(
            status,
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]


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
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Host for the local API server.")
    parser.add_argument("--port", type=int, default=8765, help="Port for the local API server.")
    parser.add_argument(
        "--chroma",
        default=None,
        help=f"Existing Chroma index path. Defaults to ${CHROMA_PATH_ENV} or {DEFAULT_CHROMA_PATH}.",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help=f"Existing Chroma collection name. Defaults to ${CHROMA_COLLECTION_ENV} or {DEFAULT_COLLECTION_NAME}.",
    )
    parser.add_argument("--model", default=None, help="Local embedding model for query embedding.")
    parser.add_argument(
        "--answer-auth-mode",
        choices=["production", "local-dev", "local_dev"],
        default=None,
        help="Auth scaffold mode for /api/answer. Defaults to STEEL_RAG_ANSWER_AUTH_MODE or production.",
    )
    parser.add_argument(
        "--auth-provider",
        choices=["scaffold", "cloudflare-access", "cloudflare_access"],
        default=None,
        help="Auth provider for production /api/answer requests. Defaults to STEEL_RAG_AUTH_PROVIDER or scaffold.",
    )
    parser.add_argument(
        "--retrieval-mode",
        default=None,
        help=f"Search retrieval mode. Defaults to ${RETRIEVAL_MODE_ENV} or sgf_only.",
    )
    parser.add_argument(
        "--enable-private-sources",
        action="store_true",
        help=f"Allow /api/search private-source modes. Defaults to ${ENABLE_PRIVATE_SOURCES_ENV}=false.",
    )
    parser.add_argument(
        "--private-chroma",
        default=None,
        help=f"Private Chroma path. Defaults to ${PRIVATE_CHROMA_PATH_ENV} or corpus-private/vector-stores/chroma.",
    )
    parser.add_argument(
        "--private-collection",
        default=None,
        help=f"Private Chroma collection. Defaults to ${PRIVATE_COLLECTION_ENV} or steel_guitar_private_sources_v1.",
    )
    parser.add_argument(
        "--retrieval-debug",
        action="store_true",
        help=f"Expose /api/search retrieval metadata to admin/dev roles. Defaults to ${RETRIEVAL_DEBUG_ENV}=false.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    env_config = configured_retrieval_mode_config()
    retrieval_config = RetrievalModeConfig(
        requested_mode=env_config.requested_mode if args.retrieval_mode is None else normalize_retrieval_mode(args.retrieval_mode),
        private_sources_enabled=args.enable_private_sources or env_config.private_sources_enabled,
        sgf_chroma_path=env_config.sgf_chroma_path,
        sgf_collection=env_config.sgf_collection,
        private_chroma_path=env_config.private_chroma_path if args.private_chroma is None else Path(args.private_chroma),
        private_collection=args.private_collection or env_config.private_collection,
        expose_debug_metadata=args.retrieval_debug or env_config.expose_debug_metadata,
    )
    app = create_app(
        ChromaSearchIndex.from_chroma(
            chroma_path=args.chroma,
            collection_name=args.collection,
            model=args.model,
        ),
        answer_auth_mode=args.answer_auth_mode,
        auth_provider=args.auth_provider,
        retrieval_config=retrieval_config,
    )
    with make_server(args.host, args.port, app) as server:
        print(f"Serving local retrieval API at http://{args.host}:{args.port}")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
