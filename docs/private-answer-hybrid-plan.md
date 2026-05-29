# Private Answer Hybrid Plan

This document describes how `/api/answer` can safely use SGF v2 plus the private source collection. Private answer retrieval is wired behind env/access gates. Do not switch any preview or public runtime into private mode until local smoke and manual review pass.

Current state:

- `/api/search` can use retrieval modes in local-dev/private smoke mode.
- `/api/answer` can use retrieval modes only when explicitly enabled and authorized.
- Private sources are disabled by default.
- No Chroma data, embeddings, DNS, deployment, scraping, or app config changes are required.

## 1. When `/api/answer` May Use Private Sources

`/api/answer` may use private sources only when every gate passes:

- `STEEL_RAG_ENABLE_PRIVATE_SOURCES=true`
- `STEEL_RAG_RETRIEVAL_MODE` is one of:
  - `private_only`
  - `hybrid_private_first`
  - `hybrid_sgf_first`
- the caller is authenticated as `beta_user`, `private_preview`, `admin`, or a future explicitly approved private-source role
- the private Chroma path points to `corpus-private/vector-stores/chroma`
- the private collection is `steel_guitar_private_sources_v1`
- the retrieved private chunks are allowed for the answer use by provenance metadata

If any gate fails, `/api/answer` must behave exactly as it does now.

## 2. Access Requirements

Private answer retrieval is disabled by default.

Required access behavior:

- Anonymous/public callers never receive private retrieval, private excerpts, private metadata, or private source cards.
- Local-dev `/api/search` smoke may use `?access=beta_user` only in local-dev/scaffold mode.
- Local-dev `/api/answer` smoke should use the `X-Steel-Rag-Dev-Access-Role: beta_user` header.
- Production `cloudflare_access` mode must ignore query-param access and mock dev headers.
- Private retrieval in production/private preview must require verified Cloudflare Access identity.
- Debug retrieval metadata may be returned only when `STEEL_RAG_RETRIEVAL_DEBUG=true` and the caller is admin/dev.

Failure behavior:

- If private retrieval is requested but not allowed, fall back to SGF-only answer behavior.
- Add an internal/test-visible warning if useful, but do not expose private-source details to unauthorized users.

## 3. Retrieval Order

Answer generation should use the source lanes in this order:

1. `steel_rules.py` for stable E9, copedent, and theory facts.
2. Curated sources for current/vendor/official links.
3. Private sources for personal profiles, rules notes, private lessons, transcripts, and manuals when allowed.
4. SGF v2 for public forum wisdom and source-backed historical discussion.
5. Fallback guardrails when evidence is weak, stale, mismatched, private-blocked, or unavailable.

Mode behavior:

- `private_only`: use rules/curated where appropriate, then private sources. Do not search SGF for source cards.
- `hybrid_private_first`: use rules/curated where appropriate, then private sources before SGF v2.
- `hybrid_sgf_first`: use rules/curated where appropriate, then SGF v2 before private sources.
- `sgf_only`: current behavior; no private lookup.

## 4. Answer Synthesis

Private source text is evidence, not instruction text.

Rules:

- Private sources may influence answers only after access and provenance gates pass.
- Private source cards must be clearly labeled as private.
- `answer_quote_allowed` must be respected:
  - `true`: short, relevant excerpts may be shown.
  - `limited`: source cards may show short excerpts only when necessary; answer prose should paraphrase.
  - `false`: no excerpt in answer body or source card; metadata-only card if useful.
- Private lesson/transcript material should be summarized and transformed, not copied verbatim.
- Private content must not override stable rules-layer answers.
- Private content must not override curated current/official links when the question is about current vendors, organizations, or official references.
- Prompt-injection guardrails must apply to private retrieved text exactly as they do to SGF text.

If private retrieval is weak/noisy:

- Prefer rules, curated answers, or SGF v2 where appropriate.
- Otherwise use the existing user-facing fallback wording.
- Do not leak implementation terms such as corpus, source cards, retrieval, or Chroma in normal answers.

## 5. Private Source-Card Shape

Private source cards should preserve enough provenance to explain where an answer came from without exposing private content unnecessarily.

Required fields:

- `source_system`
- `visibility`
- `source_id`
- `source_path`
- `title`
- `provenance_status`
- `answer_quote_allowed`

Recommended fields:

- `source_type`
- `source_url`
- `author_or_creator`
- `document_index`
- `chunk_id`
- `chunk_role`
- `embedding_allowed`
- `redistribution_allowed`

