# 2026-06-19 11:07 - Lane 06 - Hanging Sign Left-Flush Alignment

## Task Summary

Requested: align the Steel Guitar Rag hanging sign consistently across the public landing page and protected app page.

Completed:

- Used the app page's current sign height/vertical placement as the target.
- Normalized the public landing sign desktop/tablet/mobile top and size rules to match the app sign.
- Moved both app and public sign containers farther left so the visible bracket reads flush to the viewport edge despite transparent left padding in the artwork.
- Preserved sign artwork assets and page copy/CTA/form/backstage behavior.
- Preserved mobile PNG fallback behavior so the prior mobile glow/artwork issue does not regress.
- Updated focused frontend/static tests for the app shell and public landing page.

Intentionally not changed:

- No sign artwork changes.
- No Cloudflare Access, DNS, auth policy, tunnel, backend API, RAG logic, tab engine, corpus, Chroma/vector store, embeddings, scraping, or deployment script changes.
- No copy, CTA behavior, interest form behavior, or backstage behavior changes.

## Relevant Local Instructions

Read before changes:

- `AGENTS.md`: lane task workflow, exact-path staging, no broad staging, no protected path changes.
- `agents.md`: same operating-model content as `AGENTS.md`.
- `README.md`: user-facing app name is Steel Guitar RAG, but current Steel Guitar RAG naming must not be broadly renamed without explicit approval.
- `docs/handoffs/task-completions/integration-status.md`: broad dirty worktree remains parked; exact-path/hunk staging required.

Missing files requested by the prompt:

- `PLAN.md`
- `plan.md`
- root `integration-status.md`

## Files Changed

- `ui/steel-guitar-rag-mock.html`
  - App sign left offset changed from `-12px` / `-14px` to `-18px`.
  - App top/size rules otherwise preserved.
- `ui/steel-guitar-rag-landing.html`
  - Public landing sign desktop/tablet/mobile top/size/transform rules normalized to the app sign.
  - Public sign left offset set to `-18px`.
- `deploy/landing/index.html`
  - Kept deploy artifact matched to `ui/steel-guitar-rag-landing.html`.
- `tests/test_frontend_answer_ui.py`
  - Updated app sign left-offset assertions.
- `tests/test_public_landing_page.py`
  - Added focused public sign placement/asset assertions.
- `docs/handoffs/task-completions/2026-06-19-1107-06-hanging-sign-left-flush-alignment.md`
  - This handoff.

Generated/deploy assets present and included in safe stage scope if committing the current public deploy artifact:

- `deploy/landing/brand/steel-guitar-rag-landing-alpha.webm`
- `deploy/landing/brand/steel-guitar-rag-landing-fallback-alpha.png`

## Before / After Values

### App Page

Desktop/base:

- Before: `left: -12px`
- After: `left: -18px`
- Top unchanged: `top: clamp(-42px, -3vw, -24px)`
- Size unchanged: `width: clamp(300px, 23vw, 340px)`

Tablet:

- Before: `left: -12px`
- After: `left: -18px`
- Top unchanged: `top: 8px`
- Size unchanged: `width: clamp(220px, 30vw, 300px)`

Mobile:

- Before: `left: -14px`
- After: `left: -18px`
- Top unchanged: `top: 8px`
- Size unchanged: `width: clamp(190px, 55vw, 240px)`

### Public Landing Page

Desktop/base:

- Before: `top: 14px; left: 0; width: clamp(240px, 22vw, 360px); transform: translate(-8px, -10px) rotate(-1.5deg);`
- After: `top: clamp(-42px, -3vw, -24px); left: -18px; width: clamp(300px, 23vw, 340px); transform: rotate(-1.5deg);`

Tablet:

- Before: `top: 12px; left: 0; width: clamp(190px, 30vw, 270px); transform: translate(-7px, -8px) rotate(-1.5deg);`
- After: `top: 8px; left: -18px; width: clamp(220px, 30vw, 300px); transform: rotate(-1.5deg);`

Mobile:

- Before: `top: 8px; left: 0; width: clamp(150px, 48vw, 210px); transform: translate(-4px, 0) rotate(-1.5deg);`
- After: `top: 8px; left: -18px; width: clamp(190px, 55vw, 240px); transform: rotate(-1.5deg);`

