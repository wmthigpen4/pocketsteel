# 2026-06-27 11:21 - Lane 06 - Landing Explorer / Brain Redesign

## Task Summary

Requested: redesign the public landing page so the Fretboard Explorer and Steel Guitar Brain read as two clear product experiences, with the Explorer as the first-class visual anchor and the Brain as a companion help path.

Completed:
- Reworked the public static landing source around an Explorer-first hero.
- Added top navigation for `Fretboard Explorer`, `Ask the Brain`, `Modes`, `Why it works`, and `Access`.
- Added a large CSS/SVG E9 fretboard preview above the fold.
- Added two product cards: `Fretboard Explorer` and `Steel Guitar Brain`.
- Added five Explorer mode cards: `Single Grip`, `Harmonized Path Scale`, `Single-Note Finder`, `Chord Finder`, and `Voicing Identifier`.
- Moved Brain presentation into a compact lower band with prompt chips, not a dominant chat panel.
- Preserved the existing private-preview interest form and static/public safety posture.
- Synced `deploy/landing/index.html` to match `ui/steel-guitar-rag-landing.html`.

Intentionally not changed:
- No auth, DNS, Cloudflare Access, deployment config, backend routes, corpus, Chroma/vector stores, embeddings, scraping, private source data, or brand/raw visual assets were changed.
- No public link to the private app shell was added; public CTAs remain public-safe anchors or interest-form access paths.
- No broad rename was performed.

## Branch And Head

- Branch: `feature/answer-api`
- Starting HEAD: `02d9f89`
- Final HEAD / commit: included in the final task response after exact-path commit.

## Files Changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-06-27-1121-06-landing-explorer-brain-redesign.md`

## Tests And Checks

Passed:

```bash
.venv/bin/python -m pytest tests/test_public_landing_page.py -q
# 33 passed

.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py -q
# 12 passed

git diff --check
# passed
```

Not run:
- `node --check ui/answer-client.js` and `node --check ui/pedal-steel-fretboard.js`: not touched.
- `tests/test_frontend_answer_ui.py` and `tests/test_pedal_steel_fretboard_ui.py`: shared app shell / fretboard renderer files were not touched.
- Protected-preview smoke: not run in this Lane 06 implementation pass. The local app server root currently redirects to the private app shell, so protected root behavior needs Lane 12 confirmation before treating root as the public landing target.

## Local Browser Smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/steel-guitar-rag-landing.html?v=landing-explorer-brain-local-visual-2`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/steel-guitar-rag-landing.html?v=landing-explorer-brain-local-visual-2`
- Exact URL the user should use: local direct static landing path above, or the deployed public landing route after deployment
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `02d9f89` plus working-tree landing changes before commit
- Version endpoint: not used
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: local working-tree static file content and cache-busted URL
- Whether app root `/` works: yes, but it redirects to the app shell
- Whether app root `/` is expected to work: yes, as existing app-shell redirect in this local server
- Whether `/ui/steel-guitar-rag-mock.html` works: not retested for this static landing slice
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally; user after public/protected preview routing is confirmed
- Do not test these URLs: do not treat `http://127.0.0.1:8770/` as proof of the static public landing page because it redirects to the app shell locally
- Known caveats: local root is not the static public landing page in the same-origin app server

Local smoke observations:
- Desktop check found the Explorer hero, large fretboard preview, five mode cards, and compact Brain band.
- Tablet/mobile checks showed no page-level horizontal overflow.
- Mode section appears before the Brain section.
- Browser console had no relevant errors.
- Local root `http://127.0.0.1:8770/?v=landing-explorer-brain-local-root` redirected to `http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html`, which is existing local app-server behavior.

## Behavior Changed

- The landing page no longer presents the Brain/chat experience as the dominant first impression.
- The first hero section now immediately names both products and visually anchors on an E9 fretboard preview.
- The Fretboard Explorer is represented in nav, primary CTA, hero visual, product card, and mode cards.
- The Steel Guitar Brain remains visible in nav, secondary CTA, product card, and compact help band.
- The Brain band uses example prompt chips and a static/faux input; it does not submit or imply live public AI access.

## Risk Assessment

Risk: medium-low.

Why:
- Scope is isolated to the public static landing source, deploy copy, and landing tests.
- Static HTML changes are broad visually, but no backend/app runtime files were touched.
- Root-route ambiguity remains: the local same-origin server redirects `/` to the app shell, so Lane 12 must confirm the actual public/protected landing route before user smoke.

Rollback:
- Revert the scoped commit touching the two landing HTML files, landing tests, and this handoff.

## Human Decision Needed

No for the implemented slice.

Potential product/routing decision:
- Decide whether protected/public root should serve this redesigned static landing page or continue redirecting to the private app shell. This implementation does not change routing.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-06-27-1121-06-landing-explorer-brain-redesign.md`

## Files That Must Not Be Staged

- Existing unrelated dirty/parked files, including but not limited to:
  - `README.md`
  - `corpus_metadata/source_policies/README.md`
  - `corpus_metadata/source_registry.json`
  - `docs/answer-eval-report.md`
  - `docs/cloudflare-pages-landing.md`
  - `docs/copyright-provenance.md`
  - `docs/corpus-license-policy.md`
  - `docs/current-commands.md`
  - `docs/source-inbox-inventory.md`
  - `rag_answer.py`
  - `rag_build_clean_corpus.py`
  - `rag_chunk_corpus.py`
  - `rag_embed_chroma.py`
  - `source-inbox/inventory.json`
  - `ui/brand/steel-guitar-rag-landing-alpha.webm`
  - `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
  - any `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, `source-inbox` raw/provenance data, `.wrangler/`, DNS/deploy secrets, `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, or generated corpus/private artifacts.

## Commit Readiness

Safe to commit after exact-path staging and staged diff review.

## Recommended Next Lane

Lane 12 protected-preview / public route smoke.

Suggested prompt:

```text
Lane 12: Run protected/public landing smoke for the redesigned landing page at the exact cache-busted static landing URL and confirm whether root `/` should serve the landing page or continue redirecting to the app shell. Verify the Fretboard Explorer is the first-class hero, the Brain is compact and secondary, and no private app route is exposed from the public landing page.
```
