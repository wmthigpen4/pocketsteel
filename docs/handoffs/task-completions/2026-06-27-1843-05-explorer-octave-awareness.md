# E9 Explorer Octave/Register Awareness

## Task Summary

Lane 05 implemented deterministic octave/register awareness for the E9 Fretboard Explorer.

Completed:
- Added standard 10-string E9 absolute pitch values using middle C = C4.
- Added scientific pitch and player-facing octave band metadata to Explorer rows, selected copedent strings, control-impact previews, and shared browser music-rule calculations.
- Added a UI pitch-register display control with modes: Off, Scientific, and Octave band.
- Kept primary fretboard marker labels in pitch-class / NNS / Roman / Numbers notation without octave suffixes.
- Added glossary entries for scientific octave notation, pitch register, octave band, and Peterson octave-label follow-up.
- Regenerated the static Explorer data bundle from deterministic backend payload generation.

Intentionally not changed:
- No corpus, Chroma, embeddings, scraping, source records, auth, DNS, secrets, deployment, or private data.
- No Peterson/StroboPlus octave mapping was implemented.
- No broad Explorer visual redesign.
- No RAG/corpus involvement in fret/string/pedal truth.

## Files Changed

- `pocketsteel/e9_copedents.py`
- `pocketsteel/fretboard_explorer.py`
- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1843-05-explorer-octave-awareness.md`

Generated artifact:
- `ui/e9-fretboard-explorer-data.js` was regenerated from `pocketsteel.fretboard_explorer.build_explorer_payload`.

## What Changed

Backend/model:
- Added standard E9 open-string pitch values:
  - 1 F#4
  - 2 D#4
  - 3 G#4
  - 4 E4
  - 5 B3
  - 6 G#3
  - 7 F#3
  - 8 E3
  - 9 D3
  - 10 B2
- Added `scientific_pitch_for_value()` and `octave_band_for_value()`.
- Added `note_registers` and `notes_with_register` to every Explorer row.
- Added register metadata to `display_top_voice`.
- Added before/after register metadata to row/control-impact previews.
- Expanded payload validation so `note_registers` and `notes_with_register` must match played strings.

Shared UI music rules:
- Added `DEFAULT_E9_OPEN_STRING_PITCH_VALUES`.
- Added `scientificPitchForValue()`, `octaveBandForPitchValue()`, and `pitchRegisterDetail()`.
- Extended `resolveE9Note()` to return open/final absolute pitch values, scientific names, octave bands, and final register detail.

Explorer UI:
- Added `Pitch register` control:
  - Off
  - Scientific
  - Octave band
- Off preserves existing pitch-class display.
- Scientific shows register details such as `C5`.
- Octave band shows player-facing labels such as `C · upper`.
- Detail/card views can show register; SVG marker labels remain uncluttered.
- Single-note finder and voicing identifier now show register in detail panels when enabled.

Tests:
- Added backend assertions for the standard E9 register map.
- Added payload-schema checks for register metadata.
- Added shared JS rules checks for string/fret/control scientific pitch examples:
  - string 5 fret 3 open = D4
  - string 5 fret 3 with A = E4
  - string 3 fret 3 open = B4
  - string 3 fret 3 with B = C5
- Added UI VM checks for Off, Scientific, and Octave band mode behavior.

## Smoke Target

- Target type: local
- Result type: attempted browser smoke; blocked by in-app browser attach timeout
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-octave-register-local-20260627`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-octave-register-local-20260627`
- Exact URL the user should use: not ready for user smoke until protected-preview smoke runs from a committed/restarted runtime
- Auth required: no for local
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `801414c` before this task's commit
- Version endpoint: not checked for local Explorer static smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: git HEAD and local filesystem
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant for this Explorer page smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant for this Explorer page smoke
- Who should test this URL: Codex after commit/restart, then the user after protected-preview smoke
- Do not test these URLs: production URLs as proof of this local change
- Known caveats: in-app browser automation timed out waiting for webview attach twice; API/static checks and UI VM tests passed, but browser smoke is not a pass.

## Tests And Checks

Passed:
- `curl -sS -I http://127.0.0.1:8770/ui/e9-fretboard-explorer.html | head`
- `.venv/bin/python -m py_compile pocketsteel/e9_copedents.py pocketsteel/fretboard_explorer.py`
- `node --check ui/e9-music-rules.js`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py -q`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`

Full suite result:
- `864 passed in 28.16s`

Browser smoke:
- Attempted through the in-app browser plugin.
- Blocked: `Timed out waiting for the Browser webview to attach for this browser-use page`.
- This is not a browser-smoke pass.

## Integration Notes

- The backend/static payload contract now includes `note_registers` and `notes_with_register` on Explorer rows.
- Existing pitch-class fields remain present and should continue to drive chord/voicing names.
- UI marker labels intentionally do not include octave suffixes.
- The generated static data file grew from about 30 MB to about 51 MB because every bundled key/copedent row now carries per-string register metadata.
- Lane 06 can refine copy/layout for the pitch-register control if needed, but no UI lane is required for the basic control to work.
- Lane 15 should run protected-preview smoke after the scoped commit and runtime restart.

## Risk Assessment

Risk: medium.

Reasons:
- The model/schema change is deterministic and test-covered, but the static Explorer data bundle grew significantly.
- Browser smoke could not be completed because the in-app browser automation could not attach.
- The worktree contains many unrelated parked files; exact-path staging is required.

Rollback:
- Revert the scoped commit containing the listed files.
- No corpus/vector/private/deployment state was changed.

## Human Decision Needed

No for backend/UI contract implementation.

Yes before future work if adding Peterson/StroboPlus-specific octave-label mapping; that requires verified device/manual semantics.

## Safe-To-Stage Exact File List

- `pocketsteel/e9_copedents.py`
- `pocketsteel/fretboard_explorer.py`
- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1843-05-explorer-octave-awareness.md`

## Files That Must Not Be Staged

All unrelated dirty/parked files, especially:
- corpus/private/source files and generated corpus artifacts
- Chroma/vector/embedding artifacts
- deployment/auth/DNS/secrets files
- raw visual/design assets
- unrelated docs, source registry files, and scripts already dirty before this task

Do not stage via `git add .`.

## Recommended Next Lane

1. Lane 01 Repo Steward: exact-path commit of the safe-to-stage files if staged diff remains scoped.
2. Lane 12: protected-preview restart and smoke for the committed Explorer URL.
3. Lane 15: protected-preview QA smoke for Off/Scientific/Octave band modes, Single-note finder, Voicing Identifier, Chord/Voicing Finder, and no `[object Object]`.

## Commit Readiness

Safe to commit if exact-path staged diff contains only the safe-to-stage files above and `git diff --cached --check` passes.

Suggested commit message:

`feat: add explorer pitch register display`
