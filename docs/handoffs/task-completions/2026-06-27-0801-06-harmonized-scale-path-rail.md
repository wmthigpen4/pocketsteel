# 2026-06-27 08:01 - Lane 06 Harmonized Scale Path Rail

## Task Summary

Requested: improve Harmonized scale path visualization in the E9 Fretboard Explorer so a scale path reads as a linear sequence instead of stacked full chord grips on the fretboard.

Completed:
- Added a Harmonized Scale Path Rail in path mode.
- Added selected-step state with Previous / Next controls.
- Added display modes:
  - Step
  - Ghost all
  - Compare same fret
- Defaulted path display to Step mode so only one full grip is mounted on the fretboard.
- Added same-fret comparison rows for shared-fret pockets such as G/Am at fret 3 and D/Em at fret 10.
- Kept the fretboard central while preventing unreadable overlapping full stacks.
- Updated tests for rail rendering, selected-step behavior, Step/Ghost/Compare modes, same-fret pockets, and notation integration.

Intentionally not changed:
- Backend Explorer data generation.
- Fretboard pitch validation.
- Single grip mode.
- Single-note finder mode.
- Copedent chart/glossary behavior.
- Corpus, Chroma, embeddings, scraping, auth, DNS, deployment, or protected-preview runtime configuration.

## Files Changed

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-0801-06-harmonized-scale-path-rail.md`

Deleted files: none.

Generated artifacts: none.

## Features Implemented

### Scale Path Rail

In Harmonized scale path mode, the active results area now renders a compact rail of the selected path in musical order. For G major / Low path, the rail shows all eight steps:

- G - G, fret 3, strings 6-8-10, Open
- A - Am, fret 3, strings 6-7-10, With A+B
- B - Bm, fret 5, strings 6-7-10, With A+B
- C - C, fret 8, strings 6-8-10, Open
- D - D, fret 10, strings 6-8-10, Open
- E - Em, fret 10, strings 6-7-10, With A+B
- F# - F# half-diminished, fret 13, strings 6-8-10, With E-raise
- G - G, fret 15, strings 6-8-10, Open

### Selected-Step Fretboard Rendering

Step mode renders only the selected full grip on the SVG fretboard. This prevents fret 3 and fret 10 shared-fret path steps from covering each other.

### Path Display Modes

- Step: one selected full grip.
- Ghost all: selected full grip plus compact one-string markers for the other steps.
- Compare same fret: selected full grip plus compact markers for same-fret alternatives and a comparison panel.

### Same-Fret Pocket Teaching

The rail includes concise copy: "Some scale degrees share the same fret but use different strings or pedals." Compare mode shows the rows sharing the selected fret.

### Notation Integration

The rail labels update with the existing notation selector. Roman mode shows the expected sequence such as `I`, `ii`, `iii`, `IV`, `V`, `vi`, `vii°`, `I`.

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
```

Results:

- `git diff --check`: passed
- `node --check ui/e9-fretboard-explorer.js`: passed
- `node --check ui/e9-fretboard-explorer-data.js`: passed
- `node --check ui/answer-client.js`: passed
- `node --check ui/pedal-steel-fretboard.js`: passed
- `tests/test_frontend_answer_ui.py`: 23 passed
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed
- `tests/test_fretboard_explorer.py`: 38 passed

## Local Browser Smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=harmonized-path-rail-local-step-check2`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=harmonized-path-rail-local-step-check2`
- Exact URL the user should use: protected-preview URL should be supplied by Lane 12 after runtime refresh; local URL above was used for implementation smoke
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `f23559f` at task start; final HEAD depends on commit step
- Version endpoint: not checked for local UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local file changes and cache-busted URL
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not part of this UI slice
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but not part of this smoke
- Who should test this URL: Codex locally; the user should test a Lane 12 protected-preview cache-busted URL after refresh
- Do not test these URLs: unversioned protected-preview Explorer URL for this slice
- Known caveats: local smoke does not prove protected-preview runtime freshness

