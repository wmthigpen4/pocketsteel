# 2026-06-30 20:57 Lane 05 - Parameterized Movement Cards v1

## Task Summary

Requested implementation of deterministic, beginner-safe movement examples for common standard E9 major-key chord motion:

- I to IV.
- I to V.
- I to IV to V to I.

Completed:

- Added exact prompt coverage for `G to D`, numeric `1 to 4`, numeric `1 to 5`, numeric `1 4 5 1`, and no-pedals-to-A+B connection prompts.
- Added a narrow parser route for `How do I connect no-pedals to A+B positions?`, defaulting to a G I-IV no-pedals-to-A+B exercise.
- Fixed `/api/answer` attachment order so parameterized movement examples always use the tab-derived fretboard payload, even if another deterministic fretboard payload was attached earlier.
- Added API and tab-engine regression tests for the requested prompt set.

Intentionally not changed:

- No UI code.
- No corpus, Chroma/vector store, embeddings, scraper, source-inbox, auth, DNS, deployment config, private transcripts, licensing metadata, secrets, or unrelated assets.
- No arbitrary melody arrangement, copyrighted song tab, recording transcription, or public-domain song arrangement.

## Files Changed

- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/api.py`
- `tests/test_tab_engine.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-30-2057-05-parameterized-movement-cards-v1.md`

Generated artifacts:

- None committed.

## What Changed

### Movement Prompt Support

The parameterized movement path now covers:

- `Show me a G to C move.` -> `movement-g-i-iv-v1`, I-IV, G to C.
- `Show me a G to D move.` -> `movement-g-i-v-v1`, I-V, G to D.
- `Show me a 1 to 4 move in G.` -> `movement-g-i-iv-v1`, I-IV, G to C.
- `Show me a 1 to 5 move in G.` -> `movement-g-i-v-v1`, I-V, G to D.
- `Show me a 1 4 5 1 move in G.` -> `movement-g-i-iv-v-i-v1`, I-IV-V-I, G-C-D-G.
- `How do I connect no-pedals to A+B positions?` -> defaults to G I-IV and says it is defaulting to G.

The no-pedals-to-A+B prompt is intentionally narrow. It uses the existing validated G I-IV exercise:

- Event 1: G, fret 3, strings 4-5-6, no pedals/levers.
- Event 2: C partial, fret 3, strings 5-6, A+B.

### Fretboard/Tab Alignment

`/api/answer` now forces the fretboard payload for `parameterized_chord_movement` answers to come from `fretboard_payload_for_tab_example(...)`. This prevents numeric movement prompts from keeping an earlier generic fretboard payload that does not match the tab events.

Static prompts still behave as before:

- `Show me a G major grip.` remains fretboard-first with no tab.
- `Where is G on E9?` remains fretboard-first with no tab.
- `Show me a 5-7-8 G grip.` remains partial/color with no tab.

Existing regressions preserved:

- Fender Steel King settings still return concrete source-backed settings and no fretboard/tab.
- 5-7-8 G remains `G5/add9 (no 3rd)` / partial-color.

## Smoke Target

- Target type: local
- Result type: browser smoke plus API fallback details
- Exact browser URL tested: `http://127.0.0.1:8785/ui/steel-guitar-rag-mock.html?access=beta_user&v=parameterized-movement-cards-local-20260630`
- Cache-busted URL tested: `http://127.0.0.1:8785/ui/steel-guitar-rag-mock.html?access=beta_user&v=parameterized-movement-cards-local-20260630`
- Exact URL the user should use: protected-preview URL after restart, cache-busted with the commit hash
- Auth required: no for local smoke; beta role supplied by query/header
- Auth provider: none for local smoke
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8785`
- Expected backend port: `8785`
- Expected git HEAD: `c3e884f` before commit
- Version endpoint: not used for local smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree HEAD and tests
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this local answer-page smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally; user should test protected preview after restart
- Do not test these URLs: production without protected-preview restart/version confirmation
- Known caveats: protected preview was not restarted in this lane

## Local Smoke Results

API smoke against `http://127.0.0.1:8785/api/answer`:

- `Show me a G to C move.`: PASS. Tab example `movement-g-i-iv-v1`, fretboard source `steel_guitar_rag.answer_tab_examples`, sources `[]`, warnings `[]`.
- `Show me a G to D move.`: PASS. Tab example `movement-g-i-v-v1`, fretboard source `steel_guitar_rag.answer_tab_examples`, sources `[]`, warnings `[]`.
- `Show me a 1 to 4 move in G.`: PASS. Tab example `movement-g-i-iv-v1`, fretboard source `steel_guitar_rag.answer_tab_examples`, sources `[]`, warnings `[]`.
- `Show me a 1 to 5 move in G.`: PASS. Tab example `movement-g-i-v-v1`, fretboard source `steel_guitar_rag.answer_tab_examples`, sources `[]`, warnings `[]`.
- `Show me a 1 4 5 1 move in G.`: PASS. Tab example `movement-g-i-iv-v-i-v1`, four matching fretboard positions, sources `[]`, warnings `[]`.
- `How do I connect no-pedals to A+B positions?`: PASS. Defaults to G, tab example `movement-g-i-iv-v1`, matching fretboard, sources `[]`, warnings `[]`.
- `Show me a G major grip.`: PASS. Static fretboard payload, no tab.
- `Where is G on E9?`: PASS. Static position payload, no tab.
- `Show me a 5-7-8 G grip.`: PASS. Partial/color payload, no tab.
- `What are good Fender Steel King settings?`: PASS. Two source cards, no fretboard/tab payload.

Browser smoke against the local answer page:

- Movement prompts rendered direct answer prose, validated tab cards, and matching fretboard cards.
- Static G grip and explicit 5-7-8 prompts rendered fretboard cards with no visible tab cards.
- Steel King settings rendered source-backed settings and no visible tab.
- No `[object Object]` was observed.

Note: the current UI still renders placeholder shells for source-free answers and an empty fretboard shell for non-fretboard answers. The API payloads are correct; this backend slice did not change UI rendering.

## Tests And Checks

- `git status --short` - run before work and before closeout.
- `.venv/bin/python -m py_compile steel_guitar_rag/tab_engine.py steel_guitar_rag/answer_tab_examples.py steel_guitar_rag/api.py steel_guitar_rag/fretboard_examples.py` - PASS.
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q` - PASS, `26 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'tab_example or static_g_location or explicit_g_578 or Steel_King or steel_king' -q` - PASS, `19 passed, 266 deselected`.
- `.venv/bin/python -m pytest tests/test_api_search.py -q` - PASS, `285 passed`.
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q` - PASS, `69 passed`.
- `.venv/bin/python -m pytest` - PASS, `878 passed`.
- `git diff --check` - PASS.

Skipped:

- Frontend tests were not run because no UI files changed. Local browser smoke covered rendered behavior.
- Protected-preview smoke was not run because the runtime was not restarted in this lane.

## Integration Notes

- Parameterized movement cards remain deterministic/original educational exercises.
- Static grips still belong to the fretboard path, not tab.
- Movement examples use tab plus matching fretboard states.
- Parameterized movement answers explicitly suppress SGF/source cards.
- The new no-pedals-to-A+B route defaults to G only when the user gives no key.

## Risk Assessment

Risk: low to medium.

Why:

- The runtime change is small and deterministic.
- It touches `/api/answer` attachment order for movement examples, but only for `kind == "parameterized_chord_movement"`.
- Full pytest and local browser smoke passed.

Rollback:

- Revert the scoped commit containing `steel_guitar_rag/answer_tab_examples.py`, `steel_guitar_rag/api.py`, `tests/test_tab_engine.py`, `tests/test_api_search.py`, and this handoff.

## Human Decision Needed

No for this backend slice.

Protected-preview restart/smoke is still needed before marking the user-facing runtime ready.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/api.py`
- `tests/test_tab_engine.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-30-2057-05-parameterized-movement-cards-v1.md`

## Files That Must Not Be Staged

- Existing unrelated parked files in `README.md`, `docs/`, `docs/handoffs/task-completions/integration-status.md`, `rag_*.py`, `corpus_metadata/`, `source-inbox/`, `ui/brand/`, `public/brand/`, `Neon Sign/`, corpus/private/vector/scraper/deploy/auth assets, and any generated/private artifacts.

## Recommended Next Lane

Lane 12 protected-preview restart and smoke after the scoped commit.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 protected-preview smoke prompt:

Restart protected preview at the new commit, verify `/api/version`, then smoke:

- `Show me a G to C move.`
- `Show me a G to D move.`
- `Show me a 1 to 4 move in G.`
- `Show me a 1 to 5 move in G.`
- `Show me a 1 4 5 1 move in G.`
- `How do I connect no-pedals to A+B positions?`
- `Show me a G major grip.`
- `Where is G on E9?`
- `Show me a 5-7-8 G grip.`
- `What are good Fender Steel King settings?`

Verify movement prompts show direct prose plus tab and matching fretboard, static prompts show fretboard-first/no tab, Steel King remains source-backed/no fretboard/tab, and no `[object Object]`.
