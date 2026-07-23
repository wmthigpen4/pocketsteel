# Lane 20 — Canonical validation review ready

## Task summary

Regenerated the exact validation score, immutable decision ledger, preserved
human preference adjudication, and one combined canonical review packet from
clean HEAD `05b3a6356b0894c374619cebe67d50253f5e1467`.

The packet contains all nine machine-complete, mechanically valid validation
lines across both authoritative cohorts:

- 68 exact ranked decisions.
- 2 score-supported lines that require score-pitch and tablature confirmation.
- 7 tablature-only lines that require tablature confirmation only.
- No blank or structurally incomplete machine captures.

The local browser smoke passed. The packet opens at the first line with zero
reviews selected, source imagery loads, the ten-string movement table renders,
score pitch and octave labels appear on score-supported lines, previous/next
navigation works, and no browser warnings or errors were recorded.

Validation remains evaluation-only and prohibited from training. Sealed-test
data was not opened.

## Exact lineage

- Model ID: `at-90360274fad075f6`
- Model artifact SHA-256:
  `48fbb49a035225791b15611d7fda41fee6b8c60c439c62e851814a6474ce1660`
- Score report:
  `35adec905251200886046205106341756cb9ee89c6ca4d45a23001c321dda7c5`
- Decision ledger:
  `c0a218dc4800a3d9aa7bf4a6be1d4b9717890ce2d3c194616b71b14045f9df4f`
- Canonical packet:
  `6f6e2f7f37b957f4ca56aab214467976e5f1406df339a4ccd676888828eb792f`
- Preserved adjudication:
  `c47db5f8f07a63d0077c0b4612bd80f9df787e3a20fbd7fd391623b8357830e1`
- No-rereview equivalence certificate:
  `110921827b50901b187f8eb966afcb12ca834d7f393242e0080a08161b850b00`

## Current metrics

- Strict source top-choice: 64/68, 94.12%.
- Human-accepted top-choice: 65/68, 95.59%.
- Top-three coverage: 68/68, 100%.
- Predicted-top mechanical validity: 68/68, 100%.
- Main cohort strict: 22/22, 100%.
- Licks cohort strict: 42/46, 91.30%.
- Preserved adjudication: three source-preferred, one challenger-valid.
- Human rereview of those four preferences: not required.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested:
  `http://127.0.0.1:8766/validation-evaluations/at-90360274fad075f6/canonical-validation/canonical-validation-console-6f6e2f7f37b9.html?v=6f6e2f7f`
- Cache-busted URL tested: same as above
- Exact URL the user should use: same as above
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8766`
- Expected backend port: `8766`
- Expected git HEAD: `05b3a6356b0894c374619cebe67d50253f5e1467`
- Version endpoint: not applicable to the private review server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: exact packet, evaluator
  revision, and code-file digests
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: no
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no
- Who should test this URL: the user
- Do not test these URLs: production app URLs for this private review
- Known caveats: the local review server must remain running

## Files changed

- This handoff only.
- Private ignored evaluation reports, ledger, packet, crops, and preserved
  adjudication were generated beneath `corpus-private/melody-decisions/`.

## Tests and checks

- `.venv/bin/pytest -q tests/test_amazing_tablature_training.py tests/test_amazing_tablature_extraction.py`
  - PASS: 228 passed.
- `.venv/bin/pytest -q tests/test_amazing_tablature_*.py`
  - PASS: 259 passed.
- `.venv/bin/pytest -q`
  - PASS: 1,443 passed.
- `.venv/bin/ruff check` on the changed Lane 20 implementation and tests
  - PASS.
- Python compilation and CLI help
  - PASS.
- Local browser smoke
  - PASS.
- `git diff --check`
  - PASS.

## Integration notes

After the user submits all nine lines, score the exact receipt against the
packet, score report, adjudication report, and equivalence certificate. If the
fixed gates pass, enable only the private learned-versus-deterministic
comparison. Do not promote public runtime or open sealed test at that point.

## Risk assessment

Risk: medium. The review is intentionally small and complete, but only two
lines have independent machine-score support. The untouched sealed evaluation
remains necessary to establish broader generalization after the private
comparison and rules freeze.

## Human decision needed

Yes: review and submit the nine-line canonical packet.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated historical untracked handoffs
- `corpus-private/**`

## Recommended next lane

Lane 20 Amazing Tablature Training after submission, then independent Lane 15
audit before rules freeze.

## Commit readiness

Safe to commit

## Suggested next step

Have the user review and submit the nine lines. Then score the exact receipt,
record canonical eligibility, and proceed automatically to the private
learned-versus-deterministic comparison if every gate passes.
