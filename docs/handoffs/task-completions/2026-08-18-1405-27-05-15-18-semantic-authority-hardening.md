# Semantic answer authority hardening handoff

## Task summary

- Requested outcome: continue replacing case-by-case answer routing with the agreed semantic authority architecture.
- Implemented: closed the remaining paths where a valid semantic decision could be preempted by legacy deterministic handlers, corpus promotion, contextual probing, or local fragment synthesis.
- Preserved: `/api/answer`, the frontend response contract, deterministic music tools, the canonical verified frontier, and the default-off rollback flag.
- Not activated: no deployment, restart, environment, secret, auth, corpus, embedding, or index change was made.

## Lane and task mode

- Lanes: `05 Backend / RAG Integration`, `15 QA / Answer Eval`, `18 Product / Architecture`, `01 Repo Steward`.
- Mode: YELLOW architecture implementation explicitly authorized by the user. Deployment remains RED and was not performed.

## Architecture changes

- With `STEEL_RAG_SEMANTIC_ANSWER_ENABLED=true`, every non-unsafe request receives one semantic planner decision. The former legacy-classifier zero-call shortcut for recognized exact questions was removed.
- Local unsafe/unbounded classification still runs before the planner and remains a zero-call guardrail.
- A valid semantic result disables legacy corpus entity promotion and contextual corpus probes.
- Deterministic chord, melody, and progression handlers execute early only when the semantic route grants deterministic authority.
- Source-backed and hybrid semantic plans can use only the canonical verified frontier. If it is unavailable, source-backed requests return an honest `503`; hybrid requests return only the deterministic partial with an explicit warning.
- The API boundary revalidates all semantic results, including injected/alternate providers.
- Source-free teaching results are rejected when they contain numbered fret coordinates, numbered string grips, exact string-to-pitch changes, citation markers, or unsupported player/forum-consensus claims. This is a defense-in-depth output boundary, not a replacement request classifier.
- The held-out evaluator now fails teaching authority violations and reports per-route results.

## Files changed

- `steel_guitar_rag/semantic_answer_orchestrator.py`
- `steel_guitar_rag/api.py`
- `scripts/run_semantic_answer_eval.py`
- `tests/test_semantic_answer_orchestrator.py`
- `tests/test_semantic_answer_eval.py`
- `docs/semantic-answer-orchestrator.md`
- `docs/handoffs/task-completions/2026-08-18-1405-27-05-15-18-semantic-authority-hardening.md`

Deleted files: none.

## Tests and checks run

- Focused semantic/frontier/classifier/eval suite: **163 passed**.
- Full repository suite: **1,751 passed** in **85.97 seconds**.
- Ruff on changed Python implementation/test/eval files: **PASS**.
- Scoped mypy for the semantic orchestrator and eval runner: **PASS**.
- Python bytecode compilation for the changed runtime/eval modules: **PASS**.
- Eval runner `--help`: **PASS**.
- `git diff --check`: **PASS**.
- Live OpenAI 32-case bank: **NOT RUN** because no approved server-side API key is present in the workspace.
- Browser smoke: not run because the frontend and public response shape are unchanged and the path remains default off; WSGI integration tests cover routing behavior.

## Regression coverage added

- Teaching prose cannot cross into exact fret/string or unsourced player-consensus authority.
- Alternate semantic providers are revalidated before display.
- Chord names cannot preempt semantic teaching or source routes.
- Source-backed conversation follow-ups bypass the legacy contextual corpus probe while preserving conversation context for the frontier.
- Source and hybrid plans never fall into legacy retrieval when the frontier is disabled.
- Hybrid frontier failure returns only the verified deterministic portion.
- Recognized exact questions use semantic authority first, then deterministic tools.

## Risks and remaining gate

- The live model has not yet been scored against the 32-case bank. The feature must remain off until route accuracy, tool-query preservation, teaching quality, latency, and cost pass in an approved key-bearing environment.
- Enabling the feature intentionally adds one planner API call to exact deterministic requests. Source-backed and hybrid requests also retain the canonical frontier's synthesis/verification calls.
- Planner outage fallback still retains the current router for valid in-domain requests. This is the explicit rollback behavior, not the enabled-path authority.
- The old routing helpers remain technical debt but no longer own enabled-path semantic decisions after a valid plan.

## Human decision needed

Yes, before activation:

1. Provide an approved protected environment containing the server-side OpenAI key and run the live bank.
2. Review route-level accuracy, exact-tool restatements, teaching answers, latency, and API cost.
3. Explicitly authorize protected-preview flag changes and restart only after the bank passes.
4. Run source, hybrid, outage, and follow-up smoke before any public rollout.

## Safe-to-stage exact file list

- `steel_guitar_rag/semantic_answer_orchestrator.py`
- `steel_guitar_rag/api.py`
- `scripts/run_semantic_answer_eval.py`
- `tests/test_semantic_answer_orchestrator.py`
- `tests/test_semantic_answer_eval.py`
- `docs/semantic-answer-orchestrator.md`
- `docs/handoffs/task-completions/2026-08-18-1405-27-05-15-18-semantic-authority-hardening.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (coordination artifact; intentionally excluded).
- The three pre-existing unrelated untracked handoffs dated 2026-08-04, 2026-08-12, and 2026-08-13.
- `output/` and generated reports.
- Environment files, credentials, logs, corpus/private data, indexes, embeddings, or deployment artifacts.

## Recommended next lane

- Lane 15: run the live bank in the approved key-bearing environment.
- Lane 12 only with explicit authorization after that pass: activate both semantic and canonical frontier flags in protected preview and run the smoke matrix.
- Lane 05 after measured failures: improve semantic contracts or deterministic adapters; do not restore prompt-specific routing authority.

## Commit readiness

The exact-path hardening slice is ready to commit. It is not ready to activate or deploy.
