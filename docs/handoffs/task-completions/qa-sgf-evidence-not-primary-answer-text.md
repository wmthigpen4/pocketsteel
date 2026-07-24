# QA: SGF Evidence Not Primary Answer Text

## Task Summary

Requested QA review for the Lane 05 backend slice that hardens the answer stack so Steel Guitar Forum evidence does not become the primary answer text. I reviewed the implementation handoff, current answer-contract/eval guidance, backend answer files, eval runner, API tests, git status, and current diffs.

Completed:
- Verified deterministic teacher-first answers for basic chord definitions, chord qualities, chord changes/progressions, and E9 chord-position questions.
- Verified forum-wisdom prompts synthesize the primary answer while keeping SGF source cards as supporting evidence.
- Verified private/placeholder identity prompts do not retrieve or display random forum/person fragments.
- Verified off-domain guardrail behavior and retrieval gating remain intact in the focused prompt sweep.
- Verified `/api/version` returns non-secret runtime identity fields.
- Re-ran full pytest to classify the reported two failures.

Intentionally not changed:
- No implementation files were edited.
- No UI files were edited.
- No auth policy, corpus, Chroma, embeddings, scraping, source data, deployment files, or generated reports were touched.
- No staging or commit was performed.

## Pass/Fail Decision

**Pass for the SGF evidence gate.**

QA approves an exact-hunk Repo Steward commit of the backend/eval slice, provided Repo Steward stages only the SGF evidence/backend hunks and leaves unrelated parked files untouched.

The full suite is still red, but the two failures are the same unrelated static/frontend blockers reported by Lane 05:
- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

These failures do not exercise the SGF evidence backend path and should be handled as a separate Lane 06/static task.

## Focused Prompt Results

In-process `/api/answer` sweep with mocked noisy SGF sources:

| Prompt | Result |
| --- | --- |
| `What is a G chord?` | Source-free deterministic answer: `G-B-D`; no fretboard; no warnings. |
| `What is a C chord?` | Source-free deterministic answer: `C-E-G`; no fretboard; no warnings. |
| `What notes are in a D chord?` | Source-free deterministic answer: `D-F#-A`; no fretboard; no warnings. |
| `What is a sus chord?` | Source-free chord-quality explanation; no fretboard; no warnings. |
| `How do I play a B-sus chord/` | Source-free `Bsus4` explanation; no fretboard; no warnings. |
| `How do I play a B sus chord?` | Source-free `Bsus4` explanation; no fretboard; no warnings. |
| `What is a dominant 7 chord?` | Source-free dominant-7 explanation; no fretboard; no warnings. |
| `What is a diminished chord?` | Source-free diminished explanation; no fretboard; no warnings. |
| `What is an augmented chord?` | Source-free augmented explanation; no fretboard; no warnings. |
| `How do I play a Fmaj7?` | Source-free Fmaj7 explanation; no fretboard; no warnings. |
| `How do I play an F major 7th?` | Source-free Fmaj7 explanation; no fretboard; no warnings. |
| `What is a chord change?` | Source-free teacher-first explanation; no fretboard; no warnings. |
| `What is a chord progression?` | Source-free teacher-first explanation; no fretboard; no warnings. |
| `Who is <PRIVATE_PERSON_PLACEHOLDER>?` | Safe private/unknown identity guardrail; no sources; no fretboard; no warnings. |
| `What do players say about wound 6th strings?` | Synthesized forum-wisdom answer; source card retained as supporting evidence. |
| `What are common Fender Steel King settings?` | Synthesized practical answer; source card retained as supporting evidence. |
| `How do players diagnose hum that changes when touching the changer?` | Synthesized diagnostic answer; source card retained as supporting evidence. |
| `How do I play a G chord on the E9?` | Deterministic E9 position answer with fretboard payload; no source cards; no warnings. |
| `What is the capital of France?` | Off-domain guardrail; no sources; no fretboard; no warnings. |

None of the focused answers contained `[object Object]`, weak-source wording as primary text, `Top`/raw SGF opening fragments, or raw forum/source snippets as the primary answer.

## `/api/version` Result

In-process `/api/version` returned `200 OK` with keys:
- `auth_provider`
- `git_branch`
- `git_sha`
- `python_module`
- `retrieval_mode`
- `server_started_at`

