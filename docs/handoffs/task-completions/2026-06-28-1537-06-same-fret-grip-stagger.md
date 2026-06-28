# Same-Fret Grip Marker Stagger

## Task Summary

Fixed the E9 Fretboard Explorer marker rendering for Single grip mode when multiple distinct result groups share the same fret and string group.

Completed:
- Explorer marker grouping now keeps same-fret, same-string-set results separate when their active top-label differs.
- The shared SVG fretboard renderer can then stagger those separate groups horizontally while keeping each full grip vertically stacked on its correct strings.
- Added focused tests for the Explorer grouping behavior and the low-level renderer same-fret/same-string-set behavior.

Intentionally not changed:
- Backend musical data and pitch rules.
- Fret geometry, string math, corpus, scraping, embeddings, auth, DNS, deployment policy, and protected-preview runtime configuration.

## Files Changed

- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/2026-06-28-1537-06-same-fret-grip-stagger.md`

## Root Cause

The Explorer collapsed marker groups using only fret, string group, and string set:

```text
marker:<fret>:<string_group>:<strings>
```

That merged distinct results such as fret 3 `B` and `C` on `3-4-5` into one marker before the shared fretboard renderer could apply same-fret collision handling.

## Fix

The Explorer marker group key now includes the current active top label:

```text
marker:<fret>:<string_group>:<strings>:<label>
```

This preserves distinct result groups while still allowing every individual grip to keep its original string stack.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=same-fret-grip-stagger-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=same-fret-grip-stagger-local`
- Exact URL the user should use: after protected-preview static refresh, `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=same-fret-grip-stagger-<commit>`
- Auth required: no for local; yes for protected preview
- Auth provider: none for local; Cloudflare Access for protected preview
- Cloudflare Access login result: not required locally
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `21b9d02` before commit
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local static file loaded from current working tree
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this direct Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this direct Explorer smoke
- Who should test this URL: Codex tested local; the user should test protected preview after cache-busted static refresh
- Do not test these URLs: unversioned Explorer URL for this fix, because stale JS may hide the change
- Known caveats: protected preview was not restarted or separately smoke-tested in this lane before commit.

## Browser Smoke Result

PASS locally.

Scenario:
- Explore mode: Single grip
- Key: G
- Copedent: Emmons E9
- Grip vocabulary: Core
- Scale: G major
- Harmony/view: 3-string diatonic harmony
- String group: 3-4-5

DOM verification:
- Fret 3 rendered separate markers:
  - `marker:3:3-4-5:3-4-5:B`, strings `3,4,5`, offset `9.000`
  - `marker:3:3-4-5:3-4-5:C`, strings `3,4,5`, offset `-9.000`
- Fret 10 rendered separate markers:
  - `marker:10:3-4-5:3-4-5:F#`, strings `3,4,5`, offset `-9.000`
  - `marker:10:3-4-5:3-4-5:G`, strings `3,4,5`, offset `9.000`
- No `[object Object]`.

## Tests And Checks

Passed:
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` (`24 passed`)
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` (`37 passed`)
- `git diff --check`

Skipped:
- Full pytest, because this is a focused frontend grouping/rendering change and focused UI/fretboard suites passed.
- Protected-preview smoke, because this lane did not perform a runtime/static refresh of protected preview.

## Integration Notes

- The low-level renderer already staggered same-fret highlights correctly once it received separate highlight records.
- The Explorer now emits separate marker groups for same-fret/same-string-set results that have different active labels.
- This applies to shared Explorer rendering paths that use `markerGroupKey`.

## Risk Assessment

Low to medium.

Reason:
- The change is small and frontend-only.
- Same-fret labels now produce more marker records than before in merged cases; this is intended for visual distinction.
- If two truly duplicate rows share fret, strings, and label, they still merge as before.

Rollback:
- Revert `markerGroupKey` to omit the label and revert the focused test updates.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/2026-06-28-1537-06-same-fret-grip-stagger.md`

## Files That Must Not Be Staged

- Any corpus, Chroma/vector, embedding, scraper, auth, DNS, deployment, private source, raw design asset, or unrelated parked worktree file.
- Existing unrelated dirty files shown by `git status --short`.

## Recommended Next Lane

Lane 12 protected-preview smoke, then user smoke.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12: refresh protected-preview static assets and smoke:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=same-fret-grip-stagger-<commit>
```

Verify the same Single grip / G major / Core / 3-4-5 scenario shows distinct staggered markers at frets 3 and 10.
