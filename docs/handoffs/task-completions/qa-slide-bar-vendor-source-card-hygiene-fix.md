# QA: Slide Bar Vendor Source-Card Hygiene Fix

Date: 2026-06-13 03:36 CT
Lane: 15 QA / Answer Eval
Branch: `feature/answer-api`

## Task Summary

Requested: QA the clean-HEAD `slide_bar_vendor_source_cards` / curated-source-registry hygiene fix and decide whether Repo Steward can hunk-stage it.

Completed:

- Read the requested repo guidance, integration handoffs, Lane 05 hygiene handoff, current `/api/answer` implementation, curated-source-registry helper, source-card path, and tests touched by the fix.
- Verified `steel_guitar_rag.api` imports cleanly with `slide_bar_vendor_source_cards` defined in `steel_guitar_rag.curated_source_registry`.
- Verified `slide_bar_vendor_source_cards()` returns stable curated registry source-card metadata in the expected order.
- Verified slide-bar/vendor answer tests return curated registry source cards instead of stale SGF source cards.
- Verified retrieval gating and answer-quality regression tests remain green.
- Verified full pytest passes.

Intentionally not changed:

- No implementation files were modified by QA.
- No UI files were modified by QA.
- No Chroma/vector stores, embeddings, corpus-private, corpus-v2, source-inbox raw/provenance data, scraping, deployment, DNS, secrets, public assets, design assets, staging, or commits.

## Decision

Pass.

QA approves the narrow slide-bar vendor source-card hygiene fix for Repo Steward hunk-staged commit.

## Verification Notes

- Clean-HEAD source-card dependency is fixed: `steel_guitar_rag.api` imports successfully, and `slide_bar_vendor_source_cards` is available from `steel_guitar_rag.curated_source_registry`.
- Helper returns 4 curated registry cards in stable order:
  - `Steel Guitar Shopper`
  - `BJS Steel Guitar Bars`
  - `Jim Dunlop Tonebars`
  - `Steel Guitar Forum Classifieds / Forum Store`
- All returned cards use `source_system == "curated_source_registry"`.
- Registry card metadata is generated from the curated registry helper, not from parked dirty-worktree state.
- Slide-bar buying answer tests verify curated source cards are present and stale SGF slide-bar source cards are suppressed.
- Source-card excerpts are cleaned of PayPal/email/order-form/forum junk in the covered tests.
- Retrieval gating remains intact for off-domain and unsafe prompts in the focused test subset and broader API/eval tests.
- Valid steel-guitar prompts still retrieve when expected in the broader API/eval tests.
- Smoke-critical 12-prompt behavior remains covered by the focused six-smoke regression subset and full test suite. A live 12-prompt smoke was not rerun because this helper/test slice does not touch answer routing, retrieval ranking, UI rendering, or smoke-risk logic.
- No `[object Object]`, weak-source-primary-answer, or raw-forum-fragment regressions were found in the relevant tests.
- No UI file is approved for this fix. The worktree still has pre-existing dirty UI files, and they must remain parked.

## Files Changed

Changed by the Lane 05 hygiene fix:

- `steel_guitar_rag/curated_source_registry.py`
- `tests/test_curated_source_registry.py`

Created by the Lane 05 hygiene fix:

- `docs/handoffs/task-completions/slide-bar-vendor-source-card-hygiene-fix.md`

Created by this QA task:

- `docs/handoffs/task-completions/qa-slide-bar-vendor-source-card-hygiene-fix.md`

Deleted files: none.

Generated artifacts: none.

## Tests And Checks

```bash
git status --short
```

Result: broad dirty worktree. Relevant hygiene files are:

- `M steel_guitar_rag/curated_source_registry.py`
- `M tests/test_curated_source_registry.py`
- `?? docs/handoffs/task-completions/slide-bar-vendor-source-card-hygiene-fix.md`
- `?? docs/handoffs/task-completions/qa-slide-bar-vendor-source-card-hygiene-fix.md`

```bash
git diff --check
```

Result: passed.

```bash
.venv/bin/python -m pytest tests/test_curated_source_registry.py tests/test_api_search.py -k "slide_bar or source_cards_clean_contact_order_and_forum_junk or scope_guardrail_for_numbers_prompt_runs_before_retrieval or classifier_gates_unsafe_prompt_before_retrieval or classifier_gates_off_domain_prompt_before_retrieval or remaining_retrieval_gating_smoke_failures"
```

Result: `9 passed, 185 deselected in 0.08s`.

```bash
.venv/bin/python - <<'PY'
import steel_guitar_rag.api
from steel_guitar_rag.curated_source_registry import slide_bar_vendor_source_cards
cards = slide_bar_vendor_source_cards()
print('api import ok')
print(len(cards), [card['thread_title'] for card in cards[:4]])
print([card['source_system'] for card in cards[:4]])
PY
```

Result:

