# Semantic answer orchestrator handoff

## Task summary

- Requested: begin replacing prompt-specific answer routing with the agreed semantic authority architecture while preserving the public API/UI, deterministic music authority, verified source-backed path, OpenAI API usage, and a rollback path.
- Implemented: a default-off semantic answer orchestrator backed by one strict Structured Outputs call to the OpenAI Responses API.
- Preserved: `/api/answer`, the `AnswerResponse` payload, all frontend rendering, the existing deterministic tools, the canonical frontier client, corpus/index state, and the current router as the disabled-flag/runtime-failure fallback.
- Not activated: no environment, key, protected-preview, deployment, DNS, auth, corpus, embedding, or vector-index change was made.

## Lane and task mode

- Lanes: `18 Product / Architecture`, `05 Backend / RAG Integration`, `15 QA / Answer Eval`, `01 Repo Steward`.
- Task type: backend architecture, API integration, eval, docs, tests, and commit preparation.
- Mode: YELLOW implementation explicitly authorized by the user's architecture-change request; deployment remains RED and was not performed.

## Architecture delivered

- Six validated authorities: `deterministic`, `semantic_teacher`, `source_backed_rag`, `hybrid`, `clarify`, and `guardrail`.
- Known deterministic fretboard questions retain a zero-OpenAI-call fast path.
- Semantically recognized exact questions return a bounded canonical `tool_query`; the model cannot return the exact music result.
- Conceptual steel teaching may return source-free model prose, then passes the existing final quality and answer-contract gates.
- Source-backed and hybrid plans cannot return answer prose; the verified frontier remains responsible for evidence-backed output.
- Local unsafe classification remains authoritative before the semantic planner.
- A planner outage falls back for valid in-domain requests and fails closed for legacy off-domain decisions.
- Guardrail authority remains active across conversation follow-ups, preventing stale steel context from authorizing unrelated retrieval.
- The feature flag defaults off: `STEEL_RAG_SEMANTIC_ANSWER_ENABLED=false`.

## Files changed

- `steel_guitar_rag/semantic_answer_orchestrator.py`
- `steel_guitar_rag/api.py`
- `tests/test_semantic_answer_orchestrator.py`
- `evals/semantic_answer_authority_v1.jsonl`
- `scripts/run_semantic_answer_eval.py`
- `tests/test_semantic_answer_eval.py`
- `docs/semantic-answer-orchestrator.md`
- `docs/handoffs/task-completions/2026-08-18-1353-05-15-18-semantic-answer-orchestrator.md`

Deleted files: none.

## Tests and checks run

- Focused semantic/frontier/classifier/eval suite: **153 passed**.
- Full repository suite after final integration: **1,741 passed** in **86.50 seconds**.
- `ruff check` on all changed Python implementation/test/eval files: **PASS**.
- Scoped mypy for the new module with imports skipped: **PASS**.
- `python scripts/run_semantic_answer_eval.py --help`: **PASS**.
- `git diff --check`: **PASS**.
- Full-repository mypy was attempted and remains non-green because of 231 pre-existing errors across existing imported modules. The new module's one initially reported local type issue was corrected; no claim is made that the repository is globally mypy-clean.
- Live OpenAI held-out bank: **NOT RUN** because `OPENAI_API_KEY` is absent from this workspace. No key value was read or logged.
- Browser smoke: not run because the frontend and public response shape are unchanged and the new path is default off. API behavior is exercised through WSGI integration tests.

## Evaluation assets

- The held-out bank contains 32 prompts across all six route authorities.
- It includes paraphrases that the current regex classifier routes incorrectly, exact-tool restatement checks, source-required questions, hybrid questions, missing-context requests, off-domain requests, unbounded output, and prompt injection.
- The live runner exits nonzero on any route or required-tool-term miss and writes no file unless an explicit output path is provided.

## Risks

- The live model has not yet been scored against the 32-case bank; the feature must remain off until that evaluation passes.
- Source-free conceptual teaching is schema- and contract-validated but does not receive the canonical frontier's independent citation verifier because it deliberately has no external evidence claims.
- A semantically interpreted non-fast-path request adds one GPT-5.6 Terra call. Source-backed/hybrid requests then retain the canonical frontier's synthesis/verification calls.
- When the semantic flag is on but the canonical frontier is off, source-backed plans can still reach the existing legacy local source path. Protected rollout should enable and verify both services together.
- Exact semantic restatements are constrained and sent only to deterministic parsers, but their preservation of chord/key/tuning/requested operation still needs live eval review.
- The old router remains substantial technical debt. This slice changes authority at the decision boundary but does not delete the 100+ historical `mentions_*` helpers.

## Human decision needed

Yes, before activation:

1. Supply an approved server-side OpenAI API key in a protected evaluation environment and run the 32-case bank.
2. Review route accuracy, tool-query preservation, answer quality, latency, and API cost.
3. Authorize a protected-preview environment/restart if the bank passes.
4. Do not enable publicly until protected source-backed, hybrid, outage, and follow-up smoke pass.

## Safe-to-stage exact file list

- `steel_guitar_rag/semantic_answer_orchestrator.py`
- `steel_guitar_rag/api.py`
- `tests/test_semantic_answer_orchestrator.py`
- `evals/semantic_answer_authority_v1.jsonl`
- `scripts/run_semantic_answer_eval.py`
- `tests/test_semantic_answer_eval.py`
- `docs/semantic-answer-orchestrator.md`
- `docs/handoffs/task-completions/2026-08-18-1353-05-15-18-semantic-answer-orchestrator.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing coordination changes; intentionally excluded).
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md` (pre-existing unrelated untracked file).
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md` (pre-existing unrelated untracked file).
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md` (pre-existing unrelated untracked file).
- `output/` and all generated reports.
- Environment files, credentials, logs, corpus data, private data, Chroma/vector stores, embeddings, source-inbox material, or deployment artifacts.

## Recommended next lane

- Lane 15: run the live held-out bank with the approved server-side key and classify every miss by route, tool restatement, or teaching quality.
- Lane 12 only after that pass and explicit deployment authority: enable both semantic and canonical frontier flags in protected preview, restart safely, and run the protected smoke matrix.
- Lane 05 after measured failures: extend deterministic tool adapters or planner contract rather than adding new prompt regexes.

## Commit readiness

The exact-path code/docs/eval slice is ready to commit. It is not ready to activate or deploy. The default-off flag is the rollback boundary.
