# Public Landing Header and RAG Footer Adjustment

## Task summary

Implemented the user-smoke landing-page adjustment:

- changed the header `Private preview` treatment from a pill to a plain lock-and-text status label;
- removed the duplicate header `Get launch invite` link while preserving the hero form and final invite anchor;
- replaced both old footer status lines with the app landing page's centered shimmering `Powered by source-aware AI underneath.` control;
- added the matching accessible RAG explainer dialog with Retrieve/Augment/Generate context, close control, outside-click close, Escape close, focus restoration, and reduced-motion styling;
- preserved the left-anchored hanging sign, email-only D1 form, four locked static workspaces, and protected-app boundaries.

No API, D1, auth, Access policy, DNS, Tunnel, protected app, corpus, vector, secret, schema, or asset change was made.

## Files changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- this handoff

The source and Pages HTML files remain byte-identical.

## Tests and checks

- `python -m pytest -q tests/test_public_landing_page.py` could not start because this host has no `python` alias; this was an environment command issue.
- `python3 -m pytest -q tests/test_public_landing_page.py` could not start because the system Python does not have pytest installed.
- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py` — `49 passed`.
- Inline landing JavaScript parsed with Node `vm.Script` — passed (`1` inline script).
- `node --check ui/landing-home.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `cmp -s ui/steel-guitar-rag-landing.html deploy/landing/index.html` — passed.
- `git diff --check` — passed.
- Static regression coverage verifies plain header status styling, removal of the header CTA, app-matched shimmer/dialog copy, dialog semantics and keyboard handling, old footer-copy removal, email-only form boundaries, and absence of private routes.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8772/?v=rag-footer-local`
- Cache-busted URL tested: `http://127.0.0.1:8772/?v=rag-footer-local-narrow`
- Exact URL the user should use: pending committed Pages production deployment
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8772/`
- Expected backend port: `8772`
- Expected git HEAD: `202f15d5a8475d711fdd9142454fdc07b328e229` plus the scoped landing worktree diff
- Version endpoint: not exposed by the public static landing
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local Pages artifact served directly from `deploy/landing`
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not exposed by this public artifact
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no
- Who should test this URL: Codex
- Do not test these URLs: protected app routes without an authorized Cloudflare Access session
- Known caveats: production Pages smoke remains after the implementation commit

## Browser smoke result

- At `857×874`, the form remained above the fold, the header contained zero invite links/buttons, `Private preview` computed with no border/background/radius, the footer text center delta was `0px`, shimmer animation was active, and horizontal overflow was `0px`.
- The RAG trigger opened one modal dialog, focused the close button, rendered the complete Retrieve/Augment/Generate explanation, closed on Escape, restored trigger focus, and became hidden after its transition.
- At `520×1125`, the hanging sign stayed left anchored (`x=0`), ended at `213px`, the plain status began at `225px` without collision, the form remained above the fold, and horizontal overflow was `0px`.
- The narrow dialog stayed within the viewport (`left=12`, `right=508`, `top=130`, `bottom=995`), stacked the RAG flow, and focused its close control.
- Browser warning/error log: empty.
- No form was submitted during smoke, so production or local interest data was not changed.

## Integration notes

The implementation intentionally copies the app landing page's public-safe RAG explainer behavior and copy into the public landing document. It does not import protected scripts or expose app routes.

## Risk assessment

Low. The change is isolated to public landing header/footer presentation and an in-page explanatory dialog. Rollback is a Pages redeploy of the preceding committed artifact.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-07-15-1635-06-public-rag-footer-adjustment.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-15-1435-12-origin-recovery-final.md`
- `docs/handoffs/task-completions/2026-07-15-1517-12-qa-cta-promotion-blocker.md`
- `docs/handoffs/task-completions/2026-07-15-1543-12-locked-launch-landing-pages-smoke.md`
- `docs/handoffs/task-completions/2026-07-15-1606-12-app-home-locked-landing-pages-smoke.md`
- `docs/handoffs/task-completions/2026-07-15-1622-12-left-anchored-hanging-sign-pages-smoke.md`
- all unrelated, private, corpus, vector, generated, auth, and deployment-policy files

## Recommended next lane

Lane 01 for exact-path commit, followed by Lane 12 Pages production deployment and browser smoke under the already approved public-landing workflow.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the four safe-to-stage paths, deploy that exact commit to the existing `steel-guitar-rag-landing` Pages production branch, verify root/`www`, verify the anonymous app Access challenge, and hand the new cache-busted URL back for user smoke.
