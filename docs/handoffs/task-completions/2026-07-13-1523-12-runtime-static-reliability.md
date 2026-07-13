# Runtime and static-asset reliability loop

## Task summary

Implemented the approved runtime-reliability slice:

- Replaced the single-threaded preview server with one bounded threaded WSGI process so the retrieval model remains single-instance while health/static requests can proceed alongside answer work.
- Added graceful SIGINT/SIGTERM shutdown, bounded worker/queue configuration, sanitized rotating runtime logs, and a bounded content-work semaphore.
- Added unauthenticated minimal `/health/live` and `/health/ready` endpoints.
- Bounded Ollama answer and score-vision dependency timeouts and added deterministic answer fallback when the live answer provider is unavailable.
- Replaced whole-file static reads with streaming responses, gzip, ETag/Last-Modified validators, and cache policy for immutable/versioned assets.
- Added a versioned Explorer manifest and 51 deterministic gzip chunks. Initial Explorer load now transfers one roughly 28 KB key/copedent chunk instead of the 73,495,269-byte legacy JavaScript fixture.
- Kept the legacy Explorer fixture available only as a compatibility fallback pending protected regression smoke.

Intentionally unchanged: retrieval data/model contents, corpus/vector stores, auth policy, DNS/Tunnel configuration, private data, the Explorer data contract, and public API success payloads.

## Files changed

- `pocketsteel/api.py`
- `pocketsteel/answering.py`
- `pocketsteel/melody_import.py`
- `pocketsteel/runtime_server.py` (new)
- `pocketsteel/static_files.py` (new)
- `scripts/serve_answer_smoke.py`
- `scripts/serve_v2_rerank_smoke.py`
- `scripts/build_explorer_static_chunks.py` (new)
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-loader.js` (new)
- `ui/explorer-data-v1/manifest.json` (new)
- 51 content-hashed `ui/explorer-data-v1/*.json.gz` files (new, 1.4 MB total directory)
- `tests/test_api_search.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_runtime_server.py` (new)
- This handoff

No existing file was deleted. The 70 MB compatibility fixture remains tracked but is no longer part of normal initial page load.

## Tests and checks

- Focused runtime/API/static/Explorer suite: **362 passed**.
- Follow-up targeted runtime/Explorer tests: **23 passed**.
- Full suite: `PYTHONPATH=.:scripts .venv/bin/pytest -q` — **1013 passed in 49.59s**.
- JavaScript syntax checks passed for answer client, fretboard, Explorer loader, Explorer, Melody Studio, and Lessons.
- Python compile checks passed for the new runtime/static modules, generator, server entrypoints, API, answer provider, and melody importer.
- `git diff --check` passed for the scoped text files.
- Local browser smoke passed:
  - Explorer default G/Emmons loaded with `data-explorer-data-mode=lazy`.
  - Direct C/Day query loaded the correct lazy chunk.
  - Runtime key/copedent switches loaded C, G, Day, and Custom E9 chunks without rendering failure.
  - Server request log showed manifest plus individual 25–29 KB compressed chunks and no request for the 70 MB compatibility fixture.
- Runtime concurrency test proved `/health/live` stays responsive while another worker is blocked.

## Integration notes

- Runtime tuning env vars: `STEEL_RAG_RUNTIME_THREADS` (default 8, max 32), `STEEL_RAG_RUNTIME_QUEUE` (default 32, max 128), and `STEEL_RAG_CONTENT_CONCURRENCY` (default 4, max 16).
- Dependency timeout env vars: `STEEL_RAG_OLLAMA_TIMEOUT_SECONDS` and `STEEL_RAG_MELODY_VISION_TIMEOUT_SECONDS` (default 45 seconds, hard maximum 75).
- Static request logs omit query strings. `runtime.log` rotates at 5 MiB with three backups when `STEEL_RAG_LOG_DIR` is configured.
- The Explorer loader keeps the existing `window.STEEL_RAG_E9_EXPLORER_*` data objects and dynamically fills them. Existing Explorer rendering contracts remain unchanged.
- The protected preview must be restarted at the committed HEAD and smoke-tested before the compatibility fallback path is retired.

## Risk assessment

Medium. The server/runtime and Explorer boot path changed materially, but focused, full, and local browser tests are green. Rollback is the scoped runtime commit. The main remaining risk is protected Cloudflare behavior under a slow answer, specifically verifying health responsiveness and a bounded non-524 answer result.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/api.py`
- `pocketsteel/answering.py`
- `pocketsteel/melody_import.py`
- `pocketsteel/runtime_server.py`
- `pocketsteel/static_files.py`
- `scripts/serve_answer_smoke.py`
- `scripts/serve_v2_rerank_smoke.py`
- `scripts/build_explorer_static_chunks.py`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-loader.js`
- The complete new `ui/explorer-data-v1/` directory (52 files, exclusively scoped generated static chunks/manifest)
- `tests/test_api_search.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_runtime_server.py`
- `docs/handoffs/task-completions/2026-07-13-1523-12-runtime-static-reliability.md`

## Files that must not be staged

- `ui/e9-fretboard-explorer-data.js` (unchanged compatibility fixture)
- `docs/handoffs/task-completions/integration-status.md` (separate coordination refresh)
- All unrelated dirty corpus, vector, source-inbox, private-data, public/brand, deployment, design, and generated-report paths

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 protected-preview restart and authenticated Chat/Explorer/Melody/Lessons smoke. After Explorer passes, retire only the loader's legacy fallback behavior without deleting the fixture.

## Commit readiness

Safe to commit.

## Suggested next step

Commit the exact scoped paths, restart protected preview, verify `/api/version` and both health endpoints, confirm a slow answer no longer serializes health/static requests or returns 524, and confirm Explorer never requests the legacy 70 MB fixture.