Observed payload identified branch `feature/answer-api`, module `steel_guitar_rag.api`, retrieval mode `sgf_only`, auth provider `scaffold`, and git SHA `e353848`. No secrets, paths, tokens, user identity, environment values, or private-source details were exposed.

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -k "basic_chord_definition_questions_use_source_free_theory_without_fretboard or common_chord_quality_questions_are_teacher_first_and_source_free or major_seventh_questions_are_teacher_first_and_source_free or chord_change_questions_are_teacher_first_and_source_free or suspended_chord_punctuation_variants_are_teacher_first_and_source_free or unknown_person_identity_questions_do_not_retrieve_random_fragments or primary_answer_gate_rejects_named_sgf_chatter_fragments or forum_wisdom_answers_synthesize_source_evidence_without_raw_fragments or api_version"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python -m pytest
```

Results:
- `git diff --check`: passed.
- Focused SGF/API selection: `8 passed, 200 deselected`.
- `tests/test_answer_intent_classifier.py`: `65 passed`.
- `tests/test_answer_eval.py`: `9 passed`.
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: `253 passed`.
- Full pytest: `639 passed, 2 failed`.

Full-suite failures:
- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
  - Classification: unrelated parked frontend/static blocker.
  - Evidence: compares `deploy/landing/index.html` to landing source HTML; does not exercise backend answering, source-card composition, retrieval gating, or `/api/version`.
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
  - Classification: unrelated parked Lane 06/static blocker.
  - Evidence: static `/brand/pedal-steel-fretboard-background.svg` route returns `404 Not Found`; does not exercise backend answering, source-card composition, retrieval gating, or `/api/version`.

`scripts/run_answer_eval.py --help` was inspected. I did not run the live eval runner because it requires a live HTTP `/api/answer` server and writes report artifacts by default; the QA evidence above uses in-process API tests and a direct in-process focused prompt sweep instead.

## Files Changed

Created by this QA task:
- `docs/handoffs/task-completions/qa-sgf-evidence-not-primary-answer-text.md`

No implementation files were modified by this QA task.

Current dirty worktree includes many unrelated parked files. The SGF backend slice appears to involve these files/hunks:
- `steel_guitar_rag/answer_contracts.py`
  - SGF chatter fragment forbidden pattern.
  - Contract/inference additions only where they are directly required by this SGF/source-primary gate.
- `steel_guitar_rag/answering.py`
  - Deterministic fallback imports.
  - Source sentence classification for SGF chatter.
  - Answer quality rejection for SGF chatter fragments.
  - Deterministic fallback before returning raw SGF-like text.
- `steel_guitar_rag/api.py`
  - `GET /api/version` compatibility endpoint and non-secret version payload helpers.
- `steel_guitar_rag/curated_answers.py`
  - Basic chord/theory, chord-change/progression, chord-quality, and private/placeholder identity guardrail paths.
- `scripts/run_answer_eval.py`
  - Eval pattern hardening for source-fragment leakage.
- `tests/test_api_search.py`
  - Focused backend/API regressions covering chord theory, chord qualities, chord changes, private/placeholder identity, SGF chatter rejection, forum-wisdom synthesis, and `/api/version`.

## Exact-Hunk Commit Guidance

QA approves exact-hunk staging for the SGF evidence/backend slice only. Repo Steward should inspect the diff carefully because this worktree contains overlapping parked work.

Approved commit scope:
- SGF evidence/source-fragment filtering hunks in `steel_guitar_rag/answer_contracts.py`, `steel_guitar_rag/answering.py`, and `scripts/run_answer_eval.py`.
- Deterministic chord/theory/chord-quality fallback hunks in `steel_guitar_rag/answering.py` and `steel_guitar_rag/curated_answers.py`.
- Private/placeholder identity guardrail hunks in `steel_guitar_rag/curated_answers.py` and the matching tests.
- `/api/version` endpoint hunks in `steel_guitar_rag/api.py` and matching tests.
- Matching focused tests in `tests/test_api_search.py`.
- Lane 05 implementation handoff and this QA handoff.

Files/hunks that must remain parked unless separately approved:
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
- corpus, Chroma, embeddings, source data, deployment secrets, auth policy, and design assets
- unrelated changes in `steel_guitar_rag/fretboard_examples.py`, `tests/test_fretboard_examples.py`, `rag_answer.py`, `rag_build_clean_corpus.py`, `rag_chunk_corpus.py`, and `rag_embed_chroma.py`

If Repo Steward finds unrelated hunks interleaved inside approved files, use hunk-level staging and stop if the approved scope cannot be isolated cleanly.

## Integration Notes

The SGF evidence gate is functionally clean in focused backend/API tests. The two red full-suite tests should not block the backend slice if exact-hunk staging keeps static/frontend files out of the commit.

The two full-suite failures should be handled by a separate Lane 06/static task:
- Reconcile landing source and `deploy/landing/index.html`.
- Restore or correctly route the public fretboard background asset for the same-origin smoke server.

User smoke remains blocked until:
- The SGF backend slice is committed cleanly.
- The unrelated static/frontend full-suite failures are fixed or formally parked by Repo Steward.
- Protected preview is restarted/verified from the intended committed HEAD.

## Risk Assessment

Risk: medium.

Reason:
- The backend behavior under review is covered by focused prompt-level tests and broader answer/API suites.
- The worktree is heavily dirty with unrelated parked changes, so the main risk is commit-scope contamination rather than backend behavior.
- `/api/version` is low risk based on payload inspection, but it should be staged only with its exact matching tests.

Rollback:
- If the backend slice causes an issue, revert only the exact backend/eval commit containing the SGF evidence gate. Do not revert unrelated parked work.

## Commit Readiness

**Safe to commit** with exact-hunk staging.

This approval is for the SGF evidence/backend slice only, not for the whole dirty worktree and not for the unrelated static/frontend files.

## Suggested Next Step

Recommended lane: `01 Repo Steward`.

Exact next prompt:

```text
Repo Steward: QA approved the SGF Evidence Is Not Primary Answer Text backend slice in docs/handoffs/task-completions/qa-sgf-evidence-not-primary-answer-text.md. Proceed under auto-approval with exact-hunk staging only. Stage the approved backend/eval hunks in steel_guitar_rag/answer_contracts.py, steel_guitar_rag/answering.py, steel_guitar_rag/api.py, steel_guitar_rag/curated_answers.py, scripts/run_answer_eval.py, tests/test_api_search.py, plus the Lane 05 implementation handoff and QA handoff. Do not stage unrelated parked UI/static/corpus/source/deploy/design files. Run the focused backend checks and git diff --check on the staged diff, then commit the scoped slice if clean. If unrelated hunks cannot be isolated, write a blocker handoff.
```

If Repo Steward blocks on interleaved hunks, recommended lane: `05 Backend / RAG Integration`.

Revision prompt:

```text
Lane 05: The SGF evidence backend behavior passed QA, but Repo Steward could not isolate exact approved hunks from unrelated parked work. Split the SGF Evidence Is Not Primary Answer Text changes into a clean patch covering only the backend/eval files and tests named in docs/handoffs/task-completions/qa-sgf-evidence-not-primary-answer-text.md, without touching UI/static/corpus/source/deploy/design files.
```
