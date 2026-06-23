# Broader G Harmonized-Scale Routing

Pass/warn/fail: pass

Branch: `feature/answer-api`

Starting HEAD: `f15ef6c`

Final HEAD / commit hash: `f15ef6c` (not committed; repo guidance does not allow a Lane 05 commit without explicit commit approval)

## Task Summary

Lane 05 expanded deterministic answer routing for broader G harmonized-scale prompts so they use existing pitch-validated E9 fretboard logic instead of generic fallback or retrieval fragments.

Completed:
- Added source-free deterministic routing for broad G major harmonized-scale prompts.
- Added source-free deterministic routing for G natural minor harmonized-scale prompts.
- Added named diminished-position routing for F# diminished in G and A diminished in G natural minor.
- Preserved the existing scoped 5&8 branch answer behavior.
- Added API regression coverage for all requested prompt classes.

Intentionally not changed:
- No UI changes.
- No corpus, Chroma, embeddings, scraping, auth, DNS, deployment, private transcripts, or Cloudflare Access changes.
- No arbitrary-key harmonized-scale expansion.
- No tab example behavior for static harmonized-scale prompts.

## Files Changed

- `pocketsteel/fretboard_examples.py`
  - Added diminished triad support to the existing pitch validator.
  - Added G major harmonized-scale payload builder.
  - Added G natural minor harmonized-scale payload builder.
  - Added named diminished-position payload routing.
- `pocketsteel/curated_answers.py`
  - Added teacher-first source-free answer text for broad G harmonized-scale prompts and named diminished prompts.
  - Kept 5&8-specific routing ahead of broad routing.
  - Kept harmonized-scale workout routing separate.
- `tests/test_api_search.py`
  - Added API-level regressions for broad G major variants, G natural minor variants, F# diminished in G, and A diminished in G minor.

## Tests And Checks Run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'harmonized_scale or diminished_positions_in_g' -q`
  - Result: `4 passed, 269 deselected`
- `.venv/bin/python -m py_compile pocketsteel/fretboard_examples.py pocketsteel/curated_answers.py pocketsteel/api.py`
  - Result: passed
- `.venv/bin/python -m py_compile pocketsteel/fretboard_explorer.py pocketsteel/fretboard_examples.py pocketsteel/curated_answers.py pocketsteel/api.py`
  - Result: passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - Result: `30 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - Result: `5 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'harmonized or diminished or static_g or tab_example' -q`
  - Result: `19 passed, 254 deselected`
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - Result: `273 passed`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - Result: `25 passed`
- `git diff --check`
  - Result: passed
- `git diff --cached --name-only`
  - Result: no staged files
- `git diff --cached --check`
  - Result: passed

## Behavior After Change

The following prompts now route to deterministic source-free fretboard answers:

- `Show me a G harmonized scale.`
- `Show me G major harmonized scale on E9.`
- `Show me a G major harmonized scale.`
- `Show me a G harmonized scale on E9.`
- `Show me a G natural minor harmonized scale.`
- `Show me G natural minor harmonized scale on E9.`
- `Show me the F# diminished position in G.`
- `Show me the A diminished position in G minor.`

Payload behavior:
- `sources == []`
- `warnings == []`
- `fretboard` is present with `response.fretboard.positions`
- `tab_example` is omitted
- fretboard positions validate through the existing deterministic pitch logic

Naming behavior:
- F#-A-C is labeled F# diminished.
- A-C-Eb is labeled A diminished.
- Neither is labeled full m7b5 / half-diminished because the b7 is absent.

## Integration Notes

- The broad G major payload includes the validated 4-5-6 harmonized-scale family plus the existing 5&8 A+F/E-lower branch alternatives.
- The G natural minor payload includes validated 4-5-6 rows for G natural minor diatonic harmony.
- The payload uses existing user-facing lever labels from the answer/fretboard payload layer (`F` for E-raise and `E` for E-lower), consistent with existing answer payload conventions.
- No UI follow-up is required for this backend route unless Lane 15/06 finds the current `five_eight_branch` or `5-8` labels unclear in protected-preview rendering.

## Risk Assessment

Risk: low to medium.

Reason:
- The change is scoped to deterministic fretboard payload construction and curated answer routing.
- Diminished support was added to the shared chord-quality validator, which is broader than one prompt but covered by focused API and Explorer tests.
- No retrieval, corpus, UI, or deployment paths were changed.

Rollback notes:
- Revert the added G harmonized-scale helpers and routing in `pocketsteel/fretboard_examples.py`.
- Revert the curated answer route in `pocketsteel/curated_answers.py`.
- Revert the focused tests in `tests/test_api_search.py`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-05-broader-g-harmonized-scale-routing.md`

## Files That Must Not Be Staged

- Unrelated existing dirty files shown by `git status --short`, including docs, corpus metadata, `source-inbox/`, `ui/brand/`, `public/`, `Neon Sign/`, and generated/private artifacts.

## Recommended Next Lane

Lane 15 QA / Answer Eval.

Suggested prompt:

```text
Lane 15: QA the broader G harmonized-scale deterministic routing slice using docs/handoffs/task-completions/2026-06-23-05-broader-g-harmonized-scale-routing.md. Verify the requested G major, G natural minor, F# diminished, and A diminished prompts return source-free fretboard payloads with no tab_example, and confirm existing 5&8 branch behavior remains unchanged.
```

## Commit Readiness

Safe to commit if exact-path staging includes only the safe-to-stage files above and final staged diff checks pass.
