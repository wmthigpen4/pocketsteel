# 2026-06-23 Lane 05 - G Harmonized Scale Deterministic Rules

## Task Summary

Requested: add deterministic standard 10-string E9 support for G harmonized-scale position families, with special focus on the strings 5&8 A+F and E-lower branch alternatives. The user also confirmed that the old "11th fret E lever" reference was a typo and should be the 13th fret E-lower route for the C/E branch.

Completed:

- Added a distinct deterministic Explorer harmony type for `five_eight_branch`.
- Added four validated G 5&8 branch rows:
  - fret 6, A pedal + E-raise lever, strings 5&8, G/B, branch 4 minor/blue-color route;
  - fret 8, E-lower lever, strings 5&8, G/B, branch 4 major-color route;
  - fret 11, A pedal + E-raise lever, strings 5&8, C/E, branch 7 minor/blue-color route;
  - fret 13, E-lower lever, strings 5&8, C/E, branch 7 major-color route.
- Kept A+F and E-lower as separate route families; they are not collapsed into one canonical path.
- Added API-facing deterministic fretboard payload support for the static prompt `Show me a G harmonized scale on strings 5 and 8.`
- Kept this static harmonized-scale answer fretboard-first and tab-free.
- Preserved diminished naming behavior: three-note F#-A-C and A-C-Eb rows remain `diminished` partial rows with omitted `b7`, not full m7b5/half-diminished rows.

Intentionally not changed:

- No UI files.
- No corpus, Chroma, embeddings, scraping, source-inbox, auth, DNS, deployment, or private transcript files.
- No SGF/RAG source-card dependency for deterministic harmonized-scale rows.
- No generated tab for static harmonized-scale rows.

## Files Changed

- `pocketsteel/fretboard_explorer.py`
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_fretboard_explorer.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-05-g-harmonized-scale-deterministic-rules.md`

## Tests And Checks Run

- `git status --short`
- `git diff --name-only`
- `git diff --cached --name-only`
- `.venv/bin/python -m py_compile pocketsteel/fretboard_explorer.py pocketsteel/fretboard_examples.py pocketsteel/curated_answers.py pocketsteel/api.py pocketsteel/answer_tab_examples.py pocketsteel/tab_engine.py`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - 30 passed
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'harmonized or static_g or tab_example' -q` - 16 passed, 254 deselected
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q` - 25 passed
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` - 5 passed
- `.venv/bin/python -m pytest tests/test_api_search.py -q` - 270 passed
- `.venv/bin/python -m pytest` - 811 passed
- `git diff --check` - passed before handoff; rerun required after handoff/staging

## Integration Notes

- Explorer payloads now include `five_eight_branch` in `query.harmony_types` and `filters.available_harmony_types`.
- Explorer string groups now include `5-8`.
- The API-facing answer still uses the existing `response.fretboard.positions` contract, not the Explorer payload shape.
- The new harmonized-scale answer has `sources: []`, `warnings: []`, and no `tab_example`.
- Answer-fretboard payloads preserve the existing user-facing lever labels (`F`, `E`), while Explorer rows use mechanical labels (`E-raise`, `E-lower`).

## Risk Assessment

Risk: medium.

Reason:

- Backend deterministic row generation changed shared Explorer payload metadata by adding `five_eight_branch` and `5-8`.
- Full pytest passed, but Lane 06 may need to decide whether/how to expose the new 5&8 branch filter in the Explorer UI. This task intentionally did not touch UI.

Rollback:

- Revert the six scoped files listed above. No generated corpus, vector, deployment, or private-source state was changed.

## Human Decision Needed

No for the backend slice.

Potential product follow-up: decide whether Lane 06 should expose `five_eight_branch` as its own Explorer filter label or map it under the existing 2-string harmonized-scale controls.

## Safe-To-Stage Exact File List

- `pocketsteel/fretboard_explorer.py`
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_fretboard_explorer.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-05-g-harmonized-scale-deterministic-rules.md`

## Files That Must Not Be Staged

- Any unrelated dirty/untracked files shown by `git status --short`.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs.
- `source-inbox/` raw/provenance files.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets.
- Deployment, DNS, auth, Cloudflare, `.wrangler/`, secrets, private env files.

## Recommended Next Lane

Lane 15 QA / Answer Eval:

```text
Lane 15: QA the deterministic G harmonized-scale 5&8 branch slice. Verify Explorer payload rows for branch 4 and branch 7 preserve separate A+F and E-lower routes, verify the corrected fret 13 E-lower C/E branch, verify no fret 11 E-lower C/E branch appears, verify diminished triads are not labeled full m7b5, and verify the API prompt "Show me a G harmonized scale on strings 5 and 8." returns a fretboard payload with no tab_example, no sources, and no warnings.
```

## Commit Readiness

Safe to commit if exact-path staging contains only the safe-to-stage files above and `git diff --cached --check` passes.

## Suggested Next Step

Run exact-path staging and commit for this Lane 05 slice if the cached diff remains scoped. Then run Lane 15 QA on the prompt and Explorer rows.
