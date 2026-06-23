# 2026-06-23 05 - Fix Displayed Harmonized Scale Fallback

## Task Summary

Pass/warn/fail: pass

Lane: 05 Backend / RAG Integration

Branch: `feature/answer-api`

Starting HEAD: `4d58cda docs: record browser harmonized scale protected smoke`

Final HEAD / commit: not self-referential in this committed handoff; final commit hash is reported in the Codex closeout after exact-path commit.

Requested: diagnose and fix why protected browser answers still displayed the generic "I need a more specific steel-guitar question" fallback for broad G harmonized-scale prompts while the specific `strings 5 and 8` prompt passed.

Completed:
- Confirmed the displayed fallback was backend/API answer text, not frontend-generated text.
- Tightened deterministic intent classification for G harmonized-scale and named diminished visual prompts.
- Tightened the older `intent_mode_for_question` visual recognizer for the same prompt family.
- Added regression coverage proving these prompts are classified as visual/fretboard requests and that the same-origin browser-equivalent API path does not touch search for them.

Intentionally not changed:
- No UI files.
- No deployment, launchd, Cloudflare Tunnel, DNS, Cloudflare Access, auth, secrets, corpus, Chroma, embeddings, scraping, or private-source work.
- No tab-example behavior changes.
- No SGF/source-backed behavior changes outside this deterministic visual prompt family.

## Root Cause

The protected browser rendered fallback text supplied by `/api/answer`. Frontend inspection showed `ui/answer-client.js` sends the visible prompt directly to `/api/answer`, and `ui/steel-guitar-rag-mock.html` renders `response.answer`; neither file generates the generic specificity fallback.

The backend had two visual-routing classifiers drifting from the deterministic G harmonized-scale helpers:
- `classify_answer_request("Show me a G harmonized scale.")` returned `off_domain` / `guardrail_refusal` with `needs_fretboard=false`.
- `intent_mode_for_question("Show me a G harmonized scale.")` returned `unknown_low_confidence`.

The narrower `Show me a G harmonized scale on strings 5 and 8.` prompt avoided the failure because the word `strings` already made it look like an instrument visual request. Broad prompts did not.

Evidence before fix:
- Browser-equivalent protected UI test for `Show me a G harmonized scale.` displayed:
  `I need a more specific steel-guitar question to give a useful answer.`
- The rendered answer had no visible fretboard.
- Local direct `/api/answer` curl could not capture protected JSON because the production Cloudflare Access path correctly rejects unauthenticated loopback API requests with `401`.

## What Changed

Files changed:
- `pocketsteel/answer_intent_classifier.py`
- `pocketsteel/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-1302-05-fix-displayed-harmonized-scale-fallback.md`

Implementation details:
- Added a narrow G harmonized-scale visual recognizer in `pocketsteel/answer_intent_classifier.py`.
- The recognizer covers:
  - `Show me a G harmonized scale.`
  - `Show me G major harmonized scale on E9.`
  - `Show me a G major harmonized scale.`
  - `Show me a G harmonized scale on E9.`
  - `Show me a G natural minor harmonized scale.`
  - `Show me G natural minor harmonized scale on E9.`
  - `Show me the F# diminished position in G.`
  - `Show me the A diminished position in G minor.`
  - `Show me a G harmonized scale on strings 5 and 8.`
- These classify as:
  - `domain=steel_guitar`
  - `intent=copedent_position`
  - `needs_sources=false`
  - `needs_fretboard=true`
  - `needs_copedent=true`
  - `retrieval_allowed=false`
  - `allowed_answer_shape=copedent_position`
- Added the same visual recognizer to `pocketsteel/curated_answers.py` for the legacy `intent_mode_for_question` path.
- Strengthened the same-origin browser-equivalent API test to assert `FakeSearchIndex.calls == []`, proving the deterministic path wins before retrieval.

## Prompt Results After Fix

All tested prompts returned deterministic answer text, `fretboard`, `sources=[]`, `warnings=[]`, and no `tab_example`:

- `Show me a G harmonized scale.`
  - Answer lead: `Here is a concise G major harmonized-scale map on E9.`
  - Fretboard: `G major harmonized scale on E9`, 12 positions.
- `Show me G major harmonized scale on E9.`
  - Answer lead: `Here is a concise G major harmonized-scale map on E9.`
  - Fretboard: `G major harmonized scale on E9`, 12 positions.
- `Show me a G major harmonized scale.`
  - Answer lead: `Here is a concise G major harmonized-scale map on E9.`
  - Fretboard: `G major harmonized scale on E9`, 12 positions.
