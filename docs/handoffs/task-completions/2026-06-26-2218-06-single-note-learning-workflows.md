# 2026-06-26 22:18 - Lane 06 - Single-Note Learning Workflows

## Status

Pass with caveat: local browser smoke passed. Protected-preview smoke was not run in this Lane 06 slice because no protected-preview restart/deploy was performed.

## Task Summary

Implemented the fast-follow E9 Fretboard Explorer Single-note Finder learning workflow on top of the committed deterministic Explorer data. This stayed in the Explorer frontend and did not change backend routing, Explorer generation, tab generation, corpus, Chroma/vector stores, embeddings, scraping, auth, DNS, deployment config, source/provenance records, or visual assets.

Completed:

- Added Single-note Finder workflow tabs:
  - Find all
  - Reverse lookup
  - Pedal changes
  - Build grip
  - Drill
  - Event sync
- Added string filtering for note workflows.
- Kept active note targets and notation modes connected to the displayed labels/details.
- Added learner-facing affected-control rows for pedal/lever changes.
- Added grip-building cards based on validated Explorer rows instead of frontend-generated fake positions.
- Added simple drill feedback.
- Added deterministic event-sync demo buttons for the current safe example states.
- Updated Explorer script cache-bust to load the new UI slice.
- Added focused frontend regression coverage.

Intentionally not changed:

- No backend tab/event payload contract was invented.
- No arbitrary song tab or generated tab feature was added.
- No protected-preview restart/deploy was performed.
- No integration-status refresh was committed in this implementation commit.

## Files Changed

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-2218-06-single-note-learning-workflows.md`

Deleted files: none.

Generated artifacts: none.

## UI Behavior Added

### Find All

Shows matching note locations for the selected note target, current active control state, current fret range, and selected string filter.

### Reverse Lookup

Lets the user inspect note locations by string filter and note target without changing fretboard geometry or backend data.

### Pedal Changes

Shows affected strings, before note, after note, and interval effect for the active control state. Example verified locally:

- B pedal at fret 3 shows affected strings 3 and 6.
- String 3 G# changes to A.

### Build Grip

Shows validated grip candidates from the existing Explorer rows. Selecting a card focuses the related notes on the fretboard.

### Drill

Lets the user select the requested target location and shows compact `Correct` / `Try again` feedback. This is a frontend learning interaction only.

### Event Sync

Adds a deterministic, narrow event-sync demo using known safe examples:

- String 3, fret 3, Open = B
- String 3, fret 3, B pedal = C
- String 5, fret 3, A pedal = E

This is intentionally not a general tab/event engine UI.

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
  - `23 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
  - `34 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - `38 passed`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - `25 passed`
- `git diff --check`

Skipped:

- Full `pytest`: not run for this focused UI slice because the requested checks were frontend/Explorer focused and the repo has substantial unrelated parked work.
- Protected-preview smoke: not run because this lane did not restart/deploy the protected preview.

## Local Browser Smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=single-note-learning-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=single-note-learning-local`
- Exact URL the user should use: pending Lane 12 protected-preview refresh/smoke
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `88678f2` at local smoke start
- Version endpoint: not checked for local static smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree and script cache-bust
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer smoke
- Who should test this URL: Codex locally; the user after Lane 12 protected-preview refresh
- Do not test these URLs: stale Explorer URLs without the new cache-bust
- Known caveats: in-app browser automation timed out, so standalone local Playwright smoke was used. One generic local 404 console message was observed, but no app JS error was captured and all functional assertions passed.

Local smoke verified:

- Single-note Finder mode loads.
- Workflow tabs render.
- String 3, fret 3, Open shows B.
- String 3, fret 3, B pedal shows C.
- String 5, fret 3, A pedal shows E.
- Pedal Changes shows B pedal affected strings.
- Reverse Lookup shows results.
- Build Grip shows cards.
- Drill shows both `Try again` and `Correct`.
- Event Sync focuses string 3, fret 3, C.
- No `[object Object]` appears.

## Integration Notes

- The Explorer frontend still consumes existing deterministic Explorer data and existing fretboard rendering.
- No API, backend schema, or data-generation contract changed.
- Event sync is currently a narrow deterministic UI demo. A future slice should connect it to backend tab/event payloads if Lane 05 exposes a structured event list.
- The script cache-bust changed to `single-note-learning-20260626` in `ui/e9-fretboard-explorer.html`.

## Risk Assessment

Risk: medium.

Why:

- The UI change is sizeable within `ui/e9-fretboard-explorer.js`, but it is isolated to Explorer frontend behavior and covered by focused tests plus local browser smoke.
- Protected-preview behavior still depends on Lane 12 refreshing the runtime/cache-busted URL.

Rollback:

- Revert the scoped commit containing `ui/e9-fretboard-explorer.js`, `ui/e9-fretboard-explorer.html`, and `tests/test_frontend_answer_ui.py`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-2218-06-single-note-learning-workflows.md`

## Files That Must Not Be Staged

All unrelated parked work, especially:

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
- all untracked corpus/private/source/design/deploy/generated files

## Recommended Next Lane

Lane 12 protected-preview refresh/smoke, then Lane 15 focused browser QA.

Suggested next prompt:

```text
Lane 12: Refresh protected preview for commit <commit>, then smoke:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=single-note-learning-<commit>

Verify Single-note Finder workflows: Find all, Reverse lookup, Pedal changes, Build grip, Drill, and Event sync. Confirm string 3 fret 3 Open = B, B pedal = C, string 5 fret 3 A pedal = E, no [object Object], and no app console errors.
```

## Commit Readiness

Safe to commit after exact-path staging and cached-diff review.
