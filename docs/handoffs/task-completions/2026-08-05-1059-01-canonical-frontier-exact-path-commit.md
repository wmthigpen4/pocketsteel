# Canonical Frontier Exact-Path Commit

## Task summary

Repo Steward committed the approved, default-off canonical-frontier site candidate using exact-path staging. No deployment, restart, activation, secret, auth, DNS, corpus, Chroma, embedding, or vector-index action occurred.

## Files changed

Implementation commit `9e6ac02a feat: add default-off canonical frontier candidate` contains exactly:

- `steel_guitar_rag/canonical_frontier_client.py`
- `steel_guitar_rag/api.py`
- `tests/test_canonical_frontier_client.py`
- `docs/handoffs/task-completions/2026-08-05-1058-05-18-canonical-frontier-site-candidate.md`

This Repo Steward handoff and the integration-status refresh were created after the implementation commit and are not part of `9e6ac02a`.

## Tests and checks

- Cached diff path review: passed; exactly four approved files.
- `git diff --cached --check`: passed before commit.
- Focused application tests: 349 passed.
- Full application tests: 1,592 passed with one documented worktree-environment failure caused by missing `.venv/bin/python`.
- The exact catalog pipeline check passed with the existing repository Python interpreter and reported no registry errors.
- Exploration/runtime tests: 915 passed.
- Python compile checks: passed.
- Loopback client-to-service smoke: passed.
- Live candidate smoke: complete, four verified claims, one source, $0.0123489, no runtime activation.

## Integration notes

- Current branch: `fix/local-play-along-route-options`.
- Commit: `9e6ac02a`.
- The feature remains disabled unless `STEEL_RAG_CANONICAL_FRONTIER_ENABLED=true` and its URL/token are deliberately configured.
- The unrelated pre-existing `2026-08-04-1629-12-app-origin-502-diagnosis.md` file remains untracked and untouched.

## Risk assessment

Risk: **low while disabled; medium when enabled**. Rollback is to keep the flag false. The live exhaustive smoke is a tail-latency warning, not a release blocker for this disabled implementation.

## Human decision needed

**Yes, before activation.** The owner should review a small expert checkpoint and explicitly authorize any protected-preview enablement, secret configuration, or deployment action.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-05-1059-01-canonical-frontier-exact-path-commit.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- Any corpus, Chroma/vector, embedding, private-source, source-inbox, `.wrangler`, credential, log, environment, or generated artifact.

## Recommended next lane

`15 QA / Answer Eval` for the bounded expert product checkpoint; then `12 Self-Hosted Deployment` only after explicit activation authorization.

## Commit readiness

**Safe to commit.** These are coordination-only docs reflecting the already completed exact-path implementation commit.

## Suggested next step

Commit only these two coordination files, then prepare the owner-facing 8–10 question checkpoint without enabling the feature in any shared runtime.
