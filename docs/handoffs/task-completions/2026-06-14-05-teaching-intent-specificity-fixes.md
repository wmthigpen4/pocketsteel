# Teaching Intent Specificity Fixes

## Task Summary

Lane: 05 Backend / RAG Integration

Requested: fix user-smoke teaching and lick prompts that were being rejected by the generic specificity gate unless the user explicitly said "steel guitar."

Completed:
- Widened deterministic teaching intent detection for implicit steel-learning prompts about licks, turnarounds, B+C pedal skills, major chords, and minor chords.
- Added source-free teacher-first answers for the observed smoke prompts.
- Preserved missing-context behavior for prompts like "this lick" and "this position."
- Added focused API and classifier regression coverage for all listed smoke prompts.

Intentionally not changed:
- No curated_guidance public exposure.
- No curated_guidance source cards or answer-body use.
- No SGF scraper, Chroma, embeddings, deployment, DNS, auth policy, corpus-private, or UI changes.
- No staging or commit.

## Root Cause

The existing deterministic lick route worked for "Show me a steel guitar lick" because both the answer-intent classifier and curated-answer router required an explicit steel-domain phrase: `steel`, `pedal steel`, `steel guitar`, or `E9`.

Valid app-domain teaching prompts such as "Show me a lick," "Show me another lick," and "Teach me a lick in D-sharp" did not contain that exact phrase, so they missed the deterministic route and could fall into the generic specificity fallback or source-shaped answer path.

Turnaround and general major/minor chord teaching prompts had a related gap: they were steel-guitar learning prompts by product context, but did not always match an existing exact deterministic pattern.

## Files Changed

Changed:
- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`

Created:
- `docs/handoffs/task-completions/2026-06-14-05-teaching-intent-specificity-fixes.md`

Deleted:
- None

Generated artifacts:
- None

## Behavior By Smoke Prompt

| Prompt | Before | After |
| --- | --- | --- |
| `Teach me some B&C pedal skills.` | Could miss deterministic teaching route. | Source-free E9 B+C pedal skills answer with strings 3-4-5, pedal mechanics, phrase steps, what it teaches, and practice instruction. |
| `Show me another lick.` | Could hit generic specificity fallback because no steel phrase was present. | Source-free default E9 lick in G, explicitly noting no previous lick context. |
| `Show me a lick in C minor.` | Could hit generic specificity fallback. | Source-free C minor E9 lick using fret 6, strings 3-4-5, B+C, and C-Eb-G. |
| `Show me a lick.` | Could hit generic specificity fallback. | Source-free simple original E9 lick in G. |
| `Show me a steel guitar lick.` | Already decent. | Still returns source-free E9 lick in G. |
| `Show me a country lick in G.` | Could return "available matches are too thin." | Source-free country E9 lick in G with fret, grip, pedals, phrase, and practice instruction. |
| `Teach me a lick in D-sharp.` | Could hit generic specificity fallback. | Source-free Eb/D# E9 lick, treating D-sharp as Eb/D# for easier fretboard thinking. |
| `Teach me about turnarounds.` | Could miss the 1-4-5-1-specific route. | Source-free explanation of turnarounds with G-C-D-G E9 path and practice instruction. |
| `What is a turnaround?` | Could miss deterministic teaching. | Source-free steel-oriented turnaround explanation with E9 examples. |
| `Teach me about minor chords.` | Could fall to generic/source-backed behavior. | Source-free minor-chord teaching answer with C minor, fret 6, B+C. |
| `Teach me about major chords.` | Could fall to generic/source-backed behavior. | Source-free major-chord teaching answer with G-B-D and E9 position families. |
| `Give me a JavaScript sorting algorithm.` | Existing off-domain guardrail needed to remain intact. | Still returns an off-domain scope guardrail with no sources, warnings, or fretboard. |

## Tests And Checks

Commands run:

```bash
git status --short
```

Result:
- Ran at start and after changes. Worktree contains many unrelated pre-existing dirty/untracked files; scoped task files are listed below.

```bash
git diff --check
```

Result:
- Passed.

```bash
.venv/bin/python -m py_compile steel_guitar_rag/api.py steel_guitar_rag/curated_guidance_retriever.py steel_guitar_rag/curated_answers.py steel_guitar_rag/answer_intent_classifier.py
```

Result:
- Passed.

```bash
.venv/bin/python -m pytest tests/test_api_search.py -k 'lick or turnaround or chord or curated_guidance' -q
```

Result:
- `38 passed, 207 deselected`
- Includes the focused user-smoke teaching prompts plus the JavaScript sorting off-domain guardrail assertion.

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_contract.py -q
```

Result:
- `81 passed`

```bash
.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q
```

Result:
- `64 passed`

Full pytest:
- Not run for this slice. The prompt requested focused suites; prior handoff notes still list two known unrelated static/UI full-suite failures.

## Integration Notes

- The new teaching answers are deterministic and source-free: `sources == []`, `warnings == []`, and no fretboard payload for these non-position teaching prompts.
- `Explain B+C pedals.` remains on the existing copedent/mechanics classifier path; the new B+C teaching route only catches skills/practice/drill/lick-style prompts.
- Prompts with missing immediate context such as `How should I play this lick?` are still protected by the missing-context clarifier.
- The JavaScript/off-domain guardrail was not changed and remains covered by existing classifier tests.

## Risks

Risk level: low-medium.

Why:
- The change touches shared answer-intent and curated-answer routing.
- The new patterns are intentionally narrow around teaching/lick/turnaround/chord-family prompts.
- Tests cover both positive observed smoke prompts and existing classifier contracts.

Rollback:
- Revert the changes in `steel_guitar_rag/answer_intent_classifier.py`, `steel_guitar_rag/curated_answers.py`, `tests/test_answer_intent_classifier.py`, and `tests/test_api_search.py`.
- No corpus, Chroma, UI, auth, deployment, or private-data rollback is needed.

## Human Decision Needed

No for this implementation slice.

Yes before:
- exposing curated_guidance content in public/beta answers,
- wiring curated_guidance into source cards,
- changing protected-preview flags,
- broadening this into a larger teacher-first composer refactor.

## Safe-To-Stage Exact File List

For this slice only:
- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-14-05-teaching-intent-specificity-fixes.md`

Do not use `git add .`.

## Files That Must Not Be Staged

Do not stage unrelated pre-existing dirty/parked files, including:
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- SGF scraper outputs
- `source-inbox/` raw data or provenance
- `.wrangler/`
- DNS/deployment secrets
- `public/`
- `ui/brand/`
- `Neon Sign/`
- unrelated broad docs/corpus/landing/runtime files already present in the dirty worktree

## Commit Readiness

Safe to commit after QA/repo-steward exact-path review.

Reason:
- Focused tests/checks requested by the task passed.
- The worktree is broadly dirty, so Repo Steward should stage exact paths only.

## Recommended Next Lane

Recommended lane: 15 QA / Answer Eval.

Suggested next prompt:

```text
Lane 15: QA the teaching intent specificity fix in docs/handoffs/task-completions/2026-06-14-05-teaching-intent-specificity-fixes.md. Verify the listed user-smoke prompts no longer hit the specificity fallback, remain source-free, include steel-specific E9 teaching details, preserve missing-context clarification for "this lick" prompts, and keep off-domain JavaScript guardrails intact. Run the focused API/classifier/eval checks from the handoff and report whether Repo Steward can exact-path stage the listed files.
```
