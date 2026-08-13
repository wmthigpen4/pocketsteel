# Position-strategy routing repair

## Task summary

- Implemented the approved repair for the question “How does a steel guitar player decide when to move frets? Why not just stay on one fret?”
- Added a first-class deterministic `position_strategy` intent and a direct E9 teacher answer.
- Removed bare `fret`/`frets` as sufficient copedent-position evidence.
- Added deterministic-miss escalation to the verified source-backed frontier.
- Added explicit telemetry for deterministic escalation and SGF quarantine fallbacks.
- Added exact-query, paraphrase, keyword-collision, frontier-escalation, fallback-telemetry, API, contract, and golden-bank regressions.
- Intentionally did not change the SGF corpus, Chroma/vector indexes, embeddings, scraping, model/provider configuration, auth, DNS, UI, or deployment files.
- Did not stage, commit, or deploy because a required full-suite deployment-preflight check fails against the local frozen frontier service root. The protected release also remains on a different SHA, so deploying this branch would broaden scope beyond this repair.

## Files changed

### Product

- `steel_guitar_rag/answer_intent_classifier.py`
  - Added the `position_strategy` intent and answer shape.
  - Added a shared position-strategy recognizer.
  - Removed bare `fret`/`frets` from the generic copedent vocabulary trigger.
- `steel_guitar_rag/curated_contracts.py`
  - Added `position_strategy` to the curated intent type.
- `steel_guitar_rag/curated_answers.py`
  - Added position-strategy intent selection and the deterministic E9 teaching answer.
- `steel_guitar_rag/answer_contracts.py`
  - Added required content and a safe fallback for position-strategy answers.
  - Forbids the generic specificity refusal for this clear beginner intent.
- `steel_guitar_rag/api.py`
  - Keeps deterministic content first when it exists.
  - Promotes an unanswered in-domain deterministic route to `source_backed_rag`.
  - Records `deterministic_miss_to_source_backed`, `sgf_quarantine_teacher_answer`, or `sgf_quarantine_specificity_fallback` in route telemetry.

### Tests and evals

- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `tests/test_canonical_frontier_client.py`
- `evals/golden_user_smoke_bank.yaml`
  - Added `gus-253` through `gus-256` for the exact question and three paraphrases.

### Documentation

- `docs/handoffs/task-completions/2026-08-13-1002-05-position-strategy-routing-repair.md` (this handoff)
- The earlier diagnosis remains at `docs/handoffs/task-completions/2026-08-13-0948-18-search-quality-routing-diagnosis.md`.

### Deleted files and generated artifacts

- None.

## Behavioral contract

1. A broad “when/why move versus stay” question receives deterministic teacher content with no source cards.
2. A concrete fret/chord/copedent lookup still uses the deterministic fretboard path when a deterministic artifact exists.
3. A deterministic classification with no answer artifact is promoted to `source_backed_rag`; when the canonical frontier is enabled, it is answered from the verified SGF frontier instead of silently entering the old local fallback path.
4. The generic SGF quarantine response remains available only as a last resort and is now visible in telemetry.

## Tests and checks

- `.venv/bin/pytest -q tests/test_answer_intent_classifier.py tests/test_canonical_frontier_client.py tests/test_api_search.py -k 'position_strategy or deterministic_miss or generic_sgf_quarantine_fallback or intent_mode_classifier_for_practical_advice_questions'`
  - PASS: 12 passed, 466 deselected.
- `.venv/bin/pytest -q tests/test_answer_intent_classifier.py tests/test_canonical_frontier_client.py tests/test_api_search.py tests/test_golden_user_smoke_bank.py`
  - PASS: 486 passed.
- In-memory scoring of `gus-253` through `gus-256` with `score_payload`
  - PASS: all four prompts passed every configured gate.
- `.venv/bin/ruff check steel_guitar_rag/answer_intent_classifier.py steel_guitar_rag/curated_contracts.py steel_guitar_rag/curated_answers.py steel_guitar_rag/answer_contracts.py steel_guitar_rag/api.py tests/test_answer_intent_classifier.py tests/test_api_search.py tests/test_canonical_frontier_client.py`
  - PASS.
- `git diff --check`
  - PASS.
