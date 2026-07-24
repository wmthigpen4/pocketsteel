# Lane 15 Durable Private Review Drafts

## Task summary

Implemented a loopback-only durable draft layer for private combined score/tab
and validation-line review consoles. Review choices can now be copied to the
local private server as they are made and restored in another browser session
before final submission.

This fixes the operational failure where completed choices existed only in one
browser's local storage. A saved draft is explicitly ineligible for training,
ground truth, and evaluation until the unchanged frozen final-submission
endpoint accepts a complete packet.

The current Packet 2A console was hardened and the private review server was
restarted with durable capture enabled. The prior eight choices were not
recoverable because no accessible browser or server draft contained them.

## Files changed

- `pocketsteel/lane15_review_drafts.py`
- `scripts/lane15_review_drafts.py`
- `tests/test_lane15_review_drafts.py`
- This handoff
- Ignored private derivative updated:
  `corpus-private/melody-decisions/batches/lane15-sealed-ground-truth-atrf-0e5e727332f26367-main/extraction/discovery/review/combined-score-tab-audit/combined-score-tab-audit-console-bf16ad358d95.html`

No frozen rules-engine file, source image, ground-truth record, model,
submission receipt, or official evaluation artifact changed.

## Tests and checks

- `.venv/bin/python -m ruff check pocketsteel/lane15_review_drafts.py scripts/lane15_review_drafts.py tests/test_lane15_review_drafts.py`
  — PASS
- `.venv/bin/python -m pytest -q tests/test_lane15_review_drafts.py`
  — PASS, 7 tests
- `.venv/bin/python -m compileall -q pocketsteel/lane15_review_drafts.py scripts/lane15_review_drafts.py`
  — PASS
- `.venv/bin/python -m pytest -q tests/test_lane15_review_drafts.py tests/test_amazing_tablature_extraction.py`
  — PASS, 194 tests
- Frozen-code digest audit — PASS, all 21 files exactly match freeze
  `atrf-0e5e727332f26367`
- Local server — PASS, listening on `127.0.0.1:8766`
- Packet page — PASS, HTTP 200
- Browser smoke — PASS, durable-capture marker count 1 and zero console errors
- `git diff --check` — pending exact-path closeout

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested:
  `http://127.0.0.1:8766/lane15-sealed-ground-truth-atrf-0e5e727332f26367-main/extraction/discovery/review/combined-score-tab-audit/combined-score-tab-audit-console-bf16ad358d95.html?v=durable1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: same as above
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8766`
- Expected backend port: 8766
- Expected git HEAD: `e4dffd18` (the durable-capture implementation commit)
- Version endpoint: not available for the private review server
- Version endpoint result: not available
- If version endpoint missing, how version is inferred: exact git HEAD plus the
  tested durable-capture marker
- Whether app root `/` works: yes, HTTP 200 directory root
- Whether app root `/` is expected to work: not used as the review target
- Whether `/ui/steel-guitar-rag-mock.html` works: no, HTTP 404
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no
- Who should test this URL: Codex and the user
- Do not test these URLs: validation or official sealed-evaluation outputs
- Known caveats: the earlier eight unsent choices cannot be reconstructed; they
  must be confirmed again or supplied in chat

## Integration notes

The durable server delegates all static serving and final submissions to the
frozen review server implementation. The new endpoint stores only exact,
partial browser drafts beneath ignored `corpus-private/melody-decisions/`.
Generated consoles must be hardened with:

```text
.venv/bin/python scripts/lane15_review_drafts.py harden-console <console-path>
```

The durable server runs with:

```text
.venv/bin/python scripts/lane15_review_drafts.py serve --host 127.0.0.1 --port 8766
```

The frozen program remains:

- Freeze: `atrf-0e5e727332f26367`
- Frozen code revision:
  `96343ab4729c931726b5b76a0fbb8bde4499d01d`
- Rules digest:
  `0e5e727332f263672301070a4d3f377880dff0175c8d356879b9278360d9fa49`
- Frozen-file mismatches: 0 of 21
- Status: `frozen_tests_unopened`

Implementation commit: `e4dffd18` (`fix: persist private review drafts durably`).

## Risk assessment

Low to medium. The draft layer is operational and reversible and cannot itself
authorize training or evaluation. The remaining risk is that Packet 2A's prior
unsent choices are unavailable and must not be guessed.

## Human decision needed

Yes. Supply the exact Packet 2A decisions in chat, or confirm:
`All 8 approved and tab confirmed` if that accurately reflects the review.

## Safe-to-stage exact file list

- `pocketsteel/lane15_review_drafts.py`
- `scripts/lane15_review_drafts.py`
- `tests/test_lane15_review_drafts.py`
- `docs/handoffs/task-completions/2026-07-23-2056-15-durable-private-review-drafts.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- All unrelated dirty and untracked files

## Recommended next lane

Lane 15 should submit and apply only the exact user-confirmed Packet 2A
decisions, then continue the sealed ground-truth schedule. The official
one-shot evaluation remains closed.

## Commit readiness

Safe to commit

## Suggested next step

Use exact-path staging for the four safe files, commit the durable-capture
slice, then resume Packet 2A from exact user-authored decisions.
