# Mobile Safari hero-sign poster artwork fix

## Task summary

- Requested: remove the red/yellow contour artifacts shown by the hanging sign on iPhone Safari, preserve the exact artwork and placement, use `steel-guitar-rag-hanging-sign-poster.png` for any fallback, and never use `steel-guitar-rag-hanging-sign-fallback.png`.
- Lane: `06 UX/UI Design`, with focused Lane 15 QA and Lane 01 exact-path commit readiness.
- Task mode: user-smoke UI bug fix under the approved autopilot loop.
- Completed: touch/coarse-pointer and narrow screens now hide the video even after animation initialization and show the exact 800×600 transparent poster PNG. Desktop video behavior remains unchanged.
- Intentionally unchanged: all hero-sign geometry, header layout, product copy, interest capture, API/backend behavior, auth, DNS, Tunnel, Access policy, database, corpus/vector data, private data, and secrets.

## Files changed

- `ui/hero-hanging-sign.css`
- `deploy/landing/hero-hanging-sign.css`
- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_public_landing_page.py`
- `tests/test_frontend_answer_ui.py`
- This handoff.

No files were deleted or generated. The existing poster asset was reused without modification.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py tests/test_frontend_answer_ui.py` — `100 passed in 3.73s`.
- `node --check ui/landing-home.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- Source/deploy landing HTML byte identity — passed.
- Source/deploy hero CSS byte identity — passed.
- Static forbidden-asset scan for `steel-guitar-rag-hanging-sign-fallback.png` in app/public/deploy HTML — passed; no matches.
- `git diff --check` — passed.
- Local narrow browser smoke — poster displayed, video hidden, exact poster source, natural size 800×600, x −12/y −10/width 290/height 217.5, zero horizontal overflow, zero console errors.
- Local desktop browser smoke — video displayed, poster hidden, x −12/y −14/width 350 at the observed wide viewport, zero overflow, zero console errors.

## Integration notes

- The artifact is specific to the HEVC-alpha rendering path selected by iPhone Safari. CSS now bypasses that rendering path on touch/coarse-pointer and ≤520px screens.
- The mobile image element already points to `brand/steel-guitar-rag-hanging-sign-poster.png`; the old fallback filename is absent from both page implementations.
- The shared stylesheet query changed to `mobile-poster-safari-20260716-3` so Safari cannot reuse the prior mobile-video rule.
- No geometry declaration was edited.

## Risk assessment

- Low. Mobile changes only which existing media element is visible. Placement remains governed by the unchanged shared geometry.
- Rollback is the scoped commit or prior Pages deployment, though rollback would restore the observed Safari artifact.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `ui/hero-hanging-sign.css`
- `deploy/landing/hero-hanging-sign.css`
- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_public_landing_page.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-07-16-0938-06-mobile-safari-poster-artwork-fix.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` in the implementation commit.
- Existing parked Lane 12/Lane 20 handoffs.
- Runtime releases, environment files, logs, `.wrangler/`, corpus/vector data, source-inbox, private data, secrets, and generated artifacts.

## Recommended next lane

- Lane 01 exact-path commit, then Lane 12 Pages deployment and native-iPhone user smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the listed paths, deploy `deploy/landing` from the exact commit, and verify the cache-busted `www` URL before asking for native-iPhone confirmation.
