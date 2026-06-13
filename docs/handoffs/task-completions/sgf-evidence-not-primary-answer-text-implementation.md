# SGF Evidence Is Not Primary Answer Text Implementation

## Task Summary

Requested: implement the approved Lane 05 backend rule that SGF/forum/source chunks are supporting evidence only and must not become primary answer text unless the user explicitly asks for quotes or source excerpts.

Completed:

- Added/tightened deterministic handling for basic chord/theory and chord-quality fallback paths.
- Added a private/unknown-person placeholder guardrail for prompts such as `Who is <PRIVATE_PERSON_PLACEHOLDER>?`.
- Hardened the main answer quality gate against named forum-chatter fragments:
  - `which someone else is probably playing`
  - `I may be learning`
- Aligned answer contract/eval checks so forbidden internal/source-fragment language is detected consistently.
- Added `/api/version` compatibility expected by existing API tests. It reports runtime/retrieval/auth mode only and does not include identity, tokens, secrets, or local filesystem paths.
- Added focused API regressions for private placeholder identity prompts and named SGF chatter fragments.

Intentionally not changed:

- No UI files were edited.
- No `/api/answer` response schema change.
- No Chroma/vector store, embeddings, corpus, scraping, source-inbox, source data, auth policy, deployment, DNS, Cloudflare Access policy, or design asset changes.
- No protected-preview restart.
- No commit, because full pytest still fails on unrelated dirty frontend/static lanes.

## Root Cause

The answer stack already had deterministic teacher-first routes, but two gaps remained:

1. Literal private-person placeholder prompts did not match the unknown-person identity guardrail and could fall through to a noisy source-backed fallback with source cards.
2. The answer quality/eval layers did not consistently reject the newly named SGF chatter fragments from the approved plan.

There was also existing dirty-suite drift unrelated to this smoke bug: contract tests expected newer intent contract registrations and `/api/version`, while the working tree did not yet expose them.

## Files Changed

Changed implementation/test files:

- `pocketsteel/answer_contracts.py`
- `pocketsteel/answering.py`
- `pocketsteel/api.py`
- `pocketsteel/curated_answers.py`
- `scripts/run_answer_eval.py`
- `tests/test_api_search.py`

Created handoff:

- `docs/handoffs/task-completions/sgf-evidence-not-primary-answer-text-implementation.md`

No generated/private/corpus/vector/deploy/design files were intentionally modified.

## Evidence Gate Behavior

- `final_answer_quality_gate(...)` now has deterministic chord/theory fallback access after stripping bad primary-answer text. If a raw fragment is rejected for a prompt such as `What is a G chord?`, the fallback can return the source-free deterministic teacher answer rather than a generic weak-source apology.
- `classify_source_sentence(...)`, `answer_has_quality_issue(...)`, and `COMMON_FORBIDDEN` now treat `which someone else is probably playing` and `I may be learning` as forum-chatter fragments.
- `scripts/run_answer_eval.py` now flags:
  - `I found a few related practical points`
  - `match is limited`
  - `[link removed]`
  - first-person source statements
  - chopped first-person fragments
  - PayPal/order fragments

## Deterministic Theory And Chord-Quality Behavior

Verified by tests/API fallback:

- `What is a G chord?` returns `G-B-D`, root/major 3rd/perfect 5th, source-free, no fretboard.
- `How do I play a Fmaj7?` and `How do I play an F major 7th?` return `F-A-C-E` with a deterministic E9 mapping caveat, source-free, no fretboard.
- `What is a chord change?` explains harmony moving from one chord to another, source-free, no fretboard.
- `How do I play a B-sus chord/` and `How do I play a B sus chord?` normalize to Bsus4 and explain `B-E-F#`, source-free, no fretboard.
- `How do I play a G chord on the E9?` returns deterministic E9 G major starter positions with a fretboard payload and `sources: []`.

## Before / After Summaries

| Prompt | Before | After |
| --- | --- | --- |
| `Who is <PRIVATE_PERSON_PLACEHOLDER>?` | Fell through to weak/noisy source path and could return a source card. | Source-free private/unknown identity guardrail; no fretboard. |
| Raw answer containing `which someone else is probably playing` / `I MAY BE LEARNING` | Not consistently detected by final answer/eval gates. | Rejected as SGF chatter; deterministic theory fallback can answer when possible. |
| `What is a G chord?` after bad source-fragment stripping | Could fall to generic weak-source fallback if bad primary text was removed. | Returns deterministic `G-B-D` teacher answer. |

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -k "unknown_person_identity or primary_answer_gate or rootless_chord_quality or major_seventh or chord_change or suspended_chord or basic_chord_definition or smoke_ready_chord_fretboard"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_answer_eval.py tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python -m pytest
```

Results:

- Focused API regressions: `8 passed`.
- `tests/test_answer_intent_classifier.py`: `65 passed`.
- `tests/test_answer_eval.py`: `9 passed`.
- API/contract/full-quality set: `253 passed`.
- Combined required backend/eval set: `327 passed`.
- `git diff --check`: passed.
- Full pytest: `639 passed / 2 failed`.

Full pytest failures are unrelated to this backend answer-quality slice:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
  - dirty landing/deploy HTML mismatch.
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
  - dirty/missing static public fretboard background asset path.

These are existing dirty frontend/static lane blockers, not caused by the SGF-primary-answer backend fix.

## Smoke Target

- Target type: protected-preview
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not tested; browser/protected-preview smoke blocked by dirty runtime/UI state.
- Cache-busted URL tested: not tested.
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=user-smoke-a3103c0-auth-fix` after Lane 12 restarts/verifies from a clean committed HEAD.
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: current working tree at `e353848` plus uncommitted backend changes
- Version endpoint: `/api/version`
- Version endpoint result: running server returned `404 Not Found`, which indicates stale code relative to this working tree.
- If version endpoint missing, how version is inferred: in-process API helper used the patched local working tree; running protected-preview loopback was not restarted.
- Whether app root `/` works: yes, local loopback returned HTML.
- Whether app root `/` is expected to work: not the canonical smoke target.
- Whether `/ui/steel-guitar-rag-mock.html` works: not browser-tested in this task.
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, after protected-preview restart/verification.
- Who should test this URL: Lane 12/QA first, then the user.
- Do not test these URLs: do not use root `/` as substitute for the canonical UI path.
- Known caveats: API fallback is not proof of protected-preview browser behavior; dirty UI/static files still block honest protected-preview restart certification.