## Browser Smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested, public desktop: `http://127.0.0.1:8899/?v=sign-align-left-flush-desktop`
- Exact browser URL tested, public mobile: `http://127.0.0.1:8899/?v=sign-align-left-flush-mobile`
- Exact browser URL tested, app desktop: `http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=sign-align-left-flush-desktop`
- Exact browser URL tested, app mobile: `http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=sign-align-left-flush`
- Cache-busted URL tested: the URLs above include `v=sign-align-left-flush-*`.
- Exact URL the user should use after deploy/restart: `https://steelguitarrag.com/?v=<commit>` and `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<commit>`
- Auth required: local app URL no; protected-preview production app yes.
- Auth provider: Cloudflare Access for protected-preview production app only.
- Cloudflare Access login result: not required for local smoke.
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `6f51493` before commit
- Version endpoint: not checked; this was local static/app-shell layout smoke.
- Version endpoint result: not checked.
- If version endpoint missing, how version is inferred: local file server/current working tree and cache-busted URL.
- Whether app root `/` works: not tested in this task.
- Whether app root `/` is expected to work: yes in protected preview, but direct UI URL was the target.
- Whether `/ui/steel-guitar-rag-mock.html` works: yes locally.
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes.
- Who should test this URL: Codex locally; user after Lane 12 protected-preview deployment/restart.
- Do not test these URLs: do not use API fallback as proof of browser smoke.
- Known caveats: local smoke does not prove protected-preview production until Lane 12 restart/deploy smoke runs.

### Measurements

Before patch:

- Public desktop `1280x720`: rect top `-3.37`, left `-8`, width `287.03`, overflow `false`.
- App desktop `1280x720`: rect top `-46.24`, left `-12`, width `305.79`, overflow `false`.
- Public mobile `390x844`: rect top `3.10`, left `-4`, width `190.80`, overflow `false`.
- App mobile `390x844`: rect top `2.39`, left `-14`, width `218.64`, overflow `false`.

After patch:

- Public desktop `1280x720`: rect top `-46.24`, left `-18`, width `305.79`, overflow `false`, console errors `0`.
- App desktop `1280x720`: rect top `-46.24`, left `-18`, width `305.79`, overflow `false`, console errors `0`.
- Public mobile `390x844`: rect top `2.39`, left `-18`, width `218.64`, overflow `false`, console errors `0`.
- App mobile `390x844`: rect top `2.39`, left `-18`, width `218.64`, overflow `false`, console errors `0`.

The public and app sign positions now match at both tested breakpoints, and both are left-clipped enough to compensate for the asset's transparent left padding.

## Tests And Checks

Commands run:

- `git status --short`
- `git diff --name-only`
- `git diff --cached --name-only`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_public_landing_page.py -q`
- `cmp -s ui/steel-guitar-rag-landing.html deploy/landing/index.html`
- `git diff --check`

Results:

- No files were staged before this task.
- JS syntax checks passed.
- Focused frontend/static tests: `50 passed`.
- Public source and deploy artifact match.
- `git diff --check`: passed.
- No `package.json` exists, so no npm test suite was available.

## Integration Notes

- This is a UI placement/alignment change only.
- Public landing source and deploy artifact were already dirty before this task. The current change modifies the existing sign block in those files.
- The sign assets themselves were not modified.
- The local public deploy artifact server ran from `deploy/landing` on port `8899`.
- The local app server was already running on port `8770`.

## Risk Assessment

Risk: low to medium.

Reasons:

- Low runtime risk: CSS-only placement change plus tests.
- Medium git hygiene risk: the worktree has broad unrelated dirty files, and public landing files were already dirty before this task.
- Exact-path staging is required; do not broad-stage.

Rollback:

- Revert the changed `.hero-hanging-sign` top/left/width/transform values in the app and public landing files.
- Revert the focused test assertion updates.

## Human Decision Needed

No, if exact-path staging includes only the files listed below.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-mock.html`
- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_public_landing_page.py`
- `deploy/landing/brand/steel-guitar-rag-landing-alpha.webm`
- `deploy/landing/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `docs/handoffs/task-completions/2026-06-19-1107-06-hanging-sign-left-flush-alignment.md`

## Files That Must Remain Unstaged

Do not stage unrelated dirty files, especially:

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/`
- `public/`
- `Neon Sign/`
- `source-inbox/provenance.json`
- any corpus/private/Chroma/vector/embedding/scraping/deployment/auth/DNS/tunnel files

## Recommended Next Lane

Lane 12 Self-Hosted Deployment for protected-preview restart/deploy smoke after commit.

## Commit Readiness

Safe to commit with exact-path staging only.

## Suggested Next Step

After commit, run Lane 12 protected-preview smoke for:

- `https://steelguitarrag.com/?v=<commit>`
- `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<commit>`
