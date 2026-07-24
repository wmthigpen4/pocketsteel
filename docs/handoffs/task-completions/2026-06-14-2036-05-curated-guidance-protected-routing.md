# Curated Guidance Protected Routing Slice

## Task Summary

Lane: 05 Backend / RAG Integration

Requested: implement the first protected-preview curated_guidance routing slice from `docs/handoffs/task-completions/curated-guidance-routing-design-qa.md`.

Completed:
- Added a default-off `/api/answer` orchestration hook for private-review curated guidance.
- Added protected/admin-backstage role gating.
- Added multi-flag fail-closed gating.
- Added conservative teaching-query eligibility.
- Added internal-only logging of curated-guidance routing status/count.
- Added focused API tests proving default-off behavior, admin-only feature-flagged routing, beta/public blocking, explicit SGF-wisdom exclusion, and missing-corpus fallback.

Intentionally not changed:
- No public unauthenticated curated guidance.
- No source-card rendering for curated guidance.
- No private filenames, source paths, `private_review`, `curated_guidance`, or private excerpts in `/api/answer` payloads.
- No production UI wiring.
- No Chroma/vector changes.
- No embeddings.
- No SGF scraper changes.
- No corpus-private commits.
- No protected-preview restart or deployment.

## Files Changed

Changed:
- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`

Created:
- `docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md`

Deleted:
- None

Generated artifacts:
- None from this implementation slice.

## Gating Behavior Implemented

Curated guidance can be considered for `/api/answer` only when all are true:

- `ENABLE_PRIVATE_REVIEW_SOURCES=1`
- `ENABLE_CURATED_GUIDANCE_RETRIEVAL=1`
- `ENABLE_CURATED_GUIDANCE_IN_ANSWER=1`
- role is admin/backstage-like: `admin`, `dev`, `developer`, or `backstage`
- classifier domain is `steel_guitar`
- request is not a guardrail/refusal route
- request does not need fretboard output
- request is a teaching-style steel query according to the existing curated-guidance retriever
- request is not explicitly asking for forum/player/public wisdom

When eligible, `/api/answer` calls the existing `search_curated_guidance(...)` retriever and stores only:

- `curatedGuidanceStatus`
- `curatedGuidanceCount`

Those fields are internal answer-request log fields only. They are not added to the public JSON response.

Current statuses:

- `disabled`
- `role_blocked`
- `ineligible`
- `retrieved`
- `empty`
- `error`

## What Was Not Added

No curated guidance answer-body synthesis was added.

No curated guidance source cards were added. That remains the later source-card labeling slice.

No hybrid SGF + curated guidance presentation was added.

No API schema fields were added.

## Privacy And Exposure Notes

The implementation does not place curated guidance results into:

- `answer`
- `sources`
- `warnings`
- `sections`
- `fretboard`
- any other public response key

Focused tests assert that private review terms, local/private filenames, local/private paths, content-layer values, and private excerpts do not appear in the response payload.

## Tests And Checks

Commands run:

```bash
.venv/bin/python -m pytest tests/test_curated_guidance_retriever.py tests/test_api_search.py -k 'curated_guidance' -q
```

Result:
- `12 passed, 238 deselected`

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_contract.py -q
```

Result:
- `81 passed`

```bash
.venv/bin/python -m py_compile steel_guitar_rag/api.py steel_guitar_rag/curated_guidance_retriever.py
```

Result:
- Passed.

```bash
.venv/bin/python -m pytest tests/test_api_search.py -q
```

Result:
- `244 passed`

```bash
.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q
```

Result:
- `64 passed`

```bash
git diff --check
```

Result:
- Passed.

```bash
git check-ignore -v corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl corpus-private/reports/curated-guidance-inventory-full.md corpus-private/reports/curated-guidance-validation.md corpus-private/reports/curated-guidance-validation.json corpus-private/reports/curated-guidance-retrieval-eval.md corpus-private/reports/curated-guidance-retrieval-eval.json
```

Result:
- All listed private generated outputs are ignored by `.gitignore:103:corpus-private/`.

```bash
.venv/bin/python -m pytest
```

Result:
- `718 passed`
- `2 failed`

Known unrelated full-suite failures:
- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

These are static/UI route failures outside this backend curated-guidance routing slice and match recent known caveats.

## Integration Notes

Public behavior remains unchanged unless all curated-guidance flags are enabled and the caller is admin/backstage.

Even when enabled for admin/backstage, this slice does not expose curated guidance in the public response. It only proves the protected routing path can call the separate retriever and fail closed.

The next runtime slice should be source-card labeling only if product/security approves it, and it must keep labels distinct from SGF evidence.

## Risks

Risk level: medium-low.

Why:
- The code touches shared `/api/answer` orchestration.
- The feature is disabled by default.
- The routing data is internal-only and contains no private excerpts or filenames.
- Source-card and answer-body exposure are intentionally not implemented.

Rollback:
- Revert the `steel_guitar_rag/api.py` changes and the focused test additions in `tests/test_api_search.py`.
- No corpus-private, Chroma, embeddings, UI, auth, or deployment rollback is needed.

## Human Decision Needed

Yes, before:
- exposing curated guidance in source cards,
- using curated guidance in answer synthesis,
- enabling the flags in protected preview,
- enabling beta/public access,
- promoting anything to production.

## Safe-To-Stage Exact File List

For this implementation slice:
- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md`

If Repo Steward is also committing prior curated-guidance retriever/ingestion work, use that lane's approved exact-path list separately. Do not broad-stage.

## Files That Must Not Be Staged

- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- SGF scraper outputs
- `source-inbox/` raw data or provenance
- `.wrangler/`
- DNS/deployment secrets
- `public/`
- `ui/brand/`
- `Neon Sign/`
- unrelated parked files from the broad dirty worktree

## Commit Readiness

Needs human review first.

Reason:
- Focused backend/API checks passed, but full pytest still has two known unrelated static/UI failures. Lane 15 should review the protected-routing behavior and decide whether Repo Steward may exact-path commit despite the unrelated full-suite caveat.

## Recommended Next Lane

Recommended lane: 15 QA / Answer Eval.

Suggested next prompt:

```text
Lane 15: QA the protected-preview curated_guidance routing slice in docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md. Verify feature flags fail closed, public/beta users do not trigger curated guidance, admin/backstage with all flags can trigger the retriever for teaching-style queries, explicit SGF wisdom queries remain ineligible, missing corpus returns no private warning, and /api/answer responses do not expose private_review, curated_guidance, filenames, source paths, or private excerpts. Run the focused curated guidance/API tests, git diff --check, and document whether Repo Steward can exact-path stage the listed files despite the known unrelated full-suite static/UI failures.
```
