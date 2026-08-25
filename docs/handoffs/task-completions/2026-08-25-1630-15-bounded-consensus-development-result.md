# Bounded consensus development terminal result

## Task summary

The user authorized one corrected, bounded development comparison of exactly
three chord-reader correctness selectors. The run completed and is now
terminal. It used the existing engine's 48 bar/uncertainty features, the pinned
BTC checker, and a clean-room Chordino-inspired NNLS-chroma checker.

The experiment answers a narrow but useful question: can independent harmonic
evidence let the system accept more of the existing engine's bar chords while
maintaining the 98% selective-precision target? It does not claim 98% accuracy
over every chord in every song and it does not rewrite incorrect chords.

## Result

The fixed development holdout contained 623 eligible bars. Without abstention,
the existing engine was correct on 79.94% of them. At the preregistered
correctness-confidence threshold of `0.98`:

| Candidate | Accepted | Correct | Precision | Coverage | One-sided 95% Wilson lower bound |
| --- | ---: | ---: | ---: | ---: | ---: |
| Engine evidence only | 192 | 191 | 99.479% | 30.819% | 97.700% |
| Engine + BTC | 232 | 231 | 99.569% | 37.239% | 98.091% |
| Engine + BTC + NNLS | 248 | 247 | 99.597% | 39.807% | 98.213% |

The full checker candidate therefore accepted 56 more correct-or-incorrect
bars than the engine-only selector at the same fixed threshold, an absolute
coverage increase of 8.99 percentage points and a relative increase of 29.17%.
It made one accepted error, the same count as the other two candidates.

The checker evidence also improved correctness-classification accuracy from
80.10% to 82.83% and reduced Brier error from `0.15533` to `0.13689` (11.87%
relative). ROC AUC changed from `0.89777` to `0.89441`, so the gain is in the
fixed operating point and probability calibration/coverage, not better global
ranking across every threshold.

## Dataset readout for the full candidate

| Dataset | Unfiltered engine precision | Accepted/correct at 0.98 | Selective precision | Coverage |
| --- | ---: | ---: | ---: | ---: |
| AAM | 100.00% | 28/28 | 100.00% | 80.00% |
| GuitarSet | 51.12% | 19/19 | 100.00% | 10.67% |
| IDMT Guitar | 90.68% | 32/31 | 96.88% | 27.12% |
| NRG-CP | 96.18% | 121/121 | 100.00% | 77.07% |
| Winterreise | 84.44% | 48/48 | 100.00% | 35.56% |

BTC and NNLS materially increased accepted GuitarSet support from 4 bars for
the engine-only selector to 19 bars, all correct in this holdout. That is
encouraging but far too little support to certify GuitarSet. AAM also has only
28 accepted bars, and IDMT Guitar misses the 98% empirical requirement at
31/32. The candidate is therefore not promotion-ready despite clearing the
aggregate lower-bound target in this one development holdout.

## Exact execution accounting

- source examples: 1,585 development bars;
- fit role: 962 bars;
- held-out development evaluation role: 623 bars;
- unique feature tracks: 185;
- BTC feature passes: 1;
- NNLS-chroma feature passes: 1;
- candidates: 3;
- total candidate fits: 3;
- parameter searches: 0;
- automatic retries: 0;
- calibration/test/confirmation evaluations: 0;
- subagents: 0;
- deployment, promotion, threshold, or localhost proof changes: 0.

Terminal report:
`~/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/bounded-consensus-development-v1/report.json`

- report artifact SHA-256:
  `0d1f9ab9fe82e94dffb9e2d40f08dde516e423f3f3db1f4a995796437e853ece`;
- report file SHA-256:
  `bb2a53d00413a8ec036e946adb86f4f483bc40b7f35f67aa55ab314304b68d2e`;
- feature-cache artifact SHA-256:
  `119f2972288be587bb7ff95be11af856bbb6c2f5ef55d22e4e3804bead11ac32`;
- group-assignment SHA-256:
  `ba4c110f32b49b0328e19c14a18749092f1c32120b440a0a4661901c7bcb4f8d`.

## Files changed

Committed implementation and governance:

- `scripts/run_bounded_consensus_development.py`;
- `tests/test_bounded_consensus_development.py`;
- `docs/handoffs/task-completions/2026-08-25-1600-15-bounded-consensus-development-preregistration.md`;
- the two preflight-stop handoffs;
- this terminal result handoff.

Commits before this handoff:

- `6800cd92` — frozen harness and preregistration;
- `879e9342` — first binding-preflight stop receipt;
- `babbebd3` — exact track-ID binding correction;
- `83ec12ef` — evaluation-preflight stop receipt;
- `296c5c5b` — exact missing-value bridge.

Generated BTC/NNLS caches and the report remain ignored and uncommitted.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_bounded_consensus_development.py`
  — 6 passed.
- `.venv/bin/ruff check scripts/run_bounded_consensus_development.py tests/test_bounded_consensus_development.py`
  — passed.
- `.venv/bin/ruff format --check scripts/run_bounded_consensus_development.py tests/test_bounded_consensus_development.py`
  — passed.
- `git diff --check` — passed.
- full real-matrix preflight — expected shapes `1585x48`, `1585x54`, and
  `1585x64`; 300 declared missing values; zero infinities; both fit classes
  present.
- cache validation — 185/185 BTC and NNLS files, all NNLS numeric arrays finite.
- terminal report validation — canonical hash matched; three candidate fits;
  zero searches/retries; all reported floating-point values finite; sealed and
  deployment flags false.

The numerical runtime emitted NumPy/scikit-learn matrix-operation warnings,
but all three fits completed, the report is finite, and its canonical hash
recomputes. The no-retry rule prevents a diagnostic refit; this remains a
reproducibility risk for any later approved phase.

## Risk assessment

Medium. The development evidence is genuinely positive and held out by
confidence group, but the result is only one internal development split. The
small AAM/GuitarSet accepted counts and IDMT miss prevent a broad 98% claim.
The candidate is a selector/abstention improvement, not a more accurate
underlying chord transcriber.

Rollback is the scoped commits listed above. No generated cache needs to be
deleted, and no runtime behavior changed.

## Human decision needed

Yes, before any next phase. The current candidate should not be promoted or
opened on calibration/confirmation data. A later proposal could freeze the
full 64-feature candidate, strengthen numerical reproducibility, and seek more
independent GuitarSet/AAM support, but this run authorizes none of that work.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-25-1630-15-bounded-consensus-development-result.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `~/Documents/Pocket Steel/tmp/`
- all source audio, generated BTC/NNLS features, report JSON, model caches,
  credentials, and unrelated files

## Recommended next lane

Stop for human review. If later authorized, Lane 18 should design a single
prospective reliability-hardening and independent-support phase; Lane 15 must
keep calibration/test/confirmation closed until that design is frozen.

## Commit readiness

Safe to commit

## Suggested next step

Review this result as evidence that BTC and NNLS are worth retaining as
confidence features. Do not interpret it as production readiness or 98%
end-to-end transcription accuracy.
