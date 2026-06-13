## Task summary
- What was requested: diagnose why the protected preview at `app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=router-fretboard-smoke-1` appeared to serve stale fretboard UI assets even though backend behavior passed.
- What was completed: compared the current working-tree UI files against the local protected server output, classified the issue, applied the smallest cache-bust/script reference fix, verified the protected server now serves the fresh script query strings, and ran the requested checks.
- What was intentionally not changed: public deployment routing, DNS, Cloudflare Tunnel/Access config, backend/RAG behavior, Chroma, embeddings, `corpus-private`, `source-inbox`, scraping, and generated vector/corpus data.

## Files changed
- Changed files:
  - `ui/steel-guitar-rag-mock.html`
  - `tests/test_frontend_answer_ui.py`
  - `tests/test_same_origin_smoke_server.py`
  - `docs/handoffs/task-completions/2026-06-12-2228-12-protected-preview-fretboard-asset-diagnosis.md`
- Created files:
  - `docs/handoffs/task-completions/2026-06-12-2228-12-protected-preview-fretboard-asset-diagnosis.md`
- Deleted files: none.
- Generated artifacts: none.

## Tests and checks
- `grep -n "Include lever" ui/pedal-steel-fretboard.js ui/answer-client.js ui/steel-guitar-rag-mock.html || true` - passed; no matches in current working tree.
- `grep -n "Dominant pockets" ui/pedal-steel-fretboard.js ui/answer-client.js ui/steel-guitar-rag-mock.html || true` - passed; found `Dominant pockets` in `ui/pedal-steel-fretboard.js`.
- `grep -n "tierReason\\|whenToUse\\|explanationShort" ui/pedal-steel-fretboard.js ui/answer-client.js || true` - passed; found the expected reason-field handling in `ui/pedal-steel-fretboard.js`.
- `curl -sS "http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?v=asset-check-1" | grep -E "answer-client|pedal-steel-fretboard"` - passed before the fix; showed old `pitch-engine-fretboard-20260612` script query strings.
- `curl -sS "http://127.0.0.1:8770/ui/pedal-steel-fretboard.js?v=asset-check-1" | grep -n "Include lever" || true` - passed; no matches in the served JS.
- `curl -sS "http://127.0.0.1:8770/ui/pedal-steel-fretboard.js?v=asset-check-1" | grep -n "tierReason\\|whenToUse\\|explanationShort" || true` - passed; served JS includes the expected reason-field handling.
- `lsof -nP -iTCP:8770 -sTCP:LISTEN || true; ps -ww -p $(lsof -tiTCP:8770 -sTCP:LISTEN | head -1) -o pid,lstart,stat,command= 2>/dev/null || true` - passed; protected preview is the local `scripts/serve_v2_rerank_smoke.py` process on `127.0.0.1:8770`.
- `grep -nE "answer-client|pedal-steel-fretboard" ui/steel-guitar-rag-mock.html` - passed; confirmed the HTML had stale query tokens before the fix.
- `curl -sS "http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?v=asset-check-2" | grep -E "answer-client|pedal-steel-fretboard" || true` - passed after the fix; protected server now shows:
  - `answer-client.js?v=router-fretboard-smoke-20260612`
  - `pedal-steel-fretboard.js?v=router-fretboard-smoke-20260612`
- `curl -sS "http://127.0.0.1:8770/ui/pedal-steel-fretboard.js?v=router-fretboard-smoke-20260612" | grep -n "Include lever" || true` - passed; no matches.
- `curl -sS "http://127.0.0.1:8770/ui/pedal-steel-fretboard.js?v=router-fretboard-smoke-20260612" | grep -n "tierReason\\|whenToUse\\|explanationShort" || true` - passed; expected reason-field code is served.
- `node --check ui/pedal-steel-fretboard.js` - passed.
- `node --check ui/answer-client.js` - passed.
- `.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py tests/test_frontend_answer_ui.py tests/test_pedal_steel_fretboard_ui.py` - passed, `53 passed`.
- `.venv/bin/python -m pytest` - passed, `512 passed`.
- `git diff --check` - passed.
- Tests skipped and why: no browser smoke was run in this lane because the requested work was asset diagnosis and cache-bust correction; protected smoke should be rerun by Lane 12 after this fix.

## Integration notes
- Root cause classification: C/D, HTML cache-bust/script reference problem plus browser/Cloudflare cache risk.
- The current working-tree and server-served `ui/pedal-steel-fretboard.js` already contain the expected new behavior:
  - no `Include lever` text
  - `Dominant pockets`
  - `tierReason`, `whenToUse`, and `explanationShort` handling
- The server was serving current JS when requested with a fresh URL, so this was not:
  - A. latest UI code was never implemented
  - B. server is serving an old JS file
  - E. wrong server/process/path
- The stale-looking protected-preview UI was consistent with the HTML continuing to reference the older query string `pitch-engine-fretboard-20260612`, allowing a browser or intermediary cache to reuse old assets.
- The smallest safe fix updated only the script query strings in `ui/steel-guitar-rag-mock.html` and the two tests that pin those script URLs.
- Exact protected preview URL to retest:
  - `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=router-fretboard-smoke-20260612`
- Expected script URLs after fix:
  - `https://app.steelguitarrag.com/ui/answer-client.js?v=router-fretboard-smoke-20260612`
  - `https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=router-fretboard-smoke-20260612`
- Assumptions:
  - The current protected preview server reads the HTML/static files from disk per request, because curl reflected the query-string change without a process restart.
  - Browser smoke should use the new page URL and verify the UI expectations directly.
- Blockers:
  - Protected browser smoke still needs to be rerun against the new URL to confirm the user-facing stale asset issue is gone.
- Human decisions needed:
  - Decide whether Lane 12 should rerun protected smoke immediately, or have Lane 01 review the narrow diff first.

## Risk assessment
- Low.
- Why: this is a narrow cache-bust-only change to two script query strings and corresponding assertions. It does not alter application logic, backend behavior, auth, routing, Chroma, embeddings, corpus data, or deployment configuration.
- Rollback notes: revert the query-string edits in `ui/steel-guitar-rag-mock.html`, `tests/test_frontend_answer_ui.py`, and `tests/test_same_origin_smoke_server.py` to return to `pitch-engine-fretboard-20260612`.

## Commit readiness
Needs human review first

## Suggested next step
- Lane 12 Self-Hosted Deployment should rerun protected smoke against the fresh URL.
- Recommended prompt: "Rerun protected-preview smoke at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=router-fretboard-smoke-20260612`. Verify no `Include lever positions` button is visible, direct diagnostic payload hides full browser tabs, cards/details show position reasons, no `[object Object]` appears, and the loaded script URLs include `router-fretboard-smoke-20260612`."
