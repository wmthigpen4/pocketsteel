# 2026-06-27 16:40 - Lane 06 - Dark Premium Landing Redesign

## Task Summary

Redesigned the public static landing page to match the attached dark premium references: black/brown stage background, gold/orange accents, top-left neon hanging sign, Explorer-first hero, polished fretboard preview, mode cards, secondary Steel Guitar Brain section, trust cards, and an early-access/full-explorer CTA.

Intentionally not changed:
- Root routing.
- Auth, DNS, Cloudflare Access, deployment config, backend answer routing, corpus, Chroma/vector stores, embeddings, scraping, source records, or private data.
- Brand/sign assets.
- Public app-shell exposure from the static landing page.

## Files Changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-06-27-1640-06-dark-premium-landing-redesign.md`

## Visual Reference Match

Implemented:
- Dark stage-lit background using the existing stage asset plus warm radial light/glow layers.
- Compact sticky dark header with hanging sign at top-left, nav links, and gold/dark CTA buttons.
- Large serif hero headline: `Explore the neck. Ask better questions.`
- Right-side premium app preview with a mini E9 fretboard and companion Brain panel.
- Two-path Explorer/Brain section.
- Five Explorer mode cards: Single Grip, Harmonized Path Scale, Single-Note Finder, Chord Finder, Voicing Identifier.
- Compact Brain panel with prompt chips.
- Trust/why-it-works cards without fake review counts.
- `Unlock the full explorer` monetization section routed to early access instead of implying live payments.

## Tests And Checks

Passed:

```bash
git diff --check
.venv/bin/python -m pytest tests/test_public_landing_page.py -q
.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py -q
```

Results:
- `tests/test_public_landing_page.py`: 34 passed.
- `tests/test_same_origin_smoke_server.py`: 12 passed.

## Local Browser Smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/steel-guitar-rag-landing.html?v=dark-premium-landing-local-2`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/steel-guitar-rag-landing.html?v=dark-premium-landing-local-2`
- Exact URL the user should use: pending protected-preview smoke after commit
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: local uncommitted UI slice during smoke
- Version endpoint: not used for local static smoke
- Version endpoint result: not applicable
- Whether app root `/` works: not tested in local smoke
- Whether app root `/` is expected to work: root currently redirects to app shell, not the static landing page
- Whether `/ui/steel-guitar-rag-mock.html` works: not part of this smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex before commit; user after protected-preview smoke
- Do not test these URLs: uncache-busted landing URL for this slice
- Known caveats: root routing remains unchanged

Verified desktop:
- Page loads.
- Dark premium stage direction is present.
- Top-left neon/sign branding appears.
- Hero is Explorer-first.
- Large app preview renders.
- Five mode cards render.
- Brain section and pricing/full-explorer CTA render.
- No page-level horizontal overflow.
- No `[object Object]`.
- Browser console had no relevant warnings/errors.

Verified narrow/mobile viewport:
- Page loads.
- Header sign/actions/nav stack without horizontal overflow.
- Five mode cards remain present.
- Pricing section remains present.
- No page-level horizontal overflow.
- No `[object Object]`.
- Browser console had no relevant warnings/errors.

## Integration Notes

- `ui/steel-guitar-rag-landing.html` and `deploy/landing/index.html` are intentionally identical.
- The static landing page still avoids `/api/answer`, app-shell URLs, Chroma references, SGF URLs, and Stripe claims.
- `Open app` and full-access CTAs route to early access/interest form, not a public app or payment flow.
- The page still references local static assets only:
  - `assets/steel_on_stage2.png`
  - `brand/steel-guitar-rag-landing-alpha.webm`
  - `brand/steel-guitar-rag-landing-fallback-alpha.png`

## Risk Assessment

Risk: medium.

Reason:
- This is a full static landing page redesign, not a small copy change.
- Scope is contained to the public landing HTML, deploy mirror, and focused landing tests.
- Root routing remains unchanged and must be reported during protected smoke.

Rollback:
- Revert the landing HTML/test commit.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-06-27-1640-06-dark-premium-landing-redesign.md`

## Files That Must Not Be Staged

- Existing unrelated dirty/untracked corpus, source-inbox, RAG scripts, brand/public asset work, raw design assets, generated reports, and parked docs.

## Recommended Next Lane

Lane 12 protected-preview smoke after exact-path commit.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit the scoped landing redesign, then smoke:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-landing.html?v=dark-premium-landing-<commit>
```
