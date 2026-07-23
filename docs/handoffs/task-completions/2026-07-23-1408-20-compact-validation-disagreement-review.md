# Lane 20 — Compact validation disagreement review

## Task summary

Implemented a fail-closed validation diagnostic that records strict challenger
top-choice misses and turns one exact cohort into a compact private comparison
packet. The packet shows only tab-cell-complete, mechanically valid movements
with exact neighboring execution context and equivalent sounding pitches.

The licks packet for challenger `at-e00734bee5dea6fc` contained four
disagreements across three printed lines. The user reviewed all four. The
initial POST reached a stale local review server and was rejected, but the
page's local choices remained intact. The server was restarted against the new
route and the preserved choices were submitted successfully:

- submission ID:
  `validation-disagreement-submission-744c93fd5fc503bf7d1a`
- submission digest:
  `744c93fd5fc503bf7d1a266d53e817687c72e3681473d71b01d036b783871171`
- decisions: three `source_preferred`, one `challenger_valid`
- training eligible: false
- sealed test accessed: false

The strict pre-adjudication diagnostic remains 64/68 top choices
(94.1176%): main 22/22 and licks 42/46. This slice does not reinterpret that
metric, enable the challenger, freeze rules, or open either sealed cohort.

## Files changed

- `docs/amazing-tablature-training.md`
- `pocketsteel/amazing_tablature_extraction.py`
- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- this handoff

Private generated artifacts remain ignored beneath
`corpus-private/melody-decisions/` and must not be staged.

## Tests and checks

- `.venv/bin/python -m py_compile pocketsteel/amazing_tablature_extraction.py pocketsteel/amazing_tablature_training.py scripts/amazing_tablature.py`
  - passed
- `.venv/bin/ruff check pocketsteel/amazing_tablature_extraction.py pocketsteel/amazing_tablature_training.py scripts/amazing_tablature.py tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py`
  - passed
- `.venv/bin/pytest -q tests/test_amazing_tablature_training.py -k 'machine_validation_scorer' tests/test_amazing_tablature_extraction.py -k 'validation_disagreement or challenger_comparison_submission'`
  - 2 passed, 220 deselected
- `.venv/bin/pytest -q`
  - 1,435 passed
- `git diff --check`
  - passed

## Browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8766/atb-20260716-licks-34/extraction/validation/review/challenger-disagreements/challenger-disagreement-console-3c2bc63f0fae.html?v=3c2bc63f`
- Cache-busted URL tested: same URL
- Exact URL the user should use: no further user action is required for this packet
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8766`
- Expected backend port: 8766
- Expected git HEAD: `cbba67df235564311ad24377447a380ef87dee66`
- Version endpoint: not applicable to the local private review server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: repository HEAD plus the exact packet and source-file digests
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: no; this is a private file review server
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not applicable
- Who should test this URL: Codex and the user
- Do not test these URLs: validation pages outside the exact packet; all sealed-test paths
- Known caveats: the first submission attempt hit the stale server; the preserved selections were resubmitted successfully after restart

Verified:

- four comparisons across three printed lines
- 16 radio controls, exactly one choice required per comparison
- all three source images loaded at nonzero natural dimensions
- each comparison showed previous/current/following source movement context when present
- no browser console warnings or errors before submission
- final UI receipt: `Review received by Lane 20` / `Received 4 choices.`

## Integration notes

The validation submission is immutable and explicitly barred from discovery
training, preference ledgers, no-rereview accounting, prompts, and model
weights. A later adjudication report may measure both strict source-exact
accuracy and human-accepted recommendation accuracy, but it must retain the
raw 64/68 result and keep canonical/runtime/sealed gates closed unless every
precommitted validation requirement passes.

A clean-HEAD challenger `at-90360274fad075f6` was created concurrently and
its main validation extraction is still running. Its artifact and evaluation
must be treated independently even if its learned weights are equivalent.
The submitted adjudication is pinned to `at-e00734bee5dea6fc` and may not be
silently reassigned to the newer artifact.

## Risk assessment

Medium. The privacy and no-training contracts are fail closed and fully
tested, but validation evidence is still incomplete: machine consensus
contains no independently confirmed `alignment:score_supported` decisions.
The compact review resolves preference ambiguity only; it does not prove
score-reader completeness or authorize private runtime enablement.

Rollback is the code commit only. Private immutable packet and submission
artifacts should be retained for audit lineage.

## Human decision needed

No for this slice. The user's four decisions have already been received.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-23-1408-20-compact-validation-disagreement-review.md`
- `pocketsteel/amazing_tablature_extraction.py`
- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`

## Files that must not be staged

- `corpus-private/`
- `docs/handoffs/task-completions/integration-status.md`
- all unrelated untracked historical handoffs
- logs and generated review artifacts

## Recommended next lane

Lane 20.

## Commit readiness

Safe to commit.

## Suggested next step

Create an immutable no-training adjudication report for the exact submitted
packet, preserve strict source-exact metrics alongside human-accepted metrics,
then finish and independently score the clean-HEAD challenger. Do not enable a
model or open sealed test unless the fixed score-supported and preference
gates all pass.
