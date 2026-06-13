# Six Smoke Failures Answer Quality Fix

Date: 2026-06-13
Branch: `feature/answer-api`
HEAD: `ff5dc6b`

## Task Summary

Requested: fix the six remaining 12-prompt smoke failures after retrieval gating, without redesigning UI, weakening retrieval gating, changing deployment/DNS/auth, touching Chroma/embeddings/corpus/scraping, staging, or committing.

Completed: added narrow answer-routing and contract coverage so the six failed prompts now produce teacher-first answers or deterministic fretboard answers instead of raw forum fragments.

Intentionally not changed: no UI layout, source-card UI, deployment files, DNS, Chroma/vector stores, embeddings, scraping, source-inbox/corpus-private/generated data, auth, or commits.

## Files Changed

Implementation hunks:

- `pocketsteel/curated_answers.py`
  - Added/strengthened curated teacher-first routes for diminished-chord forum wisdom, Fender Steel King settings, and B+C pedal explanation.
  - Broadened the diagnostic hum/changer matcher so `hum ... touching the changer` routes to the existing diagnostic answer.
- `pocketsteel/fretboard_examples.py`
  - Broadened deterministic major-position parsing for `Where are my G chord positions?` and `Show me C positions on E9.`
- `pocketsteel/answering.py`
  - Kept diagnostic-troubleshooting route recognition aligned with the symmetric hum/changer phrasing.
- `pocketsteel/answer_contracts.py`
  - Kept contract inference aligned with the symmetric hum/changer phrasing.
- `tests/test_api_search.py`
  - Added exact regression coverage for the six smoke-failure prompts.

Created:

- `docs/handoffs/task-completions/six-smoke-failures-answer-quality-fix.md`

No files were deleted.

## Six Prompt Outcomes

### 1. Diminished Chords

Prompt: `How do players approach diminished chords on E9?`

Before: source-backed route produced weak/forum-fragment style answer.

After: answer explains diminished chords as movable passing sounds, spells the chord tones (`root, b3, b5`, with diminished-7th adding `bb7`), gives practical use/resolution guidance, keeps fretboard off, and preserves source evidence below the answer.

### 2. Fender Steel King Settings

Prompt: `What are common Fender Steel King settings?`

Before: answer was fragment/background style and not useful settings guidance.

After: answer gives practical settings guidance with existing gear-mode headings:

- `Likely causes or common settings`
- `Diagnostic steps`
- `Safety/caution`

It keeps fretboard off and preserves source evidence.

### 3. Hum/Changer Diagnosis

Prompt: `How do players diagnose hum that changes when touching the changer?`

Before: phrasing missed the diagnostic route and fell into weak/raw retrieval behavior.

After: answer starts with isolation guidance, lists likely causes, gives a diagnostic path, mentions touching strings/changer as grounding/shielding evidence, includes safety caution, keeps fretboard off, and preserves source evidence.

### 4. G Chord Positions

Prompt: `Where are my G chord positions?`

Before: deterministic fretboard route missed this phrasing; response had source-backed fallback and no fretboard.

After: deterministic E9 position answer returns G major starter positions:

- 3rd fret, no pedals
- 6th fret with A pedal + F lever
- 10th fret with A+B pedals

It includes a valid `response.fretboard` payload, `sources: []`, and no weak-source warning.

### 5. C Positions On E9

Prompt: `Show me C positions on E9.`

Before: deterministic fretboard route missed this phrasing; response had source-backed fallback and no fretboard.

After: deterministic E9 position answer returns C major starter positions:

- 8th fret, no pedals
- 11th fret with A pedal + F lever
- 15th fret with A+B pedals

It includes a valid `response.fretboard` payload, `sources: []`, and no weak-source warning.

### 6. B+C Pedals

Prompt: `Explain B+C pedals.`

Before: answer was related-source fragments instead of a direct explanation.

After: answer explains B+C as a melodic/position-shift tool, names strings 3-4-5 practice, passing movement, and pedal timing/blocking. It keeps fretboard off and preserves source evidence.

## Retrieval Gating Confirmation

Retrieval gating remains intact:

- Off-domain/unsafe prompts still skip retrieval through the classifier gate.
- Guardrail answers still return no source cards, no warnings, and no fretboard.
- Valid steel-guitar source-backed questions still retrieve and preserve source evidence.
- Non-position steel prompts in this fix do not attach fretboard.
- Deterministic position prompts attach fretboard and suppress SGF source cards.

The 264-row classifier validation remains clean.

## Teacher-First / Source-Backed Principle

This slice improves the teacher-first/source-backed split:

