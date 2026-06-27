# 2026-06-27 Lane 05 Voicing Identifier Extended Chord Fix

## Task Summary

Requested: correct the E9 Fretboard Explorer Voicing Identifier so partial extended grips are named as partial/implied pedal-steel voicings, and so major-7 color is not misclassified as dominant-7 / V7.

Completed:

- Updated deterministic voicing identification logic for partial extended chords.
- Added omitted-tone labels such as `Fmaj7(no3)`, `Fmaj7(no5)`, and `F7(no5)`.
- Separated chord-identification confidence from uncommon-grip warnings.
- Changed the Voicing Identifier's 9th-string grip label from a dominant-only label to neutral `9th-string color grip`; dominant identity now depends on the computed pitch set.
- Renamed the note-mode detail label from `Intervals against key` to `Selected-key note labels` so note names are not rendered under an interval label.
- Added focused regression coverage for Fmaj7 partials, F7 partial, V7 preservation, outside-scale warning, and no `[object Object]`.

Intentionally not changed:

- No backend API code.
- No corpus, Chroma/vector store, embeddings, scraper, private source data, auth, DNS, deployment, or source registry files.
- No broad UI redesign.
- No song/tab/source-card behavior.

## Files Changed

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-0940-05-voicing-identifier-extended-chord-fix.md`

## What Changed

### Voicing Identity

- `minor7flat5` now requires the b7 for a full m7b5 identity, preventing `1-b3-b5` triads from being treated as complete half-diminished seventh chords.
- Extended qualities can now be identified as partial/implied when the selected pitch set contains the extension and enough context.
- Missing 5th is treated as acceptable for extended partials.
- Missing 3rd lowers confidence.
- Missing root is treated as context-dependent.
- Natural-7 and flat-7 colors are separated by interval content.

### Specific Verified Cases

- `G / fret 3 / strings 5-6-9 / A+B` resolves to notes `E, C, F` and identifies `Fmaj7(no3)`, outside the selected G scale. It does not identify as Dominant 7 or V7.
- `G / fret 3 / strings 5-7-9 / A+B` resolves to notes `E, A, F` and identifies `Fmaj7(no5)` with the uncommon-grip warning preserved. It does not identify as Dominant 7 or V7.
- `F / fret 1 / strings 3-4-9 / no pedals-no levers` resolves to notes `A, F, D#` in the current display-spelling layer and identifies `F7(no5)` using the flat-7 interval role. It does not identify as `Fmaj7`.
- Existing `G / fret 10 / strings 4-5-6-9 / no pedals-no levers` still identifies `D7` and `V7 in G`.
- Existing `F / fret 3 / strings 4-6-10 / A+B` still identifies `C` / `V function in F`.

## Tests And Checks

Commands run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `curl -sS -i 'http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-extended-chords-local-20260627' | head -30`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -k 'explorer' -q`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -vv`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
- `git diff --check`

Results:

- `node --check ui/e9-fretboard-explorer.js`: pass.
- `node --check ui/answer-client.js`: pass.
- `node --check ui/pedal-steel-fretboard.js`: pass.
- `tests/test_fretboard_explorer.py -q`: 38 passed.
- `tests/test_pedal_steel_fretboard_ui.py -q`: 34 passed.
- `tests/test_frontend_answer_ui.py -k 'explorer' -q`: 3 passed, 20 deselected.
- `tests/test_frontend_answer_ui.py -vv`: 23 passed.
- `tests/test_api_contract.py -q`: 5 passed.
- `git diff --check`: pass.

Interrupted/discounted run:

- An initial `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` was interrupted after `6 passed in 166.73s` because the quiet run appeared hung. A rerun with `-vv` completed normally with 23 passed.

## Local Browser Smoke

Smoke Target:

```text
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-extended-chords-local-20260627
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-extended-chords-local-20260627
- Exact URL the user should use: protected-preview URL should be provided after Lane 12/protected smoke
- Auth required: no
- Auth provider: none for local smoke
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: b73d017 plus current scoped Explorer worktree changes before commit
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local server response and current git state
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this Explorer-only local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer-only local smoke
- Who should test this URL: Codex only
- Do not test these URLs: protected-preview URL until commit/protected smoke records exact cache-busted target
- Known caveats: API fallback was not used; local smoke does not prove protected-preview behavior
```

Browser smoke assertions:

- Voicing Identifier loaded.
- `G / fret 3 / strings 5-6-9 / A+B` returned `Fmaj7(no3)`, omitted 3, outside selected scale, and no dominant/V7 leak.
- `G / fret 3 / strings 5-7-9 / A+B` returned `Fmaj7(no5)`, omitted 5, uncommon-grip warning, and no dominant/V7 leak.
- `F / fret 1 / strings 3-4-9 / open` returned `F7(no5)`, flat-7 role, and no Fmaj7 leak.
- No `[object Object]`.
- Browser console logs for warn/error: none.

## Integration Notes

- The Explorer JS/HTML/test diff includes the prior in-flight dominant-V7 grip vocabulary and four-string Voicing Identifier work because those changes are in the same dirty Explorer files and are required by the current behavior/tests.
- This slice does not change `/api/answer` or backend response contracts.
- The note-spelling layer still renders the Eb pitch in the `F7(no5)` smoke as `D#`; the identity and interval role are correct. A future spelling polish can address display spelling separately if needed.

## Risk Assessment

Risk: medium.

Reason: The fix is deterministic and covered by focused tests and browser smoke, but it is layered onto existing dirty Explorer work in the same files. Exact-path staging should include only the Explorer HTML/JS/test/handoff files and must avoid parked corpus/RAG/brand/source files.

Rollback:

- Revert the scoped commit if created.
- No data, corpus, deployment, auth, Chroma, embeddings, or source registry changes are involved.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-0940-05-voicing-identifier-extended-chord-fix.md`

## Files That Must Not Be Staged

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- all untracked parked docs/assets/private/generated/source-inbox files not listed in Safe-To-Stage

## Recommended Next Lane

- Lane 01 exact-path commit for the scoped Explorer files.
- Lane 12 protected-preview smoke after commit if protected-preview static UI can be verified without deployment/config changes.
- Lane 15 follow-up only if protected smoke finds a discrepancy.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 prompt after commit:

```text
Lane 12: Run protected-preview smoke for the Explorer Voicing Identifier extended-chord fix. Use the committed HEAD cache-busted URL `/ui/e9-fretboard-explorer.html?v=voicing-extended-chords-<commit>`. Verify Fmaj7(no3), Fmaj7(no5), F7(no5), omitted-tone wording, no Dominant/V7 leak on major-7 partials, no [object Object], and no relevant console errors.
```
