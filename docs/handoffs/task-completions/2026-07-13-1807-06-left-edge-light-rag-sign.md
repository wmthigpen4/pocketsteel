# Left-edge light-RAG landing sign restoration

## Task summary

Restored the previously approved transparent hanging-sign artwork with bright cream `RAG` lettering and corrected the product-first shell regression that anchored the sign to the centered content container.

Completed:

- Replaced the landing alpha artwork references with the existing transparent hanging-sign WebM and PNG fallback explicitly requested by the user.
- Anchored the sign mount to approximately `-12px` from the viewport edge at every breakpoint.
- Increased desktop width from 250px to 350px (40%).
- Increased mobile width from 210px to as much as 290px (about 38% at the tested mobile breakpoint).
- Reserved layout space so the larger sign does not overlap navigation or hero content.
- Restored the approved mobile behavior that uses the static PNG fallback below 520px.
- Added regression coverage for the asset paths, viewport-edge geometry, responsive sizing, and same-origin asset serving.

Intentionally unchanged: answer-state badge, product copy, workspace routes, fretboard preview, backend, auth, corpus, source policy, DNS, Cloudflare configuration, public landing page, and unrelated brand/design assets.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lane: `19 Visual Design / Assets`
- Task mode: YELLOW UI adjustment explicitly approved through user-smoke feedback. The user explicitly named the logo/artwork, authorizing the two exact `ui/brand/` runtime assets in this slice.

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/brand/steel-guitar-rag-hanging-sign.webm` (existing approved asset, newly tracked by this slice)
- `ui/brand/steel-guitar-rag-hanging-sign-fallback.png` (existing approved asset, newly tracked by this slice)
- `tests/test_frontend_answer_ui.py`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1807-06-left-edge-light-rag-sign.md`

No files were deleted or regenerated.

Asset hashes:

- WebM: `67506fce419ae54c03794b6b020365b5eefb3b9bbda6870f8f6804b909fb4d82`
- PNG: `80dbb09d1e1baf087d7c7dc49f560f1bbc6d9b6578a7d06efda6a49ba9cf8220`

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `node --check ui/landing-home.js` — passed.
- `.venv/bin/python -m pytest -q tests/test_frontend_answer_ui.py tests/test_landing_home_ui.py tests/test_same_origin_smoke_server.py tests/test_smoke.py` — `55 passed`.
- `.venv/bin/python -m pytest -q` — `1035 passed in 49.47s`.
- Scoped `git diff --check` — passed.
- Local browser smoke — passed.
- Browser console logs — empty.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=light-rag-sign-mobile-390-2`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: 8897
- Expected git HEAD: working tree on `db7cbd4cb44376fa1b9ea44b890708e21b40e893`
- Version endpoint: not used for the local visual check
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted local assets served directly from the scoped working tree
- Whether app root `/` works: not tested in this focused visual smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: historical cached protected-preview URLs or the public marketing landing page
- Known caveats: the in-app responsive viewport capability reports a scaled layout viewport; both narrow breakpoint checks activated the mobile rules and produced zero document overflow.

Browser geometry:

- Desktop: sign `left=-11.99`, `width=350`, `bottom=248.52`; hero `top=260`; no navigation or hero overlap.
- Mobile breakpoint: sign `left=-11.99`, `width=290`, `bottom=207.5`; navigation `top=215`; hero `top=392.91`; no overlap.
- Document overflow: zero at desktop and narrow breakpoints.
- Desktop uses the animated WebM; mobile uses the bright-`RAG` PNG fallback.

## Integration notes

The two hanging-sign assets existed in the working tree but were previously untracked. This slice tracks only those exact user-approved runtime assets so the restored logo is reproducible from the commit rather than depending on local untracked files.

No public API, schema, route, answer, auth, corpus, source, or deployment contract changed.

## Risk assessment

Low. The change is isolated to home-state sign assets/layout and focused tests. The larger sign has explicit no-overlap and no-overflow browser checks. Rollback is one scoped commit.

## Human decision needed

No. The user directly selected the prior light-`RAG`, far-left treatment and requested a 30–50% size increase.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/brand/steel-guitar-rag-hanging-sign.webm`
- `ui/brand/steel-guitar-rag-hanging-sign-fallback.png`
- `tests/test_frontend_answer_ui.py`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1807-06-left-edge-light-rag-sign.md`

## Files that must not be staged

- Existing dirty `ui/brand/steel-guitar-rag-landing-alpha.webm`
- Existing dirty `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `docs/handoffs/task-completions/integration-status.md`
- `Neon Sign/`, `public/`, deploy assets, and every other unrelated dirty/untracked file.
- Backend, corpus, source-inbox, auth, DNS, Cloudflare, secret, vector, embedding, and generated-data paths.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Stage exactly the eight approved paths, commit the restored sign, restart the protected-preview runtime, and verify the authenticated cache-busted app at desktop and mobile breakpoints.
