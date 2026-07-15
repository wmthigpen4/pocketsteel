# Left-Anchored Public Hanging Sign

## Task summary

Fixed the public landing header after user smoke identified that the responsive layout centered the hanging Steel Guitar RAG sign and allowed it to overlap the Private Preview and launch-invite controls.

The sign bracket is now pinned to the left viewport edge at every tested width. Tablet widths retain the two-column header so the actions stay at the upper right. Phone widths place the action row below the sign while keeping the bracket at `x=0`. No transform-based centering remains.

## Lane classification

- Primary lane: 06 UX/UI Design
- Supporting lanes: 15 QA, 01 Repo Steward, 12 Pages deployment smoke
- Task type: responsive UI user-smoke fix
- Task mode: Autopilot user-smoke adjustment

## Files changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- This handoff

No app runtime, backend, Access policy, DNS, Tunnel, secret, corpus/vector, private-data, or source visual asset was changed.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_public_landing_page.py` — 47 passed.
- Source/deploy HTML byte comparison — passed.
- `git diff --check` — passed.
- Local browser at the reported 857×874 viewport — sign bounding box `x=-12`, no transform, no sign/action overlap, zero header/page overflow, clean browser logs.
- Local browser at 520×1125 — sign `x=0`, sign bottom 213px, actions top 225px, no overlap, zero header/page overflow.
- Local browser at 375×900 — sign `x=0`, sign bottom 213px, actions top 225px, no overlap, zero header/page overflow; signup remained above the fold.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8771/?v=left-anchor-local-857`
- Cache-busted URL tested: URL above; 520px and 375px checks used matching `left-anchor-local-*` query values
- Exact URL the user should use: pending Pages deployment of the exact commit
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8771`
- Expected backend port: 8771
- Expected git HEAD: pending exact-path commit
- Version endpoint: not available for the public static landing
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: source/deploy byte identity and exact committed Pages input
- Whether app root `/` works: yes for local Pages output
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not exposed by public Pages output
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no on the public hostname
- Who should test this URL: Codex locally; both after production deployment
- Do not test these URLs: local loopback as proof of production behavior
- Known caveats: production root/`www` must be rechecked after promotion

## Integration notes

- The removed rule was `.home-sign { left: 50%; transform: translateX(-50%); }` inside the 1099px breakpoint.
- At widths above 720px the existing left-edge calculation remains authoritative.
- At widths of 720px and below the sign uses `left: calc((100vw - 100%) / -2)` and `transform: none` so the bracket aligns exactly with the viewport edge.
- Header actions wrap safely and never share the sign’s occupied rectangle.

## Risk assessment

Low. The change is isolated to public landing responsive header CSS plus a focused regression test. Rollback is the prior Pages deployment.

## Human decision needed

No. The user explicitly specified left-edge anchoring.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-07-15-1619-06-left-anchored-hanging-sign.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-15-1435-12-origin-recovery-final.md`
- `docs/handoffs/task-completions/2026-07-15-1517-12-qa-cta-promotion-blocker.md`
- `docs/handoffs/task-completions/2026-07-15-1543-12-locked-launch-landing-pages-smoke.md`
- `docs/handoffs/task-completions/2026-07-15-1606-12-app-home-locked-landing-pages-smoke.md`

## Recommended next lane

Lane 01 exact-path commit followed by Lane 12 Pages-only production deployment and browser smoke at the reported viewport.

## Commit readiness

Safe to commit

## Suggested next step

Commit the four exact files, deploy only `deploy/landing` to the existing Pages production branch, and verify the left anchor on root and `www` at 857px and phone widths.