```text
api import ok
4 ['Steel Guitar Shopper', 'BJS Steel Guitar Bars', 'Jim Dunlop Tonebars', 'Steel Guitar Forum Classifieds / Forum Store']
['curated_source_registry', 'curated_source_registry', 'curated_source_registry', 'curated_source_registry']
```

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
```

Result: `62 passed in 0.07s`.

```bash
.venv/bin/python -m pytest tests/test_answer_eval.py
```

Result: `9 passed in 0.02s`.

```bash
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Result: `233 passed in 0.80s`.

```bash
.venv/bin/python -m pytest
```

Result: `657 passed in 4.51s`.

Final check:

```bash
git diff --check
```

Result: passed.

## Exact Files Approved For Commit

Approved for a narrow Repo Steward commit:

- `steel_guitar_rag/curated_source_registry.py`
- `tests/test_curated_source_registry.py`
- `docs/handoffs/task-completions/slide-bar-vendor-source-card-hygiene-fix.md`
- `docs/handoffs/task-completions/qa-slide-bar-vendor-source-card-hygiene-fix.md`

## Exact Hunks That Need Careful Staging

`steel_guitar_rag/curated_source_registry.py`:

- Stage only the new `slide_bar_vendor_source_cards()` helper colocated with `slide_bar_vendor_bullets()`.

`tests/test_curated_source_registry.py`:

- Stage only the import of `slide_bar_vendor_source_cards`.
- Stage only `test_slide_bar_vendor_source_cards_use_curated_registry_metadata`.

The two handoff docs above can be staged as whole files.

## Files That Should Remain Parked

Do not stage for this hygiene commit:

- `ui/pedal-steel-fretboard.js`
- `ui/steel-guitar-rag-landing.html`
- `ui/steel-guitar-rag-mock.html`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox` raw/provenance/generated files
- provenance/legal metadata dumps
- deployment/DNS/Cloudflare/`.wrangler` files
- generated reports
- unrelated docs, scripts, tests, API files, corpus tooling, and root RAG/build scripts
- `docs/handoffs/task-completions/integration-status.md` unless a separate docs-only coordination task explicitly approves it

## Integration Notes

- No API response shape changes.
- No classifier or retrieval-gating behavior changes.
- No UI/source-card rendering changes.
- The fix reconciles a runtime/import hygiene dependency that was previously satisfied only by parked dirty-worktree state.
- The helper emits source-like dicts compatible with the existing `concise_source_cards()` path.

## Risk Assessment

Risk: low.

Why:

- The implementation is a narrow helper plus direct unit coverage.
- It uses existing curated registry data and existing source-card normalization.
- Full pytest passed.
- No data stores, embeddings, UI, auth, scraping, or deployment paths were touched.

Rollback:

- Remove `slide_bar_vendor_source_cards()` and its direct test.
- No data/vector/UI/deployment rollback needed.

## Human Decision Needed

No for QA approval.

Yes for Repo Steward staging discipline: stage only the exact approved files/hunks because the broader worktree remains dirty.

## Commit Readiness

Safe to commit.

This means safe only for the exact approved hygiene slice above.

## Suggested Next Step

Lane 01 Repo Steward should hunk-stage the approved helper/test plus the two handoffs, run the focused checks, and commit the hygiene fix.

## Exact Next Prompt For 01 Repo Steward

```text
LANE: 01 Repo Steward
REASONING: MEDIUM
Branch: feature/answer-api

Read:
- AGENTS.md
- docs/handoffs/task-completions/slide-bar-vendor-source-card-hygiene-fix.md
- docs/handoffs/task-completions/qa-slide-bar-vendor-source-card-hygiene-fix.md

Do not deploy, change DNS, touch Chroma/vector stores, regenerate embeddings, run scraping, stage generated/private/corpus/source-inbox/provenance/design/deploy files, or use git add .

Hunk-stage only:
- steel_guitar_rag/curated_source_registry.py: new slide_bar_vendor_source_cards() helper
- tests/test_curated_source_registry.py: import plus test_slide_bar_vendor_source_cards_use_curated_registry_metadata
- docs/handoffs/task-completions/slide-bar-vendor-source-card-hygiene-fix.md
- docs/handoffs/task-completions/qa-slide-bar-vendor-source-card-hygiene-fix.md

Do not stage UI files, integration-status.md, source-inbox files, corpus/private/vector/generated data, deployment files, or unrelated docs/scripts/tests.

Run:
git diff --cached --check
.venv/bin/python -m pytest tests/test_curated_source_registry.py tests/test_api_search.py -k "slide_bar or source_cards_clean_contact_order_and_forum_junk or scope_guardrail_for_numbers_prompt_runs_before_retrieval or classifier_gates_unsafe_prompt_before_retrieval or classifier_gates_off_domain_prompt_before_retrieval or remaining_retrieval_gating_smoke_failures"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py

If clean, commit with a narrow message such as:
backend: add curated slide bar source cards
```

## Exact Next Prompt For Lane 05 If Blocked

Not needed. QA found no blocker in this slice.
