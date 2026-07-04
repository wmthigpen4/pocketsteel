# 2026-07-04 09:37 - Lane 05 - Progression Guide v0

## Task Summary

Implemented Progression Guide v0 as a deterministic, fretboard-first answer route for standard E9 major-key progression guidance. The slice adds validated static chord-route payloads for beginner-safe progression prompts without using SGF/forum retrieval, tab generation, copyrighted song material, or corpus-derived fret/string/pedal claims.

Completed:

- Added deterministic `progression_guide` backend response contract.
- Added C and G progression-route generation with pitch-validated fretboard payloads.
- Added frontend normalization and a compact progression guide card section.
- Hid empty source-card placeholders for source-free progression, fretboard-backed deterministic, and copyright/transcription guardrail answers.
- Preserved movement prompt behavior: two-chord movement/lick prompts remain tab-owned.
- Preserved static grip behavior: static grips remain fretboard-first and no-tab by default.

Intentionally not changed:

- No SGF/RAG/corpus lookup is used to choose progression positions.
- No Chroma, embeddings, scraping, corpus, auth, DNS, deployment, private source data, or brand assets were touched.
- No protected-preview restart was performed in this handoff.

## Files Changed

- `pocketsteel/progression_guide.py` - new deterministic route generator and pitch/fretboard payload builder.
- `pocketsteel/api.py` - pre-retrieval progression-guide route.
- `pocketsteel/api_contract.py` - optional `progression_guide` answer response field.
- `ui/answer-client.js` - progression guide normalization.
- `ui/steel-guitar-rag-mock.html` - progression guide display section and source-placeholder hiding for source-free deterministic/guardrail answers.
- `tests/test_progression_guide.py` - unit coverage for deterministic progression routes.
- `tests/test_api_search.py` - API coverage for progression guide, source suppression, tab/static regressions.
- `tests/test_frontend_answer_ui.py` - UI normalization/static wiring coverage.
- `tests/test_same_origin_smoke_server.py` - cache-bust assertion update.
- `docs/progression-guide-v0.md` - product/API contract note.
- `docs/handoffs/task-completions/2026-07-04-0937-05-progression-guide-v0.md` - this handoff.

Generated artifacts:

- None committed or staged.

## Generated Row Coverage

Deterministic routes now supported:

- C I-IV-V-I home-pocket route:
  - C: fret 8, strings 5-6-8, no pedals/no levers.
  - F: fret 8, strings 5-6-8, A+B.
  - G: fret 10, strings 5-6-8, A+B.
  - C: fret 8, strings 5-6-8, no pedals/no levers.
- C I-IV-V-I alternates:
  - ascending same-grip route ending at fret 11 with A pedal + E-raise.
  - pedals-down route around frets 13/15.
  - dominant-shell route using E-lower and G7(no5) shell.
- C diatonic home-pocket route:
  - C, Am, Em, F, Dm, G7 shell, C.
  - G7 shell is labeled as dominant shell with root, 3rd, b7 present and 5 omitted.
- G I-IV-V-I home-pocket route:
  - G: fret 3, strings 5-6-8, no pedals/no levers.
  - C: fret 3, strings 5-6-8, A+B.
  - D: fret 5, strings 5-6-8, A+B.
  - G: fret 3, strings 5-6-8, no pedals/no levers.
- G I-IV-V-I pedals-down alternate.
- V7-to-I shell routes in C and G.

## Validation Rules Implemented

- Every route event resolves notes from deterministic E9 pitch logic.
- Every route event includes a `renderablePositionId` that exists in `fretboard.positions`.
- Every fretboard position passes the existing `validate_fretboard_payload` contract.
- Inert controls are rejected by the shared fretboard validator.
- Dominant shells are labeled honestly when the 5th is omitted.
- Source cards are suppressed for deterministic progression answers.
- `tab_example` is not attached for progression-guide answers.
- Two-chord movement prompts such as "Show me a G to C move" remain tab-owned.

## Tests And Checks

Commands run:

