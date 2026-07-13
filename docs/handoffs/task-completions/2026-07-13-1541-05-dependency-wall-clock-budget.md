# Dependency Wall-Clock Budget

## Task summary

Protected smoke after commit `3d07a85` showed that per-socket timeouts were insufficient: sequential local-model calls could still exceed Cloudflare's overall request window. This follow-up adds a bounded wall-clock runner around retrieval and answer dependencies. A slow operation may finish on a daemon worker, but the user request falls back on schedule, and occupied dependency slots remain bounded.

Intentionally unchanged: retrieval ranking, source data, vector/Chroma state, prompts, answer schema, auth policy, DNS, secrets, and corpus behavior.

## Lane classification

- Primary lane: 05 Backend / RAG Integration
- Supporting lanes: 12 Self-Hosted Deployment and 15 QA
- Mode: approved Autopilot runtime reliability repair

## Files changed

- `pocketsteel/runtime_dependencies.py`
- `pocketsteel/api.py`
- `tests/test_runtime_dependencies.py`
- `tests/test_api_search.py`
- This handoff

## Tests and checks

- Focused dependency/API tests — 9 passed, 313 deselected.
- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 1,022 passed.
- Core JavaScript syntax checks for Chat, fretboard, Explorer, Melody Studio, and Lessons — passed.
- Python compile checks for the dependency runner, API, and local-model helper — passed.
- `git diff --check` — passed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=runtime-timeout-3d07a85-20260713`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=runtime-timeout-3d07a85-20260713`
- Exact URL the user should use: Not yet issued; re-smoke is required after this follow-up commit.
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `3d07a85196c4244a3c8d3a15bfcde4382cccd49d` for the diagnostic smoke; follow-up commit pending
- Version endpoint: `/api/version`
- Version endpoint result: local tunneled process returned `3d07a85`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex after commit; the user only after automated smoke passes
- Do not test these URLs: local loopback from another machine
- Known caveats: the diagnostic build still returned 524 because multiple dependency operations could consume separate timeouts. This handoff adds the missing total wall-clock boundaries and has not yet been deployed.

## Integration notes

- New optional variables:
  - `STEEL_RAG_RETRIEVAL_WALL_TIMEOUT_SECONDS` (default 20, maximum 35).
  - `STEEL_RAG_ANSWER_WALL_TIMEOUT_SECONDS` (default 25, maximum 40).
- Dependency workers are bounded to the configured content concurrency. A timed-out worker retains its slot until its operation finishes, preventing unbounded thread growth.
- The API preserves its existing payload contracts and uses existing deterministic fallback behavior.

## Risk assessment

- Risk: medium. Slow live retrieval or generation will intentionally fall back sooner.
- Rollback: revert this scoped commit; no data rollback is required.
- Operational benefit: health/static requests remain independent, and content requests now have an overall latency ceiling below the edge timeout.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/runtime_dependencies.py`
- `pocketsteel/api.py`
- `tests/test_runtime_dependencies.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-07-13-1541-05-dependency-wall-clock-budget.md`

## Files that must not be staged

All unrelated dirty/private/corpus/vector/source-inbox/brand/design/deployment/generated/coordination files, including `docs/handoffs/task-completions/integration-status.md`.

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 restart and authenticated protected smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the five exact paths, restart the installed preview job, verify `/api/version`, and repeat the protected answer while probing health concurrently.
