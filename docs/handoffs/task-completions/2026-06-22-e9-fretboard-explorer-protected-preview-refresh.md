# E9 Fretboard Explorer Protected Preview Refresh

## Task Summary

Lane 12 was asked to refresh the protected-preview E9 Fretboard Explorer static surface so it serves the user-smoke UI fix assets from `7622a9b` or later. The protected-preview runtime initially reported `5a3ed58`, but the Explorer HTML still referenced stale internal script cache-bust values from `e9-explorer-browser-surface-20260622`. After the scoped cache-bust fix was committed, the protected preview was restarted and `/api/version` reported the current scoped cache-bust commit SHA.

Completed:
- Updated only the Explorer HTML script query strings to `e9-explorer-user-smoke-fixes-20260622b`.
- Updated the narrow frontend test expectation that pins those script query strings.
- Verified the local protected-preview server serves the refreshed HTML.
- Restarted the protected-preview process on `127.0.0.1:8770` from the scoped cache-bust commit.
- Verified the authenticated protected-preview Explorer URL loads with refreshed script URLs and the expected user-smoke UI behavior.
- Did not change product logic, deployment config, Cloudflare Access, DNS, auth, corpus, Chroma, embeddings, scraper output, assets, or private source data.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded, using authenticated in-app browser context
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: scoped cache-bust commit created by this task
- Version endpoint: `/api/version`
- Version endpoint result: local protected server returned the current scoped cache-bust commit SHA on `feature/answer-api` with `retrieval_mode` `hybrid_private_first` and `auth_provider` `cloudflare_access`
- If version endpoint missing, how version is inferred: not missing locally; direct protected browser navigation to `/api/version` was blocked by browser client, so protected runtime identity is inferred from the local protected server endpoint plus protected asset inventory.
- Whether app root `/` works: not tested for this Explorer-specific refresh
- Whether app root `/` is expected to work: not required for this task
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but out of scope
- Who should test this URL: Lane 15 and the user after this refresh
- Do not test these URLs: stale `?v=e9-explorer-browser-surface-20260622` URLs for user-smoke readiness
- Known caveats: direct browser navigation to protected `/api/version` returned `net::ERR_BLOCKED_BY_CLIENT`; page-context `fetch` is unavailable in the browser automation read-only scope.

## Root Cause

The stale protected-preview behavior came from local source HTML, not a separate deploy artifact. `ui/e9-fretboard-explorer.html` still referenced:

- `pedal-steel-fretboard.js?v=e9-explorer-browser-surface-20260622`
- `e9-fretboard-explorer-data.js?v=e9-explorer-browser-surface-20260622`
- `e9-fretboard-explorer.js?v=e9-explorer-browser-surface-20260622`

The outer page URL cache-bust did not force the browser to reload those internally referenced script URLs.

## Files Changed

- Modified: `ui/e9-fretboard-explorer.html`
- Modified: `tests/test_frontend_answer_ui.py`
- Created: `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-protected-preview-refresh.md`
- Deleted files: none
- Generated artifacts: none

## Protected Preview Refresh Result

The local same-origin server serves `ui/` files directly from the repo, so the refreshed static HTML was visible before restart. The process was then restarted so `/api/version` reported the committed cache-bust refresh SHA.

Restart evidence:

```text
screen session: 35158.steel-rag-private-preview (Detached)
process: Python PID 35161 listening on 127.0.0.1:8770
api/version: current scoped cache-bust commit SHA on feature/answer-api
```

Authenticated browser verification at:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b`

Observed refreshed loaded scripts:

- `https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=e9-explorer-user-smoke-fixes-20260622b`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer-data.js?v=e9-explorer-user-smoke-fixes-20260622b`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.js?v=e9-explorer-user-smoke-fixes-20260622b`

No protected-page script reference used `e9-explorer-browser-surface-20260622`.

## Browser Smoke Result

Pass with caveat noted above for direct `/api/version` browser navigation.

Verified:
- Exact protected URL loaded after Cloudflare Access authentication.
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`.
- H1: `E9 Fretboard Explorer`.
- Key selector rendered as G-only.
- Major / natural minor selector rendered.
- 2-string harmonized scale / 3-string diatonic harmony selector rendered.
- String group selector rendered.
- G major rows displayed.
- 2-string mode changed string-group options to 2-string groups only: `3-5`, `5-6`, `6-10`, `4-6`, `3-4`.
- 2-string mode no longer showed stale 3-string groups.
- Switching to G natural minor from 2-string mode selected 3-string diatonic harmony and showed 32 visible cards.
- G natural minor displayed `G A Bb C D Eb F`.
- G natural minor did not display `G A A# C D D# F`.
- Sharp-oriented E9 mechanical labels remained visible: `F#`, `D#`, `G#`, `Eb/D#`.
- `5-7-8` appeared as advanced E-lower pocket content.
- Partial diminished / partial m7b5 warning text was visible.
- Per-string pedal/lever changes were visible in the detail panel.
- No `[object Object]`.
- No console errors.
- `/brand/pedal-steel-fretboard-background.svg` loaded from protected preview.
- Dense highlight label text was suppressed: `.pedal-steel-fretboard__highlight text` / `[data-highlight-label]` count was `0`.

