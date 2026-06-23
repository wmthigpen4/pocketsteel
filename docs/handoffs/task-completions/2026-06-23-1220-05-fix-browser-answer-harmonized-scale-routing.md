# Lane 05: Fix Browser Answer Harmonized Scale Routing

## Task Summary
- Requested: diagnose and fix why protected-preview browser prompts for broader G harmonized-scale answers still returned the generic specificity fallback with no fretboard even though route-level tests passed.
- Completed: added a backend response invariant so deterministic visual/fretboard answers cannot fall through with generic fallback text, sources, or warnings when a deterministic fretboard payload is available.
- Completed: added a same-origin browser-equivalent regression that uses the v2 rerank smoke-server wrapper, production Cloudflare Access auth mode, Cloudflare cookie auth, beta dev header, and the exact UI-style request body `{ "question": ... }`.
- Intentionally not changed: UI files, protected-preview launchd state, deployment, auth policy, DNS, Chroma, embeddings, corpus, scraper output, private data, Explorer row generation, tab engine behavior, and 5&8 branch logic.

## Files Changed
- `pocketsteel/api.py`
  - Split the generic specificity fallback detector out from tab-specific naming.
  - In final `/api/answer` assembly, when a deterministic `fretboard` payload exists:
    - suppress source cards,
    - suppress warnings,
    - replace generic fallback answer text with the deterministic visual curated answer when available.
- `tests/test_api_search.py`
  - Added same-origin browser-path regression for the broader G harmonized-scale prompt set using `scripts.serve_answer_smoke.build_app` and `scripts.serve_v2_rerank_smoke.create_v2_api_app`.
- `docs/handoffs/task-completions/2026-06-23-1220-05-fix-browser-answer-harmonized-scale-routing.md`
  - This handoff.

## Diagnosis
- The static UI request path was inspected:
  - `ui/answer-client.js` posts to `/api/answer`.
  - Browser request body is only `{ "question": submittedQuestion }`.
  - The UI may include the beta dev access header depending on current access state.
- The protected runtime served current static files and `/api/version` reported current branch/HEAD at inspection time.
- Direct in-process `/api/answer` tests already passed for the failing prompts.
- Protected browser POST logs showed the failing broad prompts returning small generic-fallback payloads while the exact 5&8 prompt returned the larger deterministic payload.
- No UI payload-shape bug was found. The missing coverage was the same-origin production-wrapper route used by the protected loopback server, plus lack of a final backend fail-closed guard for deterministic visual payloads.

## Prompt Coverage
The same-origin regression covers:
- `Show me a G harmonized scale.`
- `Show me G major harmonized scale on E9.`
- `Show me a G major harmonized scale.`
- `Show me a G harmonized scale on E9.`
- `Show me a G natural minor harmonized scale.`
- `Show me G natural minor harmonized scale on E9.`
- `Show me the F# diminished position in G.`
- `Show me the A diminished position in G minor.`
- `Show me a G harmonized scale on strings 5 and 8.`

Assertions:
- no generic specificity fallback,
- `fretboard` is present,
- no `tab_example`,
- `sources == []`,
- `warnings == []`,
- fretboard payload validates.

## Tests And Checks
- `git diff --check` - passed
- `node --check ui/answer-client.js` - passed
- `node --check ui/pedal-steel-fretboard.js` - passed
- `.venv/bin/python -m py_compile pocketsteel/api.py pocketsteel/curated_answers.py pocketsteel/fretboard_examples.py pocketsteel/fretboard_explorer.py` - passed
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` - 5 passed
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'same_origin_browser_answer_path or production_cloudflare_answer_api_routes_broader_g_harmonized_scale_prompts or broad_g_major_harmonized or natural_minor_harmonized or named_diminished' -q` - 5 passed, 271 deselected
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'api_version or harmonized or diminished or static_g or tab_example' -q` - 24 passed, 252 deselected
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - 30 passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 23 passed
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q` - 25 passed
- `.venv/bin/python -m pytest tests/test_api_search.py -q` - 276 passed

## Integration Notes
- This patch does not restart protected preview. Lane 12 still needs to restart or otherwise verify the protected runtime at the new commit before browser smoke can pass.
- The route-level behavior remains deterministic and source-free for visual/fretboard answers.
- The 5&8 branch correction remains covered and unchanged.
- Static grip prompts and tab movement prompts remain covered by existing tests.

## Risk Assessment
- Risk: low to medium.
- Reason: the runtime code change is narrow, but it is in shared `/api/answer` response assembly. The guard only activates when a deterministic fretboard payload already exists, which should already imply a deterministic visual answer path.
- Rollback: revert this commit or remove the final assembly guard and same-origin regression.

## Human Decision Needed
- No.

## Safe-To-Stage Exact File List
- `pocketsteel/api.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-1220-05-fix-browser-answer-harmonized-scale-routing.md`

## Files That Must Not Be Staged
- Any unrelated dirty or untracked files shown by `git status --short`, especially:
  - `README.md`
  - `corpus_metadata/`
  - `docs/` files outside this handoff
  - `rag_*.py`
  - `source-inbox/`
  - `ui/brand/`
  - `public/brand/`
  - `Neon Sign/`
  - corpus/private/generated/source/provenance/deployment/auth/design assets

## Recommended Next Lane
- Lane 12 protected-preview smoke after restart at the new commit.

## Commit Readiness
- Safe to commit.

## Suggested Next Step
Lane 12: restart or verify the protected-preview backend at the new commit and rerun browser smoke for the broader G harmonized-scale prompt set using the protected URL.
