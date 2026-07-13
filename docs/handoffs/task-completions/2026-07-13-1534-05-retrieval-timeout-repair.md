# Retrieval Timeout Repair

## Task summary

Protected-preview smoke of runtime commit `2b9036b` proved that the threaded server kept liveness, readiness, and version requests responsive while an answer was in flight. The answer still reached Cloudflare's 524 boundary because the retrieval embedding dependency retained a 120-second timeout. This repair bounds the embedding call to 25 seconds by default (5–45 seconds configurable) and converts a retrieval dependency failure into deterministic, source-free guidance instead of a failed request.

Intentionally unchanged: retrieval ranking, Chroma/vector data, corpus content, answer contracts, Cloudflare Access policy, DNS, secrets, and private sources.

## Lane classification

- Primary lane: 05 Backend / RAG Integration
- Supporting lanes: 12 Self-Hosted Deployment and 15 QA
- Mode: approved Autopilot runtime reliability repair

## Files changed

- `rag_common.py`
- `pocketsteel/api.py`
- `tests/test_api_search.py`
- `tests/test_rag_common.py`
- This handoff

No files were deleted. No generated artifacts were created.

## Tests and checks

- `PYTHONPATH=.:scripts .venv/bin/pytest -q tests/test_rag_common.py tests/test_api_search.py -k 'retrieval_timeout or bounded_dependency_timeout or health_checks or content_concurrency'` — 8 passed.
- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 1,018 passed.
- Core JavaScript `node --check` commands for Chat, fretboard, Explorer loader/Explorer, Melody Studio, and Lessons — passed.
- `python3 -m py_compile rag_common.py pocketsteel/api.py` — passed.
- `git diff --check` — passed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=runtime-2b9036b-20260713`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=runtime-2b9036b-20260713`
- Exact URL the user should use: Not yet issued; automated re-smoke is required after this repair commit.
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `2b9036b33dd09bd31274921aecb93a1abe687714` for the diagnostic smoke; repair commit pending
- Version endpoint: `/api/version`
- Version endpoint result: local tunneled process returned `2b9036b`; protected UI assets also matched the new build
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; local root returned 302 to the app UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex after repair commit; the user only after automated smoke passes
- Do not test these URLs: local loopback from another machine
- Known caveats: the diagnostic answer returned Cloudflare 524 after the backend completed in roughly 135 seconds; this repair specifically removes the remaining 120-second embedding wait and has not yet been deployed at the time of this handoff.

## Integration notes

- New optional environment variable: `STEEL_RAG_OLLAMA_EMBED_TIMEOUT_SECONDS`.
- Default: 25 seconds. Accepted runtime range: 5–45 seconds.
- Both modern `/api/embed` and legacy `/api/embeddings` calls use the same bound.
- SGF retrieval dependency failures return an empty result with a bounded warning. Private retrieval failures are isolated similarly without exposing private details.
- The answer endpoint preserves its response contract and returns deterministic guidance when sources are temporarily unavailable.

## Risk assessment

- Risk: medium. The change intentionally trades unavailable/slow live retrieval for a fast deterministic fallback before the edge timeout.
- Rollback: revert the scoped repair commit. No migration or data rollback is required.
- Remaining risk: a healthy but cold embedding model may time out at 25 seconds and produce source-free guidance until warmed; this is preferable to an edge 524 and is reported honestly in warnings.

## Human decision needed

No. The repair is inside the approved runtime reliability scope.

## Safe-to-stage exact file list

- `rag_common.py`
- `pocketsteel/api.py`
- `tests/test_api_search.py`
- `tests/test_rag_common.py`
- `docs/handoffs/task-completions/2026-07-13-1534-05-retrieval-timeout-repair.md`

## Files that must not be staged

All unrelated dirty corpus, source registry, source-inbox, brand, design, deployment asset, private-data, generated report, and coordination files, including `docs/handoffs/task-completions/integration-status.md`.

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 protected-preview restart and authenticated Chat/Explorer/Melody/Lessons re-smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the five exact paths above, restart the protected preview, verify the new `/api/version` HEAD, and confirm the same answer completes before Cloudflare's timeout while health endpoints remain responsive.
