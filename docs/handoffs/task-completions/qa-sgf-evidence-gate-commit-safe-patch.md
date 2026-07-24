# QA: SGF Evidence Gate Commit-Safe Patch Recheck

## Task Summary

Requested QA recheck of the SGF Evidence Is Not Primary Answer Text backend patch after Lane 05 extracted the deterministic basic chord/theory helpers into `steel_guitar_rag/basic_chord_answers.py`.

Completed:
- Reviewed the repo protocol, current integration status, prior SGF implementation/QA handoffs, commit-safe patch handoff, answer contract/rubric/teacher-first guidance, backend answer files, eval runner, API tests, git status, and current diffs.
- Verified the new helper module preserves the previously approved SGF evidence-gate behavior.
- Verified `steel_guitar_rag/answering.py` and `steel_guitar_rag/curated_answers.py` now import SGF-approved basic theory/chord-change helpers from `steel_guitar_rag.basic_chord_answers`.
- Verified the SGF slice no longer needs the dirty helper additions in `steel_guitar_rag/fretboard_examples.py` or `tests/test_fretboard_examples.py`.
- Re-ran compile checks, focused SGF/API tests, broader answer/API tests, prompt-level in-process checks, `run_answer_eval.py --help`, and full pytest.

Intentionally not changed:
- No implementation files were edited.
- No UI files were edited.
- No auth policy, deployment, DNS, Cloudflare Access policy, corpus, Chroma/vector stores, embeddings, scraping, source-inbox, source data, visual assets, or generated reports were touched.
- No files were staged or committed.

## Pass/Fail Decision

**Pass.**

QA approves exact-hunk commit of the commit-safe SGF evidence gate patch, including the new helper module `steel_guitar_rag/basic_chord_answers.py`.

The helper extraction is approved. It resolves the previous commit blocker because the SGF slice no longer depends on staging dirty `steel_guitar_rag/fretboard_examples.py` or `tests/test_fretboard_examples.py`. The new helper module imports only utility functions that already exist in clean HEAD:
- `minor_triad_spelling_for_answer`
- `normalize_chord_words_in_text`
- `normalize_key`
- `normalize_requested_root`
- `transpose`

Those clean-HEAD utility definitions were verified with `git show HEAD:steel_guitar_rag/fretboard_examples.py`.

## Focused Behavior Results

In-process `/api/answer` sweep with mocked noisy SGF sources:

| Prompt | Result |
| --- | --- |
| `What is a G chord?` | Deterministic source-free `G-B-D` answer; no fretboard; no warnings. |
| `What is a C chord?` | Deterministic source-free `C-E-G` answer; no fretboard; no warnings. |
| `What notes are in a D chord?` | Deterministic source-free `D-F#-A` answer; no fretboard; no warnings. |
| `What is a sus chord?` | Deterministic chord-quality answer; no fretboard; no warnings. |
| `How do I play a B-sus chord/` | Deterministic `Bsus4` answer with `B-E-F#`; no fretboard; no warnings. |
| `How do I play a B sus chord?` | Deterministic `Bsus4` answer with `B-E-F#`; no fretboard; no warnings. |
| `What is a dominant 7 chord?` | Deterministic dominant-7 explanation; no fretboard; no warnings. |
| `What is a diminished chord?` | Deterministic diminished explanation; no fretboard; no warnings. |
| `What is an augmented chord?` | Deterministic augmented explanation; no fretboard; no warnings. |
| `How do I play a Fmaj7?` | Deterministic `F-A-C-E` major-7 answer; no fretboard; no warnings. |
| `How do I play an F major 7th?` | Deterministic `F-A-C-E` major-7 answer; no fretboard; no warnings. |
| `What is a chord change?` | Deterministic teacher-first chord-change explanation; no fretboard; no warnings. |
| `What is a chord progression?` | Deterministic teacher-first progression explanation; no fretboard; no warnings. |
| `Who is <PRIVATE_PERSON_PLACEHOLDER>?` | Source-free private/unknown identity guardrail; no random corpus/person fragments; no warnings. |
| `What do players say about wound 6th strings?` | Synthesized forum-wisdom answer with one supporting source card. |
| `What are common Fender Steel King settings?` | Synthesized practical answer with one supporting source card. |
| `How do players diagnose hum that changes when touching the changer?` | Synthesized diagnostic answer with one supporting source card. |
| `How do I play a G chord on the E9?` | Deterministic E9 position answer with top-level fretboard payload; no sources; no warnings. |
| `What is the capital of France?` | Off-domain guardrail; no sources; no fretboard; no warnings. |

No focused response contained:
- raw SGF/forum/source fragments as primary text
- weak-source warning as primary text
- `[object Object]`
- inappropriate source cards on deterministic/guardrail answers
- missing fretboard payload for the G-on-E9 position prompt

