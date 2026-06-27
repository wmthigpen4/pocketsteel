# 2026-06-26 21:24 - Lane 06 - Explorer Copedent Label Copy

## Task Summary

User smoke reported two Explorer copy issues:

- The control label `E9 setup` should say `Copedent`.
- The header button `View chart` should say `Copedent`.

Completed the scoped UI copy fix. The Explorer control label, header action, helper copy, dialog title, and JS-rendered copedent chart header now use learner-facing `Copedent` / `copedent` language. Existing behavior is unchanged: the header button still opens the copedent chart dialog, and the selector still controls the active E9 copedent.

Intentionally not changed: Explorer data, fretboard logic, notation logic, filters, backend behavior, auth, deployment, corpus, Chroma, embeddings, scraping, or assets.

## Files Changed

- `ui/e9-fretboard-explorer.html`
  - Renamed header button text from `View chart` to `Copedent`.
  - Renamed selector label from `E9 setup` to `Copedent`.
  - Updated helper copy and dialog title to use copedent language.
- `ui/e9-fretboard-explorer.js`
  - Updated the JS-rendered copedent chart header fallback/copy to use copedent language.
- `tests/test_frontend_answer_ui.py`
  - Updated focused assertions for the new copy.
  - Added negative assertions against the old `View chart` and `E9 setup` copy paths.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -8 --oneline
git diff --name-only
git diff --cached --name-only
git diff --check
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

- JS syntax checks passed.
- `tests/test_frontend_answer_ui.py`: 23 passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed.
- `tests/test_fretboard_explorer.py`: 38 passed.
- `git diff --check`: passed.

## Smoke Target

```text
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=copedent-label-local-3
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=copedent-label-local-3
- Exact URL the user should use: after protected-preview refresh, use a fresh Explorer URL with this commit hash as cache-bust
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 974325d plus this local uncommitted patch at smoke time
- Version endpoint: not checked for local UI-only smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local source files and cache-busted static URL
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this scoped Explorer copy smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this scoped Explorer copy smoke
- Who should test this URL: Codex locally; the user after Lane 12 protected-preview refresh
- Do not test these URLs: stale protected URLs from earlier Explorer slices for this copy fix
- Known caveats: protected preview was not restarted in this Lane 06 task
```

Local browser smoke result:

- Control label: `Copedent`.
- Header button: `Copedent`.
- Helper copy: `Choose the copedent that matches your guitar. My Copedent (E9) is coming soon in Backstage.`
- Dialog title: `Selected E9 copedent chart`.
- Old `View chart` text: absent.
- Old `E9 setup` text: absent from rendered page text.
- No `[object Object]`.
- Console warnings/errors: none.

## Integration Notes

This is a copy-only UI fix. No data contract or backend behavior changed.

The old label appeared in both static HTML and JS-rendered copedent chart copy; both paths were updated.

## Risk Assessment

Risk: low. The change is limited to Explorer copy and focused assertions.

Rollback: revert the copy changes in `ui/e9-fretboard-explorer.html`, `ui/e9-fretboard-explorer.js`, and matching test assertions.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-2124-06-explorer-copedent-label-copy.md`

## Files That Must Not Be Staged

All unrelated parked dirty/untracked work, especially:

- `README.md`
- `corpus_metadata/**`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- corpus/private/generated/design/deployment/auth files

## Recommended Next Lane

Lane 12 protected-preview refresh/smoke with a fresh Explorer cache-bust, then focused user smoke for the Explorer header/control copy.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12: protected-preview smoke `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=copedent-label-<commit>` and verify the Explorer control label and header chart button both read `Copedent`.
