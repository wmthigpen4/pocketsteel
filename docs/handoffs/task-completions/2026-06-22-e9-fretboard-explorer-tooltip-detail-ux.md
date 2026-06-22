# 2026-06-22 - Lane 06 - E9 Fretboard Explorer Tooltip Detail UX

## Task Summary

Requested: fix latest E9 Fretboard Explorer user-smoke usability issues without touching backend routing, corpus, Chroma, embeddings, scraping, deployment, auth, DNS, assets, or unrelated dirty files.

Completed:

- Added learner-facing marker tooltips/accessibility labels for fretboard markers.
- Replaced the verbose full bottom card grid with compact selectable row buttons plus one selected-position detail panel.
- Deduped combined pedal/lever labels so labels such as `E-lower+E-lower` no longer render.
- Replaced the primary `N validated rows` count with `Showing validated positions`.
- Preserved validated Explorer data wording and did not imply RAG/corpus generated the deterministic rows.
- Preserved key-aware G natural minor spelling (`G A Bb C D Eb F`), core/advanced separation, `5-7-8` as advanced E-lower pocket only, warnings/per-string changes, no dense permanent SVG labels, and no `[object Object]`.

Intentionally not changed:

- Backend Explorer generation/validation.
- Canonical pitch validation.
- Fretboard geometry or fret math.
- Corpus, Chroma, embeddings, scraping, deployment, auth, DNS, public assets, raw design assets, or unrelated parked files.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-tooltip-detail-ux.md`

No files deleted.

## UI Behavior Changed

- Fretboard markers now receive:
  - `tabindex="0"`
  - `role="button"`
  - `aria-label`
  - `title`
  - mouse/focus/click/keyboard handlers for detail selection and tooltip display.
- Marker tooltip text includes:
  - chord/function/summary,
  - fret,
  - string group,
  - display notes,
  - pedals/levers,
  - warnings when present.
- Bottom row area now renders compact row buttons, not verbose full metadata cards.
- Selected detail panel shows one row at a time:
  - display notes,
  - top voice,
  - fret,
  - string group,
  - pedals/levers,
  - per-string changes,
  - warnings.
- The repeated learner-facing `Pitch validated` metadata row was removed from the detail/card area; trust is communicated by the `Showing validated positions` header pill and existing validated Explorer context.

## Browser Smoke Target

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8896/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`
- Cache-busted URL tested: `http://127.0.0.1:8896/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622` after Lane 12 restarts protected preview at the new commit.
- Auth required: local no; protected-preview yes
- Auth provider: local none; protected-preview Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: `http://127.0.0.1:8896`
- Expected backend port: static local server on `8896`
- Expected git HEAD: `7c56156` before commit
- Version endpoint: not applicable for local static server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local file server served current working tree
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this Explorer page smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this Explorer page smoke
- Who should test this URL: Lane 12 / Lane 15 / the user after protected-preview restart
- Do not test these URLs: stale cache-bust URLs from prior Explorer smoke runs
- Known caveats: local static smoke does not prove Cloudflare Access/protected-preview runtime freshness. The temporary root file server also logged `404` for `/brand/pedal-steel-fretboard-background.svg` because it did not mount `public/` as the web root; Lane 12 should verify the protected-preview `/brand/` static route.

Smoke result:

- Page loaded locally.
- Default view showed `Showing validated positions`.
- Default view had 34 row buttons and 34 fretboard markers.
- `.explorer-row-card` was absent.
- Marker `aria-label` included fret/string group, display notes, and pedals/levers.
- `5-7-8` advanced swap showed 2 row buttons/markers.
- `5-7-8` selected detail showed `E-lower`, per-string `Eb/D#`, and no `E-lower+E-lower`.
- G natural minor displayed `G A Bb C D Eb F`, with no `A#`/`D#` in the scale-note line.
- Marker click opened tooltip text with no `[object Object]`.

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js && node --check ui/e9-fretboard-explorer-data.js && node --check ui/pedal-steel-fretboard.js && node --check ui/answer-client.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 23 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 31 passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - 11 passed
- `.venv/bin/python -m pytest -q` - 791 passed
- `git diff --check`

## Integration Notes

- UI-only change.
- No API schema changes.
- No backend Explorer payload changes.
- The existing `display_notes`, `display_top_voice`, `display_summary`, warnings, and per-string changes remain the learner-facing fields used by the UI.
- The component continues to mount existing `PedalSteelFretboard` with `showHighlightLabels: false` so marker text is not densely printed inside the SVG.

## Risk Assessment

Risk: low.

Reasons:

- Scoped to one Explorer browser surface and one frontend test file.
- Full pytest is green.
- Local browser smoke verified the changed learner-facing behaviors.

Rollback:

- Revert `ui/e9-fretboard-explorer.html`, `ui/e9-fretboard-explorer.js`, and the matching test assertions in `tests/test_frontend_answer_ui.py`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-tooltip-detail-ux.md`

## Files That Must Not Be Staged

- Any unrelated dirty files shown by `git status --short`.
- `public/`
- `ui/brand/`
- `Neon Sign/`
- `source-inbox/`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- scraping outputs
- deployment/auth/DNS/secrets files
- raw design assets

## Recommended Next Lane

Lane 12 or Lane 15.

Exact next prompt:

```text
Lane 12 / Lane 15: restart or verify protected-preview freshness for the new Explorer UI commit, then browser-smoke https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-tooltip-detail-ux-20260622. Verify marker tooltip/detail behavior, G natural minor spelling, 5-7-8 advanced E-lower pocket, no duplicated lever labels, and no [object Object].
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit the scoped Lane 06 Explorer UI fix, then hand off to Lane 12 / Lane 15 for protected-preview restart/freshness and browser smoke.
