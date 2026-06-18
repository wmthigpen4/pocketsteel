# 2026-06-18 Lane 12 Answer Page Badge Protected Smoke

## Task Summary

Lane 12 smoke-tested the compact answer-page brand badge on protected preview from current `HEAD`. This was visual/deployment verification only.

Completed:

- Restarted protected preview on `127.0.0.1:8770`.
- Verified `/api/version` reported current badge commit `8074e6d`.
- Verified protected-preview `/ui` badge asset serving.
- Ran authenticated Cloudflare Access browser smoke at the cache-busted protected-preview UI URL.
- Checked desktop and narrow/mobile badge layout.
- Re-smoked answer flow for static fretboard-first, movement tab+fretboard, and non-tab/no-stale-state prompts.
- Ran the requested focused checks.

Intentionally not changed:

- No implementation files were modified.
- No DNS, Cloudflare Access policy, Cloudflare Tunnel config, auth behavior, Chroma/vector stores, embeddings, corpus/source data, scraping, or visual source assets were changed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=answer-badge-8074e6d`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=answer-badge-8074e6d`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=answer-badge-8074e6d`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; browser loaded the app shell, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `8074e6d`
- Version endpoint: `/api/version`
- Version endpoint result before handoff commit: `git_sha=8074e6d`, `git_branch=feature/answer-api`, `retrieval_mode=hybrid_private_first`, `auth_provider=cloudflare_access`
- If version endpoint missing, how version is inferred: not needed
- Whether app root `/` works: root was not the smoke target
- Whether app root `/` is expected to work: root may redirect and may drop query strings; direct `/ui` path was required by the task
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both Codex and the user
- Do not test these URLs: root URL as a substitute for this badge cache-bust; stale cache-bust URLs from older commits
- Known caveats: broad parked dirty files remain in the worktree; see Dirty Worktree section

## Branch And Runtime

- Branch: `feature/answer-api`
- HEAD commit tested: `8074e6d ui: add answer page brand badge`
- Protected-preview runtime commit during smoke: `8074e6d`
- Protected-preview process: `Python` listening on `127.0.0.1:8770`
- Protected-preview cwd: repo path, `~/Documents/Pocket Steel`

Restart command used, from the documented private-preview pattern:

```bash
lsof -tiTCP:8770 -sTCP:LISTEN | xargs kill 2>/dev/null || true
set -a
source ~/.steel-rag/env/private-preview.env
set +a
PYTHONPATH=. \
STEEL_RAG_AUTH_PROVIDER=cloudflare_access \
STEEL_RAG_ANSWER_AUTH_MODE=production \
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_RETRIEVAL_DEBUG=false \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

## Asset HTTP Results

Loopback origin checks:

| URL | Result | Content type | Notes |
| --- | --- | --- | --- |
| `http://127.0.0.1:8770/ui/brand/steel-guitar-rag-answer-badge-alpha.webm` | `200 OK` | `video/webm` | Actual path used by the protected-preview page |
| `http://127.0.0.1:8770/ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png` | `200 OK` | `image/png` | Actual fallback path used by the protected-preview page |
| `http://127.0.0.1:8770/brand/steel-guitar-rag-answer-badge-alpha.webm` | `404 Not Found` | `text/plain` | Expected for this same-origin server because static routing only serves `/ui/*`; page does not reference this bare path |
| `http://127.0.0.1:8770/brand/steel-guitar-rag-answer-badge-fallback-alpha.png` | `404 Not Found` | `text/plain` | Expected for this same-origin server because static routing only serves `/ui/*`; page does not reference this bare path |

Authenticated browser media state:

- Badge WebM resolved to `https://app.steelguitarrag.com/ui/brand/steel-guitar-rag-answer-badge-alpha.webm`.
- Badge PNG fallback resolved to `https://app.steelguitarrag.com/ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png`.
- WebM `readyState=4`, `error=null`, and `paused=false` in the answer view.
- PNG fallback `complete=true`, `naturalWidth=1500`, `naturalHeight=433`.

## Visual Badge Result

Desktop viewport, `1280x720`:

- Badge visible in answer view.
- Badge size: about `230x66` px.
- Badge did not consume excessive vertical space.
- Badge did not recreate the oversized hanging-sign problem.
- Badge did not overlap answer text, prompt cards, fretboard, tab cards, or source cards.
- WebM animation loaded and played.
- PNG fallback path existed and loaded.
- Console errors: none.

Narrow/mobile viewport, `390x844`:

- Badge visible in answer view.
- Badge size: about `164x47` px.
- Badge remained compact.
- Badge did not overlap answer text or fretboard.
- Q&A remained unlocked.
- Console errors: none.

Screenshots: not captured. The smoke used DOM/media measurements to avoid adding bulky generated artifacts to the already broad dirty worktree.

## Answer-Flow Smoke Results

