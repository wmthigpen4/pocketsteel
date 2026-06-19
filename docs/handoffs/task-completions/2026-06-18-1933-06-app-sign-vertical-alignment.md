# 2026-06-18 19:33 - Lane 06 - App Sign Vertical Alignment

## Task Summary

Requested: align the hanging sign on `app.steelguitarrag.com` vertically with the hanging sign on `www.steelguitarrag.com`; the app sign was too low.

Completed:

- Compared app and www mobile hanging-sign CSS.
- Updated only the app mobile hanging-sign vertical offset.
- Preserved app sign size, left placement, asset paths, and mobile PNG fallback behavior.
- Left www/public files unchanged for this task.
- Added a focused regression assertion preventing the old mobile `top: 48px` value from returning.

Intentionally not changed:

- No asset changes.
- No www/public landing page changes.
- No Cloudflare Access, DNS, auth, backend, corpus, Chroma, embeddings, scraping, or deployment config changes.

## Files Changed

- `ui/steel-guitar-rag-mock.html`
  - Mobile app sign vertical offset changed from `top: 48px` to `top: 8px`.
- `tests/test_frontend_answer_ui.py`
  - Updated the app sign test to expect `top: 8px`.
  - Added `top: 48px` absence assertion.
- `docs/handoffs/task-completions/2026-06-18-1933-06-app-sign-vertical-alignment.md`
  - This handoff.

## Before / After Positioning

App mobile CSS before:

- `.hero-hanging-sign { top: 48px; left: -14px; width: clamp(190px, 55vw, 240px); }`

App mobile CSS after:

- `.hero-hanging-sign { top: 8px; left: -14px; width: clamp(190px, 55vw, 240px); }`

Reference www mobile CSS:

- `.hero-hanging-sign { top: 8px; left: 0; width: clamp(150px, 48vw, 210px); }`

The app now matches the www vertical offset while preserving app-specific left and width values.

## Browser Smoke

Smoke Target:

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=app-sign-align-20260618`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=app-sign-align-20260618`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=app-sign-align-20260618`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: existing browser session succeeded
- Local backend URL: not used directly in this static home visual check
- Expected backend port: not applicable
- Expected git HEAD: `c7116d5`
- Version endpoint: not checked
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: cache-busted UI URL and DOM/CSS inspection
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both Codex and the user
- Do not test these URLs: www as a change target; it was used only as the visual/CSS reference
- Known caveats: if a different protected-preview runtime serves stale HTML, Lane 12 should restart/refresh the runtime.

Mobile app smoke at approximately `390 x 844`:

- App sign CSS top: `8px`.
- App sign CSS left: `-14px`.
- App sign CSS width: `214.5px` at viewport.
- App sign rendered rect top: approximately `2.39px` after rotation.
- App sign rendered rect left: `-14px`.
- App sign rendered rect width: approximately `218.64px`.
- PNG fallback remained active on mobile: video `display: none`, fallback image `display: block`.

Reference www smoke at approximately `390 x 844`:

- www sign CSS top: `8px`.
- www sign remained on its public page behavior and was not edited.

## Tests And Checks

Commands run:

- `git status --short`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
- `git diff --check`

Results:

- JS syntax checks: passed.
- Focused frontend test: `20 passed`.
- `git diff --check`: passed.
- Browser smoke: passed for app mobile sign vertical alignment.

## Integration Notes

- This is an app-shell CSS fix only.
- The current working tree has many unrelated dirty files. Only exact hunks from the files listed in this handoff should be staged.
- The prior app-only mobile fallback/cache-bust sign fix remains part of the app sign working diff in these same files and is directly related to current app sign correctness.

## Risk Assessment

Risk: low.

Reason:

- The functional change is one mobile CSS value in the app page.
- Size, left placement, assets, and answer-page behavior were preserved.
- The regression test covers the new value and blocks the old value.

Rollback:

- Revert app mobile `.hero-hanging-sign` top from `8px` back to `48px`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

Stage exact hunks only from:

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-18-1933-06-app-sign-vertical-alignment.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty files, especially:

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `deploy/landing/brand/`
- `tests/test_public_landing_page.py`
- `ui/brand/`
- `public/`
- `Neon Sign/`
- `corpus-private/`
- `corpus-v2/`
- `source-inbox/`
- Chroma/vector stores
- embeddings
- scraping outputs
- deployment/auth/DNS/tunnel config

## Recommended Next Lane

Lane 12 Self-Hosted Deployment if the protected-preview runtime needs a restart or version verification before user smoke.

## Commit Readiness

Safe to commit with exact-hunk staging only.

## Suggested Next Step

Have the user retest:

`https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=app-sign-align-20260618`