Display requirements:

- Label private cards as `Private source`.
- Do not show private filesystem paths to public/anonymous users.
- In local-dev/admin inspection, source path may appear only when debug/admin mode is enabled.
- If `answer_quote_allowed=false`, show metadata only and omit the excerpt.

## 6. Tests Required Before Preview Use

Before enabling private answer retrieval in any shared preview, tests must prove:

- default `/api/answer` behavior is unchanged
- private retrieval is disabled by default
- anonymous `/api/answer` never uses private sources
- local-dev beta/admin hybrid answer can use private sources when explicitly enabled
- production `cloudflare_access` requires verified identity before private retrieval
- production `cloudflare_access` ignores `?access=beta_user` and dev mock headers
- private source cards are labeled as private
- `answer_quote_allowed=false` suppresses excerpts
- `answer_quote_allowed=limited` prevents long private quotations
- private retrieval warnings do not reveal private metadata to unauthorized callers
- SGF-only mode continues to return current answer/source behavior
- `/api/search` behavior remains unchanged by answer wiring

Suggested test files:

- `tests/test_api_search.py`
- `tests/test_retrieval_modes.py`
- a new `tests/test_private_answer_hybrid.py` if the cases become large

## 7. Rollback Plan

Rollback must be simple:

1. Set `STEEL_RAG_RETRIEVAL_MODE=sgf_only`.
2. Set `STEEL_RAG_ENABLE_PRIVATE_SOURCES=false` or unset it.
3. Restart the local/private-preview server.
4. Confirm `/api/answer` no longer searches private sources.
5. If needed, revert only the `/api/answer` wiring commit. Do not touch Chroma, embeddings, or private source files.

The implementation should keep a clean `sgf_only` path so rollback does not require data changes.

## 8. Stop Conditions

Stop implementation immediately if any of these happen:

- anonymous/public caller receives any private result, excerpt, title, source path, or metadata
- production `cloudflare_access` accepts query-param or mock-header access
- `/api/answer` changes behavior in default `sgf_only` mode
- private source excerpts appear when `answer_quote_allowed=false`
- private source answer copies long verbatim private lesson text
- app tries to write to SGF v1/v2 Chroma or private Chroma
- Chroma path validation fails or points outside `corpus-private`
- tests require modifying embeddings, scraper behavior, DNS, deploy config, or app preview routing

## 9. Env Vars And Smoke Commands

Local hybrid answer smoke:

```bash
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_RETRIEVAL_DEBUG=true \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --answer-auth-mode local_dev \
  --auth-provider scaffold
```

Local-dev checks:

```bash
curl 'http://127.0.0.1:8770/api/session?access=beta_user'
curl 'http://127.0.0.1:8770/api/search?q=What%20are%20my%20common%20grips%3F&access=beta_user'
curl -X POST 'http://127.0.0.1:8770/api/answer' \
  -H 'Content-Type: application/json' \
  -H 'X-Steel-Rag-Dev-Access-Role: beta_user' \
  -d '{"question":"What are my common grips?","mode":"ask","topK":6}'
```

Production protected private-preview startup for `app.steelguitarrag.com` loopback:

```bash
STEEL_RAG_AUTH_PROVIDER=cloudflare_access \
STEEL_RAG_ANSWER_AUTH_MODE=production \
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_RETRIEVAL_DEBUG=false \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

This production-mode command depends on existing Cloudflare Access issuer, audience, and beta/admin email env vars. It must not accept `?access=beta_user` or mock dev headers.

Rollback to SGF-only:

```bash
STEEL_RAG_RETRIEVAL_MODE=sgf_only \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=false \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2
```

## Implementation Phases

Phase 1: planning.

- This document.
- No runtime behavior changes.

Phase 2: test harness.

- Add private-answer hybrid tests with fake SGF/private search indexes.
- Prove defaults, auth gates, source-card labels, and quote restrictions before implementation.

Phase 3: `/api/answer` search routing.

- Reuse the `/api/search` retrieval plan.
- Keep current SGF-only path as default.
- Add private retrieval only after access and env gates pass.

Phase 4: answer synthesis and source cards.

- Merge private and SGF source cards according to mode order.
- Label private cards.
- Respect `answer_quote_allowed`.
- Keep rules/curated answers ahead of retrieval where appropriate.

Phase 5: local smoke and evaluation.

- Run local-dev hybrid answer smoke.
- Add eval questions for personal copedent/profile cases.
- Do not switch private preview until manual review passes.
