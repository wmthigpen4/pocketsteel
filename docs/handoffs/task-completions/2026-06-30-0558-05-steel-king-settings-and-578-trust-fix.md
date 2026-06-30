# 2026-06-30 05:58 Lane 05 - Steel King Settings And 5-7-8 Trust Fix

## Task Summary

Requested fix for two user-smoke trust/correctness failures:

- E9 G-major 5-7-8 voicing/ranking correctness.
- Fender Steel King settings answer specificity and source backing.

Completed in this slice:

- Preserved the already-committed 5-7-8 correction from `c635dd5`, where G fret 3 strings 5-7-8 is treated as `G5/add9 (no 3rd)` partial/color and static grip prompts stay fretboard-first with no tab.
- Replaced the generic Fender Steel King settings answer with a concrete source-backed Buddy Emmons E9 starting-point answer.
- Added curated source-card metadata for the Steel King settings discussion.
- Added regression tests for Buddy Emmons settings, source cards, no fretboard/tab, no safety boilerplate, and the existing 5-7-8/static-grip behavior.

Intentionally not changed:

- No UI files.
- No corpus, Chroma, embeddings, scraper, source-inbox, auth, DNS, deployment, or private data.
- No protected-preview restart.

## Files Changed

- `pocketsteel/curated_answers.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-30-0558-05-steel-king-settings-and-578-trust-fix.md`

Generated artifacts:

- None committed.

## Behavior Before / After

### E9 G-major 5-7-8

Before the prior committed backend fix, user smoke saw fret 3 open 5-7-8 promoted as a G major grip and some 5-7-8 rows labeled with inert A+B.

After:

- `Where is G on E9?` starts on full practical G major grips; the browser first selected `3 open · 4-5-6`.
- `Show me a 5-7-8 G grip.` answers directly that it is not a full plain G major grip.
- The focused 5-7-8 card labels the result `G5/add9 (no 3rd)`.
- Static 5-7-8 rows in the local API payload do not carry inert A+B.
- Static grip prompts remain fretboard-first and do not show visible tab.

### Fender Steel King Settings

Before this slice, the Steel King answer was generic and started with broad advice like “Players tend to treat Steel King settings as starting points.”

After:

- The answer starts with Buddy Emmons' published E9 Steel King setting as a concrete starting point.
- It includes:
  - EQ Tilt around 10 to 11 o'clock for E9.
  - Treble around 11 o'clock.
  - Mid Level around 10 to 11 o'clock.
  - Mid Frequency around 11 o'clock.
  - Bass around 1 o'clock.
  - Reverb around 10 o'clock.
- It explains the straight-up/neutral baseline, Mid Level/Mid Frequency interaction, and JCH/room/pickup caveat.
- It returns two curated source cards for the Fender Steel King settings thread.
- It does not attach fretboard or tab payloads.
- It does not include generic safety/caution boilerplate for plain settings prompts.

## Smoke Target

- Target type: local
- Result type: browser smoke plus API fallback details
- Exact browser URL tested: `http://127.0.0.1:8784/ui/steel-guitar-rag-mock.html?access=beta_user&v=steel-king-578-smoke-20260630`
- Cache-busted URL tested: `http://127.0.0.1:8784/ui/steel-guitar-rag-mock.html?access=beta_user&v=steel-king-578-smoke-20260630`
- Exact URL the user should use: protected-preview URL after restart, cache-busted with the commit hash
- Auth required: no for local smoke; beta role supplied by query/header
- Auth provider: none for local smoke
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8784`
- Expected backend port: `8784`
- Expected git HEAD: `c635dd5` before commit
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

API smoke against `http://127.0.0.1:8784/api/answer`:

