# Steel Guitar Q&A CTA Link Alignment

## Task summary

Updated the landing-page `Open Q&A →` control to match the other three orange text-and-arrow actions. The control remains a semantic button that opens the existing in-page Q&A workspace. The active-E9-setup note now sits immediately above the action in a bottom-aligned footer group.

Intentionally unchanged: Q&A launch JavaScript, example-question behavior, answer routing, backend APIs, auth, Cloudflare policy, corpus/vector data, and all other card content.

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- This handoff

No files were deleted and no generated artifacts were added.

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `node --check ui/landing-home.js` — passed.
- Inline script parsing with `vm.Script` — passed; 1 inline script parsed.
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py -k 'not test_backstage_plan_and_activity_uses_all_approved_assets'` — 74 passed.
- `git diff --check` — passed.
- Local desktop browser at 1440×900 — visual pass against the user-provided reference; all four action bottoms matched exactly (0px spread), Q&A had the same orange color, transparent background, no border, no radius, 0px padding, and 44px action height.
- Local narrow browser at 520×1125 — visual pass; page, every product card, and Q&A card had zero horizontal overflow.
- `Open Q&A` opened the existing blank Q&A workspace; the example question opened the same workspace with `Show me a classic country move.` prefilled.
- Browser warning/error count — zero.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8771/ui/steel-guitar-rag-mock.html?v=qa-cta-local-20260715`
- Cache-busted URL tested: `http://127.0.0.1:8771/ui/steel-guitar-rag-mock.html?v=qa-cta-local-20260715`
- Exact URL the user should use: pending protected-preview promotion
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: static loopback server at `http://127.0.0.1:8771`
- Expected backend port: 8771
- Expected git HEAD: pre-commit working tree based on `a4472e4`
- Version endpoint: not available on the static local server
- Version endpoint result: not available
- If version endpoint missing, how version is inferred: inspected working-tree diff based on `a4472e4`
- Whether app root `/` works: static directory listing only; not used as app proof
- Whether app root `/` is expected to work: no for this local static smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: local loopback as proof of protected-preview behavior
- Known caveats: protected-preview browser smoke remains required after exact-release promotion

## Integration notes

The stylesheet query key changed to `qa-cta-link-20260715` so the protected browser receives the new CSS. The shared `home-card-link` class supplies the action's typography, color, hover underline, and 44px target; Q&A-specific CSS only resets native button chrome. No public API, schema, component event, or data contract changed.

## Risk assessment

Low. The change is isolated to landing-card markup/style and focused assertions. Rollback is the implementation commit revert or activation of the prior exact detached release.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-15-1511-06-qa-cta-link-alignment.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-15-1435-12-origin-recovery-final.md`
- All protected/private/corpus/vector/deployment/auth/generated paths and all other unrelated files

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 exact-release activation and authenticated protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

Stage only the five listed files, commit the green UI slice, promote that exact commit with the hardened detached-release workflow, and verify the cache-busted protected URL at desktop and narrow widths.
