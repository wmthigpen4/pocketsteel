# 2026-06-23 15:46 - Lane 06 Explorer UI Cleanup

## Task Summary

Requested Lane 06 cleanup for the E9 Fretboard Explorer and home-page header controls.

Completed:

- Kept `Go Backstage` as the backstage/settings control.
- Kept `Explore Fretboard` as the separate Explorer control and verified it shares the compact header-button styling.
- Reduced the Explorer key selector from duplicate enharmonic entries to 12 learner-facing options.
- Mapped sharp/flat duplicate selector labels to one readable option, for example `C# (or D♭)` backed by the `Db` payload.
- Removed the standalone `five_eight_branch` option from Harmony / view.
- Kept `5-8` selectable/filterable under the `2-string harmonized scale` view with a `5&8 branch` optgroup.
- Removed the learner-facing copy `These Explorer rows are deterministic teaching data, separate from source-card answers.`
- Suppressed the shared fretboard component position tools and legend only for the Explorer mount so the old `Starter` / `Common` / shared-card labels do not clutter the Explorer page.
- Bumped Explorer script cache-bust query strings for the changed Explorer and fretboard renderer files.

Intentionally not changed:

- Backend Explorer generation and pitch validation.
- Explorer data payloads.
- Fretboard geometry.
- Corpus, Chroma, embeddings, scraping, auth, DNS, deployment, secrets, private source data, raw assets, and unrelated parked work.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/pedal-steel-fretboard.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-1546-06-explorer-ui-cleanup.md`

## Tests And Checks

Passed:

- `git diff --check`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
  Result: `23 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
  Result: `32 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  Result: `32 passed`

Browser smoke:

- Protected-preview local port `127.0.0.1:8770` was not running from this workspace, so browser smoke used a temporary static server:
  - `python3 -m http.server 8896 --bind 127.0.0.1`
- App URL tested:
  - `http://127.0.0.1:8896/ui/steel-guitar-rag-mock.html?access=beta_user&v=explorer-ui-cleanup`
- Explorer URL tested:
  - `http://127.0.0.1:8896/ui/e9-fretboard-explorer.html?access=beta_user&v=explorer-ui-cleanup-3`

Browser smoke results:

- App page shows separate `Explore Fretboard` and `Go Backstage` controls.
- `Explore Fretboard` links to `/ui/e9-fretboard-explorer.html`.
- `Go Backstage` remains a button with `aria-controls="backstage"`.
- Both header controls share compact pill styling.
- Explorer page shows 12 key selector options.
- Explorer Harmony / view shows only `2-string harmonized scale` and `3-string diatonic harmony`.
- Explorer page no longer shows the removed deterministic/source-card copy.
- Explorer page no longer renders shared fretboard position tools or shared legend.
- Rendered Explorer text has no `Starter` or `Common` labels.
- `Advanced` remains present only as the intended `Advanced swaps` string-group wording.
- Rendered Explorer text has no `[object Object]`.

Smoke caveat:

- Plain repo-root `http.server` does not serve `public/brand` at `/brand`, so the decorative fretboard background asset 404ed in local static smoke. That does not affect the control/text assertions verified here and should be handled by the normal app/protected-preview server.

## Integration Notes

- `five_eight_branch` remains internal metadata and is still included when the visible `2-string harmonized scale` view is selected.
- The visible `5-8` string group remains selectable/filterable under the `5&8 branch` optgroup.
- The shared `PedalSteelFretboard` component now supports `hidePositionTools` and `hideLegend` options. These are used by the Explorer mount only.
- Answer-page fretboard behavior should remain unchanged because no answer UI call site passes those new options.

## Risk Assessment

Risk: Low to medium.

Reason:

- The UI behavior change is scoped to Explorer option presentation and Explorer-only shared component suppression.
- One shared component gained two optional booleans, but default behavior remains unchanged.
- Static smoke did not cover protected-preview asset serving; Lane 12 should verify on the supervised protected preview.

Rollback:

- Revert the four changed UI/test files in this commit if Explorer presentation regresses.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/pedal-steel-fretboard.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-1546-06-explorer-ui-cleanup.md`

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
- All untracked corpus/private/source-inbox/design/deploy/raw asset paths visible in `git status --short`.

## Recommended Next Lane

Lane 12 protected-preview smoke.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 should restart/refresh the protected-preview runtime and smoke:

- Main app URL: `/ui/steel-guitar-rag-mock.html?v=explorer-ui-cleanup`
- Explorer URL: `/ui/e9-fretboard-explorer.html?v=explorer-ui-cleanup`

Verify the protected-preview page fetches the new cache-busted scripts and that Explorer no longer shows duplicate enharmonic key choices, the old disabled 5&8 Harmony option, or shared `Starter` / `Common` labels.
