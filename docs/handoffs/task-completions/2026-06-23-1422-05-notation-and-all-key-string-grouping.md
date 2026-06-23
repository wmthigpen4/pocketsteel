# 2026-06-23 14:22 Lane 05 - Notation And All-Key String Grouping

## Task Summary

Requested Lane 05 backend fix for smoke feedback around musical accidental notation, flat-key string-grouping routing, E9 Fretboard Explorer all-key status, and G harmonized-scale regressions.

Completed:
- Added shared deterministic accidental text normalization for `♭`, `♯`, `𝄫`, `𝄪`, and spelled `flat` / `sharp` forms.
- Routed `Show me an A-flat major string grouping.`, `Show me an Ab major string grouping.`, and `Show me an A♭ major string grouping.` through deterministic E9 major-position/fretboard logic.
- Added source-free Ab/A♭/A-flat answer coverage with common string groupings `3-4-5`, `4-5-6`, `5-6-8`, and `6-8-10`.
- Added Unicode sharp regression coverage for `How do I play a C♯ chord?`.
- Confirmed backend Explorer already supports all configured key spellings and all 12 pitch classes; added tests for every backend-supported key spelling.
- Fixed Explorer flat-key row slugging so flat keys do not produce malformed `flatflat` IDs.
- Added `display_harmony_type` metadata so 5&8 branch rows can be grouped with 2-string harmonized rows without removing the existing `harmony_type` compatibility value.

Intentionally not changed:
- UI/static Explorer key selector and generated browser data. The browser currently shows six keys because `ui/e9-fretboard-explorer.html`, `ui/e9-fretboard-explorer.js`, and static data are UI/static-fixture owned and already have unrelated dirty state. Backend payloads expose all supported keys through `filters.available_keys`.
- Corpus, Chroma, embeddings, scraping, auth, DNS, deployment, source-inbox data, private-source data, and UI files.
- Static grip answers were not changed to return `tab_example`.

## Files Changed

- `pocketsteel/music_text.py` - new shared accidental text normalizer.
- `pocketsteel/fretboard_examples.py` - normalized symbols/spelled accidentals, accepted double accidentals in note lookup, expanded chord root parsing, added string-grouping major-position route.
- `pocketsteel/answer_intent_classifier.py` - normalized accidentals before classification, narrowed source-backed precedence for visual-position prompts, added `string grouping` as a visual object.
- `pocketsteel/curated_answers.py` - normalized accidentals in curated routing, added direct string-grouping answer prose, fixed D-sharp lick route after normalization.
- `pocketsteel/fretboard_explorer.py` - normalized Unicode Explorer keys, fixed flat-key slugs, added `display_harmony_type` grouping metadata.
- `tests/test_api_search.py` - API regressions for A-flat/A♭/Ab string grouping and C♯.
- `tests/test_answer_intent_classifier.py` - classifier regressions for A-flat/A♭ and C♯ visual routing.
- `tests/test_fretboard_explorer.py` - Explorer all-supported-key validation, Unicode key normalization, 5&8 display grouping metadata.

Generated artifacts:
- None.

Deleted files:
- None.

## Issues Addressed

1. Symbol normalization:
   - `♭ -> b`
   - `♯ -> #`
   - `𝄫 -> bb`
   - `𝄪 -> ##`

2. A-flat generic fallback root cause:
   - `A-flat`/`A♭` normalized inconsistently across parser/classifier paths.
   - `string grouping` was not recognized as a deterministic visual-position object.
   - `string` also let the classifier enter source-backed accessory/vendor logic before visual routing.

3. Explorer all-key status:
   - Backend `build_explorer_payload()` already supports `C, C#, Db, D, D#, Eb, E, F, F#, Gb, G, G#, Ab, A, A#, Bb, B`.
   - Tests now validate all backend-supported key spellings and confirm they cover all 12 pitch classes.
   - Remaining six-key browser display is UI/static-fixture-owned, not changed in this Lane 05 patch.

4. 5&8 branch grouping:
   - Existing `harmony_type` remains `five_eight_branch` for backward compatibility.
   - New `display_harmony_type` is `two_string_harmonized`, so Lane 06 can group 5&8 branch rows under the 2-string harmonized-scale UI without losing the branch identity.

5. Preserved G regressions:
   - Existing G major/natural minor harmonized-scale tests still pass.
   - Existing F# diminished / A diminished named prompt tests still pass.
   - Existing G 5&8 A+F and E-lower branch route tests still pass.
   - Existing corrected fret 13 E-lower C/E branch test still passes; no fret 11 E-lower C/E route is introduced.

## Prompts Checked

