# Retain BTC and NNLS confidence features

## Task summary

The user approved retaining BTC and NNLS as confidence features after the
bounded development result. This slice records that product/architecture
decision in a tracked, test-covered model contract. It does not fit or promote
a model and does not change localhost or production behavior.

The retained feature path contains:

- six BTC coverage, agreement, dominance, confidence, and transition signals;
- six clean-room NNLS-chroma coverage, agreement, dominance, confidence, and
  margin signals;
- four three-system consensus signals;
- the existing 48 engine bar/uncertainty signals, for 64 total features.

## Files changed

- `chord_reader/models/chord-consensus-confidence-v1.json` — retained research
  feature, evidence, provenance, and policy contract;
- `tests/test_bounded_consensus_development.py` — asserts the contract exactly
  matches the frozen implementation feature lists and remains confidence-only;
- this handoff.

No generated feature cache, report, audio, fitted selector, UI, runtime, model
weight, dependency, calibration artifact, or deployment file changed.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_bounded_consensus_development.py`
  — 7 passed.
- `.venv/bin/ruff check tests/test_bounded_consensus_development.py` — passed.
- `.venv/bin/python -m json.tool chord_reader/models/chord-consensus-confidence-v1.json`
  — passed.
- `git diff --check` — passed.

## Integration notes

The tracked contract binds the full 64-feature ordered-name hash, source-engine
hashes, BTC registry, clean-room NNLS method, development report/cache hashes,
and the 247/248 accepted-bar development result. It intentionally retains the
feature definitions rather than a fitted selector artifact.

Policy remains fail-closed:

- confidence selection and human-review prioritization are approved roles;
- chord-label rewriting is forbidden;
- production and localhost proof activation are off;
- promotion eligibility is false;
- calibration and confirmation remain closed;
- no new evaluation is authorized by this retention decision.

## Risk assessment

Low. This is a tracked research contract and regression test only. Runtime
behavior is unchanged. The main future risk is overreading the retained
development evidence as 98% end-to-end transcription accuracy; the contract
explicitly prohibits that interpretation.

Rollback is the model-contract file, its focused test addition, and this
handoff.

## Human decision needed

No for retention. Yes before any future fit, runtime integration, threshold
change, calibration, confirmation, promotion, localhost activation, or
deployment.

## Safe-to-stage exact file list

- `chord_reader/models/chord-consensus-confidence-v1.json`
- `tests/test_bounded_consensus_development.py`
- `docs/handoffs/task-completions/2026-08-25-1645-18-retain-btc-nnls-confidence-features.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `~/Documents/Pocket Steel/tmp/`
- all generated BTC/NNLS caches, report JSON, audio, model weights,
  credentials, and unrelated files

## Recommended next lane

Stop. The retained confidence path is documented and protected. Lane 18 should
design any later runtime-integration proposal before Lane 05 changes behavior.

## Commit readiness

Safe to commit

## Suggested next step

No further action is required for retention. Continue using the existing
localhost proof unchanged until a separately approved integration phase.
