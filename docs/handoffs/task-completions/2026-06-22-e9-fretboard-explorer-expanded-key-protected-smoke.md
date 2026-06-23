# 2026-06-22 - Lane 15 - E9 Fretboard Explorer Expanded-Key Protected Smoke

## Task Summary

Requested: run full protected-preview browser smoke for the expanded-key E9 Fretboard Explorer UI after Lane 06 exposed expanded validated keys and Lane 12 refreshed protected-preview cache-busts.

Completed:

- Read required governance files and E9 Explorer handoffs.
- Ran the requested JS syntax checks, focused frontend/fretboard tests, focused Explorer tests, and full pytest.
- Ran authenticated protected-preview browser smoke against the exact requested URL.
- Verified expanded key selector, key-aware display spelling, mode-aware filters, core/advanced grouping, `5-7-8` advanced E-lower pocket behavior, marker tooltip/detail behavior, protected SVG asset route, console error state, and mobile/narrow viewport behavior.

Intentionally not changed:

- No app/runtime/UI implementation files were modified.
- No corpus, Chroma/vector stores, embeddings, scraper output, deployment/auth/DNS/private source data, public assets, brand assets, raw design assets, or unrelated dirty/untracked files were modified.

## Pass/Warn/Fail

Pass with one non-blocking mobile usability caveat.

The protected-preview expanded-key Explorer UI is ready for the next product slice. The narrow mobile viewport is usable with no document-level horizontal overflow, but the rendered fretboard is very tall and requires significant vertical scrolling.

## Current Branch

`feature/answer-api`

## Current HEAD

`7fc3846 fix: refresh e9 explorer expanded key cache-bust`

## Commits / Version Under Test

- Expanded-key UI commit: `d4b26ad fix: expose expanded e9 explorer keys`
- Protected-preview cache-bust refresh: `7fc3846 fix: refresh e9 explorer expanded key cache-bust`
- Local protected-preview backend `/api/version` result: `{"git_sha": "7fc3846", "git_branch": "feature/answer-api", "server_started_at": "2026-06-23T13:31:36.041115+00:00", "python_module": "pocketsteel.api", "retrieval_mode": "hybrid_private_first", "auth_provider": "cloudflare_access"}`

Direct in-app browser navigation to `https://app.steelguitarrag.com/api/version` was blocked by the browser client with `net::ERR_BLOCKED_BY_CLIENT`; version was verified through the protected-preview local backend on `127.0.0.1:8770`.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-keys-20260622`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-keys-20260622`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-expanded-keys-20260622`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; browser loaded the Explorer page, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `7fc3846`
- Version endpoint: `/api/version`
- Version endpoint result: local protected-preview backend reported `7fc3846`
- If version endpoint missing, how version is inferred: not missing locally; protected direct browser navigation to `/api/version` was blocked by browser client
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this Explorer route smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but outside this task scope
- Who should test this URL: Lane 15 and the user
- Do not test these URLs: stale Explorer URLs from earlier cache-busts
- Known caveats: mobile viewport is vertically long; direct in-browser `/api/version` navigation was blocked by the browser client, while local backend version check passed

## Auth Result

Pass.

The exact protected URL loaded as `E9 Fretboard Explorer - Steel Guitar RAG` and displayed the Explorer page content. It did not display the Cloudflare Access login page.

## Refreshed Asset / Cache-Bust Result

Pass.

The loaded Explorer page used the refreshed expanded-key script URLs:

- `pedal-steel-fretboard.js?v=e9-explorer-expanded-keys-20260622`
- `e9-fretboard-explorer-data.js?v=e9-explorer-expanded-keys-20260622`
- `e9-fretboard-explorer.js?v=e9-explorer-expanded-keys-20260622`

The protected SVG asset route also passed:

- `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=e9-explorer-expanded-keys-20260622`
- Result: loaded as an SVG document, not an Access login page.

## Browser Smoke Results

Pass.

Verified:

- Page title and heading identify the E9 Fretboard Explorer.
- Page copy says the surface uses validated Explorer rows and does not use corpus/RAG-generated fretboard positions.
- Key selector rendered expanded validated keys: `G`, `C`, `D`, `F`, `Bb`, `Eb`.
- `Showing validated positions` appeared.
- `N validated rows` primary copy did not appear.
- No `[object Object]`.
- No `E-lower+E-lower`.
- No console errors were reported by the page. Repeated automation reloads produced non-blocking Statsig request-frequency warnings, not Explorer runtime errors.

## Expanded Key Results

Pass.

Protected-preview browser state by key:

| State | Scale Notes | Rows | First Visible Row |
| --- | --- | ---: | --- |
| G major default | `G A B C D E F#` | 34 | `3 I Core grip · 3: B; 4: G; 5: D` |
| G natural minor | `G A Bb C D Eb F` | 32 | `1 i · B+C Core grip · 3: Bb; 4: G; 5: D` |
| C major | `C D E F G A B` | 33 | `8 I Core grip · 3: E; 4: C; 5: G` |
| D major | `D E F# G A B C#` | 34 | `0 iii · B+C Core grip · 3: A; 4: F#; 5: C#` |
| F major | `F G A Bb C D E` | 34 | `1 I Core grip · 3: A; 4: F; 5: C` |
| Bb major | `Bb C D Eb F G A` | 34 | `6 I Core grip · 3: D; 4: Bb; 5: F` |
| Eb major | `Eb F G Ab Bb C D` | 34 | `1 iii · B+C Core grip · 3: Bb; 4: G; 5: D` |
| C natural minor | `C D Eb F G Ab Bb` | 32 | `6 i · B+C Core grip · 3: Eb; 4: C; 5: G` |

