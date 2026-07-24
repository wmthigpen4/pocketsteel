# Chord-Quality Fretboard Routing User Smoke Fix

## Task Summary

Autopilot user smoke found repeated misses for chord-quality and multi-chord E9 position questions. The app was either exposing learner-hostile/internal wording or falling back to SGF/forum fragments instead of giving direct teacher-first answers with fretboard visuals where supported.

Completed:

- Broadened deterministic chord-quality parsing for `dom 7`, `maj 7`, compact `maj7`, and `major 7th` forms.
- Replaced internal implementation wording such as "deterministic map" in major-7, dominant-7, diminished, diminished-7, and augmented theory answers.
- Added visual fallback behavior for dominant-7 and major-7 "how do I play" questions: answer the chord quality directly and attach the nearest reliable major-position fretboard as the visual reference.
- Added deterministic minor "show me" routing for prompts like `Show me an E minor chord` and `Show me E minor on the fretboard`.
- Added deterministic multi-target major/minor routing for prompts like `Show me an E major and E minor`.
- Kept source cards suppressed for these deterministic routes.

Intentionally not changed:

- No UI files changed.
- No `/api/answer` schema changes.
- No source-card layout changes.
- No auth, deployment, DNS, corpus, Chroma, embeddings, scraping, source-inbox, private source data, or visual asset changes.
- Did not add exact dominant-7/major-7 grip generation beyond the existing major-position visual reference.

## Lane Classification

- Lane: `05 Backend / RAG Integration`
- Task type: AUTOPILOT USER SMOKE BUG
- Branch: `feature/answer-api`
- HEAD during work: `658c069 backend: answer practical chord questions directly`

## Root Cause

The existing direct-answer-first slice handled some chord-quality questions, but the parser and visual attachment behavior still had gaps:

- `dom 7` and spaced `maj 7` were not consistently normalized in all parser paths.
- Compact `Fmaj7` was missed by the unsupported chord-position parser because the optional article regex matched `a` before `an`, leaving `n fmaj7` as the parsed body.
- `Show me an E minor chord` was not covered by the minor-position prompt patterns.
- Multi-target prompts such as `Show me an E major and E minor` had no deterministic route.
- Several fallback sentences still used internal implementation language such as "current deterministic map."

## Files Changed

