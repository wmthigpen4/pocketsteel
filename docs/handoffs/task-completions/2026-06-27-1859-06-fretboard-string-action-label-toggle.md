# 2026-06-27 18:59 - Lane 06 Fretboard String/Action Label Toggle

## Task Summary

Requested: add optional compact string/action labels directly on E9 Fretboard Explorer marker bubbles, controlled by a nearby toggle. Completed as a scoped UI/rendering slice.

What changed:

- Added a `String labels` toggle in the Explorer fretboard control panel.
- Default state is off, so marker bubbles remain clean unless the user asks for detail.
- When on, the SVG renderer can draw compact labels inside/on marker bubbles.
- Added compact musician shorthand mapping:
  - A/B/C pedals -> `A`/`B`/`C`
  - E-raise/F lever -> `F`
  - E-lower/E lever -> `E`
  - D-lower/D half-stop -> `D`
  - G lever/G raise/lower -> `G`
  - B-to-Bb/LKV/vertical -> `V`
- Unchanged strings render as the string number only.
- Explorer-generated positions now pass marker labels separately via `string_action_labels`; learner-facing per-string change details remain clean.
- Dense fretboard views automatically use selected/hover/focus label display mode so labels do not fill every marker in crowded maps.

Intentionally not changed:

- No backend rules, music validation, corpus, Chroma, embeddings, auth, DNS, deployment, or asset changes.
- No fretboard geometry, notation-mode behavior, card synchronization logic, or route changes.

## Label Behavior

Valid rendered examples include:

- `3`
- `4`
- `5`
- `3B`
- `4C`
- `5C`
- `4F`
- `8E`
- `2D`
- `6G`
- `5V`

Invalid marker labels are guarded by tests:

- `S3`
- `String 3`
- `3 B`
- `E-raise`
- `E-lower`
- `E↑`
- `E↓`
- `B pedal`
- `C pedal`

## Files Changed

- `ui/pedal-steel-fretboard.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1859-06-fretboard-string-action-label-toggle.md`

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/answer-client.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py -q` - 4 passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - 39 passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 24 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 36 passed
- `git diff --check`

Skipped:

- `node --check ui/e9-music-rules.js`: file not changed.
- API contract tests: backend/API contract not changed.

## Local Browser Smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=string-action-labels-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=string-action-labels-local`
- Exact URL the user should use: pending protected-preview cache-busted URL after Lane 12/runtime refresh
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `460eeeb` at smoke time
- Version endpoint: not checked for local static smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local same-origin server serving current worktree files
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this scoped Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this scoped Explorer smoke
- Who should test this URL: Codex locally; the user after protected-preview refresh
- Do not test these URLs: API fallback as browser proof
- Known caveats: local browser smoke does not prove protected-preview cache/runtime freshness

Local smoke result:

- Page loaded.
- `String labels` toggle was visible near the fretboard.
- Default/off state rendered no `data-string-action-label` SVG text.
- Voicing Identifier with strings 3-4-5 and B+C pedals rendered compact labels `3B`, `4C`, `5C` when toggled on.
- Toggling off removed the marker-label overlay.
- Invalid marker-label attributes were not present.
- No `[object Object]`.
- No browser console errors were recorded.
- No page-level horizontal overflow was detected.
- Per-string detail text did not leak `marker_label` or `string_action_labels`.

Protected-preview smoke:

- Run after the implementation commit using `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=string-action-labels-8b9ae59`.
- Cloudflare Access login result: succeeded / existing authenticated session was accepted.
- Explorer page loaded and showed the `String labels` toggle.
- Default/off state rendered no marker-label SVG text.
- Voicing Identifier with strings 3-4-5 and B+C pedals rendered compact labels `3B`, `4C`, `5C` when toggled on.
- Toggling off removed the marker-label overlay.
- Invalid marker labels were not present.
- No `[object Object]`.
- No browser console errors were recorded.
- No page-level horizontal overflow was detected.
- Per-string detail text did not leak `marker_label` or `string_action_labels`.
- Root `/` redirected to `/ui/steel-guitar-rag-mock.html?v=string-action-labels-8b9ae59`.
- `/ui/steel-guitar-rag-mock.html?v=string-action-labels-8b9ae59` loaded.
- `/api/version` returned `{"git_sha": "a6abc61", "git_branch": "feature/answer-api", ...}`.
- Caveat: protected-preview behavior passed for the cache-busted static Explorer file, but `/api/version` did not match the implementation commit. Treat this as a static UI smoke pass with runtime freshness warning. Lane 12 should refresh/restart protected preview before a clean runtime-version pass.

## Risk Assessment

Risk: medium-low.

Why:

- The renderer now accepts optional marker-label metadata and can derive labels from per-string change controls.
- Dense views switch to selected/hover/focus label visibility mode, but visual readability still needs protected-preview/user smoke.
- Several scoped files had unrelated parked changes before this task; commit staging must use exact paths/hunks only.

Rollback notes:

- Revert the scoped commit or remove the `showStringActionLabels` option, Explorer toggle markup/listener, and focused tests.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

Exact scoped files/hunks only:

- `ui/pedal-steel-fretboard.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1859-06-fretboard-string-action-label-toggle.md`

## Files That Must Not Be Staged

- Unrelated dirty docs, corpus metadata, RAG scripts, source-inbox files, brand assets, public assets, private/generated files, `Neon Sign/`, deployment/auth/DNS/secrets, Chroma/vector/embedding data, and any other untracked parked files.

## Recommended Next Lane

Lane 01 exact-path commit, then Lane 12 protected-preview smoke for the Explorer URL.

## Commit Readiness

Safe to commit after exact-path/hunk staged diff review passes.

## Suggested Next Step

Lane 12 prompt after commit:

Run protected-preview browser smoke for the E9 Fretboard Explorer string/action label toggle using `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=<commit-or-slice-cachebuster>`. Verify the toggle is visible near the fretboard, defaults off, renders compact labels like `3B`, `4C`, `5C`, `4F`, and `8E` when on, removes them when off, has no `S3` or internal `E-raise`/`E-lower` marker labels, preserves full detail text, and records console/errors plus `/api/version` freshness.
