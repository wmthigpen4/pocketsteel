# QA Answer UI Fretboard Filter Visibility Fix

- Branch: `feature/answer-api`
- HEAD: `77ff8f6`
- Lane: `15 QA / Answer Eval`
- Date: 2026-06-13
- Commit readiness: `Safe to commit`

## Task Summary

Requested QA for the Lane 06 fretboard filter visibility fix before user smoke testing.

Completed:

- Read the requested repo protocol, guidance docs, prior QA blocker handoff, Lane 06 implementation handoff, current UI files, and frontend/browser test surfaces.
- Verified the Lane 06 fix is UI-only per the handoff and targets the DOM-side filter predicate.
- Ran syntax checks, focused UI tests, focused API/eval tests, and full pytest.
- Ran local current-worktree browser smoke against the answer UI.
- Verified the prior blocker is fixed: default `Recommended` view now shows visible cards/details instead of `0`.

Intentionally not changed:

- No implementation files were modified by QA.
- No files were staged or committed.
- No backend/RAG behavior, `/api/answer` schema, Chroma/vector stores, corpus, embeddings, scraping, deployment, DNS, auth/security, source-inbox, provenance/legal files, public assets, brand assets, or design assets were touched.

## Pass / Fail Decision

Decision: `PASS / Safe to commit`.

The browser-observed blocker from `qa-answer-ui-fretboard-filter-smoke-readiness.md` is cleared.

## Browser Smoke Target

Local current-worktree loopback server:

```bash
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_ANSWER_AUTH_MODE=local_dev \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8781 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --answer-auth-mode local_dev \
  --auth-provider scaffold
```

Smoke URL:

`http://127.0.0.1:8781/ui/steel-guitar-rag-mock.html?access=beta_user&v=qa-filter-fix-...`

Reachability:

- `GET /`: `HTTP/1.0 200 OK`
- `GET /api/answer`: `HTTP/1.0 405 Method Not Allowed` as expected

## Browser Smoke Result

| Prompt | Result | Sources | Fretboard | Default visible cards | Selected detail | Notes |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `How do I play a G chord on the E9?` | Pass | 0 | yes | `3 / 44` | `g-open-3` | Default `Recommended` shows cards/details. |
| `Where do I play a G chord on the E9?` | Pass | 0 | yes | `3 / 44` | `g-open-3` | Same fixed default behavior. |
| `How do I play an A chord?` | Pass | 0 | yes | `3 / 49` | `a-open-5` | Default cards visible. |
| `How do I play a D chord?` | Pass | 0 | yes | `3 / 40` | `d-open-10` | Default cards visible. |
| `How do I play a D chord across the fretboard of the E9?` | Pass | 0 | yes | `3 / 40` | `d-open-10` | Default cards visible. |
| `Show me the fretboard` | Pass | 0 | yes | `3 / 44` | `g-open-3` | Default E9 reference shows cards. |
| `What’s it mean for a song to be a swing or a waltz?` | Pass | 6 | no | n/a | n/a | Non-fretboard prompt did not show fretboard. |
| `What is the capital of France?` | Pass | 0 | no | n/a | n/a | Retrieval gating/guardrail preserved. |

Across all browser smoke prompts:

- No `[object Object]`.
- No weak-source warning as primary answer.
- No raw SGF/forum/source fragment as primary answer.
- Deterministic fretboard prompts did not show source cards.
- Non-fretboard prompts did not show fretboard.
- Off-domain prompt did not show sources or fretboard.

## Filter Behavior Results

Detailed target: `How do I play a G chord on the E9?`

Observed:

- Default `Recommended`: `3 / 44` cards visible, selected `g-open-3`, one detail card visible.
- `Starter`: `3` cards visible, selected `g-open-3`, one detail card visible.
- `Full chord`: `32` cards visible, selected `g-open-grip-3-4-5-3`, one detail card visible.
- `Full chord + 3-4-5`: `6` cards visible, selected `g-open-grip-3-4-5-3`, one detail card visible.
- `Full chord + 4-5-6`: `6` cards visible, selected `g-open-3`, one detail card visible.
- `All positions` while grip `4-5-6` is active: `8` matching cards visible out of `44` total.
- No-match combination `Recommended + 3-4-5`: `0` cards visible, selected detail cleared, clear empty state shown.
- Empty state text: `No positions match these filters. Try All positions or a different grip.`
- Returning to `Recommended + All grips`: `3` cards visible, selected detail recovered to `g-open-3`.

The selected detail panel updates to a visible card after each matching filter change.

## Technical Details

Passed:

- Technical/internal details remain collapsed by default.
- After selecting `All`, the visible detail card had `0` technical panels open before interaction.
- Clicking `Technical details` opened exactly one technical panel.
- Learner-relevant fields remained visible in the selected detail card before expanding technical details.

## Remaining UI Issues

No blocking UI issues found for this slice.

Non-blocking notes:

- `All positions` respects the currently active grip filter. This is expected from the shared filter model, but a human tester may interpret "All positions" as clearing grip filters too. No change requested from QA.
- Protected-preview freshness is still a separate Lane 12 concern; this QA pass used local current-worktree browser smoke.

## Screenshots

Generated transient screenshots under `/tmp`:

