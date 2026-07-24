# High-Signal Broad QA P1 Blockers Fix

## Task Summary

Autopilot user smoke bug fix for the highest-signal P1 blockers found by the broad automated QA matrix at HEAD `2cdea8a`.

Completed:
- Fixed `Bb` / `B-flat` chord-symbol normalization so it no longer becomes invalid `BB`.
- Broadened deterministic major-position phrasing for `What frets give me C major?`, `Which frets are C major on E9?`, and `Where do I find C major positions?`.
- Added source-free structured answers for the recurring copedent/fretboard prompts:
  - `What does my vertical lever lower?`
  - `How does my C pedal change strings 4 and 5?`
  - `What grips should I use for A+B at the 10th fret?`
  - `Where is the IV chord from open G on my E9?`
- Added off-domain guardrail coverage for JavaScript/Python sorting-code and dishwasher prompts.
- Cleaned the Telonics slide-bar fact-check answer and suppressed weak-source warning text for that specific curated check.

Intentionally not changed:
- UI files, source-card UI, public landing/design assets.
- Chroma, embeddings, corpus, source-inbox, scraping, auth, deployment, DNS, private source data, or generated corpus artifacts.
- Broad P2/P3 matrix calibration noise and practice-plan source-required evaluator noise.
- Integration-status refresh, because `docs/handoffs/task-completions/integration-status.md` was already dirty from unrelated parked work.

## Root Cause

The five confirmed P1 clusters had separate but related routing gaps:

- `Bb` was treated as two letters before accidental parsing, so `Bb` normalized to invalid `BB`.
- Several natural-language C major fret prompts were not covered by the deterministic chord-position regexes.
- Some copedent-shaped prompts were not caught by deterministic/private-profile answer paths before SGF retrieval.
- The no-op/off-domain classifier and curated guardrail did not include common coding/household break-test prompts.
- The Telonics slide-bar curated answer and warning path exposed source-confidence internals instead of plain user wording.

## Files Changed

- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `tests/test_fretboard_examples.py`
- `docs/handoffs/task-completions/high-signal-broad-qa-p1-blockers-fix.md`

No files were deleted. No generated/private/corpus/vector/design/deploy artifacts were intentionally changed.

## Exact P1 Clusters Fixed

1. `Bb` / `B-flat` root normalization:
   - `How do I play a Bb chord on E9?`
   - `How do I play a B-flat chord on E9?`
   - `Where can I find B flat chords?`
   - `What does Bb minor look like?`
   - `Show me A# minor on E9.`

2. C major fret phrasing:
   - `What frets give me C major?`
   - `What frets give me a C chord?`
   - `Which frets are C major on E9?`
   - `Where is C major on the fretboard?`
   - `Where do I find C major positions?`

3. High-confidence copedent/fretboard prompt escapes:
   - vertical lever lower
   - C pedal strings 4 and 5
   - A+B at 10th fret grips
   - IV chord from open G

4. Off-domain guardrail escapes:
   - `Give me a JavaScript sorting algorithm.`
   - `Write Python code for quicksort.`
   - `How do I fix my dishwasher?`

5. Telonics slide-bar weak-source wording:
   - `Did Telonics ever make a slide bar?`

## Before / After Examples

`How do I play a Bb chord?`
- Before: invalid chord clarification for `BB`.
- After: `Bb major is Bb-D-F...` with E9 positions and `response.fretboard`, `sources: []`, `warnings: []`.

`What frets give me C major?`
- Before: could fall to source fragments.
- After: `C major is C-E-G...` with 8th fret open, 11th fret A+F, 15th fret A+B, `response.fretboard`, `sources: []`, `warnings: []`.

`What does my vertical lever lower?`
- Before: raw SGF-style fragments about unrelated B-to-A# choices.
- After: `On your saved 10-string E9 setup, the vertical lever (LKV) lowers strings 5 and 10 from B to Bb/A#.` Source-free.

`Give me a JavaScript sorting algorithm.`
- Before: escaped the steel-guitar scope guardrail.
- After: concise Steel Guitar RAG scope redirect, no sources, no fretboard.

`Did Telonics ever make a slide bar?`
- Before: answer/warnings exposed weak-source wording.
- After: says no strong sourced answer from listed forum material, notes limited curated information, and recommends checking Telonics/dealer/model detail. No weak-source warning in JSON for this path.

## Tests And Checks

Commands run:

