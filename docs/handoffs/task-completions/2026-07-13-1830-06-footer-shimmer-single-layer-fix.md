# Footer shimmer single-layer fix

## Task summary

Fixed the landing footer shimmer that displayed a second copy of `Powered by source-aware AI underneath.` above the real label. The animated gradient now renders directly on the button's actual text rather than on a duplicated pseudo-element.

Removed the unused `data-text` duplicate source and preserved the existing button behavior, popover, wording, animation, and reduced-motion fallback.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Task mode: GREEN smoke-blocking UI bug fix under the approved Autopilot loop.

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `tests/test_landing_home_ui.py`
- `docs/handoffs/task-completions/2026-07-13-1830-06-footer-shimmer-single-layer-fix.md`

No shared shell stylesheet, asset, backend, auth, corpus, Cloudflare, or deployment configuration changed.

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `node --check ui/landing-home.js` — passed.
- Focused frontend/fretboard suite — `94 passed in 2.96s`.
- Full Python suite — `1035 passed in 48.83s`.
- Scoped `git diff --check` — passed.
- Local desktop and below-700-pixel browser checks — passed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=footer-shimmer-local-1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: 8897
- Expected git HEAD: working tree on `9ce9fd7c7fa2e20c76dbd6f12eeb19b8ec7a5cfc`
- Version endpoint: not used for local visual smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted HTML served directly from the scoped working tree
- Whether app root `/` works: not tested in this focused local smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: historical cached preview URLs or the public marketing page
- Known caveats: the viewport override reported an effective width below 700 pixels but not the requested device width; the mobile breakpoint was still exercised.

Browser assertions:

- One visible button text node remained.
- No `data-text` duplicate source remained.
- The `::after` generated content computed to `none`.
- The actual text computed to `background-clip: text` with the shimmer animation active.
- The control retained a single 44-pixel line box.
- Desktop and mobile layouts had zero document overflow.

## Integration notes

The effect uses `.home-ai-footer .footer-trigger.footer-shimmer` specificity so the shared transparent-button reset cannot erase the text gradient. Reduced-motion mode stops the animation and leaves the readable base gradient in place.

## Risk assessment

Low. This is an isolated CSS implementation change inside the landing HTML. Rollback is the single scoped commit.

## Human decision needed

No. The user reported the duplicate text as a visual defect.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `tests/test_landing_home_ui.py`
- `docs/handoffs/task-completions/2026-07-13-1830-06-footer-shimmer-single-layer-fix.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Earlier unstaged coordination handoffs.
- Every unrelated dirty/untracked path, including protected brand, public, corpus, source-inbox, backend, private-data, auth, Cloudflare, vector, embedding, and deployment artifacts.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for authenticated protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the three exact paths, update the protected preview, and verify a single aligned shimmer line at desktop and mobile widths.
