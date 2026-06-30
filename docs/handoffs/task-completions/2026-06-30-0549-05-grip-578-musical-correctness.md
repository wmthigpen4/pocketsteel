# 2026-06-30 05:49 - Lane 05 - Grip 5-7-8 Musical Correctness

## Task Summary

Fixed the E9 fretboard/chord-position bug where grip 5-7-8 could be promoted or labeled as a plain/full G major position even though fret 3 open 5-7-8 spells D-A-G: 5, 2/9, 1, with no major 3rd.

Completed:
- Classified fret 3 open G 5-7-8 as `G5/add9 (no 3rd)` partial/color, not full G major.
- Kept it hidden from starter/default cards for broad G major prompts.
- Prevented static voicings from emitting inert pedals/levers; specifically, A+B is not emitted for 5-7-8 when the B pedal affects no selected string.
- Added explicit 5-7-8 G static-grip routing that answers as partial/color and shows a focused fretboard card.
- Preserved full G major starters on pitch-valid full-triad grips.
- Corrected static G major grip payloads so they are normal fretboard positions, not tab-event-derived cards.

Intentionally not changed:
- No UI files.
- No corpus, scraping, embeddings, Chroma/vector stores, auth, DNS, deployment config, private transcripts, licensing metadata, secrets, or source-card behavior.
- No protected-preview restart.

## Files Changed

- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/answer_tab_examples.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `tests/test_tab_engine.py`
- `docs/handoffs/task-completions/2026-06-30-0549-05-grip-578-musical-correctness.md`

## What Changed

Backend fretboard logic:
- Added selected-string control applicability checks.
- `validate_fretboard_payload()` now rejects positions whose displayed pedals/levers are inert on the selected strings.
- Static candidate generation filters out inert controls before emitting positions.
- Major-position labels now account for partial/rootless/color status.
- Major partials missing the 3rd with an added 2/9 are labeled as add9/no-3rd colors instead of plain major.
- Open/no-pedals 5-7-8 remains available only as hidden advanced partial/color when pitch-valid for that interpretation.
- E-lower 5-7-8 remains pitch-validated and explicitly E-lower labeled.

Answer routing:
- Explicit `5-7-8 G grip` and `G chord on strings 5-7-8` prompts now get a direct partial/color explanation and focused fretboard payload.
- Broad G major location prompts continue to show the full-triad starter cards first.
- Static G major grip prompts are fretboard-first and no longer use tab-event metadata.

## Local Smoke Target

Smoke Target:
- Target type: local
- Result type: browser smoke plus API verification
- Exact browser URL tested: `http://127.0.0.1:8784/ui/steel-guitar-rag-mock.html?access=beta_user&v=grip-578-smoke-20260630b`
- Cache-busted URL tested: `http://127.0.0.1:8784/ui/steel-guitar-rag-mock.html?access=beta_user&v=grip-578-smoke-20260630b`
- Exact URL the user should use: protected preview needs restart before user smoke; use the Lane 12 cache-busted protected URL after restart
- Auth required: no for local controlled-state smoke
- Auth provider: none for local controlled-state smoke
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8784`
- Expected backend port: `8784`
- Expected git HEAD: `0406b1c` before commit, dirty local code loaded by local smoke server
- Version endpoint: local smoke server `/api/version` not used as proof of commit because local server loaded dirty worktree code
- Version endpoint result: not used
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant for local same-origin smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex local only
- Do not test these URLs: do not use protected preview for this fix until after restart to the committed HEAD
- Known caveats: protected-preview runtime on port 8770 reported starting HEAD `0406b1c`; it was not restarted during this lane

## Local Smoke Results

Prompts tested:
- `Where is G on E9?`
- `Show me a G major grip.`
- `Show me a 5-7-8 G grip.`
- `Show me a G chord on strings 5-7-8.`
- `Show me a G to C move.`
- `How do I use A+B pedals?`

Observed results:
- `Where is G on E9?`: fretboard rendered; Recommended selected full G major 4-5-6 card; 5-7-8 present only as no-3rd partial/color; no A+B 5-7-8 label.
- `Show me a G major grip.`: fretboard rendered; full G major 4-5-6 static card; no tab-event metadata.
- `Show me a 5-7-8 G grip.`: fretboard rendered; answer says not a full plain G major grip; card is partial/color with no 3rd; no pedals/levers.
- `Show me a G chord on strings 5-7-8.`: same partial/color behavior as explicit 5-7-8 grip request.
- `Show me a G to C move.`: deterministic movement path still shows fretboard states and tab-event metadata.
- `How do I use A+B pedals?`: deterministic A+B movement path still shows fretboard states and tab-event metadata.

## Tests And Checks

Passed:
- `.venv/bin/python -m py_compile pocketsteel/fretboard_examples.py pocketsteel/curated_answers.py pocketsteel/api.py pocketsteel/answer_tab_examples.py`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q` -> `25 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py -q` -> `53 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'fretboard or tab_example or static_g_location or explicit_g_578 or e_lower' -q` -> `46 passed, 234 deselected`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` -> `5 passed`
- `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q` -> `64 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -q` -> `280 passed`
- `.venv/bin/python -m pytest` -> `872 passed`
- `git diff --check` -> passed

## Protected Preview Smoke

Not run in this lane.

Reason:
- Protected-preview backend port `8770` was already running the starting HEAD `0406b1c`.
- This lane did not restart protected preview because restart details were not part of the current scoped backend patch and the repo has unrelated dirty work.

Lane 12 should restart protected preview to the committed fix and rerun the focused prompts.

## Risk Assessment

Risk: low to medium.

Why:
- The fix is deterministic and covered by focused payload tests plus full pytest.
- It touches shared fretboard payload generation, so downstream UI should be smoked after protected-preview restart.
- The new inert-control validation may expose future invalid generated positions earlier, which is intended but could fail tests if another generator emits inert labels.

Rollback:
- Revert the scoped commit for the six changed runtime/test files if unexpected routing regressions appear.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/answer_tab_examples.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `tests/test_tab_engine.py`
- `docs/handoffs/task-completions/2026-06-30-0549-05-grip-578-musical-correctness.md`

## Files That Must Not Be Staged

All unrelated dirty or untracked files present before this task, including but not limited to:
- `docs/handoffs/task-completions/integration-status.md`
- `README.md`
- `corpus_metadata/*`
- `source-inbox/*`
- `ui/brand/*`
- `public/brand/*`
- `Neon Sign/`
- `rag_*.py`
- private/generated/corpus/vector/deployment/design artifacts

## Recommended Next Lane

Lane 12 protected-preview restart and smoke after commit.

Suggested prompt:
`Lane 12: Restart protected preview to the grip 5-7-8 musical-correctness commit and smoke: Where is G on E9?, Show me a G major grip., Show me a 5-7-8 G grip., Show me a G chord on strings 5-7-8., Show me a G to C move., How do I use A+B pedals?. Include the required Smoke Target block and verify /api/version matches the commit.`

## Commit Readiness

Safe to commit.