- `git status --short`
- `git diff --check`
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py -q`
  - Result: `50 passed`
- `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py -q`
  - Result: `69 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - Result: `223 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q`
  - Result: `54 passed`
- `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_answer_eval.py tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py tests/test_fretboard_examples.py -q`
  - Result: `396 passed`
- Scoped P1 API probe over the high-signal prompts from this task:
  - Result: all probed prompts returned expected clean routing characteristics.
- `.venv/bin/python -m pytest`
  - Result: `659 passed, 2 failed`
  - Unrelated known failures:
    - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
    - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
- `git diff --check`
  - Result: passed

## Smoke Target

- Target type: API-fallback
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not tested
- Cache-busted URL tested: not tested
- Exact URL the user should use: unchanged protected preview root after runtime restart by deployment lane
- Auth required: local test used local-dev app helper; protected-preview auth not exercised
- Auth provider: local scaffold in test helper
- Cloudflare Access login result: not attempted
- Local backend URL: in-process test app, not a long-running server
- Expected backend port: not applicable
- Expected git HEAD: `2cdea8a` plus this scoped patch before commit
- Version endpoint: not queried in this task
- Version endpoint result: not applicable
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: unchanged
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: unchanged
- Who should test this URL: Lane 15 / deployment lane after protected-preview restart
- Do not test these URLs: do not infer protected-preview behavior from the in-process API helper
- Known caveats: API fallback validates backend routing only; not a browser smoke

## Scoped P1 Probe Summary

Probe prompts all returned expected high-signal behavior:

- G chord on 6th fret: `sources=0`, `warnings=[]`, `fretboard=True`
- G chord across guitar: `sources=0`, `warnings=[]`, `fretboard=True`
- Bb/B-flat major prompts: `sources=0`, `warnings=[]`, `fretboard=True`
- C major fret prompts: `sources=0`, `warnings=[]`, `fretboard=True`
- vertical lever / C pedal prompts: `sources=0`, `warnings=[]`
- A+B 10th fret grips and IV from open G: `sources=0`, `warnings=[]`, `fretboard=True`
- JavaScript/Python/dishwasher prompts: `sources=0`, `warnings=[]`, `fretboard=False`
- Telonics slide-bar prompt: clean answer, no weak-source warning

## Integration Notes

- Deterministic chord/fretboard routes remain source-free and attach `response.fretboard` when visualizable.
- Valid steel source-backed answers are still allowed to retrieve.
- Telonics slide-bar source cards may remain below the answer as context, but weak-source warnings are suppressed for that specific curated fact-check path.
- The handoff and implementation do not resolve broad evaluator calibration noise in P2/P3 rows.
- The two full-suite failures are the known unrelated static/UI failures called out by the task.

## Risk Assessment

Risk: medium-low.

Why:
- The patch touches shared answer routing and parser code.
- The changed paths are deterministic, focused, and covered by API/fretboard/classifier/eval tests.
- The largest remaining risk is commit hygiene because the worktree contains many unrelated parked changes.

Rollback:
- Revert the scoped commit for:
  - `steel_guitar_rag/answer_intent_classifier.py`
  - `steel_guitar_rag/api.py`
  - `steel_guitar_rag/curated_answers.py`
  - `steel_guitar_rag/fretboard_examples.py`
  - the three focused test files
  - this handoff
- Do not use broad reset/checkout in the dirty shared worktree.

## Commit Readiness

Safe to commit.

Exact safe-to-stage file list:
- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `tests/test_fretboard_examples.py`
- `docs/handoffs/task-completions/high-signal-broad-qa-p1-blockers-fix.md`

Files that must remain unstaged:
- Existing parked docs/corpus/source-inbox/public/design/deploy/root-RAG changes.
- `docs/handoffs/task-completions/integration-status.md` because it was dirty before this task.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, source-inbox raw/provenance files, `.wrangler/`, deployment/DNS/auth files, `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, and generated private data.

## Suggested Next Step

Recommended lane: `15 QA / Answer Eval`.

Exact prompt:

```text
Rerun the broad QA smoke matrix against the commit that includes `backend: fix broad qa chord and guardrail blockers`. Focus first on the five previously confirmed high-signal P1 clusters: Bb/B-flat normalization, C-major fret phrasing, copedent/fretboard prompt escapes, JavaScript/Python/dishwasher off-domain guardrails, and Telonics slide-bar weak-source wording. Report remaining P1s separately from likely evaluator calibration noise.
```

Human decision needed: no for this scoped backend commit; yes before any protected-preview restart/deploy.
