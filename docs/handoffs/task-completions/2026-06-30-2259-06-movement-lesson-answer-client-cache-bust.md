# Movement Lesson Answer Client Cache-Bust

## Task Summary

Requested: fix the protected-preview Movement Lesson Card blocker caused by `ui/steel-guitar-rag-mock.html` still loading a stale `answer-client.js` asset query string.

Completed:
- Updated the app/protected-preview HTML to request `answer-client.js?v=movement-lesson-card-29bfd24`.
- Updated the focused frontend assertion so the stale `answer-client.js?v=e9-explorer-home-entry-20260623` reference cannot return for the answer client.
- Left `pedal-steel-fretboard.js` unchanged because the blocker was isolated to the answer renderer script.

Intentionally not changed:
- Backend routing/API behavior.
- Auth, DNS, deployment architecture, Cloudflare configuration, corpus, Chroma, embeddings, scraping, private data, or visual assets.
- Movement Lesson Card implementation logic.

## Files Changed

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-30-2259-06-movement-lesson-answer-client-cache-bust.md`

## Tests And Checks

Passed:
- `git diff --check`
- `node --check ui/answer-client.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
  - Result: `24 passed`

Local browser smoke:

```text
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8899/ui/steel-guitar-rag-mock.html?access=beta_user&v=movement-lesson-cachebust-local
- Cache-busted URL tested: http://127.0.0.1:8899/ui/steel-guitar-rag-mock.html?access=beta_user&v=movement-lesson-cachebust-local
- Exact URL the user should use: pending protected-preview smoke
- Auth required: no for local-dev smoke
- Auth provider: scaffold local-dev
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8899
- Expected backend port: 8899
- Expected git HEAD: 6202c18 at start of task
- Version endpoint: not checked for local smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local file and script URL inspection
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not needed for this cache-bust check
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally; the user after protected-preview smoke
- Do not test these URLs: uncache-busted protected preview URLs for this slice
- Known caveats: local smoke confirms browser behavior on loopback only; protected preview still needs restart/version verification after commit
```

Local browser observations:
- Loaded script URL: `http://127.0.0.1:8899/ui/answer-client.js?v=movement-lesson-card-29bfd24`
- `Show me a G to C move.` rendered Movement Lesson Card + tab + fretboard.
- `Show me a 1 4 5 1 move in G.` rendered Movement Lesson Card + tab + fretboard.
- `Show me a G major grip.` rendered fretboard without a visible tab card.
- `What are good Fender Steel King settings?` rendered a gear answer without movement card/tab/fretboard.
- No `[object Object]`.
- No relevant console errors.
- Broad text matching still finds source-warning strings in script/template text; visible element inspection showed no visible stale empty source-card shell.

## Integration Notes

The protected-preview blocker was an asset freshness issue, not a Movement Lesson Card renderer issue. The local page now requests the committed Movement Lesson Card answer client.

Next protected-preview smoke should verify:
- `/api/version` reports a HEAD containing this cache-bust fix commit.
- Protected HTML loads `answer-client.js?v=movement-lesson-card-29bfd24`.
- Protected browser URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=movement-lesson-card-29bfd24-cachefix`

## Risk Assessment

Risk: low.

Reason: the implementation changes one static script query string and one focused assertion. No runtime logic, backend, auth, deployment, corpus, or asset files changed.

Rollback: revert the single query-string/test assertion change if needed.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-30-2259-06-movement-lesson-answer-client-cache-bust.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked work, including but not limited to:
- `README.md`
- corpus/source/provenance files
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/`
- `ui/brand/`
- `Neon Sign/`
- deployment/static asset work
- any unrelated handoffs

## Recommended Next Lane

Lane 01 exact-path commit for this scoped cache-bust fix, then Lane 12 protected-preview restart/smoke.

## Commit Readiness

Safe to commit.

## Suggested Next Step

After commit, run Lane 12 protected-preview smoke against:

`https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=movement-lesson-card-29bfd24-cachefix`
