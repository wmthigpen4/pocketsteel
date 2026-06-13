# QA: Predictable Question / Raw SGF Fragment Closure

## Task Summary

Requested: determine whether the predictable-question / raw-SGF-fragment blocker is truly closed, not only partially addressed.

Completed:
- Read repo protocol, current integration status, recent SGF evidence gate handoffs, common chord-quality handoffs, default E9 routing handoffs, current answer/eval test references, git status, and current diffs.
- Ran the 23 requested prompts through the current worktree’s in-process `/api/answer` test path.
- Ran focused answer-quality/API tests and broader answer/API/eval suites.
- Inspected remaining dirty hunks that affect this blocker and classified exact commit-safe QA-approved scope.

Intentionally not changed:
- No implementation files were edited.
- No UI/browser files were edited.
- No deployment, DNS, auth policy, corpus, Chroma/vector stores, embeddings, scraping, source-inbox, source data, visual assets, or generated reports were touched.
- No browser/protected-preview smoke was performed.
- No files were staged or committed.

## Pass/Fail Decision

**Pass for backend/API behavior in the current worktree.**

The predictable-question / raw-SGF-fragment blocker is closed in API fallback testing against the current worktree:
- Basic theory prompts return deterministic teacher-first answers.
- Chord-quality prompts return deterministic teacher-first answers.
- Style/how-to prompts return practical teacher-first answers.
- Safety-adjacent prompts return safe practical guidance.
- Sensitive/private identity prompts avoid inferring or listing private attributes.
- Position prompts route to deterministic E9/fretboard behavior.
- Off-domain guardrail remains source-free and fretboard-free.
- Raw SGF/forum/source fragments did not appear as primary answer text.

Important release caveat: this is **API fallback, not browser smoke**. Lane 12 remains blocked until dirty runtime/test files are committed or isolated and protected-preview behavior is verified from a clean committed HEAD.

## Smoke Target

- Target type: API-fallback
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not tested
- Cache-busted URL tested: not tested
- Exact URL the user should use: not ready for user smoke until Lane 12 verifies protected preview from clean committed HEAD
- Auth required: no for in-process API fallback; yes for future protected preview
- Auth provider: in-process local test helper; future protected preview uses Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: in-process API helper from `tests/test_api_search.py`
- Expected backend port: n/a
- Expected git HEAD: `056ce87` plus current uncommitted question-type closure hunks
- Version endpoint: not used for this prompt sweep
- Version endpoint result: not queried
- If version endpoint missing, how version is inferred: `git rev-parse --short HEAD` reported `056ce87`; API fallback exercised the current worktree
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: outside this QA task
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes after protected-preview runtime is clean and verified
- Who should test this URL: Lane 12/QA first, then the user
- Do not test these URLs: do not treat this API fallback as proof of protected-preview browser behavior
- Known caveats: dirty runtime/test files remain; protected-preview restart/certification remains blocked

## Prompt-By-Prompt Results

| # | Prompt | Result |
| ---: | --- | --- |
| 1 | `What is a G chord?` | Pass. Deterministic `G-B-D` theory answer; sources `0`; warnings `[]`; no fretboard. |
| 2 | `What is a C chord?` | Pass. Deterministic `C-E-G` theory answer; sources `0`; warnings `[]`; no fretboard. |
| 3 | `What is a chord change?` | Pass. Teacher-first chord-change explanation; sources `0`; warnings `[]`; no fretboard. |
| 4 | `What is a chord progression?` | Pass. Teacher-first progression explanation; sources `0`; warnings `[]`; no fretboard. |
| 5 | `What is a sus chord?` | Pass. Deterministic suspended-chord quality explanation; sources `0`; warnings `[]`; no fretboard. |
| 6 | `How do I play a B-sus chord/` | Pass. Deterministic `Bsus4` answer with `B-E-F#`; sources `0`; warnings `[]`; no fretboard. |
| 7 | `How do I play a B sus chord?` | Pass. Deterministic `Bsus4` answer with `B-E-F#`; sources `0`; warnings `[]`; no fretboard. |
| 8 | `What is a dominant 7 chord?` | Pass. Deterministic dominant-7 explanation; sources `0`; warnings `[]`; no fretboard. |
| 9 | `What is a diminished chord?` | Pass. Deterministic diminished explanation; sources `0`; warnings `[]`; no fretboard. |
| 10 | `What is an augmented chord?` | Pass. Deterministic augmented explanation; sources `0`; warnings `[]`; no fretboard. |
| 11 | `How do I play a Fmaj7?` | Pass. Deterministic `F-A-C-E` major-7 answer; sources `0`; warnings `[]`; no fretboard. |
| 12 | `How do I play an F major 7th?` | Pass. Deterministic `F-A-C-E` major-7 answer; sources `0`; warnings `[]`; no fretboard. |
| 13 | `Can I play rock and roll on the steel guitar? How?` | Pass. Practical teacher-first rock/roll steel answer; sources `0`; warnings `[]`; no fretboard. |
| 14 | `How do I make steel guitar work in rock music?` | Pass. Practical teacher-first rock steel answer; sources `0`; warnings `[]`; no fretboard. |
| 15 | `Can you play steel guitar drunk?` | Pass. Safe guidance discouraging impaired playing and offering musical alternatives; sources `0`; warnings `[]`; no fretboard. |
| 16 | `Should I play a gig drunk?` | Pass. Safe guidance discouraging impaired gigging and offering musical alternatives; sources `0`; warnings `[]`; no fretboard. |
| 17 | `Who is <PRIVATE_PERSON_PLACEHOLDER>?` | Pass. Private/unknown identity guardrail; sources `0`; warnings `[]`; no fretboard. |
| 18 | `Are there gay steel guitar players?` | Pass. Sensitive/private-attribute guardrail; sources `0`; warnings `[]`; no fretboard. |
| 19 | `Who are the gay steel guitar players?` | Pass. Sensitive/private-attribute guardrail; sources `0`; warnings `[]`; no fretboard. |
| 20 | `How do I play a G chord on the E9?` | Pass. Deterministic G major E9 positions; sources `0`; warnings `[]`; fretboard present. |
| 21 | `How do you play a C chord?` | Pass. Deterministic C major E9 positions; sources `0`; warnings `[]`; fretboard present. |
| 22 | `What is the location for a G chord with A+B?` | Pass. Deterministic G A+B location at 10th fret; sources `0`; warnings `[]`; fretboard present. |
| 23 | `What is the capital of France?` | Pass. Off-domain guardrail; sources `0`; warnings `[]`; no fretboard. |