- `Where is G on E9?`: PASS. Fretboard payload present, first position full G major 3-4-5/open, no tab, no sources.
- `Show me a G major grip.`: PASS. Fretboard payload present, no tab, no sources.
- `Show me a 5-7-8 G grip.`: PASS. Answer says not full plain G major, payload labels `G5/add9 (no 3rd)`, no tab, no sources.
- `Show me a G chord on strings 5-7-8.`: PASS. Same partial/color behavior.
- `What are good Fender Steel King settings?`: PASS. Buddy answer, two source cards, no fretboard/tab.
- `What Steel King settings did Buddy Emmons use?`: PASS. Buddy answer, two source cards, no fretboard/tab.
- `How do I set the mid controls on a Fender Steel King?`: PASS. Buddy answer with mid-control interaction, two source cards, no fretboard/tab.
- `Why does my amp buzz at idle?`: PASS. Diagnostic answer still routes separately.
- `Show me a G to C move.`: PASS. Movement tab and fretboard remain present.
- `How do I use A+B pedals?`: PASS. Movement/pedal tab and fretboard remain present.

Browser smoke against the local answer page:

- Static G prompts rendered fretboard cards and no visible tab.
- Focused 5-7-8 prompts rendered partial/color wording and no visible tab.
- Steel King prompts rendered Buddy settings, Mid Level/Mid Frequency explanation, and two visible source cards.
- Movement prompts still rendered tab plus fretboard.
- No `[object Object]` was observed.

Note: the current UI still renders a “No sources returned” placeholder in the source-card area for source-free deterministic answers. The API payload has `sources: []`; this UI placeholder is pre-existing and was not changed in this backend slice.

## Tests And Checks

- `git status --short` - run before work and before closeout.
- `.venv/bin/python -m py_compile pocketsteel/curated_answers.py pocketsteel/api.py pocketsteel/fretboard_examples.py pocketsteel/answer_tab_examples.py` - PASS.
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'Steel_King or steel_king or Fender or amp_hum or static_g_location or explicit_g_578 or tab_example' -q` - PASS, `16 passed, 265 deselected`.
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_tab_engine.py -q` - PASS, `78 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py -q` - PASS, `281 passed`.
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q` - PASS, `69 passed`.
- `.venv/bin/python -m pytest` - PASS, `873 passed`.
- `git diff --check` - PASS.

## Integration Notes

- The Steel King answer now uses curated explicit source cards rather than relying on noisy retrieval.
- The Steel King matcher excludes buzz/hum/noise/diagnostic terms so amp troubleshooting does not route to settings.
- The G 5-7-8 correctness behavior is in the prior committed backend fix and was regression-smoked here because the user request included both failures.
- No protected-preview restart was performed. Lane 12 should restart protected preview and smoke the same prompts at the new commit.

## Risk Assessment

Risk: low.

Why:

- Runtime change is limited to one curated answer path and its matcher.
- The matcher is narrowed away from diagnostic/noise prompts.
- Full pytest passed.

Rollback:

- Revert the scoped commit containing `pocketsteel/curated_answers.py`, `tests/test_api_search.py`, and this handoff.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `pocketsteel/curated_answers.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-30-0558-05-steel-king-settings-and-578-trust-fix.md`

## Files That Must Not Be Staged

- Existing unrelated parked files in `README.md`, `docs/`, `docs/handoffs/task-completions/integration-status.md`, `rag_*.py`, `corpus_metadata/`, `source-inbox/`, `ui/brand/`, `public/brand/`, `Neon Sign/`, corpus/private/vector/scraper/deploy/auth assets, and any generated or private artifacts.

## Recommended Next Lane

Lane 01 Repo Steward is satisfied by exact-path staging and commit in this autopilot run if staged diff remains scoped. After commit, Lane 12 should restart protected preview and run protected-preview smoke for the same prompt set.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 protected-preview smoke prompt:

Run protected-preview smoke for the new commit against:

- `Where is G on E9?`
- `Show me a G major grip.`
- `Show me a 5-7-8 G grip.`
- `Show me a G chord on strings 5-7-8.`
- `What are good Fender Steel King settings?`
- `What Steel King settings did Buddy Emmons use?`
- `How do I set the mid controls on a Fender Steel King?`
- `Why does my amp buzz at idle?`
- `Show me a G to C move.`
- `How do I use A+B pedals?`

Verify the new `/api/version` commit hash before testing and record the cache-busted protected-preview URL.