Local smoke verified:
- Page loads.
- Harmonized scale path mode shows a Scale path rail.
- G major low path shows 8 ordered steps.
- Step mode is default.
- Selecting G / step 1 mounts one full fretboard grip: fret 3, strings 6-8-10, Open.
- Selecting Am / step 2 mounts one full fretboard grip: fret 3, strings 6-7-10, A+B.
- Previous / Next moves through steps and keeps one mounted grip in Step mode.
- Ghost all mode mounts 8 markers: 1 full selected grip and 7 compact markers.
- Compare same fret mode shows fret 3 contains G and Am.
- Compare same fret mode also covers same-fret behavior for fret 10 in automated tests.
- Roman notation updates the path rail labels.
- No `[object Object]` appeared.

## Protected-Preview Smoke

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=harmonized-path-rail-0396390`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=harmonized-path-rail-0396390`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=harmonized-path-rail-0396390`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded via existing authenticated browser session
- Local backend URL: protected-preview tunnel to local runtime
- Expected backend port: 8770
- Expected git HEAD: final committed UI slice; `/api/version` remained stale during this smoke
- Version endpoint: `https://app.steelguitarrag.com/api/version`
- Version endpoint result: reported `4040a47` on branch `feature/answer-api`
- If version endpoint missing, how version is inferred: not applicable; endpoint was present but stale relative to this commit
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes, root redirects to `/ui/steel-guitar-rag-mock.html`
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both Codex and the user
- Do not test these URLs: unversioned Explorer URL for this slice
- Known caveats: `/api/version` still reports old backend process HEAD `4040a47`; the static Explorer HTML served the fresh script cache-bust and the UI behavior was verified, but Lane 12 should restart/verify runtime freshness if a HEAD match is required.

Protected-preview browser smoke verified:
- Explorer page loaded after Cloudflare Access.
- `e9-fretboard-explorer.js?v=harmonized-path-rail-20260627` was present in the page.
- Harmonized scale path mode rendered the Scale path rail.
- Step mode was selected by default.
- 8 path steps rendered.
- Step mode mounted one selected fretboard highlight.
- No `[object Object]` appeared.
- Browser console had no captured error logs.

Root behavior:
- `https://app.steelguitarrag.com/` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Root/app page loaded and still showed the app entry controls.

## Integration Notes

- The UI continues to consume existing Explorer rows; no new backend fields are required.
- Path mode now passes `pathRowsForFretboard(currentRows)` to the existing fretboard renderer.
- Step mode intentionally hides non-selected full grips from the SVG to avoid shared-fret collisions.
- Ghost/Compare compact non-selected path rows to one-string markers so the selected full grip remains readable.
- Existing row cards remain available below the rail; the rail is the primary path navigation surface.

## Risk Assessment

Risk: medium-low.

Reason:
- The change is scoped to Explorer path-mode presentation and tests.
- Existing Single grip, notation, copedent, glossary, and fretboard tests still pass.
- The browser smoke covered the primary interaction states.

Rollback notes:
- Revert the three scoped UI/test files if the path rail behavior needs to be removed:
  - `ui/e9-fretboard-explorer.js`
  - `ui/e9-fretboard-explorer.html`
  - `tests/test_frontend_answer_ui.py`

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-0801-06-harmonized-scale-path-rail.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files, including:

- `README.md`
- `corpus_metadata/**`
- `docs/**` other than the handoff above
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- `corpus-private/**`
- `corpus-v2/**`
- Chroma/vector stores
- embeddings
- deployment/auth/DNS/private-source files

## Recommended Next Lane

Lane 01 exact-path commit, then Lane 12 protected-preview refresh/smoke.

## Commit Readiness

Committed.

Commit:

- Created by this task; see final report or `git log -1 --oneline` for the final hash.

## Suggested Next Step

Lane 01:

```text
Stage and commit only the scoped Harmonized Scale Path Rail files from docs/handoffs/task-completions/2026-06-27-0801-06-harmonized-scale-path-rail.md, then hand off to Lane 12 for protected-preview smoke.
```
