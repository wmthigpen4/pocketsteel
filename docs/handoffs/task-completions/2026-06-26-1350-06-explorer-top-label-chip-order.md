# E9 Explorer Top-Label Chip Order

## Task Summary

Lane: 06 UX/UI Design

Requested: fix the E9 Fretboard Explorer `Find [notation] top label` chip order so chips follow musical scale-degree order instead of fallback interval/alphabetical ordering.

Completed:

- Ordered top-label filter chips from the active key/scale sequence.
- Preserved `All` as the first chip.
- Refreshed the Explorer page script query for `e9-fretboard-explorer.js` so protected-preview fetches this updated chip-order logic.
- Preserved existing chip filtering, notation selector behavior, marker sync, compact controls, and Explorer data rendering.
- Added focused frontend VM assertions for Notes, NNS, Roman, and Numbers chip order.

Intentionally not changed:

- Backend Explorer generation.
- Fretboard geometry and marker logic.
- Corpus, Chroma, embeddings, auth, DNS, deployment, protected-preview runtime, and visual assets.

## Files Changed

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1350-06-explorer-top-label-chip-order.md`
- `docs/handoffs/task-completions/assets/2026-06-26-top-label-chip-order/local-chip-order.png`

## Behavior Changed

Before:

- Top-label filter chips could render in non-musical order such as `All, 1, 4, 5, 2m, 3m, 6m, 7dim`.

After:

- Notes mode follows selected key/scale note order. Example G major: `All, G, A, B, C, D, E, F#`.
- NNS mode follows selected scale-degree order. G major: `All, 1, 2-, 3-, 4, 5, 6-, 7°`.
- Roman mode follows selected scale-degree order. G major: `All, I, ii, iii, IV, V, vi, vii°`.
- Numbers mode follows selected scale-degree order. G major: `All, 1, 2m, 3m, 4, 5, 6m, 7dim`.
- Subsets still preserve degree order because the sort uses the active sequence and only orders the labels present.

## Tests And Checks

Commands run:

```bash
node --check ui/e9-fretboard-explorer.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
git diff --check
```

Results:

- `node --check ui/e9-fretboard-explorer.js`: passed
- `node --check ui/answer-client.js`: passed
- `node --check ui/pedal-steel-fretboard.js`: passed
- `tests/test_frontend_answer_ui.py`: 23 passed
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed
- `tests/test_fretboard_explorer.py`: 38 passed
- `git diff --check`: passed

## Browser Smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=top-label-chip-order-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=top-label-chip-order-local`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=top-label-chip-order-64f9fff`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `d32905b` plus local scoped changes
- Version endpoint: not checked for local static browser smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local working tree and browser URL cache-bust
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant to direct Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this direct Explorer smoke
- Who should test this URL: Codex locally, then the user after protected-preview smoke
- Do not test these URLs: uncache-busted Explorer URLs for this fix
- Known caveats: local browser smoke does not prove protected-preview static asset freshness

Local smoke result:

- Page loaded.
- Notes chips: `All, G, A, B, C, D, E, F#`.
- NNS chips: `All, 1, 2-, 3-, 4, 5, 6-, 7°`.
- Roman chips: `All, I, ii, iii, IV, V, vi, vii°`.
- Numbers chips: `All, 1, 2m, 3m, 4, 5, 6m, 7dim`.
- No `[object Object]`.
- No relevant console errors.

Screenshot:

- `docs/handoffs/task-completions/assets/2026-06-26-top-label-chip-order/local-chip-order.png`

Protected-preview smoke:

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=top-label-chip-order-64f9fff`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=top-label-chip-order-64f9fff`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=top-label-chip-order-64f9fff`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded via existing in-app browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `64f9fff`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `{"git_sha":"4040a47","git_branch":"feature/answer-api","server_started_at":"2026-06-26T01:51:23.747502+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not checked for this direct Explorer slice
- Whether app root `/` is expected to work: yes, but root behavior was not part of this smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but main app behavior was not part of this smoke
- Who should test this URL: the user
- Do not test these URLs: uncache-busted Explorer URLs for this fix
- Known caveats: `/api/version` still reports runtime SHA `4040a47`; this pass verifies static UI behavior at the cache-busted Explorer URL, not a runtime restart.

Protected result:

- Page loaded after Cloudflare Access.
- HTML loaded `e9-fretboard-explorer.js?v=top-label-chip-order-20260626`.
- G major Notes chips: `All, G, A, B, C, D, E, F#`.
- G major NNS chips: `All, 1, 2-, 3-, 4, 5, 6-, 7°`.
- G major Roman chips: `All, I, ii, iii, IV, V, vi, vii°`.
- G major Numbers chips: `All, 1, 2m, 3m, 4, 5, 6m, 7dim`.
- No `[object Object]`.
- No relevant console errors.

Protected screenshot:

- `docs/handoffs/task-completions/assets/2026-06-26-top-label-chip-order/protected-chip-order.png`

## Integration Notes

- The fix is frontend-only and uses existing notation/scale sequences already present in `ui/e9-fretboard-explorer.js`.
- `ui/e9-fretboard-explorer.html` now references `e9-fretboard-explorer.js?v=top-label-chip-order-20260626`.
- No schema/API/backend contract changed.
- Protected-preview smoke should use a fresh cache-busted Explorer URL after commit.

## Risk Assessment

Risk: low.

Reason: the change is limited to sorting already-derived filter labels. Filtering still compares against the same label values as before.

Rollback: revert `topFilterSortIndex` usage and the focused frontend assertions.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1350-06-explorer-top-label-chip-order.md`
- `docs/handoffs/task-completions/assets/2026-06-26-top-label-chip-order/local-chip-order.png`

## Files That Must Not Be Staged

- Existing unrelated dirty files listed by `git status --short`, especially corpus/source/private/design/deployment-adjacent files.
- `docs/handoffs/task-completions/integration-status.md` until protected-preview smoke is recorded.

## Recommended Next Lane

Lane 01 exact-path commit for this scoped UI fix, then Lane 12 protected-preview smoke.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit scoped files with:

```bash
git add ui/e9-fretboard-explorer.js ui/e9-fretboard-explorer.html tests/test_frontend_answer_ui.py docs/handoffs/task-completions/2026-06-26-1350-06-explorer-top-label-chip-order.md docs/handoffs/task-completions/assets/2026-06-26-top-label-chip-order/local-chip-order.png
git commit -m "fix: order explorer top label chips by scale degree"
```
