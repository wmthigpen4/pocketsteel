# Lane 20 — Structured-input greater-than-95% contract

Date: 2026-07-22 09:10 America/Chicago

## Task summary

Implemented the pre-validation accuracy contract approved by the user. The
canonical arrangement metric now applies only after notes have been normalized
into exact score events. It explicitly excludes score-image and audio
recognition, requires structured-input top-choice accuracy to be strictly
greater than 95%, requires at least 99% top-three coverage, retains 100%
mechanical validity, and raises cohort plus score-backed/tab-only floors to
90%. Exactly 95% does not pass.

The sealed-test evaluator now consumes the frozen overall, cohort,
evidence-mode, top-three, and minimum-sample thresholds instead of silently
using one overall floor and a hard-coded one-decision minimum. Typed/staff-style
pitch events, interval entry, MusicXML, and MIDI were verified to converge on
the same normalized scientific pitches.

No validation or sealed-test source, annotation, ground truth, membership, or
metric was opened. No runtime model was activated. The discovery-only
automation audit and one score-remediation canary remained private; the canary
did not alter current page records or create human approval.

## Files changed

- `docs/amazing-tablature-training.md`
- `pocketsteel/amazing_tablature_training.py`
- `pocketsteel/amazing_tablature_sealed_test.py`
- `tests/test_amazing_tablature_training.py`
- `tests/test_amazing_tablature_sealed_test.py`
- `tests/test_melody_import.py`
- This handoff.

Generated private artifacts beneath ignored `corpus-private/`:

- refreshed discovery-completion audits for both authoritative batches;
- one digest-pinned main-batch score-remediation canary report;
- no current reviewed record, source asset, validation artifact, sealed-test
  artifact, or runtime model was modified.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_melody_import.py tests/test_melody_assistant.py tests/test_melody_workbench_ui.py tests/test_amazing_tablature_training.py tests/test_amazing_tablature_sealed_test.py` — PASS, 83 tests.
- `.venv/bin/python -m pytest -q` — PASS, 1,338 tests.
- `git diff --check` — PASS.
- Discovery audits — PASS; validation and sealed access flags remained false.
- Score-remediation canary — completed without changing current records; no
  line passed the joint correspondence gate.

## Integration notes

The current clean discovery challenger predates this contract code and must be
rebuilt after this exact implementation is committed so model and scorer
lineage share one reproducible HEAD. Canonical training remains blocked by 129
undisposed discovery pages: 128 main and one licks page. Automation currently
classifies the main remainder as 68 internal-remediation pages, 38
feedback-protected pages, and 22 non-tab disposition pages. The one licks page
requires confirmation of an existing machine correction.

The score-remediation canary selected two eligible pages but regressed its
aggregate count and pitch-column diagnostics, so it correctly created no
review packet and no approval. Do not open validation merely to compensate for
that upstream OMR weakness.

## Risk assessment

Risk: medium. The contract and evaluators are test-green, but greater-than-95%
has not been measured on held-out data. Top-three coverage is meaningful only
where a reviewed decision has enough alternatives. Discovery completion still
requires explicit page dispositions; automation may recommend or quarantine
but must not fabricate human approval.

Rollback: revert the exact contract commit before any validation access. Once
validation is opened, threshold rollback or adjustment is prohibited.

## Human decision needed

No decision is needed for continued discovery-only automation and challenger
rebuild. A bounded human disposition/confirmation step will be required before
canonical training because machine automation cannot grant review approval.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `pocketsteel/amazing_tablature_training.py`
- `pocketsteel/amazing_tablature_sealed_test.py`
- `tests/test_amazing_tablature_training.py`
- `tests/test_amazing_tablature_sealed_test.py`
- `tests/test_melody_import.py`
- `docs/handoffs/task-completions/2026-07-22-0910-20-structured-input-95-contract.md`

## Files that must not be staged

- `corpus-private/**`.
- `docs/handoffs/task-completions/integration-status.md` in its current parked state.
- All unrelated untracked historical handoffs.
- Raw images, derivatives, private reviews, annotations, models, reports,
  manifests, and sealed-test material.

## Recommended next lane

Lane 01 exact-path commit, then Lane 20 rebuild the full discovery-only
challenger lineage and shadow report from that clean HEAD. Continue automatic
discovery triage without opening validation or sealed-test data.

## Commit readiness

Safe to commit.

## Suggested next step

Commit only the seven exact files above, rebuild the clean discovery-only
challenger lineage under the new contract HEAD, verify preference/no-rereview
accounting, and prepare only bounded disposition or confirmation work that
automation cannot safely resolve.
