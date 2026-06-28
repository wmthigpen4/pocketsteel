# 2026-06-28 06 Explorer Compact Tool Cleanup

## Task Summary

User smoke feedback identified six learner-facing Explorer UI cleanup items:

- Remove the duplicate `Labels` heading next to the `String labels` toggle.
- Compact the fretboard display controls so Notation and Pitch register do not consume excessive vertical space.
- Reorder lever impact controls and label them as `F`, `E`, `G`, and `D`.
- Remove the always-visible impact context sentence beginning `Choose one or more controls...`.
- Remove the copedent/profile label from the Pedal and lever impact panel.
- Move the scale summary from its standalone pill into the main controls panel.

Completed these as a scoped Lane 06 UI change. No music rules, backend contracts, Explorer data rows, fretboard geometry, corpus, Chroma, auth, DNS, deployment, or assets were changed.

## Files Changed

- `ui/e9-fretboard-explorer.html`
  - Compact fretboard display controls from a 3-column grid into a wrapping inline control row.
  - Removed the duplicate `Labels` text label and kept the `String labels` toggle with an ARIA label.
  - Moved `#explorer-scale-notes` into the main Explorer controls box.
  - Refreshed the Explorer JS cache-bust to `compact-explorer-tools-20260628`.
- `ui/e9-fretboard-explorer.js`
  - Shortened lever impact button labels to `F`, `E`, `G`, and `D`.
  - Sorted lever impact controls in F/E/G/D order.
  - Removed the unused always-visible impact context sentence.
  - Removed the impact-panel copedent/profile line.
- `tests/test_frontend_answer_ui.py`
  - Updated cache-bust assertions.
  - Added/updated assertions for compact display controls, absent duplicate `Labels` heading, absent context sentence, absent impact copedent label, and F/E/G/D lever order.

## Tests And Checks

Passed:

```bash
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Focused pytest results:

- `tests/test_frontend_answer_ui.py`: 24 passed
- `tests/test_pedal_steel_fretboard_ui.py`: 36 passed

## Browser Smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=compact-explorer-tools-local-20260628`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=compact-explorer-tools-local-20260628`
- Exact URL the user should use: pending protected-preview smoke after commit
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: pre-commit working tree during local smoke
- Version endpoint: not checked for this static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: static file cache-bust and local DOM state
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant for direct Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant for direct Explorer smoke
- Who should test this URL: Codex locally; user should test protected-preview URL after commit/smoke
- Do not test these URLs: stale `?v=voicing-identifier-copy-b02e9c6` for this new slice
- Known caveats: local smoke does not prove protected-preview static cache freshness

Local browser smoke verified:

- Scale summary is inside `.explorer-controls`.
- Standalone `main > .explorer-summary` is absent.
- String labels control no longer has duplicate `Labels` heading.
- Pedal/lever impact context sentence is absent.
- Impact panel no longer repeats `Emmons E9` profile text.
- Lever controls render in order `F`, `E`, `G`, `D`.
- No `[object Object]`.
- No relevant console errors or warnings.
- No horizontal page overflow in the measured viewport.

## Integration Notes

This is presentation-only. The internal control IDs remain unchanged:

- `E-raise`
- `E-lower`
- `G-lower`
- `D-lower`

Only the learner-facing impact-preview button labels changed to F/E/G/D.

The scale summary still uses the existing `#explorer-scale-notes` element, so existing notation-mode updates continue to work.

## Risk Assessment

Risk: low.

Reason: changes are limited to Explorer layout/copy, display labels, and focused assertions. Music rules, data payloads, row generation, and backend behavior were not touched.

Rollback: revert the scoped commit or restore the prior `e9-fretboard-explorer.js?v=voicing-identifier-copy-20260627` cache-bust and UI snippets.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-28-0853-06-explorer-compact-tools-cleanup.md`

## Files That Must Not Be Staged

Do not stage unrelated parked work, including but not limited to:

- `corpus_metadata/**`
- `corpus-private/**`
- `corpus-v2/**`
- `source-inbox/**`
- Chroma/vector stores or embeddings
- raw/generated reports
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- unrelated RAG/backend scripts
- unrelated existing handoff backlog files

## Recommended Next Lane

Lane 12 protected-preview smoke after commit, then user smoke against the fresh cache-busted Explorer URL.

## Commit Readiness

Safe to commit after exact-path staging and `git diff --cached --check`.

## Suggested Next Step

Lane 12: run protected-preview browser smoke for the committed Explorer compact-tools slice using a fresh URL such as:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-explorer-tools-<commit>`