- `PYTHONPATH=. .venv/bin/python scripts/serve_answer_smoke.py --help` - passed.
- `.venv/bin/python -m py_compile pocketsteel/progression_guide.py pocketsteel/api.py`
- `.venv/bin/python -m py_compile pocketsteel/progression_guide.py pocketsteel/api.py pocketsteel/api_contract.py`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_progression_guide.py -q` - `6 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'progression or tab_example or static_g_location or copyright or transcribe' -q` - `26 passed, 263 deselected`.
- `.venv/bin/python -m pytest tests/test_progression_guide.py tests/test_tab_engine.py tests/test_api_contract.py -q` - `37 passed`.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_pedal_steel_fretboard_ui.py -q` - `61 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py -q` - `289 passed`.
- `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q` - `64 passed`.
- `.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py -q` - `12 passed`.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py -q` - `36 passed`.
- `.venv/bin/python -m pytest` - `888 passed`.
- `git diff --check` - passed.

## Local Smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8786/ui/steel-guitar-rag-mock.html?access=beta_user&v=progression-guide-v0-local`
- Cache-busted URL tested: `http://127.0.0.1:8786/ui/steel-guitar-rag-mock.html?access=beta_user&v=progression-guide-v0-local`
- Exact URL the user should use: local smoke only, not for user testing.
- Auth required: no Cloudflare Access; local dev beta access query used.
- Auth provider: scaffold/local dev
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8786`
- Expected backend port: `8786`
- Expected git HEAD: `cf00ec9` before commit
- Version endpoint: not checked for local smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree/current HEAD
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: protected preview was not restarted in this handoff
- Known caveats: local smoke does not prove protected-preview behavior

Local browser prompts tested:

- `Show me a C F G C progression on E9.` - pass; progression guide visible, fretboard visible, no tab, no sources, no `[object Object]`.
- `How do I play I IV V I in C on pedal steel?` - pass; progression guide visible, fretboard visible, no tab, no sources, no `[object Object]`.
- `Give me a beginner route through G C D G.` - pass; progression guide visible, fretboard visible, no tab, no sources, no `[object Object]`.
- `Show me C Am Em F Dm G7 C as a pedal steel progression.` - pass; progression guide visible, fretboard visible, no tab, no sources, no `[object Object]`.
- `Show me a G to C move.` - pass; existing movement tab visible, fretboard visible, no progression guide, no sources, no `[object Object]`.
- `Show me a G major grip.` - pass; fretboard visible, no tab, no progression guide, no sources, no `[object Object]`.
- `Give me the full tab for a modern copyrighted song.` - pass; clean refusal, no tab, no fretboard, no progression guide, no sources, no `[object Object]`.
- `Transcribe this YouTube recording into tab.` - pass; clean refusal, no tab, no fretboard, no progression guide, no sources, no `[object Object]`.

Local API smoke for the same prompts also passed, with progression answers returning `sources: []`, `warnings: []`, `fretboard`, and `progression_guide`, and no `tab_example`.

## Integration Notes

- New optional response field: `progression_guide`.
- Existing `fretboard.positions` remains the SVG/fretboard rendering contract.
- Existing `tab_example` contract remains unchanged.
- UI exposes a progression route card only when `response.progressionGuide` is present.
- The source section is hidden for source-free deterministic visual answers and copyright/tab guardrails to avoid a misleading "No sources returned" card.

## Risk Assessment

Risk: medium.

Reasons:

- `/api/answer` routing has a new pre-retrieval deterministic branch.
- `ui/steel-guitar-rag-mock.html` has a small new answer section and source-placeholder condition.
- Full pytest and browser smoke passed locally.

Rollback:

- Revert `pocketsteel/progression_guide.py`, the API import/branch, the optional API contract field, UI progression rendering, and related tests/docs.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `pocketsteel/progression_guide.py`
- `pocketsteel/api.py`
- `pocketsteel/api_contract.py`
- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_progression_guide.py`
- `tests/test_api_search.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/progression-guide-v0.md`
- `docs/handoffs/task-completions/2026-07-04-0937-05-progression-guide-v0.md`

## Files That Must Not Be Staged

All unrelated parked files shown by `git status --short`, especially:

- `README.md`
- `corpus_metadata/**`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_*.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/**`
- `Neon Sign/**`
- existing untracked handoffs/assets not listed above

## Recommended Next Lane

Lane 01 exact-path commit, then Lane 12 protected-preview restart/smoke if the runtime restart command is available and safe.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit this scoped slice with exact-path staging:

`feat: add deterministic progression guide`

Then run protected-preview smoke for:

- `Show me a C F G C progression on E9.`
- `How do I play I IV V I in C on pedal steel?`
- `Give me a beginner route through G C D G.`
- `Show me C Am Em F Dm G7 C as a pedal steel progression.`
- `Show me a G to C move.`
- `Show me a G major grip.`
- `Give me the full tab for a modern copyrighted song.`
- `Transcribe this YouTube recording into tab.`
