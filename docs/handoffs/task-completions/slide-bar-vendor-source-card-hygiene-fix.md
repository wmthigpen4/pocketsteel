# Slide Bar Vendor Source Card Hygiene Fix

Date: 2026-06-13
Branch: `feature/answer-api`
HEAD: `c2815e3`

## Task Summary

Requested: fix the clean-HEAD backend hygiene blocker from `integration-status.md`: `/api/answer` imports `slide_bar_vendor_source_cards`, but clean HEAD did not define that helper in `pocketsteel.curated_source_registry`. The fix needed to reconcile curated-source-registry source cards for slide bar/vendor curated answers while preserving retrieval gating and current answer behavior.

Completed: made the curated-source-registry dependency explicit and testable by adding `slide_bar_vendor_source_cards()` to the registry helper module and adding direct registry tests for its source-card metadata/order/excerpt hygiene.

Intentionally not changed:

- No UI files or answer-page layout.
- No classifier behavior changes.
- No new teacher-first answer categories.
- No Chroma/vector stores, embeddings, corpus-private, corpus-v2, source-inbox raw/provenance data, scraping, deployment, DNS, secrets, design assets, staging, or commits.

## Exact Blocker Found

Clean HEAD had this runtime dependency:

- `pocketsteel/api.py` imports `slide_bar_vendor_source_cards` from `pocketsteel.curated_source_registry`.
- The `/api/answer` vendor-buying branch uses it when `curated_answer.intent == "vendor_buying_guidance"` and the question mentions `slide bar`, `steel bar`, or `tone bar`.

But clean `pocketsteel/curated_source_registry.py` only exposed:

- `slide_bar_vendor_bullets()`
- generic curated-source lookup/format helpers

So API test collection/import could fail on a clean checkout even though a broad dirty worktree happened to supply the missing symbol.

## Where The Dependency Lives

References inspected:

- `pocketsteel/api.py`
  - import: `from pocketsteel.curated_source_registry import slide_bar_vendor_source_cards`
  - source-card replacement path: curated slide/steel/tone-bar buying answers use `concise_source_cards(slide_bar_vendor_source_cards())`
- `pocketsteel/curated_answers.py`
  - answer text uses `slide_bar_vendor_bullets()` for curated buying guidance.
- `pocketsteel/curated_source_registry.py`
  - registry loader and filter helpers load `corpus_metadata/source_registry.json`.
  - new source-card helper is colocated with `slide_bar_vendor_bullets()` so answer text and source cards share the same curated registry source selection.
- `tests/test_api_search.py`
  - existing API tests verify slide-bar buying answers show curated source cards instead of stale SGF source cards.
- `tests/test_curated_source_registry.py`
  - new direct test now proves the helper exists and emits stable curated source-card metadata.

## Files Changed

Implementation:

- `pocketsteel/curated_source_registry.py`
  - Added `slide_bar_vendor_source_cards()`.

Tests:

- `tests/test_curated_source_registry.py`
  - Imported `slide_bar_vendor_source_cards`.
  - Added `test_slide_bar_vendor_source_cards_use_curated_registry_metadata`.

Handoff:

- `docs/handoffs/task-completions/slide-bar-vendor-source-card-hygiene-fix.md`

## Why The Source-Card Dependency Failed

The API had already been wired to replace stale forum source cards with curated source-registry cards for slide/steel/tone-bar buying answers, but the registry module did not provide the source-card helper on clean HEAD. That meant clean test collection could fail before any answer tests ran.

The helper had existed only as a parked dirty worktree change, which made local dirty-tree tests misleading.

## How The Curated-Source-Registry Dependency Was Reconciled

`slide_bar_vendor_source_cards()` now:

- selects active curated sources for `vendor_buying_guidance` with `tone_bars` or `used_market` tags;
- sorts them in the same stable order as the buying-answer bullets:
  - Steel Guitar Shopper
  - BJS Steel Guitar Bars
  - Jim Dunlop Tonebars
  - Steel Guitar Forum Classifieds / Forum Store
- emits source-like dicts compatible with `concise_source_cards()`:
  - `thread_title`
  - `forum_name`
  - `thread_url`
  - `excerpt`
  - `score`
  - `chunk_id`
  - `post_uid`
  - `source_system`
- uses registry descriptions plus caveats for excerpts;
- sets `source_system` to `curated_source_registry`.

The answer text still comes from the existing curated vendor answer path, and API response source cards still flow through the normal `concise_source_cards()` normalization path.

## Test Coverage Added

New direct registry test verifies:

- stable source order;
- every source card is labeled `curated_source_registry`;
- every source card has `Pocket Steel curated source` as the source/forum label;
- every source card has a stable `chunk_id`;
- every source card has an HTTPS URL;
- excerpts include registry caveats such as current-inventory cautions;
- excerpts do not include contact/order junk like PayPal or email addresses.

Existing API tests continue to verify:

- slide-bar buying answer uses curated registry source cards;
- stale SGF slide-bar source cards are suppressed;
- source card excerpts are cleaned;
- no `[object Object]`;
- no weak-source warning as primary answer;
- retrieval-gating guardrail tests still pass.

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_curated_source_registry.py tests/test_api_search.py -k "slide_bar or source_cards_clean_contact_order_and_forum_junk or scope_guardrail_for_numbers_prompt_runs_before_retrieval or classifier_gates_unsafe_prompt_before_retrieval or classifier_gates_off_domain_prompt_before_retrieval or remaining_retrieval_gating_smoke_failures"
.venv/bin/python - <<'PY'
import pocketsteel.api
from pocketsteel.curated_source_registry import slide_bar_vendor_source_cards
cards = slide_bar_vendor_source_cards()
print('api import ok')
print(len(cards), [card['thread_title'] for card in cards[:4]])
PY
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python -m pytest
git diff --check
```

Results:

- Focused curated/API subset: `9 passed, 185 deselected`
- API import smoke: passed; returned 4 slide-bar vendor source cards in the expected order.
- `tests/test_answer_intent_classifier.py`: `62 passed`
- `tests/test_answer_eval.py`: `9 passed`
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: `233 passed`
- Full pytest: `657 passed`
- `git diff --check`: passed

## Retrieval Gating Confirmation

Retrieval gating remains intact:

- Focused tests included off-domain and unsafe guardrail checks.
- Full API/eval tests passed.
- No classifier code was changed.
- No answer routing was widened.

## UI Confirmation

No UI files were changed by this slice.

Note: the broader worktree still has pre-existing dirty UI files. They are unrelated and must remain parked for this backend hygiene slice.

## Remaining Risks

Risk: low.

Why:

- The implementation is a small helper in an existing registry module plus direct tests.
- It does not change retrieval ranking, source registry data, answer layout, UI, Chroma, embeddings, scraping, or auth.
- The broad worktree is dirty, so Repo Steward must stage only this exact slice.

Rollback:

- Remove `slide_bar_vendor_source_cards()` and the direct test.
- No data/vector/UI/deployment rollback is needed.

## Commit Readiness

Commit readiness: `Needs human review first`.

Reason: tests are green and the slice is narrow, but the worktree remains broadly dirty. Repo Steward should hunk-stage only:

- `pocketsteel/curated_source_registry.py`
- `tests/test_curated_source_registry.py`
- `docs/handoffs/task-completions/slide-bar-vendor-source-card-hygiene-fix.md`

Do not stage:

- UI files
- deployment/DNS/security artifacts
- corpus-private/corpus-v2/vector/embedding/generated data
- source-inbox raw/provenance/generated files
- unrelated backend/eval/docs changes parked in the worktree

## Exact Next QA Prompt

```text
Lane 15 QA / Answer Eval:

Please QA the slide-bar vendor source-card hygiene fix on branch feature/answer-api.

Read:
- AGENTS.md
- docs/handoffs/task-completions/slide-bar-vendor-source-card-hygiene-fix.md
- docs/handoffs/task-completions/integration-status.md
- pocketsteel/api.py
- pocketsteel/curated_source_registry.py
- tests/test_curated_source_registry.py
- tests/test_api_search.py

Verify:
1. Clean import of /api/answer no longer depends on parked dirty-worktree symbols.
2. `slide_bar_vendor_source_cards()` returns stable curated registry cards for:
   - Steel Guitar Shopper
   - BJS Steel Guitar Bars
   - Jim Dunlop Tonebars
   - Steel Guitar Forum Classifieds / Forum Store
3. `Where can I buy a slide bar?` returns curated source cards, not stale SGF source cards.
4. Retrieval gating still blocks off-domain/unsafe prompts.
5. The 12-prompt smoke remains 12 pass / 0 fail if rerun.
6. No UI files or source-card UI behavior changed.

Run focused curated-source/API/eval tests and report whether Repo Steward can hunk-stage this slice.
```

## Human Decision Needed

Yes. QA should recheck the clean-HEAD/import/source-card issue, then Repo Steward should hunk-stage this narrow slice if approved.

## Recommended Next Step

Lane 15 should run the QA prompt above. If green, Lane 01 Repo Steward can commit the exact safe-to-stage paths for this hygiene fix.
