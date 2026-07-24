# Curated Guidance Protected Routing QA

## Task Summary

- What was requested: QA review the first default-off protected-preview `/api/answer` curated-guidance routing slice before Repo Steward staging.
- What was completed: reviewed the Lane 05 handoff, `steel_guitar_rag/api.py`, `steel_guitar_rag/curated_guidance_retriever.py`, focused curated-guidance API tests, API contract/intent tests, and retriever tests; ran the requested focused checks plus full pytest to classify the reported failures.
- What was intentionally not changed: no implementation files, tests, `/api/answer` behavior, source cards, answer-body curated guidance, UI, Chroma/vector stores, embeddings, corpus-private files, SGF scraper, deployment, DNS, auth policy, staging, or commits were changed by this QA task.

## Pass/Fail Decision

Pass.

QA approves exact-path staging of the protected-preview curated-guidance routing slice despite the two full-suite failures, because the failures reproduced exactly as unrelated static/UI caveats and do not involve this backend slice.

## Files Reviewed

- `docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/curated_guidance_retriever.py`
- `tests/test_curated_guidance_retriever.py`
- `tests/test_api_search.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_contract.py`

## Privacy And Security Findings

Pass.

- Curated-guidance participation in `/api/answer` is fail-closed.
- The API hook requires all three flags:
  - `ENABLE_PRIVATE_REVIEW_SOURCES`
  - `ENABLE_CURATED_GUIDANCE_RETRIEVAL`
  - `ENABLE_CURATED_GUIDANCE_IN_ANSWER`
- Public/unauthenticated users cannot trigger curated guidance.
- `beta_user` cannot trigger curated guidance even when all flags are enabled.
- Admin/backstage-like roles can trigger the retriever only when all flags and query-eligibility checks pass.
- Explicit SGF/forum-wisdom prompts remain ineligible.
- Missing/empty curated guidance falls back safely without user-facing private path warnings.
- The `/api/answer` response does not include curated-guidance results in:
  - `answer`
  - `sources`
  - `warnings`
  - `sections`
  - `fretboard`
  - public JSON response keys
- The API hook logs only `curatedGuidanceStatus` and `curatedGuidanceCount`; it does not log private excerpts, filenames, paths, full bodies, or raw private metadata.
- The retriever still returns excerpts capped at 500 characters and does not return full `body` fields.

## Feature-Flag Findings

Pass.

Direct flag-combination check showed only the all-three-on combination enables `/api/answer` curated-guidance routing:

```text
enabled_combinations [{'ENABLE_PRIVATE_REVIEW_SOURCES': '1', 'ENABLE_CURATED_GUIDANCE_RETRIEVAL': '1', 'ENABLE_CURATED_GUIDANCE_IN_ANSWER': '1'}]
```

The routing remains default-off.

## Role-Gating Findings

Pass.

Direct role check:

```text
roles {None: False, '': False, 'anonymous': False, 'beta_user': False, 'admin': True, 'dev': True, 'developer': True, 'backstage': True, 'ADMIN': True}
```

The allowed role set matches the Lane 05 report: admin, dev, developer, and backstage.

## Answer And Source-Card Leakage Findings

Pass.

- No curated guidance is rendered in answer text.
- No curated guidance source cards are added.
- No curated guidance warnings or sections are added.
- No `private_review`, `curated_guidance`, private filenames, private paths, or private excerpts appear in the public response payload in focused tests.
- The retriever result count/status are internal answer-request log fields only.
- Source-card labeling remains intentionally unimplemented for this slice.

## Scope Findings

Pass.

Scoped diff for this slice is limited to:

- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md`

No scoped changes were found to:

- Chroma/vector stores
- embeddings
- SGF scraper behavior
- production UI
- deployment/DNS
- auth policy
- corpus-private files
- source-inbox raw/provenance files

The broader worktree is dirty with many unrelated parked files, including protected-looking paths. Repo Steward must exact-path stage only the approved slice.

## Tests And Checks

Commands run:

- `git status --short`
  - Passed. Broad dirty worktree remains; scoped slice files are identifiable.
- `git diff --check`
  - Passed.
- `.venv/bin/python - <<'PY' ...`
  - Passed. Verified all-three feature flag behavior and role gating directly.
- `git check-ignore -v corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl corpus-private/reports/curated-guidance-retrieval-eval.md corpus-private/reports/curated-guidance-retrieval-eval.json`
  - Passed. All checked outputs are ignored by `.gitignore:103:corpus-private/`.
- `.venv/bin/python -m pytest tests/test_curated_guidance_retriever.py tests/test_api_search.py -k 'curated_guidance' -q`
  - Passed: `12 passed, 238 deselected`.
- `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_contract.py -q`
  - Passed: `81 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - Passed: `244 passed`.
- `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q`
  - Passed: `64 passed`.
- `.venv/bin/python -m py_compile steel_guitar_rag/api.py steel_guitar_rag/curated_guidance_retriever.py`
  - Passed.