Manual payload checks:
- `Show me an A-flat major string grouping.`
  - Answer starts: `Ab major is Ab-C-Eb: root, major 3rd, and perfect 5th.`
  - Sources: `0`
  - Warnings: `[]`
  - Fretboard: `Ab major positions on E9`
- `Show me an A♭ major string grouping.`
  - Answer starts: `Ab major is Ab-C-Eb: root, major 3rd, and perfect 5th.`
  - Sources: `0`
  - Warnings: `[]`
  - Fretboard: `Ab major positions on E9`
- `How do I play a C♯ chord?`
  - Answer starts: `C# major is C#-E#-G#: root, major 3rd, and perfect 5th.`
  - Sources: `0`
  - Warnings: `[]`
  - Fretboard: `C# major positions on E9`

## Tests And Checks

Passed:
- `.venv/bin/python -m py_compile pocketsteel/api.py pocketsteel/curated_answers.py pocketsteel/fretboard_examples.py pocketsteel/fretboard_explorer.py pocketsteel/answer_intent_classifier.py pocketsteel/music_text.py`
- `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py -q` -> `86 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` -> `5 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'flat or sharp or accidental or string_grouping or harmonized or diminished or tab_example' -q` -> `24 passed, 254 deselected`
- `.venv/bin/python -m pytest tests/test_api_search.py -q` -> `278 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` -> `32 passed`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q` -> `25 passed`
- `git diff --check` -> passed

Command caveat:
- The user-specified command `.venv/bin/python -m pytest tests/test_api_search.py -k 'flat or sharp or accidental or string grouping or harmonized or diminished or tab_example' -q` fails because pytest parses `string grouping` as two identifiers. I reran the intended subset with `string_grouping`.

Skipped:
- Full pytest was not requested for this slice and is known to have unrelated static/UI caveats in recent handoffs.
- Browser smoke was not run; this is a backend slice.

## Integration Notes

- Public `/api/answer` response schema is unchanged.
- `response.fretboard` continues to use existing deterministic fretboard payloads; no raw UI geometry added.
- Explorer row payloads gain one additive field: `display_harmony_type`.
- Backend Explorer all-key support is covered, but Lane 06 still needs to update the UI/static selector/data if browser smoke requires all keys in the visible selector.

## Risk Assessment

Risk: low to medium.

Why:
- The accidental normalizer is shared and deterministic.
- Regex root parsing was broadened from single accidental to double accidental in several existing parser paths. This is intentional, but broad enough that answer/eval smoke should rerun.
- `display_harmony_type` is additive and preserves `harmony_type`, lowering compatibility risk.

Rollback:
- Revert this commit to restore prior parser/classifier behavior.
- If only UI grouping is problematic, remove or ignore `display_harmony_type` without changing generated rows.

## Human Decision Needed

No for this backend slice.

Human/product decision still needed:
- Whether Lane 06 should expose all backend-supported Explorer keys in the browser UI now, and whether to regenerate/commit static Explorer data.

## Safe-To-Stage Exact File List

- `pocketsteel/music_text.py`
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/answer_intent_classifier.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/fretboard_explorer.py`
- `tests/test_api_search.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-23-1422-05-notation-and-all-key-string-grouping.md`

## Files That Must Not Be Staged

- Existing unrelated dirty files listed by `git status --short`, including `README.md`, corpus metadata docs, `rag_*.py`, `source-inbox/inventory.json`, UI brand assets, `ui/e9-fretboard-explorer.html`, `ui/steel-guitar-rag-mock.html`, private/generated corpus outputs, public/brand assets, deployment/auth/DNS files, and all unrelated untracked handoffs/assets.

## Recommended Next Lane

Lane 15 QA / Answer Eval:
- Re-run focused answer/API smoke for accidental notation, flat-key string grouping, C♯, and G harmonized-scale regressions.

Lane 06 UX/UI Design:
- If product wants all Explorer keys visible in browser, update the UI key selector/static Explorer data to match backend `filters.available_keys`.
- If desired, use `display_harmony_type` to group 5&8 branch rows under 2-string harmonized scale while retaining branch-specific labels.

## Commit Readiness

Safe to commit after exact-path staging and cached diff review.

## Suggested Next Step

Lane 15 exact prompt:

```text
Lane 15 QA: Re-run focused answer/API smoke for 2026-06-23-1422-05-notation-and-all-key-string-grouping.md. Verify A-flat/A♭/Ab string grouping routes deterministically with fretboard and no sources, C♯ matches C#, G harmonized-scale regressions remain green, and Explorer backend all-key metadata is intact. Do not modify code.
```
