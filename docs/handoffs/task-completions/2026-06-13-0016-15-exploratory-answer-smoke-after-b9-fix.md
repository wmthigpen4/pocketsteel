# Exploratory Answer Smoke After B9/E-Lower Fix

## Task Summary
- Requested: rerun the exploratory answer smoke after the Lane 05 B9/E-lower fretboard payload fix, with a direct preflight check for `Is 5-7-8 with E lowered a B9 pocket?`.
- Completed: confirmed the Lane 05 handoff exists, restarted the loopback local answer API from the current worktree, verified API reachability, ran the direct B9/E-lower POST check, reran the exploratory smoke, and ran the requested QA checks.
- Intentionally not changed: no runtime implementation files, Chroma stores, embeddings, `corpus-private`, `corpus-v2`, `source-inbox`, scraping, provenance/legal files, deployment secrets, `.wrangler`, DNS config, design assets, staging, commits, deployment, or DNS.

## Branch And HEAD
- Branch: `feature/answer-api`
- HEAD: `bad18d8`
- Prerequisite handoff found: `docs/handoffs/task-completions/2026-06-13-0011-05-b9-elower-fretboard-payload.md`

## API Startup And Reachability
- Startup method: stopped the stale loopback process and restarted the repo-supported local smoke server from the current worktree:

```bash
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first STEEL_RAG_ENABLE_PRIVATE_SOURCES=true STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 STEEL_RAG_RETRIEVAL_DEBUG=true .venv/bin/python scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8783 --v2-chroma-path corpus-v2/vector-stores/chroma --v2-collection steel_guitar_unified_v2 --answer-auth-mode local_dev --auth-provider scaffold
```

- Reachability evidence:
  - `curl -sS -i http://127.0.0.1:8783/ | head -20 || true` returned `HTTP/1.0 200 OK`.
  - `curl -sS -i http://127.0.0.1:8783/api/answer | head -20 || true` returned `HTTP/1.0 405 Method Not Allowed`, which is acceptable for GET `/api/answer` and confirms the server was reachable.

## Direct POST Result
- Prompt tested: `Is 5-7-8 with E lowered a B9 pocket?`
- Result: pass.
- Verified:
  - Answer says it is not B9.
  - Answer explains the D major / rootless B minor 7 color.
  - `response.fretboard` exists.
  - `response.fretboard.positions` is non-empty.
  - Position id returned: `b9-check-e-lower-5-7-8-3`.
  - Sources were empty.
  - Warnings were empty.
  - No `[object Object]` leakage.

## Exploratory Smoke
- Command used:

```bash
.venv/bin/python scripts/run_exploratory_answer_smoke.py \
  --base-url http://127.0.0.1:8783 \
  --output /tmp/steel_guitar_rag-exploratory-answer-smoke-after-b9-fix.md \
  --json-output /tmp/steel_guitar_rag-exploratory-answer-smoke-after-b9-fix.json
```

- Output artifacts:
  - `/tmp/steel_guitar_rag-exploratory-answer-smoke-after-b9-fix.md`
  - `/tmp/steel_guitar_rag-exploratory-answer-smoke-after-b9-fix.json`
- Note: outputs were written to `/tmp` to avoid touching `corpus-private` or `corpus-v2`.

## Smoke Results
- Total prompts: 178
- Pass: 98
- Warn: 80
- Fail: 0
- Hard product failures by prompt/bucket: none.
- B9/E-lower prompt result in full smoke: `pass`, HTTP 200, fretboard present, no failure flags.

## Warning Clusters
- `warn:source_excerpt_unrelated`: 207
- `warn:source_excerpt_too_short`: 37
- `warn:low_teaching_value`: 6

These are warning-level quality signals, not blockers for the B9/E-lower regression gate.

## Tests And Checks
- `git diff --check` - passed.
- `.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py` - passed, `9 passed`.
- `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py` - passed, `43 passed`.
- Full pytest was not rerun because no implementation or smoke/test script files were changed during this rerun task.

## Files Changed
- Created:
  - `docs/handoffs/task-completions/2026-06-13-0016-15-exploratory-answer-smoke-after-b9-fix.md`
- Changed files:
  - None for runtime implementation.
- Deleted files:
  - None.
- Generated artifacts:
  - `/tmp/steel_guitar_rag-exploratory-answer-smoke-after-b9-fix.md`
  - `/tmp/steel_guitar_rag-exploratory-answer-smoke-after-b9-fix.json`

## Integration Notes
- The previous hard blocker is cleared: the B9/E-lower diagnostic answer now returns a deterministic top-level fretboard payload.
- The stale local loopback server initially reflected old behavior; restarting from the current worktree was required before verification.
- `integration-status.md` should be refreshed from parked/blocked to exploratory smoke pass with warnings only.
- Existing dirty/untracked worktree files from other lanes were left untouched.

## Risk Assessment
- Risk: Low.
- Why: this task only reran local loopback QA and added a markdown handoff. No app behavior, data stores, generated repo reports, deployment config, or source assets were changed.
- Rollback: remove this handoff file if the rerun needs to be superseded by a later QA handoff.

## Commit Readiness
- Safe to commit.

This means the QA blocker from the B9/E-lower smoke is cleared. Repo Steward should still stage only the intended files from the broader dirty worktree.

## Suggested Next Step
- Recommended lane: `01 Repo Steward`.
- Suggested prompt: refresh `integration-status.md` to record that the Lane 05 B9/E-lower fretboard payload fix passed direct POST verification and exploratory answer smoke with `178 total / 98 pass / 80 warn / 0 fail`, then prepare a scoped commit that excludes generated reports and unrelated dirty worktree files.

## Current Status
- B9/E-lower deterministic visual payload fix verified.
- Exploratory smoke has no hard failures.
- Remaining quality observations are warning clusters around source excerpt relevance/length and low teaching value.

## Remaining Blockers
- No hard QA blocker remains for this lane.

## Recommended Next Lane
- `01 Repo Steward` for integration-status refresh and scoped commit coordination.