`/api/version` in-process check returned `200 OK` with non-secret keys:
- `auth_provider`
- `git_branch`
- `git_sha`
- `python_module`
- `retrieval_mode`
- `server_started_at`

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
git show HEAD:steel_guitar_rag/fretboard_examples.py | rg -n "def (minor_triad_spelling_for_answer|normalize_chord_words_in_text|normalize_key|normalize_requested_root|transpose)"
.venv/bin/python -m py_compile steel_guitar_rag/basic_chord_answers.py steel_guitar_rag/answering.py steel_guitar_rag/curated_answers.py steel_guitar_rag/answer_contracts.py steel_guitar_rag/api.py scripts/run_answer_eval.py
.venv/bin/python -m pytest tests/test_api_search.py -k "unknown_person_identity or primary_answer_gate or rootless_chord_quality or major_seventh or chord_change or suspended_chord or basic_chord_definition or smoke_ready_chord_fretboard"
.venv/bin/python scripts/run_answer_eval.py --help
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python -m pytest
git diff --check
```

Results:
- `git diff --check`: passed.
- Clean-HEAD utility check: required utility functions exist in committed `steel_guitar_rag/fretboard_examples.py`.
- `py_compile`: passed.
- Focused SGF/API selection: `8 passed, 200 deselected`.
- `scripts/run_answer_eval.py --help`: passed.
- `tests/test_answer_intent_classifier.py`: `65 passed`.
- `tests/test_answer_eval.py`: `9 passed`.
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: `253 passed`.
- Full pytest: `639 passed, 2 failed`.

Full-suite failure classification:
- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
  - Classification: unrelated parked static/UI blocker.
  - Reason: compares landing source HTML and `deploy/landing/index.html`; does not exercise backend answering, helper extraction, SGF source-fragment gating, retrieval gating, or `/api/version`.
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
  - Classification: unrelated parked Lane 06/static blocker.
  - Reason: static `/brand/pedal-steel-fretboard-background.svg` route returns `404 Not Found`; does not exercise backend answering, helper extraction, SGF source-fragment gating, retrieval gating, or `/api/version`.

These two failures require separate Lane 06/static work. They are blocking full-suite green and protected-preview restart certification, but they do **not** block exact-hunk commit of this backend SGF evidence patch.

## Files Changed By This QA Task

Created:
- `docs/handoffs/task-completions/qa-sgf-evidence-gate-commit-safe-patch.md`

No implementation files were modified by this QA task.

## Approved Commit Scope

QA approves exact-hunk staging for the SGF evidence gate patch only.

Approved files/hunks:
- `steel_guitar_rag/basic_chord_answers.py`
  - New standalone helper module for deterministic basic chord/theory and chord-change answers.
- `steel_guitar_rag/answer_contracts.py`
  - SGF/source-fragment forbidden pattern additions and directly related contract/inference hunks required by this SGF gate.
- `steel_guitar_rag/answering.py`
  - Import of `basic_chord_theory_answer_for_question` and `chord_change_answer_for_question` from `steel_guitar_rag.basic_chord_answers`.
  - SGF chatter classification/rejection for fragments such as `which someone else is probably playing` and `I may be learning`.
  - Deterministic fallback loop that tries rootless quality, basic chord/theory, chord-change/progression, and generic chord concept answers before weak fallback text.
- `steel_guitar_rag/api.py`
  - `GET /api/version` endpoint and non-secret runtime identity payload helpers.
- `steel_guitar_rag/curated_answers.py`
  - Import of helpers from `steel_guitar_rag.basic_chord_answers`.
  - Basic theory/chord-change curated answer routing.
  - Private/placeholder unknown-identity guardrail routing.
- `scripts/run_answer_eval.py`
  - Eval hardening for raw source-fragment and weak/source-internal wording leakage.
- `tests/test_api_search.py`
  - Focused regressions for source-free basic theory, chord quality, chord-change/progression, private/placeholder identity, SGF chatter rejection, forum-wisdom synthesis, E9 position preservation, and `/api/version`.
- `docs/handoffs/task-completions/sgf-evidence-not-primary-answer-text-implementation.md`
- `docs/handoffs/task-completions/qa-sgf-evidence-not-primary-answer-text.md`
- `docs/handoffs/task-completions/sgf-evidence-gate-commit-safe-patch.md`
- `docs/handoffs/task-completions/qa-sgf-evidence-gate-commit-safe-patch.md`

Repo Steward should still use exact-hunk staging because approved files may contain nearby unrelated dirty changes.

## Must Remain Parked

Do not stage for this SGF backend commit unless a separate lane explicitly approves:
- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_fretboard_examples.py`
- `ui/steel-guitar-rag-mock.html`
- `deploy/landing/index.html`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- `corpus_metadata/`
- `source-inbox/`
- `docs/source-inbox-inventory.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- root RAG/corpus scripts such as `rag_answer.py`, `rag_build_clean_corpus.py`, `rag_chunk_corpus.py`, `rag_embed_chroma.py`, and `rag_build_forum.py`
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, databases, logs, generated reports, private source data, deployment secrets, `.wrangler/`, DNS config, private env files, and visual/design assets
- broad historical handoffs and docs unrelated to the SGF evidence gate

## Integration Notes

The previous helper-scope contradiction is resolved:
- Before: approved `answering.py` / `curated_answers.py` hunks depended on helper definitions living only in dirty `steel_guitar_rag/fretboard_examples.py`.
- Now: helper definitions live in `steel_guitar_rag/basic_chord_answers.py`, which is in the approved commit scope.
- The new helper module depends only on utility functions that exist in clean HEAD, so dirty `steel_guitar_rag/fretboard_examples.py` hunks are not required for this backend commit.

Retrieval gating remains intact in the prompt sweep and answer/API tests:
- Off-domain prompt returned a source-free guardrail.
- Steel/forum-wisdom prompts retained source-backed synthesis.
- Deterministic E9 position prompt returned fretboard payload and no SGF source cards.

Protected-preview restart remains blocked until:
- Repo Steward lands the SGF backend slice from exact hunks.
- The unrelated static/UI failures are fixed or explicitly parked by the responsible lane.
- Runtime/user-facing dirty files are resolved enough for Lane 12 to restart/verify from a clean committed HEAD.

## Risk Assessment

Risk: low-to-medium.

Why:
- The helper extraction is narrow and behavior-preserving under focused prompt checks and broader answer/API tests.
- The primary remaining risk is commit-scope contamination from the very dirty worktree.
- Full pytest remains red, but only for unrelated static/UI failures.

Rollback:
- Revert the exact SGF evidence gate commit if needed, including `steel_guitar_rag/basic_chord_answers.py` and the import/call-site changes.
- Do not use destructive cleanup commands against parked work.

## Commit Readiness

**Safe to commit** with exact-hunk staging.

This approval applies only to the SGF evidence gate backend/eval slice and the new helper module. It does not approve staging the whole dirty worktree.

## Suggested Next Step

Recommended lane: `01 Repo Steward`.

Exact next prompt:

```text
Lane 01 Repo Steward
Branch: feature/answer-api