## API Fallback Smoke Result

In-process API fallback against the patched code:

| Prompt | Result | Sources | Fretboard | Summary |
| --- | --- | ---: | --- | --- |
| `What is a G chord?` | PASS | 0 | no | `G-B-D`, root/major 3rd/perfect 5th. |
| `How do I play a Fmaj7?` | PASS | 0 | no | `F-A-C-E`, major-7 explanation and E9 caveat. |
| `How do I play an F major 7th?` | PASS | 0 | no | Same deterministic Fmaj7 behavior. |
| `What is a chord change?` | PASS | 0 | no | Harmony moves from one chord to another. |
| `Who is <PRIVATE_PERSON_PLACEHOLDER>?` | PASS | 0 | no | Private/unknown identity guardrail. |
| `How do I play a B-sus chord/` | PASS | 0 | no | Bsus4 = `B-E-F#`. |
| `How do I play a B sus chord?` | PASS | 0 | no | Bsus4 = `B-E-F#`. |
| `What do players say about wound 6th strings?` | PASS | 1 | no | Synthesized tradeoff answer; source card remains evidence. |
| `What are common Fender Steel King settings?` | PASS | 1 | no | Synthesized settings guidance; source card remains evidence. |
| `How do I play a G chord on the E9?` | PASS | 0 | yes | Deterministic E9 G positions and fretboard payload. |
| `What is the capital of France?` | PASS | 0 | no | Off-domain guardrail. |

No raw SGF/source fragments appeared as primary answer text in the fallback smoke.

## Integration Notes

- `/api/version` was added to satisfy existing API tests and future smoke target clarity. It does not expose user identity, token data, secrets, or `/Users/...` paths.
- The running local loopback on `127.0.0.1:8770` is stale relative to this working tree, because it returned `404` for `/api/version`.
- Protected-preview restart should still wait for Repo Steward/Lane 12 because the worktree has unrelated dirty runtime/user-facing files.

## Risk Assessment

Risk: medium.

Why:

- Backend answer behavior is improved and focused tests pass.
- The worktree is very dirty and includes unrelated frontend/static/corpus/deploy/docs changes.
- Full pytest is still red due unrelated dirty UI/static paths, so this is not commit-ready under autopilot stop conditions.

Rollback notes:

- Revert the hunks in `pocketsteel/answer_contracts.py`, `pocketsteel/answering.py`, `pocketsteel/api.py`, `pocketsteel/curated_answers.py`, `scripts/run_answer_eval.py`, and `tests/test_api_search.py` if this answer-quality slice needs to be parked.
- Do not use destructive git commands; preserve unrelated dirty work.

## Commit Readiness

Not ready to commit.

Reason: full pytest failed with two unrelated dirty frontend/static failures, and the repo remains too dirty for an autopilot exact-path commit without Repo Steward hunk review.

Safe-to-stage candidate list after QA/Repo Steward review:

- `pocketsteel/answer_contracts.py`
- `pocketsteel/answering.py`
- `pocketsteel/api.py`
- `pocketsteel/curated_answers.py`
- `scripts/run_answer_eval.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/sgf-evidence-not-primary-answer-text-implementation.md`

Files that must remain unstaged unless separately approved:

- `ui/steel-guitar-rag-mock.html`
- `deploy/landing/index.html`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, DBs, logs
- raw `source-inbox` content and provenance files
- root corpus/RAG build scripts and broad docs/provenance/deploy changes not part of this backend slice

## Suggested Next Step

Recommended lane: `01 Repo Steward`.

Exact next prompt:

```text
LANE: 01 Repo Steward
Branch: feature/answer-api

Review the SGF Evidence Is Not Primary Answer Text backend slice and isolate exact safe hunks for commit.

Read:
- docs/handoffs/task-completions/sgf-evidence-not-primary-answer-text-implementation.md
- git status --short
- git diff -- pocketsteel/answer_contracts.py pocketsteel/answering.py pocketsteel/api.py pocketsteel/curated_answers.py scripts/run_answer_eval.py tests/test_api_search.py

Do not stage UI/static/corpus/deploy/source-inbox/private/generated files.

Goal:
- Determine whether the backend slice can be exact-hunk staged despite unrelated dirty work.
- If safe, stage only the approved hunks and rerun the backend/eval gate.
- Do not commit if full pytest blockers from unrelated UI/static lanes remain policy-blocking; write a blocker handoff instead.
```
