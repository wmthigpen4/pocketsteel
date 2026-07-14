# Mobile Safari logo transparency fix

## Task summary

Fixed two user-smoke logo regressions:

- Touch devices now use a clean transparent static hanging-sign image instead of the alpha WebM. This avoids the red/yellow RGB matte Safari exposed when the phone rotated to landscape.
- Answer mode now renders its transparent compact badge as a normal PNG image rather than placing it inside a video element that Safari painted as a black rectangle.

The landing sign remains anchored at the upper-left with the existing responsive size and position. No workspace layout, answer content, auth, backend, or deployment behavior changed.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lane: `19 Visual Design / Assets`
- Mode: Autopilot user-smoke bug fix

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- This handoff

The static hanging-sign PNG already existed locally and matches the previously committed Cloudflare-login artwork hash. It was not modified during this task; it is added to the app asset path so the runtime does not depend on an unrelated untracked file.

## Tests and checks

- `node --check ui/answer-client.js` — passed
- `node --check ui/pedal-steel-fretboard.js` — passed
- `node --check ui/landing-home.js` — passed
- Focused UI suite — `95 passed in 2.96s`
- Full suite — `1036 passed in 47.65s`
- Scoped `git diff --check` — passed
- Local browser smoke — passed

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=mobile-logo-local-1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: 8897
- Expected git HEAD: working tree based on `311b88deab08200d78b54ed2ce3e5924a207ce29`
- Version endpoint: not used for working-tree smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted static files served directly from the scoped working tree
- Whether app root `/` works: not tested in this focused smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: historical cached logo URLs
- Known caveats: desktop browser automation cannot emulate iPhone Safari's alpha-WebM compositor; the regression is prevented structurally by the touch-pointer media rule and clean PNG fallback.

Browser assertions:

- Home animation remains available on non-touch desktop.
- The fallback source resolves to the clean transparent static hanging-sign PNG.
- Answer mode contains one `IMG`, no video, for the badge.
- The badge image and its button both compute to transparent backgrounds.
- The badge loaded at its expected intrinsic 1500×433 dimensions.
- No document overflow occurred.

## Integration notes

The key compatibility boundary is `(hover: none) and (pointer: coarse)`. Touch devices use the PNG at every orientation, while pointer-based desktop browsers retain the alpha animation. The existing below-520-pixel and reduced-motion fallbacks continue to work.

## Risk assessment

Low. The change narrows media behavior on touch devices and simplifies answer-logo markup. Rollback is the scoped commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1949-06-mobile-safari-logo-fix.md`

## Files that must not be staged

- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `docs/handoffs/task-completions/integration-status.md`
- All unrelated dirty/untracked brand, public, Neon Sign, corpus, source-inbox, backend, auth, Cloudflare, vector, embedding, private-data, and deployment paths.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for authenticated portrait, landscape, and answer-mode protected smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the six exact paths, refresh the protected preview, and verify the clean static sign and transparent answer badge at a cache-busted URL.