- The answer card now synthesizes the practical guidance.
- Forum/source evidence remains secondary and available where expected.
- Deterministic fretboard answers remain source-free and visual.
- No raw SGF snippets are used as the primary answer for the six prompts.

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -k "remaining_retrieval_gating_smoke_failures or amp_hum_advice_stays_diagnostic or product_red_team_forum_wisdom or location_based_g_chord"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python - <<'PY'
# 264-row question-bank classifier validation
PY
.venv/bin/python -m pytest
git diff --check
```

Results:

- Focused six/follow-on API subset: `4 passed, 184 deselected`
- `tests/test_answer_intent_classifier.py`: `62 passed`
- `tests/test_answer_eval.py`: `9 passed`
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: `233 passed`
- 264-row classifier validation:
  - rows: `264`
  - contract key mismatches: `0`
  - enum mismatches: `0`
  - off-domain/unsafe domain mismatches: `0`
  - off-domain/unsafe retrieval mismatches: `0`
  - off-domain/unsafe source mismatches: `0`
  - off-domain/unsafe fretboard mismatches: `0`
  - non-position fretboard overclassification: `0`
  - source-backed steel retrieval disabled: `0`
- Full pytest: `656 passed`
- Final `git diff --check`: passed

## Risks

Risk: low to medium.

Why:

- Changes are narrow, prompt-routing/answer-shape focused, and test-covered.
- Several touched files already contain parked edits from other lanes. Repo Steward must stage exact hunks, not whole files.
- The source-backed answer strategy is still partly curated/template-backed; broader teacher-first source synthesis remains separate future work.

Rollback:

- Revert the exact hunks in `pocketsteel/curated_answers.py`, `pocketsteel/fretboard_examples.py`, `pocketsteel/answering.py`, `pocketsteel/answer_contracts.py`, and `tests/test_api_search.py`.
- No data, vector, corpus, UI, auth, or deployment rollback is needed.

## Commit Readiness

Commit readiness: `Needs human review first`.

Reason: tests are green, but the worktree is broadly dirty and the changed files overlap with other parked backend lanes. This is ready for Lane 15 QA re-smoke, then Repo Steward should hunk-stage only this slice.

## Safe-To-Stage List

Hunk-level safe-to-stage for this task:

- `pocketsteel/curated_answers.py`
  - Diminished-chord curated route.
  - Steel King settings curated route and recognizer.
  - B+C pedals recognizer/route for `Explain B+C pedals.`
  - Symmetric hum/changer diagnostic matcher.
- `pocketsteel/fretboard_examples.py`
  - Parser patterns for `Where are my <root> chord positions?`
  - Parser pattern for `Show me <root> positions on E9.`
- `pocketsteel/answering.py`
  - Symmetric hum/changer diagnostic matcher.
- `pocketsteel/answer_contracts.py`
  - Symmetric hum/changer diagnostic matcher.
- `tests/test_api_search.py`
  - `test_remaining_retrieval_gating_smoke_failures_get_teacher_first_answers`
- `docs/handoffs/task-completions/six-smoke-failures-answer-quality-fix.md`

Do not stage entire files blindly; use patch/hunk staging.

## Must Remain Unstaged

Unless separately approved by their lane, keep parked:

- UI/design files: `ui/`, `public/`, `ui/brand/`, `Neon Sign/`, design assets.
- Deployment/DNS/auth/secrets: `deploy/`, `.wrangler/`, Cloudflare/DNS config, secrets.
- Corpus/vector/private/generated data: `corpus-private/`, `corpus-v2/`, `source-inbox/`, Chroma stores, embeddings, generated reports.
- Broad unrelated docs and pipeline files already dirty in the worktree.

## Exact Next QA Prompt

```text
Lane 15 QA / Answer Eval:

Please QA the six-smoke-failures answer-quality fix on branch feature/answer-api.

Read:
- docs/handoffs/task-completions/six-smoke-failures-answer-quality-fix.md
- AGENTS.md
- docs/llm-guidance/answer-contract.md
- docs/llm-guidance/eval-rubric.md
- docs/llm-guidance/teacher-first-answer-policy.md
- pocketsteel/curated_answers.py
- pocketsteel/fretboard_examples.py
- tests/test_api_search.py

Verify the 12-prompt retrieval-gating smoke now passes, especially:
- How do players approach diminished chords on E9?
- What are common Fender Steel King settings?
- How do players diagnose hum that changes when touching the changer?
- Where are my G chord positions?
- Show me C positions on E9.
- Explain B+C pedals.

Confirm:
- off-domain/unsafe retrieval gating still passes;
- non-position prompts do not attach fretboard;
- G/C position prompts attach fretboard and suppress SGF sources;
- valid source-backed steel prompts still show source evidence;
- no raw forum fragments, weak-source warnings, or [object Object].

Run focused answer/API/eval tests and protected/local smoke as appropriate. Report pass/fail and whether Repo Steward can hunk-stage this slice.
```

## Human Decision Needed

Yes. Human/QA should re-run the 12-prompt smoke and approve hunk-level staging because the worktree contains many unrelated parked changes.

## Recommended Next Step

Lane 15 should rerun the 12-prompt retrieval-gating smoke. If green, Lane 01 Repo Steward should hunk-stage the safe-to-stage list above and keep all unrelated dirty files parked.
