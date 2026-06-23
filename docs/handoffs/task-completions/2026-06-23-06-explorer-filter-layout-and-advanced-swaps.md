# 2026-06-23 Lane 06 - Explorer Filter Layout And Advanced Swaps

## Task Summary

Requested: fix the E9 Fretboard Explorer filter/control area so Key, Scale, and Harmony remain visually aligned while preserving the String Group multi-select behavior. Also clarify learner-facing 5&8 branch and Advanced swaps copy, keep 5-8 selectable in the 2-string harmonized-scale context, and prevent raw/internal labels from leaking into the UI.

Completed:

- Moved the String Group multi-select into a full-width control section below the compact Key/Scale/Harmony row.
- Preserved String Group as a native multi-select.
- Kept 5-8 selectable when the 2-string harmonized-scale view is active.
- Removed the separate `5&8 branch` dropdown family so 5-8 appears inside the 2-string groups.
- Added learner-facing help copy for 5&8 branch behavior and Advanced swaps.
- Updated focused frontend tests for layout, copy, 5-8 grouping, and internal-copy guardrails.

Intentionally not changed:

- Backend Explorer generation and validation.
- Explorer data rows.
- Fretboard geometry/rendering logic.
- Answer routing, auth, DNS, deployment, launchd, tunnel, corpus, Chroma, embeddings, scraping, secrets, and private-source files.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-explorer-filter-layout-and-advanced-swaps.md`

## UI Behavior

- Key, Scale, and Harmony remain in the compact main control row.
- String Group now spans the full control width below them, avoiding the mismatched tall-list appearance in the main row.
- 5-8 is part of the `2-string groups` dropdown family when the 2-string harmonized-scale view is active.
- `five_eight_branch` remains internal metadata only and does not appear in learner-facing Explorer text.
- Advanced swaps are explained near the String Group control where users encounter those options.

## Browser Smoke Target

```text
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=explorer-filter-layout-smoke
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=explorer-filter-layout-smoke
- Exact URL the user should use: protected-preview cache-busted URL after Lane 12 refresh
- Auth required: no for local smoke
- Auth provider: none for local smoke
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 99b7251
- Version endpoint: not checked for this local UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local file changes and browser DOM inspection
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this Explorer-only smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this Explorer-only smoke
- Who should test this URL: Codex locally; Lane 12 should test protected preview after commit
- Do not test these URLs: production URLs for this local UI slice
- Known caveats: local browser smoke does not prove protected-preview cache freshness
```

Smoke result:

- Explorer route loaded on local port 8770.
- String Group section rendered below the compact controls.
- Switching Harmony/View to `2-string harmonized scale` showed option values `all`, `3-5`, `5-6`, `6-10`, `4-6`, `3-4`, and `5-8`.
- 5-8 was inside the `2-string groups` optgroup, not a separate 5&8 family.
- Raw `five_eight_branch` was not present in body text.
- Internal copy such as `deterministic teaching data`, `corpus retrieval`, `source-card answers`, and `RAG-generated` was not visible.

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
- `git diff --check`

Skipped:

- Full pytest, not required by this scoped UI layout task and broad unrelated dirty/untracked work remains parked.
- Protected-preview smoke, explicitly left for Lane 12 after commit/cache refresh.

## Risk Assessment

Risk: low.

Reason: the change is limited to Explorer presentation and the UI-only grouping of existing validated rows. It does not change data generation, validation, answer routing, or fretboard geometry.

Rollback: revert the scoped HTML/JS/test commit if the full-width String Group panel is not acceptable.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-explorer-filter-layout-and-advanced-swaps.md`

## Files That Must Not Be Staged

- Existing unrelated modified files, including `README.md`, corpus metadata/docs, RAG scripts, `source-inbox/inventory.json`, and landing-sign assets.
- Existing unrelated untracked docs, data, public/brand, ui/brand, source-inbox, Neon Sign, and generated/private files.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment: refresh protected-preview/runtime cache and smoke the Explorer at a cache-busted protected-preview URL.

## Commit Readiness

Safe to commit after exact-path staging and cached-diff review.

## Suggested Next Step

Lane 12 prompt: run protected-preview smoke for the E9 Fretboard Explorer filter layout at a fresh cache-busted URL and verify Key/Scale/Harmony alignment, String Group multi-select behavior, 5-8 inside 2-string groups, no `five_eight_branch` leak, and no stale Explorer assets.