All 23 prompts passed the requested criteria in API fallback:
- no raw SGF/forum/source fragments as primary answer
- no unrelated source cards for deterministic/guardrail answers
- no weak-source primary warning
- no `[object Object]`
- source cards only where appropriate

## Remaining Failures

No remaining failures were found in the 23-prompt API fallback sweep or the requested focused/broader answer tests.

Remaining non-behavior blockers:
- Dirty runtime/test files remain.
- Browser/protected-preview smoke has not been rerun for this exact closure set.
- Lane 12 remains blocked until dirty runtime/test files are committed or isolated and protected-preview runtime is verified from clean committed HEAD.

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -k "basic_chord_definition_questions_use_source_free_theory_without_fretboard or rootless_chord_quality_questions_are_teacher_first_and_source_free or major_seventh_questions_are_teacher_first_and_source_free or chord_change_questions_are_teacher_first_and_source_free or suspended_chord_punctuation_variants_are_teacher_first_and_source_free or unknown_person_identity_questions_do_not_retrieve_random_fragments or primary_answer_gate_rejects_named_sgf_chatter_fragments or predictable_question"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Results:
- `git diff --check`: passed.
- Focused predictable/SGF/API selection: `7 passed, 202 deselected`.
- `tests/test_answer_intent_classifier.py`: `66 passed`.
- `tests/test_answer_eval.py`: `9 passed`.
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: `254 passed`.

Full pytest was not rerun for this task. Latest integration status still reports known unrelated full-suite failures in static/UI areas.

## Current Dirty Scope Relevant To This Blocker

The current worktree still contains dirty runtime/test hunks that are directly relevant to closing this blocker:
- `pocketsteel/answer_intent_classifier.py`
  - Adds pre-retrieval/retrieval-disabled routing for sensitive personal attributes, specific biographical facts, style/how-to prompts, and safety-adjacent impaired-playing prompts.
- `pocketsteel/curated_answers.py`
  - Adds source-free curated answers for specific biography guardrails, sensitive personal attributes, rock/how-to, and safety-adjacent impaired playing.
- `pocketsteel/api.py`
  - Keeps the relevant curated intents source-free so deterministic/guardrail answers do not display unrelated source cards.
- `tests/test_answer_intent_classifier.py`
  - Adds classifier coverage that the relevant user-smoke question types disable retrieval and do not request fretboard payloads.
- `tests/test_api_search.py`
  - Adds API regression coverage for private/sensitive, style/how-to, and safety-adjacent prompts so noisy SGF fragments cannot pass.
- `pocketsteel/fretboard_examples.py`
  - Keeps concept-only chord prompts from attaching fretboard payloads.
- `tests/test_fretboard_examples.py`
  - Updates concept-prompt expectations to deterministic answers without fretboard payloads.

These hunks are relevant to this blocker and are QA-approved for exact-hunk staging, subject to Repo Steward diff isolation.

## Exact Files/Hunks Approved If Ready For Commit

Approved for exact-hunk staging:
- `pocketsteel/answer_intent_classifier.py`
  - `_mentions_sensitive_personal_attribute`
  - `_mentions_specific_biography_fact`
  - `_mentions_style_how_to`
  - `_mentions_safety_adjacent_playing`
  - early decisions that return retrieval-disabled guardrail/practice-plan shapes for those prompts
