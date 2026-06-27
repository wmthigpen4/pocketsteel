# 2026-06-26 21:03 - Lane 06 - Hide Harmony/View In Path Mode

## Task Summary

User smoke identified that `Harmony / view` still appeared while `Explore mode` was set to `Harmonized scale path`. That control is misleading in path mode because the UI already forces the harmony value to `three_string_diatonic` and uses `Path family` as the actual path control.

Completed:

- Added an explicit `#explorer-harmony-control` wrapper around the `Harmony / view` selector.
- Hid and aria-hid `Harmony / view` in harmonized-scale path mode.
- Preserved the forced internal `three_string_diatonic` value for path mode.
- Restored `Harmony / view` when switching back to `Single grip`.
- Added focused regression checks for the control visibility behavior.

Intentionally not changed:

- No backend rules or Explorer payload data.
- No string-group/path-family filtering logic.
- No notation, marker, pedal/lever impact, or fretboard rendering logic.
- No corpus, Chroma, embeddings, scraping, auth, DNS, deployment, or design assets.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`

## Tests And Checks

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

- `tests/test_frontend_answer_ui.py`: 23 passed
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed
- `tests/test_fretboard_explorer.py`: 38 passed

## Browser Smoke

Smoke Target:

```text
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=hide-harmony-in-path-local
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=hide-harmony-in-path-local
- Exact URL the user should use: pending protected-preview smoke after commit
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 93865c1 before commit
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local working tree served by same-origin preview
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: yes in protected preview; not required for this Explorer-only local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally; user after protected-preview smoke
- Do not test these URLs: uncache-busted Explorer URLs for this slice
- Known caveats: local smoke proves current working-tree UI behavior only, not protected-preview cache freshness
```

Local smoke result:

- Initial `Single grip` mode showed `Harmony / view`.
- Switching to `Harmonized scale path` hid `Harmony / view`.
- Path mode still forced `explorer-harmony` to `three_string_diatonic`.
- `Path family` remained visible and enabled in path mode.
- `String group` remained hidden in path mode.
- Switching back to `Single grip` restored `Harmony / view`.
- No `[object Object]`.
- No relevant browser console errors.

Protected-preview smoke attempt after commit:

```text
- Target type: protected-preview
- Result type: browser smoke attempt, stale runtime/static HTML caveat
- Exact browser URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=hide-harmony-in-path-d665bcf
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=hide-harmony-in-path-d665bcf
- Exact URL the user should use: pending Lane 12 protected-preview refresh/restart
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; Explorer page loaded
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: d665bcf before amend
- Version endpoint: http://127.0.0.1:8770/api/version
- Version endpoint result: git_sha=4040a47, git_branch=feature/answer-api
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: yes in protected preview
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Lane 12 after preview refresh/restart, then the user
- Do not test these URLs: stale `compact-controls-672ec51` URL for this fix
- Known caveats: protected page loaded but did not contain the new `#explorer-harmony-control` wrapper, so it was serving stale Explorer HTML and could not validate this commit.
```

Protected-preview observed result:

- Cloudflare Access was passed and the Explorer page loaded.
- `Harmonized scale path` still disabled `Harmony / view`, but the new wrapper was absent on the protected page.
- This indicates the protected preview had not refreshed to the committed static HTML yet.
- Protected-preview verification is therefore **not passed** for this slice until Lane 12 refreshes/restarts the runtime/static page and retests with a fresh cache-busted URL.

## Integration Notes

- This is a learner-facing control cleanup. It removes a disabled/redundant control from the active path-mode filter area.
- The underlying path-mode logic remains unchanged: path mode still uses three-string diatonic harmony plus `Path family`.
- Protected-preview smoke should use a fresh cache-busted Explorer URL after commit.

## Risk Assessment

Risk: low.

Reason:

- Existing path-mode value forcing is preserved.
- The change only controls visibility and accessibility state for a redundant control.
- Focused VM tests and local browser smoke cover mode switching.

Rollback:

- Revert the scoped commit if the product decision changes and the disabled `Harmony / view` control should remain visible in path mode.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-2103-06-hide-harmony-view-in-path-mode.md`

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
- Any untracked corpus, design, brand, deployment, private-data, or source-inbox files.

## Recommended Next Lane

Lane 12 protected-preview smoke for the cache-busted Explorer URL after this commit.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Run protected-preview smoke against:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=hide-harmony-in-path-<commit>
```