Not tested:
- Narrow/mobile viewport. This task targeted the stale asset refresh; Lane 15 should rerun the full protected-preview browser smoke at the refreshed URL.
- Landing entry "Explore the E9 Fretboard" from the mock/landing surface.

## Tests and Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log --oneline -5
grep -n "e9-explorer-browser-surface-20260622\\|e9-explorer-user-smoke-fixes" ui/e9-fretboard-explorer.html tests/test_frontend_answer_ui.py
curl -sS "http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b" | grep -nE "script|e9-explorer"
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/pedal-steel-fretboard.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
grep -R -n "e9-explorer-browser-surface-20260622" ui/e9-fretboard-explorer.html tests/test_frontend_answer_ui.py || true
curl -sS http://127.0.0.1:8770/api/version
screen -dmS steel-rag-private-preview zsh -lc "cd /Users/cory/Documents/Pocket\\ Steel && source .venv/bin/activate && set -a && source ~/.steel-rag/env/private-preview.env && set +a && PYTHONPATH=. STEEL_RAG_AUTH_PROVIDER=cloudflare_access STEEL_RAG_ANSWER_AUTH_MODE=production STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first STEEL_RAG_ENABLE_PRIVATE_SOURCES=true STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 STEEL_RAG_RETRIEVAL_DEBUG=false .venv/bin/python scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 --answer-auth-mode production --auth-provider cloudflare-access > /tmp/steel-rag-private-preview-8770.log 2>&1"
lsof -nP -iTCP:8770 -sTCP:LISTEN
curl -sS http://127.0.0.1:8770/api/version
git diff --check
```

Results:

- JS syntax checks: passed.
- `tests/test_pedal_steel_fretboard_ui.py -q`: 31 passed.
- `tests/test_frontend_answer_ui.py -q`: 23 passed.
- `tests/test_fretboard_explorer.py -q`: 11 passed.
- Full pytest: 791 passed.
- `git diff --check`: passed before handoff creation.
- Stale query grep against touched source/test files: no matches.
- Protected-preview restart: passed; detached `screen` process is listening on `127.0.0.1:8770`.
- Post-restart `/api/version`: current scoped cache-bust commit SHA.
- Post-restart protected browser verification: passed at the refreshed URL with refreshed internal script URLs and no console errors.

## Integration Notes

This is a cache-bust/static preview refresh only. No Explorer behavior code changed in this lane. The refreshed exact URL for Lane 15 retest is:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b`

Lane 15 should rerun the full protected-preview browser smoke at that URL, including mobile/narrow viewport if still required.

## Risk Assessment

Risk: low.

Reason:
- The change is limited to static script query strings and the associated test expectation.
- No runtime logic, auth, DNS, deployment config, data, corpus, Chroma, embeddings, or scraper behavior changed.
- Full pytest passed.

Rollback:
- Revert the cache-bust changes in `ui/e9-fretboard-explorer.html` and `tests/test_frontend_answer_ui.py`, or use a newer cache-bust value if another Explorer UI slice lands.

## Human Decision Needed

No.

## Safe-to-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-protected-preview-refresh.md`

## Files That Must Not Be Staged

- Unrelated dirty docs and generated handoff artifacts not listed above.
- `README.md`
- `corpus_metadata/`
- `source-inbox/`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- scraper output
- `.wrangler/`
- DNS/auth/secrets files
- `public/`
- `ui/brand/`
- `Neon Sign/`
- raw visual/design assets

## Recommended Next Lane

Lane 15 QA / Answer Eval.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 15: rerun protected-preview E9 Fretboard Explorer browser smoke at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-user-smoke-fixes-20260622b` and verify the full user-smoke checklist, including mobile/narrow viewport and the landing entry if required.
