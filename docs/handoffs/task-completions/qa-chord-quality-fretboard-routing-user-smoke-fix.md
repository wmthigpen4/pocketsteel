# QA Chord Quality Fretboard Routing User Smoke Fix

## Task Summary

Lane 15 QA reviewed the uncommitted Lane 05 chord-quality/fretboard routing fix and decided whether it is safe for Repo Steward exact-path/exact-hunk commit.

Completed:

- Read the requested repo protocol, integration status, Lane 05 handoff, answer-contract/eval guidance, teacher-first policy, current backend files, current tests, git status, and git diff.
- Verified the patched working tree by API fallback, not protected-preview browser smoke.
- Verified the requested chord-quality, fretboard, multi-target, and regression prompts.
- Ran focused chord-quality tests, required answer/API/eval suites, `git diff --check`, and full pytest to classify the known failures.

Intentionally not changed:

- No implementation files were modified by this QA task.
- No staging or commit was performed.
- No protected-preview browser smoke was claimed, because Lane 05 already found the live server still serving committed `658c069`, not this uncommitted patch.
- No deployment, DNS, auth, Chroma, corpus, embeddings, scraping, source-inbox, private source data, UI, or visual asset work was performed.

## Pass/Fail Decision

**Pass for the chord-quality/fretboard routing backend slice.**

QA approves exact-hunk commit of this backend/test slice. The patched working tree passes the prompt checks and the focused/required answer suites. Full pytest still fails on the same two unrelated static/UI blockers:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

Classification: **unrelated parked blocker / separate Lane 06 or static asset task**. These failures should not block exact-hunk commit of this backend slice, but they still block claiming a fully clean full-suite gate.

## Smoke Target

- Target type: API-fallback
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not tested
- Cache-busted URL tested: not applicable
- Exact URL the user should use: not ready until this slice is committed and protected preview is restarted/verified
- Auth required: no for in-process API fallback
- Auth provider: none
- Cloudflare Access login result: not attempted
- Local backend URL: in-process `/api/answer` test app via `tests.test_api_search.answer_for_question`
- Expected backend port: not applicable
- Expected git HEAD: `658c069` plus uncommitted patched working tree
- Version endpoint: not used for API fallback
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: git status/diff and in-process test harness
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not applicable for API fallback
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not applicable for API fallback
- Who should test this URL: Lane 12 / the user after commit and protected-preview restart
- Do not test these URLs: do not treat this local in-process API fallback as protected-preview browser proof
- Known caveats: protected preview must be restarted or verified from a commit containing this patch before user smoke resumes

## Prompt Results

All prompt checks were run against the patched working tree through API fallback.

| Prompt | Result | Sources | Fretboard | Notes |
| --- | --- | --- | --- | --- |
| `How do I play a G dom 7?` | Pass | 0 | `G major positions on E9`, 44 positions | Explains `G7 = G-B-D-F`, recognizes `dom 7`, no internal wording or SGF fragments. |
| `How do I play a G7?` | Pass | 0 | `G major positions on E9`, 44 positions | Same clean dominant-7 answer and visual reference. |
| `What is a G dominant 7?` | Pass | 0 | none | Pure theory answer explains `G-B-D-F`; no fretboard required. |
| `How do I play an F maj 7?` | Pass | 0 | `F major positions on E9`, 44 positions | Explains `Fmaj7 = F-A-C-E`, recognizes spaced `maj 7`, no SGF fragments. |
| `How do I play an Fmaj7?` | Pass | 0 | `F major positions on E9`, 44 positions | Same clean major-7 answer and visual reference. |
| `How do I play an F major 7th?` | Pass | 0 | `F major positions on E9`, 44 positions | Same clean major-7 answer and visual reference. |
| `Show me an E minor chord` | Pass | 0 | `E minor positions on E9`, 20 positions | Teacher-first E minor answer with A-pedal, E-lower, and B+C minor positions. |
| `Show me an E major and E minor.` | Pass | 0 | `E major and E minor positions on E9`, 64 positions | Answers both targets with clear major/minor labels in one combined payload. |
| `What is a G chord?` | Pass | 0 | none | Direct `G-B-D` basic theory answer. |
| `How do I play a G chord on the E9?` | Pass | 0 | `G major positions on E9`, 44 positions | Existing G major E9 position routing still works. |
| `How do you play a C chord?` | Pass | 0 | `C major positions on E9`, 44 positions | Existing C major position routing still works. |
| `What is a sus chord?` | Pass | 0 | none | Clean sus theory answer with no source or fretboard. |
| `What is a chord change?` | Pass | 0 | none | Clean direct theory answer with no source or fretboard. |
| `What is the capital of France?` | Pass | 0 | none | Off-domain guardrail still works. |

Internal language ban result:

