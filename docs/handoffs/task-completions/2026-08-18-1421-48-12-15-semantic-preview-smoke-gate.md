# Semantic protected-preview smoke gate handoff

## Task summary

- Requested outcome: continue making the semantic search experience real and verifiable rather than stopping at default-off implementation.
- Implemented: a bounded protected-preview acceptance bank and runner covering all six answer authorities plus contextual follow-ups.
- Preserved: no activation, restart, deployment, secret access, paid model call, auth change, corpus/index change, or public API contract change.

## Lane and task mode

- Lanes: `12 Deployment / Protected Preview`, `15 QA / Answer Eval`, `01 Repo Steward`.
- Mode: YELLOW local tooling and verification only. Actual protected activation and paid answer requests remain RED until explicitly authorized.

## Acceptance matrix

The eight cases cover:

- deterministic exact chord mapping;
- source-free conceptual harmony/melody teaching using the reported failure class;
- source-backed player reports;
- deterministic plus sourced hybrid output;
- missing-context clarification;
- off-domain guardrail after steel conversation context;
- contextual source-backed follow-up;
- prompt-injection guardrail.

Each case checks the allowed response shape: HTTP status, minimum answer content, required/forbidden language, source presence or absence, fretboard presence or absence, and clarification punctuation where applicable.

## Runner safety

- Validates all six authorities before any network call.
- Accepts HTTPS origins and loopback HTTP only; rejects embedded credentials, paths, queries, and fragments.
- Reads the Cloudflare Access JWT from `STEEL_RAG_PREVIEW_ACCESS_JWT` or another explicitly named environment variable; there is no CLI token value.
- Requires exact `--authorize-answer-requests 8` approval before network execution.
- Calls authenticated `/api/session` first and makes zero answer calls unless both `semanticAnswer` and `canonicalFrontier` are proven active.
- Converts HTTP, network, oversized, malformed-JSON, and non-object responses into explicit scoreable failures.
- Prints only case status/latency. Full payload capture occurs only when an explicit output path is supplied.

## Files changed

- `evals/semantic_answer_preview_smoke.yaml`
- `scripts/run_semantic_answer_preview_smoke.py`
- `tests/test_semantic_answer_preview_smoke.py`
- `docs/semantic-answer-orchestrator.md`
- `docs/handoffs/task-completions/2026-08-18-1421-48-12-15-semantic-preview-smoke-gate.md`

Deleted files: none.

## Tests and checks

- Focused smoke-runner tests: **20 passed**.
- Full repository suite: **1,777 passed** in **87.05 seconds**.
- Ruff on runner/tests: **PASS**.
- Scoped mypy on runner: **PASS**.
- Validation-only runner execution: **PASS**, eight cases across all six authorities.
- `git diff --check`: **PASS**.
- Protected network smoke: **NOT RUN** because the active app is an older commit and no release/flag/restart or eight-request paid-smoke authorization was granted.

## Authorized command shape

Run only after an exact protected release has both required flags active and eight answer requests are explicitly authorized:

```bash
STEEL_RAG_PREVIEW_ACCESS_JWT=<protected-session-jwt> \
  .venv/bin/python scripts/run_semantic_answer_preview_smoke.py \
  --base-url https://app.steelguitarrag.com \
  --authorize-answer-requests 8 \
  --output output/semantic-answer-preview-smoke.json
```

The output remains an uncommitted QA artifact.

## Risks and remaining gate

- The runner proves product response shapes but cannot directly observe the internal route name because the public answer payload intentionally does not expose it. Structure, source, fretboard, answer, trace, and activation evidence are used instead.
- Source-backed and hybrid cases may trigger multiple frontier model calls behind a single answer request. The authorization is an application-request bound, not a claim about exact internal provider-call count.
- Live planner-bank quality and protected enabled-path behavior remain unproven until their separately authorized runs pass.

## Human decision needed

Yes:

1. Authorize the 32-call live planner bank with an approved server-side key.
2. If it passes, authorize an exact protected release with semantic and canonical-frontier flags together.
3. Authorize the eight protected answer requests and run this matrix.

## Safe-to-stage exact file list

- `evals/semantic_answer_preview_smoke.yaml`
- `scripts/run_semantic_answer_preview_smoke.py`
- `tests/test_semantic_answer_preview_smoke.py`
- `docs/semantic-answer-orchestrator.md`
- `docs/handoffs/task-completions/2026-08-18-1421-48-12-15-semantic-preview-smoke-gate.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (coordination artifact; intentionally uncommitted).
- The pre-existing unrelated untracked handoffs dated 2026-08-04, 2026-08-12, and 2026-08-13.
- `output/`, credentials, environment files, logs, corpora, indexes, embeddings, and deployment artifacts.

## Commit readiness

The exact-path smoke-gate slice is ready to commit. The protected search experience itself remains gated.