- `Show me a G harmonized scale on E9.`
  - Answer lead: `Here is a concise G major harmonized-scale map on E9.`
  - Fretboard: `G major harmonized scale on E9`, 12 positions.
- `Show me a G natural minor harmonized scale.`
  - Answer lead: `Here is a concise G natural minor harmonized-scale map on E9.`
  - Fretboard: `G natural minor harmonized scale on E9`, 8 positions.
- `Show me G natural minor harmonized scale on E9.`
  - Answer lead: `Here is a concise G natural minor harmonized-scale map on E9.`
  - Fretboard: `G natural minor harmonized scale on E9`, 8 positions.
- `Show me the F# diminished position in G.`
  - Answer lead: `F# diminished in G major is F#-A-C.`
  - Fretboard: `F# diminished position in G`, 1 position.
- `Show me the A diminished position in G minor.`
  - Answer lead: `A diminished in G natural minor is A-C-Eb.`
  - Fretboard: `A diminished position in G natural minor`, 1 position.
- `Show me a G harmonized scale on strings 5 and 8.`
  - Answer lead: `Here are the validated G harmonized-scale 5&8 branch options on E9.`
  - Fretboard: `G harmonized scale 5&8 branches`, 4 positions.

The 5&8 branch correction remains intact:
- Both A+F and E-lower branches remain present.
- Corrected fret 13 E-lower C/E branch remains present.
- Fret 11 E-lower is not used as the C/E branch.

## Tests And Checks

Run and passed:
- `git diff --check`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m py_compile pocketsteel/api.py pocketsteel/curated_answers.py pocketsteel/fretboard_examples.py pocketsteel/fretboard_explorer.py pocketsteel/answer_intent_classifier.py`
- `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py -q`
  - `86 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - `5 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'harmonized or diminished' -q`
  - `6 passed, 270 deselected`
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'api_version or harmonized or diminished or static_g or tab_example' -q`
  - `24 passed, 252 deselected`
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - `276 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - `30 passed`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
  - `23 passed`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - `25 passed`

Skipped:
- Full `pytest`; focused backend/API/UI-adjacent suites required by the task passed, and the repo has known unrelated full-suite static/UI caveats in recent handoffs.
- Protected-preview restart/smoke; explicitly out of scope for Lane 05 and should be run by Lane 12 after this commit.

## Browser-Equivalent Coverage

Covered by `tests/test_api_search.py::test_same_origin_browser_answer_path_routes_broader_g_harmonized_scale_prompts`.

The test now:
- Uses the same-origin app wrapper.
- Uses production Cloudflare Access auth mode with a fake verifier.
- Sends the browser-style JSON body without explicit `mode` / `topK`.
- Asserts no generic fallback text.
- Asserts `fretboard` exists.
- Asserts no `tab_example`.
- Asserts `sources == []`.
- Asserts `warnings == []`.
- Asserts the fake search index was not called.

## Integration Notes

Backend/frontend ownership:
- Backend was the blocker.
- Frontend rendering was inspected but not changed.

Response-shape behavior:
- Deterministic visual answers remain source-free and warning-free.
- Static harmonized-scale prompts do not attach tab examples.
- No `/api/answer` schema change.

Protected paths:
- Deployment, auth, corpus, Chroma, embeddings, scraping, source-inbox, private source data, and UI brand/design assets were not touched.

## Risk Assessment

Risk: low.

Why:
- Change is narrow to G harmonized-scale and named diminished visual prompt classification.
- Existing deterministic payload generation was already present and tested.
- Stronger same-origin API test now proves pre-retrieval behavior.

Rollback notes:
- Revert the two classifier helper additions and associated tests if this causes unexpected prompt classification issues.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `pocketsteel/answer_intent_classifier.py`
- `pocketsteel/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-1302-05-fix-displayed-harmonized-scale-fallback.md`

## Files That Must Not Be Staged

Unrelated parked dirty/untracked files visible in `git status --short`, including but not limited to:
- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- All untracked corpus/source/deploy/design/generated artifacts not named in the safe-to-stage list.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment:

Run protected-preview restart/smoke against the new committed runtime and verify the exact protected URL with cache busting. Required smoke prompts are the nine harmonized-scale/diminished prompts listed above.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 prompt:

`Lane 12: Restart protected preview on the new commit from docs/handoffs/task-completions/2026-06-23-1302-05-fix-displayed-harmonized-scale-fallback.md and rerun the broader G harmonized-scale protected browser smoke. Verify /api/version matches the new HEAD, use a cache-busted protected URL, and report exact browser results for the nine prompts.`
