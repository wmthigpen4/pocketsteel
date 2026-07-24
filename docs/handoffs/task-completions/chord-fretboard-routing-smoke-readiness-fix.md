# Chord/Fretboard Routing Smoke Readiness Fix

## Task Summary

Requested: fix current chord/fretboard routing gaps before user smoke testing.

Completed: added narrow deterministic routing coverage for the current protected-preview failures:

- `How do I play a G chord on the E9?`
- `Where do I play a G chord on the E9?`
- `Where the the G chords?`
- `Show me the fretboard`
- `How do I play an A chord?`
- `How do I play a D chord?`
- `How do I play a D chord across the fretboard of the E9?`

The chord prompts now route to deterministic E9 major-position answers with top-level `response.fretboard`. The generic fretboard prompt now returns a compact default standard E9/G-major reference view instead of retrieving source fragments.

Intentionally not changed: no UI files, no public API schema changes, no source-card layout, no deployment/DNS/auth, no Chroma/vector stores, no embeddings, no scraping, no corpus/source-inbox/private/generated data.

Branch/HEAD at verification: `feature/answer-api` / `e60324f`.

## Why These Prompts Fell Through

The deterministic major-chord router already handled some variants such as `How do I play a G chord?`, but missed:

- `on the E9` because the parser accepted `on e9` but not `on the e9`.
- `Where do I play...` phrasing.
- Typo phrase `Where the the G chords?`.
- Generic `Show me the fretboard`, which had no deterministic curated route.

When those missed, `/api/answer` continued to retrieval/source-backed fallback and could produce weak source-fragment answers without a fretboard payload.

## Files Changed

- `steel_guitar_rag/fretboard_examples.py`
  - Added parser patterns for `where do I play`, `on the E9`, and `where the the <root> chords`.
  - Added a deterministic default payload for `Show me the fretboard`, using a standard E9/G-major reference map.
- `steel_guitar_rag/curated_answers.py`
  - Added a source-free default teacher-first answer for `Show me the fretboard`.
- `tests/test_fretboard_examples.py`
  - Added rules-layer tests for the smoke prompt variants and default fretboard payload.
- `tests/test_api_search.py`
  - Added API-level tests proving the smoke prompts are deterministic, teacher-first, source-free, and fretboard-backed where appropriate.
- `docs/handoffs/task-completions/chord-fretboard-routing-smoke-readiness-fix.md`
  - This handoff.

Note: these shared backend/test files were already dirty with previous lane work. Repo Steward should use hunk-level staging and avoid staging unrelated parked changes.

## Before / After Summaries

### `How do I play a G chord on the E9?`

Before: fallback answer with no fretboard and source-like weak text.

After:

- Answer starts with standard E9 G major starter positions.
- Includes:
  - 3rd fret, no pedals
  - 6th fret with A pedal + F lever
  - 10th fret with A+B pedals
- `sources: []`
- `warnings: []`
- `response.fretboard.title: G major positions on E9`

### `Where do I play a G chord on the E9?`

Before: same fallthrough as above.

After: same deterministic G major route and fretboard payload as above.

### `Where the the G chords?`

Before: typo phrasing missed deterministic routing.

After: treated as a likely G chord-position request; returns deterministic G major answer and fretboard payload.

### `Show me the fretboard`

Before: retrieval-style fallback with no fretboard.

After:

- Answer starts: `Here’s a starter standard E9 fretboard view using G major as the reference chord.`
- Includes:
  - 3rd fret, no pedals
  - 6th fret with A pedal + F lever
  - 10th fret with A+B pedals
- `sources: []`
- `warnings: []`
- `response.fretboard.title: G major positions on E9`

### A and D major prompts

`How do I play an A chord?` and `How do I play a D chord?` continue to return teacher-first deterministic major-position answers with fretboard payloads.

`How do I play a D chord across the fretboard of the E9?` continues to include D major starter positions plus across-fretboard alternates such as 5th fret A+B and 3rd fret E-lower when validated by the engine.

### Off-domain regression

`What is the capital of France?` remains guardrailed:

- no retrieval
- no source cards
- no fretboard

## Fretboard Payload Behavior

- G prompt variants: `G major positions on E9`.
- A prompt: `A major positions on E9`.
- D prompt: `D major positions on E9`.
- `Show me the fretboard`: default `G major positions on E9` reference payload.

No raw UI geometry is emitted. Existing `response.fretboard.positions` remains the frontend contract.

## Tests And Checks

Commands run:

```bash
git status --short
```

Result: ran; broad pre-existing dirty/untracked worktree remains.

```bash
git diff --check
```

Result: passed before full suites and passed again after this handoff was written.

```bash
.venv/bin/python -m pytest tests/test_fretboard_examples.py::test_smoke_ready_chord_position_prompt_variants_are_supported tests/test_fretboard_examples.py::test_show_me_the_fretboard_returns_default_e9_reference_payload tests/test_api_search.py::test_smoke_ready_chord_fretboard_prompts_route_deterministically tests/test_api_search.py::test_show_me_the_fretboard_returns_default_visual_without_retrieval_fragments
```

Result: `4 passed`.

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
```

Result: `62 passed`.

```bash
.venv/bin/python -m pytest tests/test_answer_eval.py
```

Result: `9 passed`.

```bash
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Result: `238 passed`.

Question-bank classifier validation:

- Rows checked: `264`
- Failures: `0`

```bash
.venv/bin/python -m pytest
```

Result: `668 passed`.

## Integration Notes

- Retrieval gating remains intact for off-domain/unsafe prompts.
- Deterministic chord/fretboard answers suppress top-level sources.
- Source evidence behavior for valid non-deterministic steel questions was not changed.
- UI files were not changed.
- This is not a broad answer-engine redesign; it is a parser/default-route fix for smoke readiness.

## Risk Assessment

Risk: low to medium.

Runtime risk is low because the change is narrow and full pytest passed. Git hygiene risk is medium because the same files contain unrelated previous lane changes; staging should be exact-hunk only.

Rollback: remove the added parser patterns, default fretboard payload condition, default curated answer block, and associated tests.

## Commit Readiness

Safe to commit after Repo Steward hunk-level review.

Safe-to-stage file list for this slice:

- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/chord-fretboard-routing-smoke-readiness-fix.md`

Must remain unstaged unless separately approved:

- UI files
- deployment/DNS/Cloudflare/auth/security files
- Chroma/vector stores
- embeddings
- corpus-private/corpus-v2
- source-inbox raw/generated/provenance files
- generated reports/data
- legal/provenance/source-ingestion artifacts
- design assets and `Neon Sign/`
- unrelated dirty files from other lanes

## Suggested Next Step

Lane 15 QA / Answer Eval should rerun the smoke-readiness prompt set against the protected preview:

```text
Run authenticated protected-preview smoke for:
- How do I play a G chord on the E9?
- Where do I play a G chord on the E9?
- Where the the G chords?
- Show me the fretboard
- How do I play an A chord?
- How do I play a D chord?
- How do I play a D chord across the fretboard of the E9?
- What is the capital of France?

Verify:
- chord/fretboard prompts are teacher-first
- fretboard payload/card appears for chord-position/default-fretboard prompts
- no raw forum/source fragments appear as the primary answer
- no [object Object]
- no weak-source warning as primary answer
- off-domain guardrail still has no sources and no fretboard
```