- `.venv/bin/pytest -q`
  - BLOCKED: 1 failed, 1,665 passed in 86.68 seconds.
  - The only failure is `CanonicalFrontierLaunchFilesTests.test_installer_render_and_preflight_are_read_only`.
  - The hard-coded service root `/Users/cory/Documents/sgf-scrape-test` contains a required path that resolves into `/Users/cory/.steel-rag/services/canonical-frontier-v1034-fallback-20260806`, so the fail-closed verifier reports that the bundle path escapes the service root.
  - The failure was reproduced alone with the same result.
- `.venv/bin/pytest -q -k 'not test_installer_render_and_preflight_are_read_only'`
  - PASS: 1,665 passed, 1 deselected in 87.14 seconds.
- `.venv/bin/mypy steel_guitar_rag/answer_intent_classifier.py steel_guitar_rag/curated_contracts.py steel_guitar_rag/curated_answers.py steel_guitar_rag/answer_contracts.py steel_guitar_rag/api.py`
  - BLOCKED by the repository’s existing transitive type-check baseline: 223 errors in 23 files. No new position-strategy-specific type error was identified.

## Integration notes

- Internal schema addition: `AnswerIntent`, `AllowedAnswerShape`, and curated `IntentMode` now include `position_strategy`.
- No public API response fields changed.
- New telemetry fallback values:
  - `deterministic_miss_to_source_backed`
  - `sgf_quarantine_teacher_answer`
  - `sgf_quarantine_specificity_fallback`
- Exact question behavior is deterministic and source-free; SGF remains the verified failover for eligible unanswered deterministic routes.
- The worktree had unrelated parked changes before this repair. They remain untouched.
- Current branch: `fix/local-play-along-route-options`, HEAD before this uncommitted repair: `3989d8170849daecef0b8a0610e8b2832c8e9413`.
- A protected deployment was not attempted. The protected app was previously observed on `4a77e849`, and publishing the current branch would include unrelated branch history beyond this scoped repair.

## Risk assessment

- Risk: medium.
- The direct intent is narrow and well covered, but deterministic-miss escalation affects all in-domain deterministic classifications that exhaust their known answer selectors.
- The escalation fails honestly when the verified frontier is unavailable and does not substitute an uncited generic answer.
- Rollback is the exact product/test/eval diff listed above; no corpus or deployment state was mutated.

## Human decision needed

- Yes.
- Exact blocker decision: repair or replace the stale `/Users/cory/Documents/sgf-scrape-test` frozen-service layout so the fail-closed preflight resolves entirely beneath one verified service root, then rerun the complete suite. Do not bypass the path-containment check.
- After the full suite is green, choose an isolated release path based on the protected SHA or explicitly approve the additional branch history; do not deploy the current branch implicitly as part of this repair.

## Safe-to-stage exact file list

- None while the required full-suite preflight check is failing.
- After that blocker is cleared and the full suite is green, the intended exact scope is:
  - `steel_guitar_rag/answer_intent_classifier.py`
  - `steel_guitar_rag/curated_contracts.py`
  - `steel_guitar_rag/curated_answers.py`
  - `steel_guitar_rag/answer_contracts.py`
  - `steel_guitar_rag/api.py`
  - `tests/test_answer_intent_classifier.py`
  - `tests/test_api_search.py`
  - `tests/test_canonical_frontier_client.py`
  - `evals/golden_user_smoke_bank.yaml`
  - `docs/handoffs/task-completions/2026-08-13-0948-18-search-quality-routing-diagnosis.md`
  - `docs/handoffs/task-completions/2026-08-13-1002-05-position-strategy-routing-repair.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing unrelated modification).
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md` (pre-existing unrelated untracked file).
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md` (pre-existing unrelated untracked file).
- Corpus, Chroma/vector indexes, embeddings, raw SGF/source data, scraping outputs, private data, credentials, environment files, logs, generated artifacts, deployment files, or auth policy.

## Recommended next lane

- Lane 12 / deployment infrastructure: restore a self-contained verified canonical-frontier service root without weakening path-containment checks.
- Then Lane 15: rerun the full suite and an isolated protected-preview smoke.
- Then Lane 01: exact-path commit only after green QA.

## Commit readiness

Not ready to commit.

## Suggested next step

Run: `Lane 12: Repair the frozen canonical-frontier service-root layout reported in docs/handoffs/task-completions/2026-08-13-1002-05-position-strategy-routing-repair.md without weakening path containment or changing corpus contents; rerun the failing preflight test and full pytest, then hand back to Lane 15.`
