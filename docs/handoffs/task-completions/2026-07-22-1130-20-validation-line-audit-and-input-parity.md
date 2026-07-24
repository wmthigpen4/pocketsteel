# Lane 20 — Validation line audit and structured-input parity

Date: 2026-07-22 11:30 America/Chicago

## Task summary

Built the compact held-out validation audit required after the v17 reader run.
The audit presents one complete score/tab line at a time, keeps the original
score and tablature together, opens the full-line independent score-versus-tab
comparison, shows the complete ten-string tablature, bounds long difference
lists within an internal scroll area, and records one decision per line.

Generated immutable private packets for both authoritative validation cohorts:

- Main: 28 validation pages, 25 pages with 57 paired lines, 3 pages with no
  detected score/tab line, 192 machine blocking issues.
- Licks: 3 validation pages, 6 paired lines, no page without a detected line,
  8 machine blocking issues.

Pages without a paired line are recorded as automatic validation failures and
are not silently omitted. Both packets pin extractor v17, the exact challenger
`at-1fa9630a173af769`, its artifact SHA, the validation-run digest, each machine
page digest, and `sealedTestAccessed: false`.

Validation submissions are now accepted only when every displayed line has one
decision. The server verifies the immutable packet digest and target identities,
requires explicit tablature confirmation except for correction feedback, and
writes a private receipt marked `eligibleForTraining: false` and
`validationGroundTruthMayTrain: false`.

Also extended the structured-input parity test. Typed note names, intervals,
MusicXML, MIDI, and normalized score events converge on the same scientific
pitches and now must produce the same route set, tablature notes, controls,
grips, and pattern families. This proves input-path equivalence; it is not a
held-out model-accuracy claim.

No validation answer was used for training. No sealed-test source, membership,
ground truth, or result was opened. No runtime model was activated.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_melody_import.py`
- `docs/amazing-tablature-training.md`
- This handoff.

Ignored private artifacts were generated beneath the two batches' validation
review directories. They include immutable packets, source-pair derivatives,
HTML consoles, packet summaries, and current private pointers. They must not be
staged.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py` —
  PASS, 129 tests.
- `.venv/bin/python -m pytest -q tests/test_melody_import.py tests/test_amazing_tablature_extraction.py`
  — PASS, 137 tests.
- `.venv/bin/python -m pytest -q` — PASS, 1,343 tests.
- `git diff --check` — PASS.
- Main validation packet preparation — PASS, 57 lines, digest prefix
  `4663b12e863d`, sealed test closed.
- Licks validation packet preparation — PASS, 6 lines, digest prefix
  `aafa20b92a96`, sealed test closed.

## Browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8766/atb-20260716-training-278-semantic-v2/extraction/validation/review/validation-line-audit/validation-line-audit-console-4663b12e863d.html?v=4663b12e`
- Cache-busted URL tested: same as exact URL
- Exact URL the user should use: same as exact URL
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8766`
- Expected backend port: `8766`
- Expected git HEAD: `ec9120eef099d3b744a3a4d8c5c2b468952a39c6` before this slice is committed
- Version endpoint: not applicable to the private review server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: immutable packet and console digest
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: no; this is a private file review server
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no
- Who should test this URL: Codex and the user
- Do not test these URLs: validation image or packet paths outside the generated console; every sealed-test path
- Known caveats: 3 main validation pages have no detected paired line and are automatic failures rather than review pages

The main page loaded 57-line progress, source imagery, open full-line evidence,
bounded difference scrolling, disabled-until-complete submission, and functional
next-page navigation from page 1 to page 2. The licks page loaded 6-line
progress, source imagery, open full-line evidence, and disabled-until-complete
submission. This was browser smoke, not API fallback.

## Integration notes

The structured-input layer is no longer the ambiguity: all five supported exact
input paths feed identical musical information to the arranger. The remaining
held-out questions are (1) score/tab recognition and alignment and (2) whether
the exact challenger ranks the independently reviewed source choice above its
valid alternatives.

After both validation packets are submitted, Lane 20 should score recognition
and source-choice ranking separately. Correction feedback counts as a held-out
failure; it must not be used to refine this challenger. Only if the fixed
strictly-greater-than-95% structured-input gate, top-three, cohort,
evidence-mode, and mechanical-validity gates all pass may the exact model and
rules be frozen. The sealed test remains closed until then.

## Risk assessment

Risk: medium. The validation/no-training boundary is enforced and all tests are
green, but the current validation evidence already shows substantial upstream
recognition errors. Human review remains necessary to establish authoritative
metrics. The three no-line pages prevent a misleading page-completeness claim.

Rollback: revert the exact scoped commit and retain the immutable private
packets as historical, non-training evidence. Do not delete private receipts or
rewrite validation history.

## Human decision needed

Yes. The user must complete and submit the 57-line main validation audit and
the 6-line licks validation audit. No threshold, model, or sealed-test decision
is needed before those submissions are scored.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_melody_import.py`
- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-22-1130-20-validation-line-audit-and-input-parity.md`

## Files that must not be staged

- `corpus-private/**`.
- `docs/handoffs/task-completions/integration-status.md` in its current parked state.
- Every unrelated untracked historical handoff.
- Raw sources, derivatives, packets, submissions, annotations, models,
  reports, split manifests, validation ground truth, and sealed-test material.

## Recommended next lane

Lane 20 after the two validation submissions, followed by Lane 15 only if every
fixed validation gate passes.

## Commit readiness

Safe to commit.

## Suggested next step

Complete the main and licks validation audits. Lane 20 should then ingest both
immutable receipts, report separate recognition and structured-input ranking
metrics, and either freeze the exact passing rules or stop with the failed
categories while keeping sealed test closed.
