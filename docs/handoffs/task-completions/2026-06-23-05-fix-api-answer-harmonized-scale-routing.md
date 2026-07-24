# 2026-06-23 Lane 05 - Fix API Answer Harmonized-Scale Routing

## Task Summary

Requested: diagnose and fix the protected-preview blocker where broader G harmonized-scale prompts returned the generic specificity fallback through the real `/api/answer` browser path, even though in-process helper tests passed.

Completed:

- Reproduced the current production-auth WSGI `/api/answer` path locally with Cloudflare Access-style auth.
- Confirmed the committed deterministic harmonized-scale route already answers correctly through `/api/answer` for the blocked prompts.
- Added API-level regression coverage for the actual production Cloudflare Access answer path.
- Fixed `/api/version` so it reports app-start identity instead of recalculating git state on every request.

Intentionally not changed:

- No UI changes.
- No deployment, restart, DNS, auth-policy, corpus, Chroma, embeddings, scraping, source-inbox, or private transcript changes.
- No changes to deterministic row generation or fretboard payload shape.

## Root Cause

The route logic itself was not the remaining blocker. The actual `/api/answer` path answers the blocked prompts correctly when loaded from current code.

The protected-preview diagnosis was confused by `/api/version`: it recalculated `git_sha`, `git_branch`, and `server_started_at` at request time. That allowed a stale long-running Python process to report the current checkout after git changed, even if the loaded modules were still from older code. This made Lane 12 believe the intended commit was live while browser behavior still matched stale runtime code.

The missing test coverage was an API-level production-auth regression for the broader harmonized-scale prompts. Prior coverage exercised helper/in-process answer construction, not the Cloudflare Access `/api/answer` route used by protected preview.

## Files Changed

- `steel_guitar_rag/api.py`
  - Capture `git_sha`, `git_branch`, and `server_started_at` once during `RetrievalApi` initialization.
  - `/api/version` now reports the loaded app/process identity consistently for the life of the process.

- `tests/test_api_search.py`
  - Added a `/api/version` stability regression.
  - Added a production Cloudflare Access `/api/answer` regression for:
    - `Show me a G harmonized scale.`
    - `Show me G major harmonized scale on E9.`
    - `Show me a G natural minor harmonized scale.`
    - `Show me the F# diminished position in G.`
    - `Show me the A diminished position in G minor.`
    - `Show me a G harmonized scale on strings 5 and 8.`

- `docs/handoffs/task-completions/2026-06-23-05-fix-api-answer-harmonized-scale-routing.md`
  - This handoff.

## Behavior Verified

Through the actual WSGI `/api/answer` route with production Cloudflare Access-style auth, each blocked prompt now verifies:

- HTTP `200 OK`.
- No generic `I need a more specific steel-guitar question` fallback.
- Top-level `fretboard` payload is present.
- No `tab_example`.
- `sources == []`.
- `warnings == []`.
- Fretboard payload validates with the existing contract helper.

The 5&8 branch prompt remains deterministic and visual:

- `Show me a G harmonized scale on strings 5 and 8.`

## Local Runtime Notes

The live local server at `http://127.0.0.1:8770` currently requires Cloudflare Access identity. A direct curl with only `X-Steel-Rag-Dev-Access-Role` returned:

```text
401 Unauthorized
{"error": "/api/answer requires Cloudflare Access identity"}
```

That is expected for the protected-preview auth mode. This task used the production-auth WSGI route with `FakeCloudflareVerifier` to cover the backend path without changing auth or deployment.

## Tests And Checks

Passed:

```bash
.venv/bin/python -m pytest tests/test_api_search.py -k 'api_version or harmonized or diminished or static_g or tab_example' -q
# 23 passed, 252 deselected

.venv/bin/python -m py_compile steel_guitar_rag/api.py steel_guitar_rag/curated_answers.py steel_guitar_rag/fretboard_examples.py steel_guitar_rag/fretboard_explorer.py

.venv/bin/python -m pytest tests/test_api_contract.py -q
# 5 passed

.venv/bin/python -m pytest tests/test_api_search.py -q
# 275 passed

.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
# 30 passed

.venv/bin/python -m pytest tests/test_tab_engine.py -q
# 25 passed

git diff --check
```

## Integration Notes

- Lane 12 should restart protected preview before rerunning browser smoke. `/api/version` will now reveal stale process identity correctly after future checkouts.
- A browser smoke rerun should target the same failed prompt set from `2026-06-23-12-broader-g-harmonized-scale-protected-smoke.md`.
- If `/api/version` reports an older `git_sha` after a new checkout, that is now a real restart/load problem, not a version endpoint false positive.

## Risk Assessment

Risk: low.

The runtime change only stabilizes `/api/version` identity fields at app initialization. It does not change `/api/answer` response schema or routing behavior.

Rollback: revert the small `steel_guitar_rag/api.py` initialization/version diff and the associated tests.

## Human Decision Needed

No product decision needed.

Operational decision: Lane 12 should restart protected preview and rerun the protected browser smoke for the broader G harmonized-scale prompts.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-05-fix-api-answer-harmonized-scale-routing.md`

## Files That Must Not Be Staged

Do not stage unrelated parked work shown by `git status --short`, including:

- `README.md`
- `corpus_metadata/**`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- unrelated existing handoffs and `docs/handoffs/task-completions/assets/**`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- private/corpus/generated/deployment/auth/design assets

## Recommended Next Lane

Lane 12 Self-Hosted Deployment: restart protected preview, verify `/api/version` reports the committed `git_sha`, then rerun protected browser smoke for the broader G harmonized-scale prompt set.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 prompt:

```text
Lane 12: Restart protected preview after the Lane 05 harmonized-scale API routing fix. Verify /api/version reports the new HEAD, then rerun the protected browser smoke prompts from docs/handoffs/task-completions/2026-06-23-12-broader-g-harmonized-scale-protected-smoke.md. Record exact URL, auth result, version endpoint result, and pass/fail per prompt.
```
