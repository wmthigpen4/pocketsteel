# 2026-06-23 Lane 06 - E9 Fretboard Explorer Home Entry

Pass/warn/fail: pass

## Task Summary

Requested: add a clear learner-facing entry point from the protected-preview/app home page to the E9 Fretboard Explorer at `/ui/e9-fretboard-explorer.html`, while keeping Q&A/search as the primary app flow.

Completed:

- Replaced the existing small Explorer pill link with a compact secondary card near the ask/search area.
- Added the requested label: `Explore the E9 Fretboard`.
- Added the requested description: `Choose a key, scale, harmony type, and string group to see validated E9 positions visually.`
- Added the requested button/link text: `Open Fretboard Explorer`.
- Linked to the permanent route `/ui/e9-fretboard-explorer.html` with no smoke-test cache-bust.
- Preserved the primary ask/search prompt, suggested prompts, source note, answer page, backend behavior, Explorer generation, and protected-preview route assumptions.

Intentionally not changed:

- No backend pitch/Explorer generation.
- No RAG, corpus, Chroma/vector stores, embeddings, scraper output, deployment, auth, DNS, private source data, `public/`, `ui/brand/`, `Neon Sign/`, or raw design assets.
- No temporary cache-bust was added to the permanent home-page link.

## Current Branch And HEAD

- Branch before commit: `feature/answer-api`
- HEAD before commit: `444f4ed`

## Files Changed

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-e9-fretboard-explorer-home-entry.md`

## What Changed

### Home-Page Entry Behavior

- The Explorer entry now appears as a secondary card below the example prompt/source note area.
- The textarea/search card remains above the Explorer card, preserving the Q&A flow as primary.
- The card uses existing dark/brass visual language and responsive layout.
- The link target is the stable protected-preview route: `/ui/e9-fretboard-explorer.html`.
- The copy refers to `validated E9 positions` and does not imply RAG generated Explorer rows.

### Tests

- Updated `test_answer_ui_links_to_e9_fretboard_explorer_surface` to verify:
  - `Explore the E9 Fretboard` appears.
  - The exact description appears.
  - `Open Fretboard Explorer` appears.
  - The link target is `/ui/e9-fretboard-explorer.html`.
  - The Explorer entry uses the card class.
  - No `[object Object]` appears in the app HTML.
  - The primary prompt/search appears before the Explorer entry.

## Tests And Checks Run

Passed:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
```

Results:

- `tests/test_frontend_answer_ui.py -q`: `23 passed`
- `tests/test_pedal_steel_fretboard_ui.py -q`: `31 passed`
- `tests/test_fretboard_explorer.py -q`: `28 passed`
- Full pytest: `808 passed`
- JS syntax checks: passed

Pending final checks before commit:

```bash
git diff --check
git diff --cached --check
```

## Browser Smoke

Not run for this Lane 06 commit. The task explicitly routes the next phase to Lane 12 for protected-preview cache-bust refresh and then Lane 15 for full app smoke from the home page into Explorer. Static tests verify the entry markup, route, and ordering.

## Risk Assessment

Risk: low.

Why:

- The change is a scoped app-home presentation update with no runtime/backend contract changes.
- The new card links to an existing route.
- Tests verify the Explorer link and primary search ordering.

Rollback:

- Revert the scoped commit containing the three files listed above.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-e9-fretboard-explorer-home-entry.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files.
- `README.md` and parked docs/source metadata not listed above.
- Root RAG scripts and parked source/corpus metadata changes.
- `source-inbox/` raw/provenance files.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, and scraper output.
- Deployment/auth/DNS/secrets files.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment: refresh protected-preview cache-busts so the home-page entry is visible in the protected preview.

Then Lane 15 QA / Answer Eval: run full app smoke from the normal app home page into the Explorer.

## Commit Readiness

Safe to commit after final `git diff --check`, exact-path staging, `git diff --cached --check`, and cached diff review pass.

## Suggested Next Prompt

```text
Lane 12: Refresh protected-preview cache-busts for the E9 Fretboard Explorer home-entry UI at HEAD <commit>. Verify /api/version, then open the protected app home page and confirm the “Explore the E9 Fretboard” card links to /ui/e9-fretboard-explorer.html. After that, hand off to Lane 15 for full app smoke from home into Explorer.
```