## Display Spelling Results

Pass.

- G behavior remains unchanged for default major and natural minor.
- C/D/F/Bb/Eb major display spellings are learner-facing and key-aware.
- C natural minor displays flats: `C D Eb F G Ab Bb`.
- Bad C/G natural-minor sharp spellings such as `G A A# C D D# F` did not appear.
- E9 mechanical labels remain visible where appropriate, including sharp-oriented strings and `Eb/D#` in E-lower details.

## Mode-Aware Filter Results

Pass.

Verified:

- Major 2-string mode shows only `2-string groups`: `3-5`, `5-6`, `6-10`, `4-6`, `3-4`.
- 3-string mode shows valid core and advanced groups.
- Core grips remain separated: `3-4-5`, `4-5-6`, `5-6-8`, `6-8-10`.
- Advanced swaps remain separated: `5-6-7`, `6-7-10`, `5-7-8`.
- Natural minor disables unavailable 2-string mode and keeps a nonblank 3-string state.
- Attempting to select unavailable C natural-minor 2-string mode was rejected by the control; the UI stayed on valid 3-string rows with `C D Eb F G Ab Bb`.

## 5-7-8 / E-Lower Result

Pass.

Selecting `C major` plus `5-7-8` showed one advanced E-lower pocket row:

- `13 I · E-lower Advanced swap - E-lower pocket · 5: C; 7: G; 8: E`

The selected detail showed:

- `Advanced swap - E-lower pocket`
- `Pedals / levers E-lower`
- `Per-string changes 8: controls: E-lower; from: E; to: Eb/D#`

`5-7-8` remained under `Advanced swaps`, not core grips.

## Tooltip / Detail Result

Pass.

Clicking the SVG marker for the filtered `C major 5-7-8` row:

- selected the matching row button;
- kept the detail panel on the matching row;
- displayed tooltip text for `C on strings 5-7-8 at fret 13`;
- preserved displayed notes and E-lower controls.

## Partial Voicing / Per-String Detail Result

Pass.

Partial diminished / partial m7b5 warning text remained present in the page/details. Per-string pedal/lever details remained visible in selected details, including B/C examples and E-lower string-8-only detail.

## Mobile / Narrow Viewport Result

Pass with caveat.

Viewport tested: `390x844`.

Observed:

- Controls visible.
- Key selector still showed `G`, `C`, `D`, `F`, `Bb`, `Eb`.
- `Bb major` displayed `Bb C D Eb F G A`.
- Fretboard present.
- No document-level horizontal overflow: `documentElement.scrollWidth` and `body.scrollWidth` were both `390`.
- No `[object Object]`.
- Dense SVG row text labels were not present.

Caveat:

- The fretboard area measured about `4531px` tall in the narrow viewport. It remains scrollable and does not overflow horizontally, but mobile ergonomics would benefit from a future UI tightening pass.

## Console Errors

Pass.

Explorer page console errors: none.

Non-blocking note: repeated browser automation reloads emitted Statsig request-frequency warnings. These were warnings, not console errors, and did not affect Explorer behavior.

## Automated Tests Run

Passed:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/pedal-steel-fretboard.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
curl -sS -i http://127.0.0.1:8770/api/version | head -20 || true
git diff --check
```

Results:

- `tests/test_frontend_answer_ui.py -q`: `23 passed`
- `tests/test_pedal_steel_fretboard_ui.py -q`: `31 passed`
- `tests/test_fretboard_explorer.py -q`: `21 passed`
- Full pytest: `801 passed`
- JS syntax checks: passed
- `git diff --check`: passed

## Files Changed

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-expanded-key-protected-smoke.md`

No files deleted. No generated artifacts created.

## Issues Found

No blockers.

Non-blocking issues/caveats:

- Direct in-app browser navigation to protected `/api/version` was blocked by the browser client, so version was verified through the local protected-preview backend on `127.0.0.1:8770`.
- Narrow mobile viewport is functionally usable but vertically tall.

## Blockers

None.

## Risks

Risk: low.

The smoke verified the protected-preview URL, cache-busted scripts, expanded keys, display spellings, filters, detail/tooltip behavior, static asset route, and automated tests. No runtime code was changed in this QA lane.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-expanded-key-protected-smoke.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files.
- `public/`
- `ui/brand/`
- `Neon Sign/`
- `source-inbox/`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- scraper output
- deployment/auth/DNS/secrets files
- private source data
- raw design assets
- generated/private reports

## Recommended Next Lane

Lane 05 Backend / RAG Integration.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Exact next prompt:

```text
Lane 05: Add the E9 Fretboard Explorer explanation panel using deterministic Explorer rows only. Do not ingest corpus guidance, do not use RAG as musical truth, and do not modify Chroma/vector stores. Use the existing validated row payloads to explain scale degree, grip, fret, pedals/levers, per-string changes, partial-voicing warnings, and why core vs advanced groups differ.
```