- `pocketsteel/curated_answers.py`
  - new `IntentMode` values for `factual_biography`, `sensitive_personal_attribute`, `style_how_to`, and `safety_adjacent`
  - `intent_mode_for_question(...)` routing for those modes
  - source-free curated answers for those modes
  - helper predicates for sensitive attribute, specific biography fact, style/how-to, and safety-adjacent playing
  - `mentions_sensitive_demographic_question(...)` delegation to the broader sensitive-attribute predicate
- `pocketsteel/api.py`
  - `_curated_answer_should_be_source_free(...)`
  - source suppression for source-free curated intents
- `pocketsteel/fretboard_examples.py`
  - `chord_concept_payload_for_question(...)` returning `None` for concept-only theory prompts
- `tests/test_answer_intent_classifier.py`
  - non-position coverage for the new prompt families
  - retrieval-disabled classifier coverage for specific biography, sensitive attributes, style/how-to, and safety-adjacent prompts
- `tests/test_api_search.py`
  - `test_user_smoke_question_type_gate_prevents_forum_fragment_answers`
  - related sensitive demographic assertion update to the new private-attribute wording
- `tests/test_fretboard_examples.py`
  - concept-prompt tests updated to assert deterministic answer text without fretboard payloads
- `docs/handoffs/task-completions/qa-predictable-question-raw-sgf-fragment-closure.md`

Must remain parked unless separately approved:
- unrelated hunks in the same files
- `README.md`
- `corpus_metadata/`
- source-inbox inventory/provenance paths
- root RAG/build scripts
- static landing/public/design files
- `deploy/landing/index.html`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- generated/private/corpus/vector artifacts
- broad historical handoffs/assets unrelated to this closure

## Blocker #4 Closure

**Blocker #4 is closed for backend/API behavior in the current worktree.**

It is not yet protected-preview/user-smoke certified because:
- the closure depends on dirty runtime/test hunks that are not committed yet
- browser/protected-preview smoke was not run for this closure set
- Lane 12 remains blocked by dirty runtime/test state

## Lane 12 Status

Lane 12 remains blocked.

Reason:
- Dirty runtime/test files remain.
- The closure was verified via API fallback, not protected-preview browser smoke.
- Protected preview should not certify a dirty worktree.

After Repo Steward commits or isolates the approved dirty hunks, Lane 12 should restart/verify protected preview from clean committed HEAD and rerun a small predictable-question browser smoke set.

## Risk Assessment

Risk: medium.

Why:
- The observed behavior is clean and test-backed.
- The change affects pre-retrieval classification for predictable user-smoke prompt families.
- The primary risk is still commit-scope contamination from overlapping dirty files.

Rollback:
- Revert only the eventual exact-hunk commit for this question-type closure if it over-classifies future prompts.
- Do not use destructive git cleanup against parked work.

## Commit Readiness

**Safe to commit** with exact-hunk staging.

This approval is only for the predictable-question/raw-SGF-fragment closure hunks listed above. It does not approve staging the whole dirty worktree.

## Suggested Next Step

Recommended lane: `01 Repo Steward`.

Exact prompt:

```text
Lane 01 Repo Steward
Branch: feature/answer-api

QA approved the predictable-question/raw-SGF-fragment closure in docs/handoffs/task-completions/qa-predictable-question-raw-sgf-fragment-closure.md. Proceed under auto-approval with exact-hunk staging only.

Stage only the approved hunks in:
- pocketsteel/answer_intent_classifier.py
- pocketsteel/api.py
- pocketsteel/curated_answers.py
- pocketsteel/fretboard_examples.py
- tests/test_answer_intent_classifier.py
- tests/test_api_search.py
- tests/test_fretboard_examples.py
- docs/handoffs/task-completions/qa-predictable-question-raw-sgf-fragment-closure.md

Do not stage unrelated docs/source/corpus/provenance/static/design/deploy/generated files or unrelated hunks in the same files.

Run git diff --cached --check, focused predictable-question tests, tests/test_answer_intent_classifier.py, tests/test_answer_eval.py, and tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py. If staged scope and tests are clean, commit the scoped closure. If exact hunks cannot be isolated safely, write a blocker handoff.
```

If this later fails in protected-preview browser smoke, recommended lane: `05 Backend / RAG Integration`.

Revision prompt:

```text
Lane 05 Backend / RAG Integration
Branch: feature/answer-api

Protected-preview smoke reproduced predictable-question/raw-SGF-fragment failures after QA API fallback passed. Compare protected-preview HEAD/version with the committed closure, then fix only the prompt family that regressed. Preserve retrieval-disabled deterministic/guardrail behavior for basic theory, chord quality, style/how-to, safety-adjacent, sensitive/private identity, position sanity, and off-domain prompts. Add focused API/browser regression coverage and write a handoff.
```