QA approved the commit-safe SGF Evidence Gate patch in docs/handoffs/task-completions/qa-sgf-evidence-gate-commit-safe-patch.md. Proceed under Repo Steward auto-approval with exact-hunk staging only.

Stage only the approved SGF backend/eval/documentation scope:
- steel_guitar_rag/basic_chord_answers.py
- exact approved hunks in steel_guitar_rag/answer_contracts.py
- exact approved hunks in steel_guitar_rag/answering.py
- exact approved hunks in steel_guitar_rag/api.py
- exact approved hunks in steel_guitar_rag/curated_answers.py
- exact approved hunks in scripts/run_answer_eval.py
- exact approved hunks in tests/test_api_search.py
- docs/handoffs/task-completions/sgf-evidence-not-primary-answer-text-implementation.md
- docs/handoffs/task-completions/qa-sgf-evidence-not-primary-answer-text.md
- docs/handoffs/task-completions/sgf-evidence-gate-commit-safe-patch.md
- docs/handoffs/task-completions/qa-sgf-evidence-gate-commit-safe-patch.md

Do not stage steel_guitar_rag/fretboard_examples.py, tests/test_fretboard_examples.py, UI/static files, corpus/source/provenance files, deployment/design assets, generated reports, or unrelated docs.

Run git diff --cached --check, py_compile for touched Python files, focused SGF/API tests, and the backend/eval gate. If the staged diff is clean and tests pass, commit the scoped SGF backend slice. If exact hunks cannot be isolated safely, write a blocker handoff instead.
```

If Repo Steward cannot isolate approved hunks, recommended lane: `05 Backend / RAG Integration`.

Revision prompt:

```text
Lane 05 Backend / RAG Integration
Branch: feature/answer-api

QA approved the commit-safe SGF Evidence Gate behavior, but Repo Steward could not isolate exact approved hunks from unrelated dirty work. Split the SGF Evidence Gate patch into a clean, stageable patch containing only the files/hunks approved in docs/handoffs/task-completions/qa-sgf-evidence-gate-commit-safe-patch.md. Do not touch UI/static/corpus/source/deploy/design files.
```