Authenticated protected-preview browser URL:

`https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=answer-badge-8074e6d`

| Prompt | Expected | Actual | Result |
| --- | --- | --- | --- |
| `Show me a G major grip` | Static grip remains fretboard-first | Direct prose appeared; fretboard/SVG visible; tab not visible; badge compact and non-overlapping | Pass |
| `Show me a G to C move` | Movement prompt still shows tab plus fretboard | Direct prose appeared; tab card visible; tab block monospaced with `white-space: pre` and horizontal overflow; fretboard/SVG visible; badge compact and non-overlapping | Pass |
| `What are good Fender Steel King settings?` | Non-tab prompt does not show stale tab/fretboard | Gear answer appeared; no tab; no fretboard; no stale visual example remained; badge compact and non-overlapping | Pass |

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git log --oneline -12
git diff --check
curl -sS http://127.0.0.1:8770/api/version
lsof -nP -iTCP:8770 -sTCP:LISTEN
curl -sS -I http://127.0.0.1:8770/ui/brand/steel-guitar-rag-answer-badge-alpha.webm
curl -sS -I http://127.0.0.1:8770/ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png
curl -sS -I http://127.0.0.1:8770/brand/steel-guitar-rag-answer-badge-alpha.webm
curl -sS -I http://127.0.0.1:8770/brand/steel-guitar-rag-answer-badge-fallback-alpha.png
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py pocketsteel/answer_tab_examples.py
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_tab_engine.py -q
.venv/bin/python -m pytest tests/test_api_search.py -q
```

Results:

- `git diff --check`: passed
- `/api/version`: reported `8074e6d`
- `node --check ui/answer-client.js`: passed
- `node --check ui/pedal-steel-fretboard.js`: passed
- `py_compile pocketsteel/tab_engine.py pocketsteel/api.py pocketsteel/answer_tab_examples.py`: passed
- `tests/test_frontend_answer_ui.py tests/test_pedal_steel_fretboard_ui.py`: 49 passed
- `tests/test_tab_engine.py`: 23 passed
- `tests/test_api_search.py`: 259 passed

## Known Unrelated Caveats

- Full pytest was not requested and was not run.
- Known unrelated full-suite caveat remains: `tests/test_same_origin_smoke_server.py` has a missing public fretboard background route failure.
- Known unrelated full-suite caveat remains: landing source vs deployed static HTML mismatch.
- The same-origin smoke server serves static assets under `/ui/*`; bare `/brand/*` returned `404`, while the actual page-referenced `/ui/brand/*` badge assets returned `200`.
- The worktree remains broadly dirty with parked docs/corpus/source/static/design files.

## Dirty Worktree Notes

The task started with broad unrelated dirty and untracked files. The only dirty runtime UI hunk inspected before restart was in `ui/steel-guitar-rag-mock.html` for the landing hero sign cache-bust:

- `brand/steel-guitar-rag-landing-fallback-alpha.png?v=rag-clean-alpha-20260618b`
- `brand/steel-guitar-rag-landing-alpha.webm?v=rag-clean-alpha-20260618b`

That dirty hunk is unrelated to the answer-page badge selector/media paths verified here, but it means the served HTML file is not byte-for-byte clean relative to `HEAD`. The badge feature itself was verified from committed `HEAD` `8074e6d`, and `/api/version` reported `8074e6d` during smoke.

Unrelated dirty files left untouched include, but are not limited to:

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `deploy/landing/index.html`
- `docs/handoffs/task-completions/integration-status.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `tests/test_frontend_answer_ui.py`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `ui/steel-guitar-rag-mock.html`
- broad untracked historical handoffs/assets/docs and generated/private-adjacent paths already present before this task

## Defects Found

None for the answer-page badge protected-preview smoke.

## Risk Assessment

Risk: low.

Reason:

- This lane changed only the smoke handoff.
- Protected preview was restarted using the documented loopback command.
- `/api/version` matched the expected badge commit during smoke.
- Badge assets and visual layout passed in authenticated browser smoke.

Rollback/restart note:

- If the protected preview needs to be rolled back, restart `127.0.0.1:8770` from the last known good committed checkout using the documented private-preview command.
- This handoff commit can be reverted independently; it contains no runtime behavior changes.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-12-answer-page-badge-protected-smoke.md`

## Files That Must Not Be Staged

- Any corpus, Chroma/vector, embedding, source-inbox, private corpus, scraping, credential, `.wrangler`, DNS/deployment secret, generated data, visual-design source asset, or unrelated dirty file.
- Existing parked dirty files listed above.

## Recommended Next Lane

Lane 06 can continue visual polish only if new user smoke feedback identifies a real badge/UI issue. Otherwise, user smoke may continue from the protected-preview URL above.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Continue user smoke at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=answer-badge-8074e6d`, focusing on whether the compact answer-page badge feels appropriately small during normal answer use.