- No checked answer body contained `deterministic map`, `current deterministic map`, `rules engine`, `payload`, `classifier`, or `contract`.
- No checked answer body contained `[object Object]`, SGF/forum/source fragments, weak-source language, or contact/order junk.

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -k "major_seventh_questions or dominant_seventh or major_seventh_play or suspended_usage or rooted_suspended or minor_show_requests or multi_target_major_minor"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python -m pytest
```

Results:

- `git diff --check`: passed.
- Focused chord-quality/fretboard tests: `7 passed, 211 deselected`.
- `tests/test_answer_intent_classifier.py`: `66 passed`.
- `tests/test_answer_eval.py`: `9 passed`.
- Required answer/API/eval suite: `263 passed`.
- Full pytest: `649 passed, 2 failed`.

Full-suite failure classification:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`: unrelated static landing source/deploy mismatch. Separate Lane 06/static task.
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`: unrelated missing public fretboard background route/static asset. Separate Lane 06/static task.

## Files Changed

Changed by Lane 05 chord-quality/fretboard routing patch, approved for exact-hunk commit:

- `pocketsteel/basic_chord_answers.py`
  - Approve only the `maj 7` alias/regex expansion.
  - Approve only learner-facing wording cleanup that removes internal implementation language from major-7, dominant-7, diminished, diminished-7, and augmented answers.
- `pocketsteel/curated_answers.py`
  - Approve only the `multi_chord_answer_for_question` import and route.
  - Approve only the unsupported chord-quality fallback wording cleanup that explains chord tones plus closest reliable E9 positions.
- `pocketsteel/fretboard_examples.py`
  - Approve only `MultiChordLocationRequest`.
  - Approve only additional minor `show me` request patterns.
  - Approve only `multi_chord_location_request_for_question`, `multi_chord_payload_for_question`, and `multi_chord_answer_for_question`.
  - Approve only the minor answer article grammar fix.
  - Approve only the multi-chord payload route in `fretboard_payload_for_question`.
  - Approve only the dominant-7/major-7 unsupported-quality visual fallback using existing major positions.
  - Approve only the `an|a` article regex fix and chord-quality alias normalization for `dom 7`, `maj 7`, `major 7`, `major 7th`, and `major seventh`.
- `tests/test_api_search.py`
  - Approve only `assert_no_internal_answer_language`.
  - Approve only updates/additions covering dominant-7, major-7, definition-only Fmaj7, sus internal-language cleanup, minor show requests, multi-target major/minor requests, and unsupported chord-quality visual fallback.

Handoff artifacts approved to include with the slice if Repo Steward policy includes task handoffs:

- `docs/handoffs/task-completions/chord-quality-fretboard-routing-user-smoke-fix.md`
- `docs/handoffs/task-completions/qa-chord-quality-fretboard-routing-user-smoke-fix.md`

Files/hunks that must remain parked:

- All unrelated docs/source/legal/provenance/source-inbox changes.
- All parked root RAG helper script changes.
- `README.md`, broad docs, integration-status refreshes, and unrelated historical handoffs/assets.
- `deploy/landing/index.html`, `public/`, `ui/brand/`, `Neon Sign/`, static assets, generated reports, private/corpus/vector data, deployment/auth/DNS config, and any unrelated untracked files.

## Integration Notes

- This patch is uncommitted on top of HEAD `658c069`.
- Protected-preview browser smoke could not prove this patch because the live runtime still served committed `658c069` during Lane 05 verification.
- After Repo Steward commits this exact backend slice, Lane 12 must restart or verify protected preview from the new commit before user smoke resumes.
- No `/api/answer` schema change was introduced.
- Multi-target major/minor uses the existing single `response.fretboard` slot with a combined payload.
- No UI files changed.
- Retrieval gating remains intact in the tested off-domain and source-suppressed deterministic routes.

## Risk Assessment

Risk: **medium-low for exact-hunk backend commit**.

Why:

- The slice changes deterministic answer/fretboard routing but stays within existing API shape and existing fretboard payload contract.
- Focused and required backend/eval tests pass.
- The visual fallback for dominant-7/major-7 uses major-position payloads as a teaching reference, not exact dominant/major-7 grip generation. That is intentional per the Lane 05 handoff and should be represented clearly in answer text.

Rollback notes:

- Revert only the approved hunks in the four implementation/test files if a regression appears.
- Do not revert unrelated parked files.

## Commit Readiness

**Safe to commit** for exact-hunk staging of the approved backend/test slice.

The two unrelated static/UI full-suite failures need separate Lane 06/static work. They should not block this backend commit, but they remain blockers for a fully green full-suite gate.

Protected-preview restart remains blocked until:

1. Repo Steward commits the approved exact hunks.
2. Lane 12 restarts or verifies protected preview from the new commit.

## Suggested Next Step

Recommended lane: **01 Repo Steward**.

Exact next prompt:

```text
Repo Steward: QA approved the chord-quality/fretboard routing backend slice in docs/handoffs/task-completions/qa-chord-quality-fretboard-routing-user-smoke-fix.md. Proceed under auto-approval. Stage only the approved exact hunks in pocketsteel/basic_chord_answers.py, pocketsteel/curated_answers.py, pocketsteel/fretboard_examples.py, tests/test_api_search.py, plus the Lane 05 and QA handoff files if handoff policy requires them. Keep all unrelated parked corpus/source/static/UI/root-script/docs files unstaged. Run git diff --check and the focused/required backend tests named in the QA handoff, then commit with a scoped message. If exact-hunk staging cannot isolate the approved slice, write a blocker handoff instead of committing.
```

If a revision is required, exact Lane 05 prompt:

```text
Lane 05: QA found a blocker in docs/handoffs/task-completions/qa-chord-quality-fretboard-routing-user-smoke-fix.md. Fix only the chord-quality/fretboard routing backend issue described there. Do not touch UI, Chroma, corpus, embeddings, scraping, auth, DNS, deployment, source-inbox, private data, or unrelated docs. Add focused regression coverage, run the focused/required answer/API/eval tests, and write a handoff.
```
