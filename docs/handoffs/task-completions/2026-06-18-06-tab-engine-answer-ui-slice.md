# 2026-06-18 - Lane 06 - Tab Engine Answer UI Slice

## Task Summary

Implemented the first narrow answer-page UI slice for deterministic tab output. The answer client now normalizes display-ready tab payloads from `/api/tab/render`-style responses and the answer page can render up to three tab examples below the primary answer card and above fretboard/source material.

Intentionally not changed:

- No backend tab generation or routing changes.
- No fake frontend tab generator.
- No SVG fretboard sync.
- No tab editor.
- No answer-page branding or landing-sign changes.

Branch: `feature/answer-api`

HEAD at task time: `0bd07801435ba83bf0c3c0d314839aad61903d79`

## Files Changed

- `ui/answer-client.js`
  - Added tab payload normalization helpers.
  - Preserves `/api/tab/render` fields such as `tab`, `ok`, `issues`, and `metadata`.
  - Supports future `tabs: []` answer payloads.
  - Avoids object coercion in tab display fields.
- `ui/steel-guitar-rag-mock.html`
  - Added a hidden answer tab section between the main answer card and the optional fretboard/source area.
  - Added calm dark/amber tab card styles.
  - Renders tab text with `pre > code`.
  - Clears tab examples on loading, error, and return-to-stage.
- `tests/test_frontend_answer_ui.py`
  - Added normalization coverage for tab render payloads.
  - Added static wiring checks for answer-page tab display placement and whitespace-preserving styles.
- `docs/handoffs/task-completions/2026-06-18-06-tab-engine-answer-ui-slice.md`
  - This handoff.

No files deleted.

## Component / Rendering Summary

The UI slice uses the existing static answer page structure:

- `STEEL_RAG_ANSWER_UI.normalizeAnswerResponse()` now attaches `tabs` when a response includes a renderable tab payload.
- `renderTabExamples(response.tabs)` mounts tab cards only when normalized tabs exist.
- Tab examples remain secondary content: answer first, then tab examples, then fretboard/source material.
- The renderer caps visible tab cards to three to avoid overwhelming the answer page.

## Alignment Preservation

Tab alignment is preserved with:

- `pre` and `code`.
- `white-space: pre`.
- monospaced font stack.
- no text wrapping inside the tab block.
- horizontal scrolling on overflow.

The normalizer treats object maps as compact key/value text rather than allowing `[object Object]`.

## Mobile Behavior

The tab block uses `max-width: 100%` and `overflow-x: auto`, so smaller screens scroll horizontally instead of reflowing ASCII tab and breaking alignment.

## Tests and Checks Run

Passed:

- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
  - `20 passed`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - `16 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - `4 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
  - `29 passed`
- `git diff --check`

Skipped:

- Full pytest was not run because the user noted two known unrelated failures: landing source/deploy HTML mismatch and missing public fretboard background route. This slice did not touch those areas.
- Browser smoke was not run because this is a display-only component slice and normal answers may not yet emit answer-page tab payloads. The next slice should smoke once an answer flow returns `tabs`.

## Integration Notes

The UI is ready to display either:

- direct `/api/tab/render`-style payloads: `{ ok, tab, issues, metadata }`
- answer-page payloads with `tabs: [{ title, tabText, metadata, issues }]`

The current slice does not decide which answer intents should show tab examples. That belongs to Lane 05 / answer composer work.

## Risk Assessment

Risk: Low.

Why:

- Display-only frontend slice.
- No backend, corpus, retrieval, Chroma, auth, deployment, or scraper changes.
- Hidden by default when no tab payload exists.
- Focused regression tests cover normalization and placement.

Rollback:

- Revert the three tab UI hunks in `ui/answer-client.js`, `ui/steel-guitar-rag-mock.html`, and `tests/test_frontend_answer_ui.py`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

Stage only the tab-related hunks from:

- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-18-06-tab-engine-answer-ui-slice.md`

Because `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py` already contain unrelated landing-sign changes, use exact-hunk staging and inspect the cached diff before committing.

## Files That Must Not Be Staged

Do not stage unrelated parked work, including but not limited to:

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `deploy/landing/index.html`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- untracked `public/`, `Neon Sign/`, `source-inbox/provenance.json`, and other parked assets/docs.

## Recommended Next Lane

Lane 05 / Backend RAG Integration should decide when normal answer responses include `tabs` and what answer intents produce small tab examples.

After that, Lane 06 should browser-smoke the answer page with a real answer payload containing tabs.

## Commit Readiness

Safe to commit after exact-hunk staging confirms no unrelated landing-sign or parked work is included.

## Suggested Next Step

Lane 05: Connect selected deterministic tab examples to answer composer payloads for one narrow educational intent, returning `tabs` without changing the frontend display contract.
