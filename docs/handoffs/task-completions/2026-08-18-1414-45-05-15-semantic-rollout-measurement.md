# Semantic rollout measurement handoff

## Task summary

- Requested outcome: continue moving the search experience from case-specific routing to the agreed semantic authority architecture and prove its real operating cost and enabled behavior.
- Implemented: provider usage/latency capture, route-correlated server telemetry, resilient full-bank reporting, authenticated activation signals, and an end-to-end `/api/answer` regression through the real Responses adapter.
- Preserved: the public answer contract, deterministic exact-music authority, verified frontier authority, minimal public health/version responses, default-off rollout, and current-router rollback.
- Not activated: no secret, paid live-bank call, environment change, restart, deployment, auth, corpus, embedding, index, or DNS action occurred.

## Lane and task mode

- Lanes: `05 Backend / RAG Integration`, `15 QA / Answer Eval`, `18 Product / Architecture`, `01 Repo Steward`.
- Mode: YELLOW local implementation and verification. Paid API use and protected activation remain separately gated.

## Changes delivered

- Each successful OpenAI semantic planner result carries internal `SemanticAnswerMetrics` metadata:
  - resolved model;
  - provider latency;
  - input and cached-input tokens;
  - output and reasoning-output tokens;
  - total tokens.
- Metrics never enter the provider Structured Outputs schema or public `/api/answer` payload.
- The API logs metrics with the route trace ID but not the question or answer.
- The live evaluator now reports request/completion counts, model identities, token totals, and total/median/p95 wall latency.
- An expected provider/contract failure becomes a failed row and does not abort the rest of the 32-case bank.
- Authenticated `/api/session` reports `features.semanticAnswer` and `features.canonicalFrontier` when active; `/api/version` and health responses remain minimal.
- A keyless end-to-end test exercises the actual `OpenAIResponsesSemanticAnswerer` through `/api/answer` for the chord/harmony conceptual-teaching class, proving one provider request, no retrieval, no sources, and no fabricated fretboard.

## Runtime audit

- Current shell: `OPENAI_API_KEY` absent and `STEEL_RAG_FRONTIER_TOKEN` absent.
- No `openai-platform-api-key` tool is available.
- Site adapter on `127.0.0.1:8770` is healthy but reports older commit `476a51e`; it was not restarted.
- Canonical frontier on `127.0.0.1:8771` is live and ready; its readiness payload reports provider credentials and structured startup checks ready.
- Existing service credentials were not read, copied, borrowed, or logged.
- The 32-call live planner bank was not run because no approved planner credential/cost authorization is available in this shell.

## Files changed

- `steel_guitar_rag/semantic_answer_orchestrator.py`
- `steel_guitar_rag/api.py`
- `scripts/run_semantic_answer_eval.py`
- `tests/test_semantic_answer_orchestrator.py`
- `tests/test_semantic_answer_eval.py`
- `tests/test_api_search.py`
- `docs/semantic-answer-orchestrator.md`
- `docs/handoffs/task-completions/2026-08-18-1414-45-05-15-semantic-rollout-measurement.md`

Deleted files: none.

## Tests and checks

- Focused semantic/frontier/classifier/session/eval suite: **169 passed**.
- Full repository suite: **1,757 passed** in **86.62 seconds**.
- Ruff on changed Python implementation/test/eval files: **PASS**.
- Scoped mypy for semantic orchestrator and eval runner: **PASS**.
- `git diff --check`: **PASS**.
- Live OpenAI bank: **NOT RUN** for the authorization/credential reason above.
- Protected browser smoke: **NOT RUN** because the deployed app is an older commit and no activation/restart was authorized.

## Risks and remaining gate

- Correctness, latency, and token usage are now measurable but still need real values from the approved `gpt-5.6-terra` 32-case run.
- Cost is not hard-coded because pricing can change. Calculate it from the captured usage against the approved environment's current pricing.
- Provider failures are fully reported, but no retry was added to the semantic planner. The app's documented rollback/fail-closed behavior remains authoritative.
- The feature remains default off; the requested experience is not complete until the live bank passes and protected enabled-path smoke succeeds.

## Human decision needed

Yes:

1. Authorize use of an approved server-side planner key for the 32-call bank.
2. After reviewing route accuracy, teaching quality, tokens, latency, and cost, authorize a protected release/flag activation if acceptable.
3. Verify authenticated session flags, exact deterministic, conceptual teaching, source-backed, hybrid, outage, and contextual follow-up behavior in protected preview.

## Safe-to-stage exact file list

- `steel_guitar_rag/semantic_answer_orchestrator.py`
- `steel_guitar_rag/api.py`
- `scripts/run_semantic_answer_eval.py`
- `tests/test_semantic_answer_orchestrator.py`
- `tests/test_semantic_answer_eval.py`
- `tests/test_api_search.py`
- `docs/semantic-answer-orchestrator.md`
- `docs/handoffs/task-completions/2026-08-18-1414-45-05-15-semantic-rollout-measurement.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (coordination artifact; intentionally uncommitted).
- The pre-existing unrelated untracked handoffs dated 2026-08-04, 2026-08-12, and 2026-08-13.
- `output/` and generated reports.
- Environment files, credentials, logs, corpus/private data, indexes, embeddings, or deployment artifacts.

## Recommended next lane

- Lane 15: run the live bank after explicit credential/cost authorization and review every failed row plus route-level/token/latency summaries.
- Lane 12 only after a pass and explicit deployment authority: build the exact release, enable semantic and canonical frontier together, restart safely, and run protected smoke.
- Lane 05 only for measured misses: improve the semantic contract, prompt, or deterministic adapters without restoring prompt-specific routing authority.

## Commit readiness

The exact-path rollout-measurement slice is ready to commit. The experience is not ready to activate.