- `.venv/bin/python -m pytest`
  - Failed with known unrelated static/UI failures: `718 passed, 2 failed`.
- `git diff --name-only`
  - Passed for worktree inspection. Confirmed broad unrelated dirty files remain.
- `git status --short -- steel_guitar_rag/api.py steel_guitar_rag/curated_guidance_retriever.py tests/test_curated_guidance_retriever.py tests/test_api_search.py tests/test_answer_intent_classifier.py tests/test_api_contract.py docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md`
  - Passed. Scoped implementation files are `M steel_guitar_rag/api.py`, `M tests/test_api_search.py`, plus the untracked Lane 05 handoff.
- `git diff --stat -- steel_guitar_rag/api.py tests/test_api_search.py docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md`
  - Passed. Scoped diff shows only API/test changes; the untracked handoff is not included in normal diff stat.
- `git diff --check`
  - Passed after writing this QA handoff.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/2026-06-14-15-curated-guidance-protected-routing-qa.md`
  - Passed with expected exit code `1` for a new untracked file diff and no whitespace-error output.
- `git status --short -- steel_guitar_rag/api.py tests/test_api_search.py docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md docs/handoffs/task-completions/2026-06-14-15-curated-guidance-protected-routing-qa.md`
  - Passed. Shows only the two implementation files and two handoffs in the approved staging scope.

## Full Pytest Caveat Decision

Full pytest result:

- `718 passed`
- `2 failed`

Failures:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
  - Landing source vs deployed static HTML mismatch.
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
  - Same-origin server returns `404 Not Found` for `/brand/pedal-steel-fretboard-background.svg`.

Decision: these failures do not block this curated-guidance backend slice.

Reason:

- They match the Lane 05 reported full-suite caveats exactly.
- They are static/UI route failures outside `steel_guitar_rag/api.py`, `steel_guitar_rag/curated_guidance_retriever.py`, and the curated-guidance `/api/answer` hook.
- The focused backend/API/eval checks for this slice all passed.

They should remain parked for a separate Lane 06/static task if still relevant.

## Bugs Found

No blocking bugs found.

Non-blocking test coverage note:

- Existing tests cover default-off, all-flags-on admin routing, beta blocking, unauthenticated blocking, SGF-wisdom ineligibility, and empty-corpus fallback. The direct QA snippet verified all individual flag combinations. A future unit test could encode the individual missing-flag permutations, but this is not required to approve the slice.

## Files Changed

- Created:
  - `docs/handoffs/task-completions/2026-06-14-15-curated-guidance-protected-routing-qa.md`
- Reviewed:
  - `docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md`
  - `steel_guitar_rag/api.py`
  - `steel_guitar_rag/curated_guidance_retriever.py`
  - `tests/test_curated_guidance_retriever.py`
  - `tests/test_api_search.py`
  - `tests/test_answer_intent_classifier.py`
  - `tests/test_api_contract.py`
- Deleted:
  - None
- Generated artifacts:
  - None

## Safe-To-Stage Exact File List

For this protected-routing slice:

- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md`
- `docs/handoffs/task-completions/2026-06-14-15-curated-guidance-protected-routing-qa.md`

If Repo Steward also commits prior curated-guidance retriever/ingestion work, use that lane's separate approved exact-path list. Do not combine scopes unless explicitly instructed.

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files outside the four safe-to-stage paths above.
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
- generated reports or raw design assets
- unrelated parked docs/runtime files visible in the broad dirty worktree.

## Risk Assessment

Risk level: medium-low.

Why:

- The slice touches shared `/api/answer` orchestration.
- The new behavior is default-off, role-gated, and internal-only.
- No private guidance content is exposed in responses or source cards.
- Full pytest has unrelated static/UI failures, so Repo Steward must treat this as an exact-path backend slice rather than a whole-worktree green state.

Rollback notes:

- Revert the scoped changes in `steel_guitar_rag/api.py` and `tests/test_api_search.py`.
- No corpus-private, Chroma, embeddings, UI, auth-policy, deployment, or DNS rollback is needed for this slice.

## Human Decision Needed

No for exact-path commit of this slice.

Yes before any later step that:

- exposes curated guidance in source cards,
- uses curated guidance in answer synthesis,
- enables flags in protected preview,
- grants beta/public access,
- promotes anything to production.

## Commit Readiness

Safe to commit.

This approval is for exact-path staging only, despite the known unrelated full-suite static/UI failures.

## Recommended Next Lane

Recommended lane: `01 Repo Steward`.

Suggested next prompt:

```text
Lane 01: Run ExactPathCommit using docs/handoffs/task-completions/2026-06-14-15-curated-guidance-protected-routing-qa.md. Stage only steel_guitar_rag/api.py, tests/test_api_search.py, docs/handoffs/task-completions/2026-06-14-2036-05-curated-guidance-protected-routing.md, and docs/handoffs/task-completions/2026-06-14-15-curated-guidance-protected-routing-qa.md. Do not stage corpus-private, public/UI/static files, source-inbox files, generated reports, or unrelated parked worktree files.
```
