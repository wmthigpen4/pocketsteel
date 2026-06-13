# Answer Card Real Estate User Smoke Fix

## Task Summary

Autopilot user-smoke bug: the protected-preview answer card wasted desktop space for `Show me G chord positions.` because the `Why these families matter` answer section was trapped in the first grid column while the answer card remained wide.

Completed:
- Made qualifying teaching sections span the full answer section grid.
- Rendered `Why these families matter` as a compact two-column bullet layout on desktop.
- Preserved a single-column layout on narrow/mobile viewports.
- Preserved backend answer text, `/api/answer` schema, auth, deployment, corpus, Chroma, embeddings, scraping, source data, and visual assets.

Intentionally not changed:
- Backend answer routing or answer composition.
- Fretboard geometry, filters, source cards, or response schema.
- Cloudflare Access, deployment, DNS, or protected-preview runtime configuration.

## Root Cause

The answer detail area uses a multi-column CSS grid. Structured answer sections were rendered as normal `.answer-section` blocks, so the `Why these families matter` section occupied only the first grid column. Its bullet list stacked vertically inside that narrow column while the rest of the wide answer card remained mostly empty.

## Files Changed

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/answer-card-real-estate-user-smoke-fix.md`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-g-chord-positions-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-c-chord-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-g-e9-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-swing-waltz-settled-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/mobile-g-chord-positions-after.png`

Generated but not needed for final evidence:
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-swing-waltz-after.png` captured before the answer finished loading.

## Exact Layout Change

Added `shouldUseWideAnswerSection(section)` to classify `Why these families matter` as a wide answer section. Wide sections receive `.answer-section.is-wide`.

Desktop CSS:
- `.answer-section.is-wide { grid-column: 1 / -1; }`
- `.answer-section.is-wide .try-list { columns: 2 280px; column-gap: 34px; }`

Mobile/narrow CSS:
- At `max-width: 960px`, `.answer-section.is-wide .try-list { columns: 1; }`

The helper also supports future wide handling for larger teaching sections with at least four bullets and titles such as `why it works`, `how to use`, or `position families`.

## Browser Smoke Target

Smoke Target:
- Target type: protected-preview root
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/`
- Cache-busted URL tested: none; exact root target was used
- Exact URL the user should use: `https://app.steelguitarrag.com/`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded in the authenticated in-app browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `f457d8b`
- Version endpoint: not checked
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: root loaded the protected UI and rendered the patched `.answer-section.is-wide` CSS/DOM in browser
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes; root redirects to `/ui/steel-guitar-rag-mock.html`
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both Codex and the user
- Do not test these URLs: public landing page, Cloudflare Pages root, corpus/source endpoints
- Known caveats: one retained console error came from an older local fretboard demo tab, not the protected smoke page; current-page filtered logs were empty.

## Browser Smoke Result

Protected root loaded:
- Requested: `https://app.steelguitarrag.com/`
- Result: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- Page title: `Steel Guitar RAG - Simple Search Mock`

Desktop prompt results:

| Prompt | Result |
| --- | --- |
| `Show me G chord positions.` | Pass. `Why these families matter` rendered as `.answer-section.is-wide`, `grid-column: 1 / -1`, two-column list, fretboard visible. |
| `How do I play a C chord?` | Pass. Same wide layout applied; fretboard visible. |
| `How do I play a G chord on the E9?` | Pass. Same wide layout applied; fretboard visible. |
| `What’s it mean for a song to be a swing or a waltz?` | Pass. Plain teaching answer rendered cleanly with no fretboard and no unnecessary empty columns. |

Measured desktop layout for `Show me G chord positions.`:
- Viewport: `1280 x 720`
- Answer card width: `1060px`
- Answer grid width: `1006px`
- `Why these families matter` section width: `1006px`
- Section grid column: `1 / -1`
- Bullet list column count: `2`
- Right-side unused space inside card after patch: normal padding only, about `27px`

Mobile/narrow prompt result:
- Prompt: `Show me G chord positions.`
- Viewport: `390 x 844`
- Answer card width: `362px`
- Answer grid width: `324px`
- `Why these families matter` section width: `324px`
- Bullet list column count: `1`
- Page-level horizontal overflow: `0px`
- Fretboard still visible and usable.

## Screenshots

Before evidence:
- The before state is the user-smoke screenshot described in the task. A local pre-patch screenshot was not captured before applying the autopilot fix.

After screenshots captured:
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-g-chord-positions-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-c-chord-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-g-e9-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-swing-waltz-settled-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/mobile-g-chord-positions-after.png`

## Tests And Checks

Run before handoff:
- `git status --short` - completed; large pre-existing dirty worktree noted.
- `git diff --check` - passed.
- `node --check ui/answer-client.js` - passed.
- `node --check ui/pedal-steel-fretboard.js` - passed.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `18 passed`.
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `29 passed`.

Final checks should be rerun after this handoff file is written and before commit.

## Integration Notes

- This is a frontend presentation fix only.
- No `/api/answer` schema or backend answer text changed.
- The wide-section helper is title-based and conservative. It targets the repeated smoke blocker while avoiding a broad renderer refactor.
- Fretboard rendering and filters were not touched.
- Non-fretboard answers still render without a fretboard area.
- Existing parked dirty files outside the scoped UI/test/handoff files were left untouched.

## Risk Assessment

Risk: low.

Why:
- The behavior is constrained to answer sections that opt into `.is-wide`.
- Desktop layout uses existing answer grid width rather than new containers.
- Narrow/mobile layout explicitly falls back to one column.
- Focused frontend tests and browser smoke covered chord, fretboard, and non-fretboard answer cases.

Rollback:
- Revert the `.answer-section.is-wide` CSS, `shouldUseWideAnswerSection`, and related test assertions.

## Commit Readiness

Safe to commit after final checks pass.

Exact safe-to-stage file list:
- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/answer-card-real-estate-user-smoke-fix.md`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-g-chord-positions-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-c-chord-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-g-e9-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-swing-waltz-settled-after.png`
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/mobile-g-chord-positions-after.png`

Do not stage:
- `docs/handoffs/task-completions/assets/answer-card-real-estate-user-smoke-fix/desktop-swing-waltz-after.png`
- Any pre-existing dirty corpus, docs, backend, deploy, public, `ui/brand`, `Neon Sign`, source-inbox, or generated/private files.

## Suggested Next Step

Lane 15 QA / Answer Eval should run a focused user-smoke pass at `https://app.steelguitarrag.com/` after the scoped commit and protected-preview runtime refresh, using:

```text
Verify the answer-card real-estate fix in protected preview. Test `Show me G chord positions.`, `How do I play a C chord?`, `How do I play a G chord on the E9?`, and `What’s it mean for a song to be a swing or a waltz?`. Confirm the family-explanation section uses the full answer-card width on desktop, collapses cleanly on mobile, fretboard answers still show the fretboard, non-fretboard answers do not show a fretboard, and no page-level horizontal overflow appears.
```
