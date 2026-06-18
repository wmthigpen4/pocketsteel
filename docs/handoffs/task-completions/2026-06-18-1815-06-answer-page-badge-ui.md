# 2026-06-18 18:15 06 Answer Page Badge UI

## Task Summary

Lane: 06 UX/UI Design + 01 Repo Steward

Branch: `feature/answer-api`

Starting HEAD: `d937c3b`

Requested:

- Add the missing transparent PNG fallback for the answer-page badge.
- Wire a compact answer-page badge into the answer page header/top-left brand area.
- Do not change landing-page branding, landing sign placement, answer logic, fretboard, tab rendering, citations, backend, Chroma, deployment, or DNS.

Completed:

- Generated `public/brand/steel-guitar-rag-answer-badge-fallback-alpha.png` from the transparent ProRes 4444 master.
- Kept the existing generated WebM at `public/brand/steel-guitar-rag-answer-badge-alpha.webm`.
- Copied the WebM and PNG into `ui/brand/` so the existing `/ui/steel-guitar-rag-mock.html` static asset model can serve them with relative `brand/...` URLs.
- Replaced the answer-state top-left static logo image with a compact WebM-first badge inside the existing `.brand-home` control.
- Added responsive sizing for the answer badge.
- Left the landing-page hanging sign markup and placement unchanged except for pre-existing unrelated dirty cache-bust changes already in the worktree.

## Files Changed

Intended implementation/assets:

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `public/brand/steel-guitar-rag-answer-badge-alpha.webm`
- `public/brand/steel-guitar-rag-answer-badge-fallback-alpha.png`
- `ui/brand/steel-guitar-rag-answer-badge-alpha.webm`
- `ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png`
- `docs/handoffs/task-completions/2026-06-18-1815-06-answer-page-badge-ui.md`

Existing source master used but not intended for staging:

- `public/brand/steel-guitar-rag-answer-badge-alpha-master.mov.mov`

Deleted files: none.

Generated artifacts:

- PNG fallback from frame 3 seconds of the ProRes alpha master.

## Asset Paths

Canonical/generated assets:

- `public/brand/steel-guitar-rag-answer-badge-alpha.webm`
- `public/brand/steel-guitar-rag-answer-badge-fallback-alpha.png`

Runtime copies for the existing `/ui` page static model:

- `ui/brand/steel-guitar-rag-answer-badge-alpha.webm`
- `ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png`

HTML runtime references:

```html
<video class="answer-brand-badge" autoplay muted loop playsinline poster="brand/steel-guitar-rag-answer-badge-fallback-alpha.png" preload="metadata" aria-label="Steel Guitar RAG">
  <source src="brand/steel-guitar-rag-answer-badge-alpha.webm" type="video/webm">
  <img class="answer-brand-fallback" src="brand/steel-guitar-rag-answer-badge-fallback-alpha.png" alt="Steel Guitar RAG">
</video>
```

## Tests And Checks

Passed:

