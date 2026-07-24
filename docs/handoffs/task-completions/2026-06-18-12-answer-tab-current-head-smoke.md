# 2026-06-18 Lane 12 Answer Tab Current-Head Smoke

## Task Summary

Lane 12 reran answer-tab local and protected-preview smoke from current `feature/answer-api` HEAD after the backend answer-body fix. The goal was to prove commit `425e14c fix: add direct prose for tab example answers` is live in runtime and that safe answer-triggered tab prompts now show deterministic tab examples plus useful direct prose, without the generic fallback text.

Completed:
- Restarted the protected-preview runtime on `127.0.0.1:8770`.
- Verified `/api/version` on the protected-preview backend reports `425e14c`.
- Ran local API smoke against a temporary local-dev server on `127.0.0.1:8781`.
- Ran local browser smoke against the same local-dev server.
- Ran authenticated protected-preview browser smoke through Cloudflare Access.
- Ran focused syntax and pytest checks requested by the task.

Intentionally not changed:
- No backend, frontend, auth, deployment config, DNS, corpus, Chroma, embeddings, source data, or scraping behavior was modified.
- No broad QA/full pytest was rerun.
- The temporary local-dev smoke server on `8781` was stopped after testing.
- The protected-preview server on `8770` was left running.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/?v=answer-tab-smoke-425e14c`
- Cache-busted URL tested: `https://app.steelguitarrag.com/?v=answer-tab-smoke-425e14c`
- Exact URL the user should use: `https://app.steelguitarrag.com/`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `425e14c`
- Version endpoint: `/api/version`
- Version endpoint result: local backend returned `git_sha: 425e14c`, `git_branch: feature/answer-api`, `retrieval_mode: hybrid_private_first`, `auth_provider: cloudflare_access`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, root redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex and the user
- Do not test these URLs: old `af645c9` cache-busted smoke URLs for this answer-body verification
- Known caveats: the root redirect drops the query string; protected-browser page evaluation could not fetch `/api/version`, so runtime identity was verified by direct loopback `/api/version` against the same `8770` process.

## Branch And Runtime Evidence

- Branch: `feature/answer-api`
- HEAD commit tested: `425e14c`
- Runtime `/api/version` commit: `425e14c`
- Runtime includes `425e14c`: yes
- Protected-preview process:
  - Listening on `127.0.0.1:8770`
  - CWD verified as `/Users/cory/Documents/Steel Guitar RAG`
  - Command used the documented private-preview server script: `scripts/serve_v2_rerank_smoke.py`
- Local-dev smoke server:
  - Temporarily started on `127.0.0.1:8781`
  - Auth mode: `local_dev`
  - Stopped after local API/browser smoke

## Local API Smoke Results

Endpoint: `http://127.0.0.1:8781/api/answer` with local dev beta header.

| Prompt | Expected | Actual | Result |
| --- | --- | --- | --- |
| `Show me a G major grip` | Direct prose plus tab payload | Returned direct prose, `tab_example` id `g-major-456-open`, no generic fallback, no source cards | Pass |
| `Show me a G to C move` | Direct prose plus tab payload | Returned direct prose, `tab_example` id `g-to-c-456-beginner`, no generic fallback, no source cards | Pass |
| `How do I use A+B pedals?` | Direct prose plus tab payload | Returned direct prose, `tab_example` id `a-b-pedal-major-position`, no generic fallback, no source cards | Pass |
| `Show me an A+B example` | Direct prose plus tab payload | Returned direct prose, `tab_example` id `a-b-pedal-major-position`, no generic fallback, no source cards | Pass |
| `Show me an E-lower move` | Direct prose plus tab payload | Returned direct prose, `tab_example` id `e-lower-color-move`, no generic fallback, no source cards | Pass |
| `Give me a beginner lick in G` | Direct prose plus tab payload | Returned direct prose, `tab_example` id `beginner-g-two-event-lick`, no generic fallback, no source cards | Pass |
| `Show me a 4-5-6 grip` | Direct prose plus tab payload | Returned direct prose, `tab_example` id `g-major-456-open`, no generic fallback, no source cards | Pass |
| `What are good Fender Steel King settings?` | Normal non-tab answer | Answered normally with source support and no generated tab | Pass |
| `Tab the whole solo from Together Again` | No generated full-song tab | Returned safe song-approach guidance with no generated tab | Pass |
| `Transcribe this YouTube recording into tab` | No generated transcription tab | Returned safe song-approach guidance with no generated tab | Pass |
| `Give me the full tab for a modern copyrighted song` | No generated full-song tab | Returned safe song-approach guidance with no generated tab | Pass |

Local API conclusion: safe tab prompts now include direct useful prose and no longer show `I need a more specific steel-guitar question...`.

## Local Browser Smoke Results

URL: `http://127.0.0.1:8781/ui/steel-guitar-rag-mock.html?access=beta_user&v=answer-tab-smoke-425e14c`

Safe tab prompts:
- All seven safe prompts rendered a visible tab card/block.
- Tab text preserved spacing with `white-space: pre`.
- Tab text used a monospace stack: `ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace`.
- Tab container used horizontal overflow handling (`overflow-x: auto`).
- Tab card did not remain after returning to the stage.
- No generic fallback text appeared in the answer body.
- No console errors were observed.

Negative/no-tab prompts:
- Gear prompt rendered as a normal non-tab answer.
- Copyright/full-song/transcription prompts did not show generated tab.
- No stale tab card remained after returning to the stage.