- `steel_guitar_rag/basic_chord_answers.py`
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/chord-quality-fretboard-routing-user-smoke-fix.md`

No files were deleted.

## Parser / Composer Behavior Changed

### Dominant 7

Prompts covered:

- `How do I play a G dom 7?`
- `How do I play a G7?`
- `What is a G dominant 7?`

Behavior:

- Answers directly: `G7, or G dominant 7, is G-B-D-F`.
- Explains root, major 3rd, perfect 5th, and flat 7th.
- For `How do I play...` position-shaped prompts, attaches a `G major positions on E9` fretboard payload as the reliable visual reference.
- Does not mention `deterministic map`, `rules engine`, `payload`, `classifier`, or `contract`.
- Uses `sources: []` and `warnings: []`.

### Major 7

Prompts covered:

- `How do I play an F maj 7?`
- `How do I play an Fmaj7?`
- `How do I play an F major 7th?`
- `What is Fmaj7?`

Behavior:

- Answers directly: `Fmaj7 is F-A-C-E`.
- Explains root, major 3rd, perfect 5th, and major 7th.
- For `How do I play...` position-shaped prompts, attaches an `F major positions on E9` fretboard payload as the reliable visual reference.
- For `What is Fmaj7?`, keeps the answer source-free and does not force a fretboard.
- Does not use SGF fragments.

### Minor

Prompts covered:

- `Show me an E minor chord.`
- `How do I play E minor on E9?`
- `Show me E minor on the fretboard.`

Behavior:

- Answers directly: `An E minor chord means the notes E-G-B`.
- Uses existing pitch-validated minor-position logic.
- Attaches `E minor positions on E9`.
- Keeps SGF/forum fragments out of the primary answer.

### Multi-Target Major / Minor

Prompts covered:

- `Show me an E major and E minor.`
- `Show me G major and G minor.`

Behavior:

- Answers both chord targets in the main answer.
- Uses one combined fretboard payload because the current public answer contract has one `response.fretboard` slot.
- Combined payload title example: `E major and E minor positions on E9`.
- Card labels distinguish major and minor positions.
- Does not change the public API schema.

## Before / After Examples

### How do I play a G dom 7?

Before:

- Answer exposed learner-hostile/internal wording: `The current deterministic map may not show every dominant-7 grip yet...`

After:

- First sentence: `G7, or G dominant 7, is G-B-D-F: root, major 3rd, perfect 5th, and flat 7th.`
- Fretboard: `G major positions on E9`
- Sources: `[]`
- Warnings: `[]`

### How do I play an F maj 7?

Before:

- Fell through to SGF/forum fragments about C Maj, C7, D maj 7th, and AB pedals.

After:

- First sentence: `Fmaj7 is F-A-C-E: root, major 3rd, perfect 5th, and major 7th. F major 7 is the same chord label written out.`
- Fretboard: `F major positions on E9`
- Sources: `[]`
- Warnings: `[]`

### Show me an E minor chord.

Before:

- Fell through to SGF/forum fragments about knee levers, relative minor, and 6th string lower.

After:

- First sentence: `An E minor chord means the notes E-G-B: root, minor 3rd, and perfect 5th.`
- Fretboard: `E minor positions on E9`
- Sources: `[]`
- Warnings: `[]`

### Show me an E major and E minor.

Before:

- Fell through to SGF/forum fragments about 8-string setup and 3rd fret pedals.

After:

- First sentence: `Here are both E major and E minor on E9.`
- Fretboard: `E major and E minor positions on E9`
- Sources: `[]`
- Warnings: `[]`

## Tests Added / Updated

Updated `tests/test_api_search.py` with coverage for:

- Dominant-7 direct answers and visual fallback for `How do I play...` prompts.
- Major-7 direct answers and visual fallback for `How do I play...` prompts.
- Definition-only `What is Fmaj7?` remaining source-free and non-visual.
- Suspended usage/rooted sus internal-language regression.
- Minor "show me" prompts producing teacher-first answers and fretboard payloads.
- Multi-target major/minor prompts producing both answer text and combined fretboard payload.
- Internal language ban for `deterministic map`, `rules engine`, `payload`, `classifier`, and `contract` in these answer bodies.

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -k "major_seventh_questions or dominant_seventh or major_seventh_play or suspended_usage or rooted_suspended or minor_show_requests or multi_target_major_minor"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_answer_eval.py tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python -m pytest
```

Results:

- `git diff --check`: passed.
- Focused chord-quality/fretboard tests: `7 passed, 211 deselected`.
- Required backend/eval suite: `338 passed`.
- Full pytest: `649 passed, 2 failed`.

Known full-suite failures, unchanged from integration status and unrelated to this backend slice:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

## Smoke Target

