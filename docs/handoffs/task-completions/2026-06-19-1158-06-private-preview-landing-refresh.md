# 2026-06-19 06 Private Preview Landing Refresh

## Task Summary

Requested a focused refresh of the public/private-preview landing page so it reads less like a template and more like a backstage invite to a steel-guitar learning/search assistant.

Completed:

- Refreshed the public landing hero headline and support copy.
- Reworked the feature section around pedal-steel-specific help: grips, pedals, levers, tone, copedents, blocking, positions, and practice.
- Added clearer fretboard-aware/source-aware positioning.
- Added a copyright/provenance guardrail section for full copyrighted song tabs and recording/solo transcriptions.
- Updated example questions to be more concrete and answerable.
- Kept the interest form, `/api/interest` routing, hanging sign placement, stage background, and static asset references unchanged.
- Kept `ui/steel-guitar-rag-landing.html` and `deploy/landing/index.html` synced.

Intentionally not changed:

- Backend/API behavior.
- Interest form routing or storage behavior.
- Landing sign placement, sizing, assets, or animation behavior.
- Auth, DNS, deployment config, Chroma, embeddings, scraping, corpus data, or private source data.

## Files Changed

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-06-19-1158-06-private-preview-landing-refresh.md`

## Tests And Checks

Run:

- `git diff --check` - passed.
- `.venv/bin/python -m pytest tests/test_public_landing_page.py -q` - passed, `31 passed`.
- `cmp -s ui/steel-guitar-rag-landing.html deploy/landing/index.html` - passed.
- Local static browser smoke at `http://127.0.0.1:8899/?v=private-preview-refresh` - passed.

Smoke notes:

- H1 rendered as `The steel-guitar answers you wish were easier to find.`
- Hero copy rendered the private-preview E9 positioning.
- Copyright/provenance guardrail copy rendered.
- Hanging sign element and fallback/poster paths remained present.
- Interest form remained present with `action="/api/interest"`.
- User-facing page text did not include `Pocket Steel`.

## Integration Notes

- Branch: `feature/answer-api`
- Starting HEAD: `ae1d669`
- The user-facing copy still uses `Steel Guitar RAG` because the requested landing copy specifically named that product text. No broad rename was attempted.
- The source and generated/static public landing copies are byte-identical after the change.

## Risk Assessment

Risk: low.

Reason:

- Static HTML copy/test change only.
- No API, auth, DNS, deployment, form routing, asset, corpus, Chroma, or scraping changes.
- Focused public landing test suite passed.

Rollback:

- Revert the scoped landing/test/handoff commit if the copy direction is rejected.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-landing.html`
- `deploy/landing/index.html`
- `tests/test_public_landing_page.py`
- `docs/handoffs/task-completions/2026-06-19-1158-06-private-preview-landing-refresh.md`

## Files That Must Not Be Staged

- Existing unrelated dirty/parked files, including but not limited to `README.md`, `docs/handoffs/task-completions/integration-status.md`, corpus/source-inbox files, RAG scripts, `ui/brand/*`, `public/brand/*`, `Neon Sign/`, and other untracked docs/assets not listed above.

## Recommended Next Lane

Lane 01 Repo Steward for exact-path commit of the scoped landing refresh.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit exact paths only with:

`refresh private preview landing page`