```bash
ffmpeg -y -ss 00:00:03 \
  -i public/brand/steel-guitar-rag-answer-badge-alpha-master.mov.mov \
  -frames:v 1 \
  -pix_fmt rgba \
  public/brand/steel-guitar-rag-answer-badge-fallback-alpha.png
sips -g hasAlpha -g pixelWidth -g pixelHeight public/brand/steel-guitar-rag-answer-badge-fallback-alpha.png
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Results:

- PNG fallback: `hasAlpha: yes`, `1500x433`.
- `tests/test_frontend_answer_ui.py` + `tests/test_pedal_steel_fretboard_ui.py`: 49 passed.
- `git diff --check`: passed.

Known unrelated failure observed:

```bash
.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py -q
```

Result:

- 10 passed, 1 failed.
- Failure: `test_same_origin_server_serves_public_fretboard_background`.
- Cause: existing known `/brand/pedal-steel-fretboard-background.svg` same-origin route caveat documented in `integration-status.md`.
- This task did not change the fretboard background route or asset.

## Local Smoke

Smoke Target:

- Target type: local
- Result type: API/HTTP fallback, not browser smoke
- Exact browser URL tested: not completed; in-app browser blocked local HTTP and file URLs with browser URL policy.
- Cache-busted URL tested by HTTP: `http://127.0.0.1:8896/ui/steel-guitar-rag-mock.html?access=beta_user&v=answer-badge-smoke`
- Exact URL the user should use: local fixture only, not persistent
- Auth required: no
- Auth provider: local fixture
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8896`
- Expected backend port: `8896`
- Expected git HEAD: `d937c3b` plus working-tree badge changes
- Version endpoint: not provided by temporary fixture
- Version endpoint result: not available
- If version endpoint missing, how version is inferred: `git rev-parse --short HEAD`
- Whether app root `/` works: fixture redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes for fixture
- Whether `/ui/steel-guitar-rag-mock.html` works: yes by HTTP fallback
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex via HTTP fallback only; browser verification should be done by Lane 12/protected preview
- Do not test these URLs: production or Cloudflare Access URLs for this local UI slice
- Known caveats: in-app browser blocked local URLs; HTTP fallback is not browser smoke.

HTTP fallback checks passed:

```bash
curl -sS -I 'http://127.0.0.1:8896/ui/steel-guitar-rag-mock.html?access=beta_user&v=answer-badge-smoke'
curl -sS -I 'http://127.0.0.1:8896/ui/brand/steel-guitar-rag-answer-badge-alpha.webm'
curl -sS -I 'http://127.0.0.1:8896/ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png'
curl -sS 'http://127.0.0.1:8896/ui/steel-guitar-rag-mock.html?access=beta_user&v=answer-badge-smoke' | rg 'answer-brand-badge|steel-guitar-rag-answer-badge|hero-hanging-sign|steel-guitar-rag-landing'
curl -sS 'http://127.0.0.1:8896/api/session'
curl -sS -X POST 'http://127.0.0.1:8896/api/answer' -H 'Content-Type: application/json' --data '{"question":"What is my copedent?"}'
```

Results:

- Page returned `200 OK`, `text/html`.
- WebM returned `200 OK`, `video/webm`, `101811` bytes.
- PNG returned `200 OK`, `image/png`, `707389` bytes.
- HTML contained the answer badge markup and retained the landing sign markup.
- Fixture `/api/session` and representative `/api/answer` returned `200 OK`.

## Integration Notes

- The answer page uses `brand/...` relative URLs because `/ui/steel-guitar-rag-mock.html` currently serves `ui/brand` assets. This avoids changing same-origin static routing in this slice.
- The generated canonical assets were also left in `public/brand` per the task requirement.
- The ProRes master remains named `steel-guitar-rag-answer-badge-alpha-master.mov.mov` and was not renamed.
- The full landing-page hanging sign is not reused for the answer-state badge.
- Landing-page sign placement was not intentionally changed.

## Risk Assessment

Risk: medium-low.

Why:

- UI change is limited to the existing answer-state brand button and compact badge CSS.
- No backend/API/schema/retrieval/fretboard/tab/source-card logic changed.
- Browser smoke could not be completed due in-app browser local URL policy; HTTP fallback and frontend tests passed.

Rollback:

- Revert the `.answer-brand-*` CSS and the `.brand-home` video markup.
- Remove the four answer badge runtime/canonical assets if not needed.

## Human Decision Needed

No for this scoped UI slice.

Optional later decision:

- Whether to rename the doubled `.mov.mov` source master in a separate asset hygiene task.
- Whether to consolidate `public/brand` and `ui/brand` static serving in a separate static-server cleanup task.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-mock.html` exact answer-badge hunks only; exclude unrelated landing-sign cache-bust hunk.
- `tests/test_frontend_answer_ui.py` exact answer-badge assertion hunk only; exclude unrelated landing-sign cache-bust hunk.
- `public/brand/steel-guitar-rag-answer-badge-alpha.webm`
- `public/brand/steel-guitar-rag-answer-badge-fallback-alpha.png`
- `ui/brand/steel-guitar-rag-answer-badge-alpha.webm`
- `ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png`
- `docs/handoffs/task-completions/2026-06-18-1815-06-answer-page-badge-ui.md`

## Files That Must Not Be Staged

- `public/brand/steel-guitar-rag-answer-badge-alpha-master.mov.mov`
- The unrelated landing-sign cache-bust hunks in `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py`.
- Existing unrelated dirty/parked files shown by `git status --short`.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, source-inbox raw data, scraping outputs, deployment secrets, `.wrangler/`, DNS config, unrelated raw design assets, and unrelated landing/static files.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment for protected-preview browser verification of the answer page badge.

## Commit Readiness

Safe to commit, if exact-hunk staging excludes the unrelated landing-sign cache-bust hunks and the source master remains unstaged.

## Suggested Next Step

Lane 12: restart/verify protected preview if needed and browser-smoke the answer page at `/ui/steel-guitar-rag-mock.html`, confirming the compact answer badge appears in answer state and does not affect answer, fretboard, tab, or source-card layout.
