# Lane 20 — Anchored Tablature Row-Geometry Challenger

## Task summary

Continued the discovery-only machine improvement loop from clean HEAD `3dadc30109dc4084e0106dec95b1fc88e6015fbe`. The first broad geometry supplement was rejected because it recovered 10 event row sets but regressed 35; it was removed before this slice was retained. The accepted challenger is deliberately narrow: when source geometry splits the exact middle string of a three-string grip into an adjacent candidate, it merges that candidate with the two outer strings only when the string pattern and horizontal tolerance are exact.

The checked-in behavior is a challenger and evaluator only. It does not alter the default extractor path, current page records, reviewed records, training ledgers, or runtime behavior. It creates no human review packet.

Opened discovery result:

- Development: 23 digest-pinned archived-machine cases evaluated.
- Development source-candidate count: 5 exact before, 6 exact after.
- Development count improvements: 1; regressions: 0.
- Development missing-row proposals: 2 exact, 0 false.
- Opened shadow: 10 digest-pinned archived-machine cases evaluated.
- Opened-shadow source-candidate count: 3 exact before and after.
- Opened-shadow missing-row proposals: 1 exact, 0 false.
- Six benchmark cases had no archived pre-correction machine snapshot and remained blocked.
- Opened discovery gate: PASS.

As a separate private diagnostic, the configured independent tablature token reader read all three merged missing cells after the source crop was centered on the combined grip. The one opened-shadow token exactly matched the later reviewed steel action. The two development tokens required the same-fret context of their outer grip to form complete actions and then matched the later reviewed actions. This diagnostic is not promotion evidence and is not written into current records.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
  - Adds the pure, narrow split-middle-grip geometry merger.
  - Adds a discovery-only evaluator with inference digested before reviewed truth is joined.
  - Records development and opened-shadow count and row-proposal regressions independently.
- `scripts/amazing_tablature.py`
  - Adds `evaluate-discovery-tab-row-geometry-challenger`.
- `tests/test_amazing_tablature_extraction.py`
  - Covers the exact merge and unrelated-neighbor rejection.
- `docs/handoffs/task-completions/2026-07-22-1521-20-anchored-tab-row-geometry-challenger.md`
  - This handoff.

Ignored private report only:

- `corpus-private/melody-decisions/batches/atb-20260716-training-278-semantic-v2/extraction/discovery/review/automation/anchored-tab-row-geometry-v1/report-38c508fede1a.json`
- Report digest: `38c508fede1ae8183e71121259cc1608ba8a700e7922e1c2ce5afdf68316a07b`.

The rejected broad-rule report and private token-reader caches remain ignored diagnostic artifacts and must not be treated as authoritative training evidence or staged.

## Tests and checks

- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_extraction.py scripts/amazing_tablature.py` — PASS.
- `.venv/bin/ruff check steel_guitar_rag/amazing_tablature_extraction.py scripts/amazing_tablature.py tests/test_amazing_tablature_extraction.py` — PASS.
- Focused split-grip tests — PASS, 3 tests.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py` — PASS, 145 tests.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py tests/test_amazing_tablature_sealed_test.py tests/test_amazing_tablature_input_parity.py` — PASS, 38 tests using repository fixtures only.
- `git diff --check` — PASS.
- Discovery-only challenger replay — PASS; report digest `38c508fede1ae8183e71121259cc1608ba8a700e7922e1c2ce5afdf68316a07b`.

## Integration notes

- The challenger fixes one specific, repeatedly observed omission: a horizontally displaced middle-string token in an otherwise simultaneous three-string grip.
- It does not solve general event-count recognition, arbitrary missing rows, score recognition, ties, dotted values, or control recognition.
- The default extractor remains unchanged. Promotion into the extractor requires either a fresh pre-review discovery shadow or a larger no-regression opened-discovery replay plus an exact token/action construction contract.
- The unified machine timeline from the preceding slice remains the acceptance gate. This geometry result alone cannot make a line reviewable.
- Reviewed truth is joined only after the source derivative, archived pre-correction anchors, candidate geometry, and row proposals receive an inference digest.
- Validation review remains withdrawn. Validation and sealed-test data were not accessed.
- Human rereview requested: 0.

## Risk assessment

**Low to medium.** The new rule is not active in extraction or runtime behavior. Its opened-shadow support is only one row, so it is too small for promotion despite zero observed regressions. Rollback is the scoped commit; ignored reports and caches may remain for lineage audit.

## Human decision needed

No. Do not request another human audit yet.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-1521-20-anchored-tab-row-geometry-challenger.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs.
- Everything beneath `corpus-private/`.
- Raw images, current page records, reviewed records, human decisions, training ledgers, validation artifacts, sealed-test data, rejected reports, and token-reader caches.

## Recommended next lane

Lane 20 Amazing Tablature Training.

Freeze this exact geometry contract, capture it on future not-yet-reviewed discovery lines before any later truth is available, and pair a successful row proposal with an independently legible complete fret/control token plus mechanical validation. In parallel, continue source-score grouping improvements behind the unchanged unified timeline gate. Do not create another human packet until both score and tablature states are complete and mutually consistent.

## Commit readiness

Safe to commit.

## Suggested next step

`Lane 20: Capture the frozen split-middle-grip geometry contract on eligible not-yet-reviewed discovery lines, require complete independently read steel actions and mechanical validity, and keep validation and sealed-test data closed.`
