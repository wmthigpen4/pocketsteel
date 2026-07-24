# General Chord-Position Routing User Smoke Fix

## Task Summary

Requested: fix real user-smoke blockers where predictable E9 chord-location questions still fell through to raw RAG/forum fragments instead of teacher-first deterministic chord-position/fretboard answers.

Completed: generalized deterministic major chord-position parsing and classifier coverage for normal user phrasing around E9 neck, pedal steel, spelled accidentals, location wording, and A+B modifiers. The fixed prompts now short-circuit before retrieval, return teacher-first E9 chord-position answers, suppress top-level sources, and attach `response.fretboard`.

Intentionally not changed: no UI files, no public `/api/answer` schema change, no source-card layout change, no deployment/DNS/auth, no Chroma/vector stores, no embeddings, no scraping, no corpus-private/corpus-v2/source-inbox data.

Branch/HEAD at verification: `feature/answer-api` / `97071e6`.

## Why Previous Fixes Were Too Prompt-Specific

Previous fixes handled exact forms such as `How do I play a G chord on the E9?`, `Where do I play a G chord on the E9?`, and D-across-fretboard prompts. The remaining failures used ordinary but slightly different language:

- `How do I play an E chord on the E9 neck?`
- `How do I play a B-flat chord on the E9 pedal steel?`
- `What is the location for a G chord with A+B?`

Those missed because the parser did not normalize spelled accidentals like `B-flat`, did not accept context suffixes such as `E9 neck` or `E9 pedal steel`, and did not treat `location ... with A+B` as a concrete visual position request.

## New Generalized Routing Behavior

The deterministic major chord parser now handles:

- roots with spelled accidentals: `B-flat` -> `Bb`, `C sharp` -> `C#`
- E9/pedal-steel contexts: `on E9`, `on the E9`, `on the E9 neck`, `on the E9 pedal steel`, `on pedal steel`
- position language: `where`, `location`, `positions`, `frets`, `across the fretboard`, `how do I play`, `how do I make`
- A+B modifiers such as `What is the location for a G chord with A+B?`

The classifier now marks these as:

```json
{
  "domain": "steel_guitar",
  "intent": "copedent_position",
  "needs_sources": false,
  "needs_fretboard": true,
  "needs_copedent": true,
  "retrieval_allowed": false,
  "allowed_answer_shape": "copedent_position"
}
```

## Before / After Summaries

### `How do I play an E chord on the E9 neck?`

Before: fell through to weak retrieval fallback/source-fragment-style answer, no fretboard.

After:

- deterministic teacher-first E major answer
- includes standard E9 positions:
  - fret 0/open, no pedals
  - 3rd fret with A pedal + F lever
  - 7th fret with A+B pedals
- `sources: []`
- `warnings: []`
- `response.fretboard.title: E major positions on E9`

### `How do I play a B-flat chord on the E9 pedal steel?`

Before: fell through to weak retrieval fallback/source-fragment-style answer, no fretboard.

After:

- `B-flat` is normalized to `Bb` for display and to the existing pitch engine internally.
- deterministic teacher-first Bb major answer
- includes standard E9 positions:
  - 6th fret, no pedals
  - 9th fret with A pedal + F lever
  - 13th fret with A+B pedals
- `sources: []`
- `warnings: []`
- `response.fretboard.title: Bb major positions on E9`

### `How do I play a Bb chord on E9?`

After:

- same route and payload as B-flat
- display stays `Bb`, not user-facing `A#`

### `What is the location for a G chord with A+B?`

Before: fell through to weak retrieval fallback/source-fragment-style answer, no fretboard.

After:

- direct first sentence: `With A+B, G major is at the 10th fret on standard E9.`
- includes the broader deterministic G major position family:
  - 3rd fret, no pedals
  - 6th fret with A pedal + F lever
  - 10th fret with A+B pedals
- `sources: []`
- `warnings: []`
- `response.fretboard.title: G major positions on E9`

## Fretboard Payload Behavior

- Major chord-position prompts attach top-level `response.fretboard`.
- Deterministic source context remains inside `fretboard.sourceContext`.
- Top-level SGF/forum source cards are suppressed for these deterministic visual answers.
- No raw UI geometry is emitted.
- Existing `response.fretboard.positions` remains the frontend contract.

## Source-Card Behavior

For deterministic chord-position prompts in this slice:

- `sources: []`
- `warnings: []`
- no weak-source warning
- no raw SGF/forum fragments as primary answer

Valid non-deterministic steel questions were not changed; source evidence remains available through the existing source-backed path.

## Tests And Checks

Commands run:

```bash
git status --short
```

Result: ran; broad pre-existing dirty/untracked worktree remains.

```bash
python3 -m py_compile steel_guitar_rag/fretboard_examples.py steel_guitar_rag/curated_answers.py
```

Result: passed.

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_fretboard_examples.py::test_smoke_ready_chord_position_prompt_variants_are_supported tests/test_api_search.py::test_smoke_ready_chord_fretboard_prompts_route_deterministically
```

Result: `67 passed`.

```bash
.venv/bin/python -m pytest tests/test_answer_eval.py
```

Result: `9 passed`.

```bash
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Result: `238 passed`.

264-row classifier validation:

- Rows checked: `264`
- Failures: `0`

```bash
.venv/bin/python -m pytest
```

Result: `671 passed`.

```bash
git diff --check
```

Result: passed before handoff and passed again after handoff.

## Integration Notes

- Retrieval gating remains intact for off-domain and unsafe prompts.
- `What is the capital of France?` remains source-free, warning-free, and fretboard-free.
- `Write me a Python script to scrape Instagram.` remains source-free, warning-free, and fretboard-free.
- UI files were not changed.
- This is a backend routing/composer fix, not a UI redesign.

## Risk Assessment

Risk: medium.

Why: runtime behavior is narrowly targeted and full pytest passed, but this work touches shared backend/test files that already contain parked changes from earlier lanes. Repo Steward should stage exact hunks only.

Rollback: remove the spelled-accidental normalization, generalized context/location parser additions, Bb display/payload-title adjustment, classifier regex additions, and corresponding tests.

## Commit Readiness

Safe to commit after Repo Steward hunk-level review.

Safe-to-stage file list for this slice:

- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/general-chord-position-routing-user-smoke-fix.md`

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

## Exact Next QA Prompt

```text
LANE: 15 QA / Answer Eval
REASONING: MEDIUM
Branch: feature/answer-api

Run API fallback or protected-preview smoke for the generalized chord-position routing fix.

Required prompts:
- How do I play an E chord on the E9 neck?
- How do I play a B-flat chord on the E9 pedal steel?
- How do I play a Bb chord on E9?
- What is the location for a G chord with A+B?
- How do I play a G chord on the E9?
- Where do I play a G chord on the E9?
- How do I play an A chord?
- How do I play a D chord?
- How do I play a D chord across the fretboard of the E9?
- What is the capital of France?
- Write me a Python script to scrape Instagram.

Verify:
- chord prompts are teacher-first
- chord prompts attach top-level response.fretboard
- E/Bb/G+A+B answers include the expected E9 locations
- G+A+B directly says G with A+B is at the 10th fret
- deterministic chord prompts have sources: [] and warnings: []
- no raw SGF/forum/source fragments as primary answer
- no [object Object]
- off-domain/unsafe prompts remain retrieval-blocked with no sources and no fretboard

If this is browser smoke, include the required Smoke Target block from AGENTS.md.
```

## Ready For QA

Yes. Backend tests are green and the change is ready for Lane 15 verification.