- `/tmp/pocketsteel-answer-ui-fretboard-filter-visibility-fix/screenshots/01-g-default-recommended.png`
- `/tmp/pocketsteel-answer-ui-fretboard-filter-visibility-fix/screenshots/02-g-starter.png`
- `/tmp/pocketsteel-answer-ui-fretboard-filter-visibility-fix/screenshots/03-g-full-chord.png`
- `/tmp/pocketsteel-answer-ui-fretboard-filter-visibility-fix/screenshots/04-g-full-chord-grip-456.png`
- `/tmp/pocketsteel-answer-ui-fretboard-filter-visibility-fix/screenshots/10-g-recommended-grip-345-no-match.png`
- `/tmp/pocketsteel-answer-ui-fretboard-filter-visibility-fix/screenshots/11-g-recovered-recommended-all-grips.png`
- `/tmp/pocketsteel-answer-ui-fretboard-filter-visibility-fix/screenshots/show-me-the-fretboard.png`
- `/tmp/pocketsteel-answer-ui-fretboard-filter-visibility-fix/screenshots/what-s-it-mean-for-a-song-to-be-a-swing-or-a-waltz.png`
- `/tmp/pocketsteel-answer-ui-fretboard-filter-visibility-fix/screenshots/what-is-the-capital-of-france.png`

Transient browser state:

- `/tmp/pocketsteel-answer-ui-fretboard-filter-visibility-fix/browser-smoke-results.json`

## Tests And Checks

Passed:

```bash
git status --short
git diff --check
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py -q
.venv/bin/python -m pytest
```

Results:

- JS syntax checks: passed
- Focused frontend/fretboard tests: `49 passed`
- Focused API/search/full-answer-quality tests: `238 passed`
- Full pytest: `668 passed`
- Whitespace check: passed before handoff

## Files Changed

Created by this QA task:

- `docs/handoffs/task-completions/qa-answer-ui-fretboard-filter-visibility-fix.md`

Implementation files changed by Lane 06 and approved by this QA:

- `ui/pedal-steel-fretboard.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/answer-ui-fretboard-filter-visibility-fix.md`

No backend files are approved as part of this UI visibility fix. The shared worktree still has unrelated backend dirt parked.

## Exact Hunks Needing Careful Staging

Stage only the Lane 06 filter-visibility hunks:

- `ui/pedal-steel-fretboard.js`
  - semantic DOM flags on selector cards, detail cards, and SVG highlights:
    - `data-is-starter`
    - `data-is-full-chord`
  - `positionElementMatchesVoicing(...)` branches for:
    - `recommended`
    - `starter`
    - `full-chord`
    - `dominant`
  - no-match empty state text and initial visibility handling
  - selected-detail reset/recovery behavior around filter changes
- `tests/test_pedal_steel_fretboard_ui.py`
  - assertions for default `Recommended`, `Starter`, `Full chord`, grip filtering, combined filters, no-match empty state, and selected visible detail behavior
- `docs/handoffs/task-completions/answer-ui-fretboard-filter-visibility-fix.md`
- `docs/handoffs/task-completions/qa-answer-ui-fretboard-filter-visibility-fix.md`

## Files That Should Remain Parked

Keep parked unless a future exact-path prompt approves them:

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- all backend/RAG files
- `docs/handoffs/task-completions/integration-status.md`
- unrelated docs, source policy/provenance files, source-inbox files, corpus/private/vector/generated outputs, deployment/DNS/security files, `public/`, `ui/brand/`, `Neon Sign/`, raw design assets

## User Smoke Testing Status

Local current-worktree user smoke for the fretboard/filter UI slice is allowed after Repo Steward commits this exact UI slice.

External/protected-preview user smoke remains blocked until Lane 12 verifies protected-preview freshness for `77ff8f6` plus the eventual UI filter visibility commit or a later commit containing it.

## Risk Assessment

Risk: Low to medium.

Why:

- The original browser-observed blocker is fixed in the same browser path.
- Focused and full test suites are green.
- The worktree remains broadly dirty, so the remaining risk is commit hygiene, not observed UI behavior.

Rollback:

- Revert the staged hunks in `ui/pedal-steel-fretboard.js` and `tests/test_pedal_steel_fretboard_ui.py` if later protected-preview smoke shows stale or unexpected behavior.

## Exact Next Prompt For 01 Repo Steward

```text
LANE: 01 Repo Steward
REASONING: MEDIUM

Branch: feature/answer-api

Prepare an exact-path/hunk-staged commit for the QA-approved answer UI fretboard filter visibility fix.

Read:
- AGENTS.md
- docs/handoffs/task-completions/answer-ui-fretboard-filter-visibility-fix.md
- docs/handoffs/task-completions/qa-answer-ui-fretboard-filter-visibility-fix.md
- git status and git diff

Approved files/hunks:
- ui/pedal-steel-fretboard.js: only the semantic filter flag/predicate/no-match/selected-detail hunks described in the QA handoff
- tests/test_pedal_steel_fretboard_ui.py: only matching tests for filter visibility behavior
- docs/handoffs/task-completions/answer-ui-fretboard-filter-visibility-fix.md
- docs/handoffs/task-completions/qa-answer-ui-fretboard-filter-visibility-fix.md

Do not stage:
- ui/steel-guitar-rag-mock.html
- tests/test_frontend_answer_ui.py
- backend/RAG files
- integration-status.md unless explicitly doing a separate coordination commit
- corpus/private/vector/source-inbox/provenance/legal/deployment/design/generated assets
- any unrelated dirty files

Run:
- git diff --check
- git diff --cached --check after staging
- focused UI tests if needed

Commit only if the staged diff matches the approved slice.
```

## Exact Lane 06 Revision Prompt If Blocked

Not needed. QA approves the Lane 06 visibility fix.

## Suggested Next Step

Recommended lane: `01 Repo Steward`.

Hunk-stage and commit the exact approved UI visibility fix slice, then route to Lane 12 for protected-preview freshness/version verification before external user smoke.
