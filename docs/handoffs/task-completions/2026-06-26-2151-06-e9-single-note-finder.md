# 2026-06-26 21:51 - Lane 06 - E9 Single-note Finder

## Task summary

Implemented the first E9 Fretboard Explorer `Single-note finder` mode. The new mode is deterministic UI/copedent logic only; it does not use retrieval, source cards, backend routing, corpus data, Chroma, embeddings, scraping, auth, DNS, or deployment.

Completed:

- Added `Single-note finder` to the Explorer mode selector.
- Hid string-group, path-family, harmony/view, and pedal/lever impact preview controls while note mode is active.
- Added control-state chips for Open, A pedal, B pedal, A+B, B+C, E-raise, and E-lower.
- Added target-note chips that respect the existing key/scale/notation context.
- Added a fret/string note grid with target-result highlighting, affected-string indication, hover preview, and click/tap pinning.
- Added a detail panel showing string, fret, active controls, open string, open/no-control note at fret, final note, notation-context value, and whether the selected controls changed the string.
- Verified required examples:
  - String 3, fret 3, Open: open note B, final note B.
  - String 3, fret 3, B pedal: open note B, final note C.
  - String 5, fret 3, A pedal: open note D, final note E.
- Bumped the Explorer JS cache-bust to `single-note-finder-20260626`.

Intentionally not changed:

- Existing `Single grip` behavior.
- Existing `Harmonized scale path` behavior.
- Backend Explorer data generation.
- Fretboard SVG/background geometry.
- Corpus, scraping, Chroma/vector stores, embeddings, auth, DNS, deployment, source cards, or provenance files.

## Files changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-2151-06-e9-single-note-finder.md`

## Tests and checks

Passed:

```bash
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
git diff --check
```

Results:

- `tests/test_frontend_answer_ui.py`: 23 passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed.
- `tests/test_fretboard_explorer.py`: 38 passed.
- `git diff --check`: passed.

Full pytest was not run because this was a scoped UI slice and the requested checks were focused frontend/Explorer checks.

## Local browser smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=single-note-finder-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=single-note-finder-local`
- Exact URL the user should use: pending protected-preview restart/smoke
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `d758be8` before commit
- Version endpoint: not checked for local UI-only smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local working tree plus cache-busted URL
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not required for this Explorer-specific local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer-specific local smoke
- Who should test this URL: Codex locally; the user after Lane 12 protected-preview smoke
- Do not test these URLs: protected-preview URL until Lane 12 refreshes/restarts the runtime
- Known caveats: in-app browser automation reached the local URL but timed out on scripted select interaction; the completed browser smoke used the bundled Playwright package with the system Chrome channel.

Browser smoke verified:

- `Single-note finder` mode can be selected.
- Note finder section becomes visible.
- String group and harmony/view controls are hidden in note mode.
- String 3, fret 3 Open shows B as both open/no-control and final note.
- Selecting target B marks string 3, fret 3 as a result.
- B pedal changes string 3, fret 3 from B to C.
- A pedal changes string 5, fret 3 from D to E.
- No `[object Object]` appeared.

## Integration notes

- Note mode intentionally bypasses the position-card/SVG grip pipeline because it is a single-note lookup surface, not a row/position browser.
- The existing notation mode selector is reused for the note detail context value.
- The existing visible fret range selector is reused for the note grid and result list.
- The Explorer JS query string must be deployed/refreshed as `e9-fretboard-explorer.js?v=single-note-finder-20260626`.

## Risk assessment

Risk: medium-low.

Reasoning:

- The change is isolated to Explorer frontend code and focused tests.
- Existing single-grip, harmonized-path, fretboard renderer, and backend Explorer tests still pass.
- Browser automation was validated locally with Chrome, but protected-preview smoke still needs a Lane 12 refresh/restart to prove the committed runtime.

Rollback:

- Revert the scoped commit that changes `ui/e9-fretboard-explorer.html`, `ui/e9-fretboard-explorer.js`, and `tests/test_frontend_answer_ui.py`.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-2151-06-e9-single-note-finder.md`

## Files that must not be staged

Any unrelated dirty or untracked files, especially:

- Corpus/private/source-inbox/provenance files.
- Chroma/vector stores or embedding outputs.
- Auth, DNS, deployment, Cloudflare, `.wrangler`, or secret files.
- Landing/sign/brand assets.
- Existing parked docs and generated reports not listed in the safe-to-stage list.

## Recommended next lane

Lane 12 protected-preview restart/smoke after this scoped UI commit.

## Commit readiness

Safe to commit after exact-path staging and cached-diff review.

## Suggested next step

Lane 12 prompt:

> Run protected-preview smoke for the E9 Fretboard Explorer single-note finder after commit `<commit>`. Use `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=single-note-finder-20260626`. Verify the page is serving the expected HEAD, select `Single-note finder`, confirm string 3 fret 3 Open is B, string 3 fret 3 with B pedal is C, string 5 fret 3 with A pedal is E, existing Single grip and Harmonized scale path modes still work, and no `[object Object]` appears.
