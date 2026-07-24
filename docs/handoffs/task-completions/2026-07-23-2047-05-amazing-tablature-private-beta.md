# Lane 05 — Amazing Tablature private beta runtime

## Task summary

Continued the existing Amazing Tablature goal under the approved pivot from
further annotation to visible private runtime value.

Implemented a fail-closed runtime adapter for exact challenger
`at-b97d1a6cf902ba05`. The adapter:

- loads only a strict, SHA-256-pinned sanitized artifact;
- preserves the frozen 21-feature calculation and hard pitch, register,
  harmony, and mechanical gates;
- adds a `Learned beta recommendation` route;
- keeps a `Deterministic comparison` route beside it;
- reports the exact model ID, 702 reviewed decisions, and changed-position
  count without exposing weights or source material;
- defaults off and returns the existing deterministic behavior for any missing,
  malformed, mismatched, or unreadable artifact;
- states explicitly that score-image recognition remains a separate reviewed
  step.

The official sealed evaluator and its hashed source files were not modified.
The official sealed test was not run.

## Files changed

- `steel_guitar_rag/amazing_tablature_runtime.py`
- `steel_guitar_rag/melody_assistant.py`
- `steel_guitar_rag/api.py`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_amazing_tablature_runtime.py`
- `tests/test_api_search.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- This handoff

Generated but not staged:

- `~/.steel-rag/private-models/at-b97d1a6cf902ba05.runtime.json`
- Sanitized artifact SHA-256:
  `e45593b1d80c1dd2a03e406261879dcfe0226fb43885c2aa17f5289985d62fd1`

No files were deleted.

## Tests and checks

- `python3 -m py_compile ...` — PASS.
- `node --check ui/melody-workbench.js` — PASS.
- Ruff on all touched Python files — PASS.
- Focused private-beta, arranger parity, API, assistant, and UI tests —
  PASS, 22 tests in the final focused run.
- Full repository test suite — PASS, 1,455 tests.
- `git diff --check` — PASS.
- Frozen-code verification for `atrf-0e5e727332f26367` — PASS.
- The official one-shot sealed evaluation was not invoked.

## Integration notes

The private preview must set all four runtime variables:

- `STEEL_RAG_ENABLE_AMAZING_TABLATURE_BETA=1`
- `STEEL_RAG_AMAZING_TABLATURE_MODEL_PATH` to the absolute sanitized artifact
- `STEEL_RAG_AMAZING_TABLATURE_MODEL_ID=at-b97d1a6cf902ba05`
- `STEEL_RAG_AMAZING_TABLATURE_MODEL_SHA256` to the sanitized artifact digest

The feature defaults off everywhere else. The API session advertises
`amazingTablaturePrivateBeta` only after exact artifact validation succeeds.
The full private training model, source images, annotations, evidence, and
weights remain outside the repository and outside API/UI payloads.

The frozen arranger is unchanged. The adapter injects the validated policy
through the existing shadow-policy seam, then builds a mechanically validated
learned route and retains the deterministic route for comparison.

## Risk assessment

Medium. The integration is private, reversible, feature-flagged, and
fail-closed, and all repository tests pass. The challenger passed validation,
but has not yet received an unbiased sealed-test score. The UI therefore says
`Private learned beta`, not promoted or production-proven.

Rollback is to remove or disable
`STEEL_RAG_ENABLE_AMAZING_TABLATURE_BETA`; deterministic behavior resumes
without changing code or data.

## Human decision needed

No for implementation or private preview activation. User evaluation of the
learned-versus-deterministic routes can begin after protected-preview smoke.
Stable promotion and the official sealed-test run remain separate decisions.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_runtime.py`
- `steel_guitar_rag/melody_assistant.py`
- `steel_guitar_rag/api.py`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_amazing_tablature_runtime.py`
- `tests/test_api_search.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-23-2047-05-amazing-tablature-private-beta.md`

## Files that must not be staged

- `corpus-private/**`
- `~/.steel-rag/private-models/**`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- All unrelated historical untracked handoffs

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 private protected-preview activation
and authenticated Melody Studio smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the exact file list above, create an immutable release, enable the
hash-pinned artifact only in the private-preview environment, and verify the
signed-in Melody Studio shows both learned and deterministic routes.
