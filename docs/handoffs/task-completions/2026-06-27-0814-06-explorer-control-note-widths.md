# Lane 06 - Explorer Control Note And Widths

## Task Summary

Requested UI cleanup for the E9 Fretboard Explorer based on browser comments:

- Move the explanatory text about core grips, advanced swaps, 5-7-8, and 5-8 out of the bottom detail area where users will miss it.
- Keep that guidance subtle and avoid adding another large card.
- Reduce the width of the Copedent dropdown.
- Give Path Family more width so its labels have room.

Completed:

- Moved the grip/path guidance into a subtle one-line note inside the top controls area.
- Removed the old buried bottom `explorer-note` placement.
- Changed Copedent from a two-column control to a one-column control.
- Changed Path Family to span two columns.
- Preserved existing Explorer behavior, path/harmony logic, fretboard rendering, backend data, and navigation.

Intentionally not changed:

- No backend, corpus, Chroma, embeddings, auth, DNS, deployment, design assets, or source data changes.
- No changes to fretboard geometry, harmonized-scale data, notation logic, or pedal/lever impact logic.

## Files Changed

- `ui/e9-fretboard-explorer.html`
  - Added `.explorer-controls-note` styling.
  - Rebalanced `.explorer-control--copedent` and `#explorer-path-family-control` grid spans.
  - Added the subtle guidance note to the controls section.
  - Removed the old bottom detail note and unused `.explorer-note` style.
- `tests/test_frontend_answer_ui.py`
  - Added assertions for the Copedent/Path Family width rules.
  - Added assertions that the guidance note lives in the controls area.
  - Added assertions that the old bottom note/style are not restored.
- `docs/handoffs/task-completions/2026-06-27-0814-06-explorer-control-note-widths.md`
  - This handoff.

## Tests And Checks

Run:

```bash
node --check ui/e9-fretboard-explorer.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Results:

- `node --check ui/e9-fretboard-explorer.js`: passed.
- `node --check ui/answer-client.js`: passed.
- `node --check ui/pedal-steel-fretboard.js`: passed.
- `tests/test_frontend_answer_ui.py`: `23 passed`.
- `tests/test_pedal_steel_fretboard_ui.py`: `34 passed`.
- `git diff --check`: passed before handoff; rerun after handoff as final gate.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=control-note-widths-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=control-note-widths-local`
- Exact URL the user should use: protected-preview URL should use a fresh commit/cache-bust after Lane 12 refresh
- Auth required: no for local
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `c57ba92` at start of task
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree and cache-busted URL
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this scoped Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this scoped Explorer smoke
- Who should test this URL: Codex locally; user should test protected-preview after Lane 12 refresh
- Do not test these URLs: none
- Known caveats: local browser smoke does not prove protected-preview cache freshness

Local smoke result:

- Explorer loaded.
- Harmonized scale path mode selected.
- Controls note exists in `.explorer-controls`.
- Old bottom `.explorer-details .explorer-note` is gone.
- Copedent measured narrower than Path Family.
- Path Family remained visible.
- No `[object Object]` found.
- No relevant console errors.

Measured local DOM values:

```json
{
  "copedentWidth": 160,
  "pathFamilyWidth": 330,
  "controlsNoteWidth": 980,
  "noteInControls": true,
  "oldBottomNoteExists": false,
  "noObjectObject": true
}
```

## Integration Notes

- The guidance now sits where users change Key/Copedent/Explore Mode/Path Family, without becoming a full card.
- Path Family has enough room for labels like `Middle path: 5-6-8 / 5-6-7`.
- Copedent remains selectable but no longer consumes excessive horizontal space.
- No contract/data/schema changes.

## Risk Assessment

Risk: low.

Reason:

- HTML/CSS-only Explorer layout adjustment plus focused static tests.
- No data generation, backend, protected preview runtime, or routing changes.
- Mobile CSS resets the Copedent and Path Family grid spans to avoid narrow-screen overflow.

Rollback:

- Revert this commit or restore the old grid spans and bottom note markup.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-0814-06-explorer-control-note-widths.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked work, including but not limited to:

- `README.md`
- `corpus_metadata/**`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- private/corpus/vector/generated/design/deployment/auth assets or data

## Recommended Next Lane

Lane 12 protected-preview refresh/smoke, then user smoke on the Explorer controls area.

## Commit Readiness

Safe to commit after final `git diff --check`, exact-path staging review, and `git diff --cached --check` pass.

## Suggested Next Step

Lane 12: run protected-preview smoke against a cache-busted Explorer URL and verify the controls note location plus Copedent/Path Family widths.