Mobile/narrow spot check:
- Viewport: `390x844`
- Prompt: `Give me a beginner lick in G`
- Tab card rendered, monospace/pre formatting remained intact, and horizontal overflow handling was present.

Screenshots: none captured for this run; DOM/browser assertions were captured through the in-app browser automation.

## Protected Preview Browser Smoke Results

URL: `https://app.steelguitarrag.com/?v=answer-tab-smoke-425e14c`

Access/browser result:
- Cloudflare Access login succeeded.
- Final browser URL after root redirect: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- App shell loaded.
- Q&A input was unlocked.
- Browser console errors: none.

Protected prompt matrix:

| Prompt | Expected | Actual | Result |
| --- | --- | --- | --- |
| `Show me a G major grip` | Direct prose plus visible tab | Direct prose, visible tab card, no generic fallback, no stale tab after return | Pass |
| `Show me a G to C move` | Direct prose plus visible tab | Direct prose, visible tab card, no generic fallback, no stale tab after return | Pass |
| `How do I use A+B pedals?` | Direct prose plus visible tab | Direct prose, visible tab card, no generic fallback, no stale tab after return | Pass |
| `Show me an A+B example` | Direct prose plus visible tab | Direct prose, visible tab card, no generic fallback, no stale tab after return | Pass |
| `Show me an E-lower move` | Direct prose plus visible tab | Direct prose, visible tab card, no generic fallback, no stale tab after return | Pass |
| `Give me a beginner lick in G` | Direct prose plus visible tab | Direct prose, visible tab card, no generic fallback, no stale tab after return | Pass |
| `Show me a 4-5-6 grip` | Direct prose plus visible tab | Direct prose, visible tab card, no generic fallback, no stale tab after return | Pass |
| `What are good Fender Steel King settings?` | Normal non-tab answer | Normal answer, no generated tab, no stale tab after return | Pass |
| `Tab the whole solo from Together Again` | No generated full-song tab | Safe song-approach guidance, no generated tab, no stale tab after return | Pass |
| `Transcribe this YouTube recording into tab` | No generated transcription tab | Safe song-approach guidance, no generated tab, no stale tab after return | Pass |
| `Give me the full tab for a modern copyrighted song` | No generated full-song tab | Safe song-approach guidance, no generated tab, no stale tab after return | Pass |

Protected preview conclusion: pass. The current protected runtime serves the answer-body fix and renders answer-triggered tab examples in the authenticated browser.

## Expected vs Actual Summary

- Safe tab prompts return/render deterministic tab cards: yes.
- Safe tab prompts show useful direct prose: yes.
- Safe tab prompts omit the generic fallback: yes.
- Tab spacing is preserved: yes.
- Tab block is monospaced: yes.
- Tab block does not dominate the answer page: yes in browser smoke.
- Normal non-tab behavior remains intact: yes.
- Unsafe copyrighted/full-solo/transcription requests do not show generated tab: yes.
- API payload contains `tab_example` for safe prompts: yes.
- API does not crash when `tab_example` is absent: yes.

## Tests And Checks

Passed:
- `git diff --check`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m py_compile steel_guitar_rag/tab_engine.py steel_guitar_rag/api.py`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` -> `20 passed`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q` -> `20 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` -> `5 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -q` -> `257 passed`

Not run:
- Full pytest, because the task requested the focused checks. Existing known unrelated full-suite failures remain documented elsewhere:
  - landing source vs deployed static HTML mismatch
  - missing public fretboard background route

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-18-12-answer-tab-current-head-smoke.md`

No implementation files were changed.

## Defects And Caveats

- Protected root redirect drops the cache-bust query string when it lands on `/ui/steel-guitar-rag-mock.html`; this did not block the smoke because the runtime version was verified separately and the browser behavior passed.
- Protected-browser page evaluation could not fetch `/api/version` because the automation context lacked `fetch`/`XMLHttpRequest`; direct loopback `/api/version` against the same `8770` protected-preview process proved `425e14c`.
- Several unrelated dirty/parked files exist in the worktree, including runtime-adjacent files such as `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py`. They were not touched or staged by this Lane 12 verification.
- No screenshots were captured.

## Risk Assessment

Risk: low.

Reasoning:
- This task only added a documentation handoff.
- Local API, local browser, and authenticated protected-preview browser smoke all passed for the answer-tab behavior.
- The protected-preview runtime was restarted from current HEAD and `/api/version` confirmed `425e14c`.

Rollback/restart note:
- If the protected preview needs a clean restart, use the documented Lane 12 private-preview command for `scripts/serve_v2_rerank_smoke.py` on `127.0.0.1:8770` with Cloudflare Access production auth and the v2 Chroma settings.
- No code rollback is needed for this handoff-only task.

## Human Decision Needed

No.

## Safe To Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-12-answer-tab-current-head-smoke.md`

## Files That Must Not Be Staged

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `deploy/landing/index.html`
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
- `tests/test_frontend_answer_ui.py`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `ui/steel-guitar-rag-mock.html`
- Any untracked corpus, source-inbox, private, generated, design, deployment, or unrelated handoff files.

## Recommended Next Lane

Lane 01 Repo Steward only if further exact-path commit coordination is needed. Otherwise, user smoke can continue against the protected preview.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit this exact handoff with:

```bash
git add docs/handoffs/task-completions/2026-06-18-12-answer-tab-current-head-smoke.md
git commit -m "docs: record current-head answer tab smoke"
```
