# App-Home Locked Landing Rebuild

## Task summary

Rebuilt the public launch-invite page after user feedback that the first pass did not represent the product strongly enough. The public page now follows the protected app home page’s structure and visual system instead of using a generic split hero and invented miniature previews.

The page uses the app home’s real 10-string E9 Fretboard Explorer renderer for the large product demonstration and reuses the same Fretboard Explorer, Melody Studio, Lessons, and Steel Guitar Q&A card structures, copy, notation preview, lesson preview, and Q&A spotlight artwork. Every product workspace remains non-interactive and ends with a lock plus `Coming at launch`; the invite form is the only data-entry control.

Intentionally unchanged: `/api/interest`, D1 schema/data rules, protected app runtime, `/api/answer`, Cloudflare Access policy, DNS, Tunnel, auth, payments, corpus/vector data, secrets, and private sources.

## Lane classification

- Primary lane: 06 UX/UI Design
- Supporting lanes: 15 QA, 01 Repo Steward, 12 Pages deployment smoke
- Task type: mixed UI, test, commit, and approved Pages-only deployment
- Task mode: user-approved Autopilot adjustment; no new RED action beyond the already approved Pages-only deployment

## Files changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `deploy/landing/pedal-steel-fretboard-styles.js` (exact deployment copy)
- `deploy/landing/pedal-steel-fretboard.js` (deployment copy with protected Explorer handoff URLs removed)
- `deploy/landing/melody-score.js` (exact deployment copy)
- `deploy/landing/landing-home.js` (exact deployment copy)
- `deploy/landing/assets/landing/melody-score.png` (existing app asset copied for Pages)
- `deploy/landing/assets/landing/spotlight.png` (existing app asset copied for Pages)
- `deploy/landing/brand/pedal-steel-fretboard-background.svg` (existing app asset copied for Pages)
- This handoff

No source app renderer, source visual asset, backend, auth, deployment configuration, or database file was modified. The public deployment copy of the fretboard renderer returns no Explorer handoff URL, so the public bundle does not expose the protected `/ui/` route.

## Tests and checks

- `cmp -s ui/steel-guitar-rag-landing.html deploy/landing/index.html` — passed.
- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py` — 46 passed.
- `node --check` for the four deployed preview scripts — passed.
- Inline landing JavaScript parse through `vm.Script` — passed; one inline script parsed.
- Static forbidden-string scan across `deploy/landing` — clean for private app/API/runtime/auth/payment strings.
- Production asset cache-bust revision `locked-public-app-home-2-20260715` prevents a pre-propagation fallback response from shadowing the new preview scripts or Q&A artwork.
- `git diff --check` — passed.
- Local desktop browser at 1440×1000 — full app-home visual pass; invite form above the fold; real 10-string fretboard mounted; four locked cards; zero card controls; zero Explorer controls; one form; one submit button; zero page overflow; clean browser logs.
- Local narrow browser at 520×1125 — form above the fold; real fretboard mounted; four 496px single-column cards; zero card overflow; zero page overflow; zero card controls; clean browser logs.
- Visual comparison confirmed the large Fretboard Explorer, notation preview, lesson block, and Q&A spotlight match the protected app home’s corresponding presentation.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8771/?v=app-home-rebuild-desktop`
- Cache-busted URL tested: desktop URL above; narrow used `http://127.0.0.1:8771/?v=app-home-rebuild-mobile`
- Exact URL the user should use: pending Pages deployment of the exact commit
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: static Pages output at `http://127.0.0.1:8771`
- Expected backend port: 8771
- Expected git HEAD: pending exact-path commit
- Version endpoint: not available for the public static landing
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: source/deploy byte comparison and exact committed Pages input
- Whether app root `/` works: yes for the local Pages output
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not exposed by the public Pages output
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no on the public hostname; the separate app hostname remains Access-protected
- Who should test this URL: Codex locally; both after production deployment
- Do not test these URLs: local loopback as proof of production Pages or anonymous Access behavior
- Known caveats: production root/`www`, D1 capture, and anonymous app Access challenge must be reverified after deployment

## Integration notes

- The public page reuses app-home renderers only for static presentation. The rendered Fretboard Explorer has no links, buttons, inputs, or selectors in the DOM, and its stage has pointer events disabled.
- All four workspace articles have zero anchors, buttons, or form controls.
- The only links are skip/home/invite anchors within the public page; there is no `/ui/` or protected-app link in the landing HTML.
- The only transmitting control is the existing email-only `/api/interest` form.
- The public name remains `Steel Guitar RAG`; no broad rename was made.

## Risk assessment

Low to medium. The visual change is substantial, and the Pages artifact is larger because it now includes the existing app preview renderer and assets. Runtime risk is bounded to the public static Pages project. Rollback is redeployment of the prior Pages release.

## Human decision needed

No. The requested visual direction and the prior Pages-only rollout approval are explicit.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `deploy/landing/pedal-steel-fretboard-styles.js`
- `deploy/landing/pedal-steel-fretboard.js`
- `deploy/landing/melody-score.js`
- `deploy/landing/landing-home.js`
- `deploy/landing/assets/landing/melody-score.png`
- `deploy/landing/assets/landing/spotlight.png`
- `deploy/landing/brand/pedal-steel-fretboard-background.svg`
- `docs/handoffs/task-completions/2026-07-15-1558-06-app-home-locked-landing-rebuild.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-15-1435-12-origin-recovery-final.md`
- `docs/handoffs/task-completions/2026-07-15-1517-12-qa-cta-promotion-blocker.md`
- `docs/handoffs/task-completions/2026-07-15-1543-12-locked-launch-landing-pages-smoke.md`
- All protected app source, source brand/design assets, auth, DNS, Tunnel, secret, corpus/vector, private, generated, and unrelated files

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 deployment of only `deploy/landing` to the existing Pages project and production root/`www` smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the exact listed files, deploy the committed Pages directory to the production branch, then verify the public UI, one test-classified D1 capture, and the anonymous Cloudflare Access challenge on the app hostname.