- Target type: protected-preview root
- Result type: API fallback, not browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/`
- Cache-busted URL tested: not applicable
- Exact URL the user should use: not ready for user smoke until protected preview is restarted/verified from a commit containing this patch
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: failed / not completed by Codex; browser reached Cloudflare Access login
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `658c069` during browser/API target check; patched working tree is uncommitted
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `git_sha=658c069`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: root redirects to Cloudflare Access login when unauthenticated
- Whether app root `/` is expected to work: yes, after Cloudflare Access auth
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested after auth because Cloudflare Access login was not completed
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, after Cloudflare Access auth
- Who should test this URL: Lane 12 / the user after commit and protected-preview restart
- Do not test these URLs: do not treat local `127.0.0.1` API fallback as protected-preview browser proof
- Known caveats: protected-preview browser smoke could not authenticate; local backend at 8770 served committed `658c069`, not this uncommitted patch

## Smoke Result

Protected-preview browser result:

- Failed to proceed past Cloudflare Access login in this run.
- Browser smoke is not valid for the patched behavior.

API fallback result against patched working tree, not browser smoke:

| Prompt | Result | First sentence / answer summary | Fretboard | Sources | Warnings | Internal language |
| --- | --- | --- | --- | --- | --- | --- |
| `How do I play a G dom 7?` | pass | `G7, or G dominant 7, is G-B-D-F...` | `G major positions on E9` | 0 | 0 | no |
| `How do I play an F maj 7?` | pass | `Fmaj7 is F-A-C-E...` | `F major positions on E9` | 0 | 0 | no |
| `Show me an E minor chord.` | pass | `An E minor chord means the notes E-G-B...` | `E minor positions on E9` | 0 | 0 | no |
| `Show me an E major and E minor.` | pass | `Here are both E major and E minor on E9.` | `E major and E minor positions on E9` | 0 | 0 | no |
| `What is Fmaj7?` | pass | `Fmaj7 is F-A-C-E...` | none | 0 | 0 | no |
| `How do I play a G chord on the E9?` | pass | `On standard E9, several useful G major starter positions are:` | `G major positions on E9` | 0 | 0 | no |
| `What is the capital of France?` | pass | scope guardrail | none | 0 | 0 | no |

## Integration Notes

- This is a backend/API answer-routing patch only.
- Deterministic chord-quality answers remain source-free.
- Fretboard payloads use the existing `response.fretboard.positions` contract.
- Multi-target support is represented as one combined fretboard payload to avoid schema changes.
- Source evidence for unrelated valid steel questions is not removed.
- Retrieval gating is not weakened.

## Risk Assessment

- Risk: medium.
- Reason: shared answer routing was touched, but the change is narrow and covered by focused and required backend/eval suites.
- Main operational risk is not code behavior but preview freshness: protected-preview browser smoke could not authenticate, and the running local backend is still committed `658c069`, not this uncommitted patch.
- Rollback: revert the changes in `steel_guitar_rag/basic_chord_answers.py`, `steel_guitar_rag/curated_answers.py`, `steel_guitar_rag/fretboard_examples.py`, and `tests/test_api_search.py`.

## Commit Readiness

Not ready to commit under autopilot.

Reasons:

- Protected-preview browser smoke could not authenticate, so no true browser proof was captured.
- Full pytest is red due two known unrelated static/UI failures.
- Worktree contains broad unrelated parked files; exact staging would be required by Repo Steward.

If QA accepts API fallback plus focused/backend green results, exact safe-to-stage file list:

- `steel_guitar_rag/basic_chord_answers.py`
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/chord-quality-fretboard-routing-user-smoke-fix.md`

Must remain unstaged:

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `deploy/landing/index.html`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- All untracked `corpus-private`, `corpus-v2`, `source-inbox`, `public/`, `ui/brand/`, `Neon Sign/`, generated reports/assets, private lesson scripts/data, design assets, deployment artifacts, and historical handoffs not listed in the safe-to-stage list.

## User Smoke Continuation

User smoke should not continue yet.

Required before user smoke resumes:

1. Lane 15 QA review the API fallback behavior or run authenticated protected-preview smoke.
2. Lane 01 Repo Steward exact-stage/commit the scoped patch if approved.
3. Lane 12 restart or verify protected preview from the resulting commit.
4. Run authenticated browser smoke on the protected-preview root URL.

## Suggested Next Step

Lane 15 QA / Answer Eval:

```text
Review the chord-quality fretboard routing user-smoke fix in docs/handoffs/task-completions/chord-quality-fretboard-routing-user-smoke-fix.md. Verify the API fallback results for G dom 7, F maj 7, E minor, E major + E minor, Fmaj7, G chord on E9, and the off-domain guardrail. If possible, complete authenticated protected-preview browser smoke after Repo Steward commit/restart. Confirm no internal implementation language, SGF primary fragments, or inappropriate source cards appear.
```

Lane 01 Repo Steward, after QA approval:

```text
Exact-stage only the scoped chord-quality fretboard routing patch: steel_guitar_rag/basic_chord_answers.py, steel_guitar_rag/curated_answers.py, steel_guitar_rag/fretboard_examples.py, tests/test_api_search.py, and docs/handoffs/task-completions/chord-quality-fretboard-routing-user-smoke-fix.md. Do not stage parked docs/static/source/design/corpus/deploy files. Run git diff --cached --check and the focused/required backend tests before committing.
```
