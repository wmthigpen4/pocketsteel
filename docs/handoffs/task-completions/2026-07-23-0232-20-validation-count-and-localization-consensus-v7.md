# Lane 20 — Validation Count and Localization Consensus v7

## Task summary

Continued the approved production-adapter and canonical-validation goal after the v6 validation remediation withheld all 63 lines before ranker evaluation.

The v6 aggregate established that the dominant failures were upstream reconstruction failures, not challenger-ranking failures:

- 29/57 main lines had incompatible score-derived and tab-derived counts.
- 11/57 main lines failed tab-cell/event localization.
- Only 5/57 main lines reached the unique score/tab/copedent hypothesis gate.
- All 6 licks lines and all 57 main lines were withheld; none were applied.

Implemented validation remediation v7:

1. The deterministic tab candidate detector is now one count vote rather than an upper bound on the independent score reader.
2. Two independently seeded, tab-only readers provide the other count votes.
3. Exactly one count must receive at least two of the three votes.
4. If both tab-only readers agree that deterministic geometry missed or added columns, two independently seeded full-line reads must agree on event count, execution labels, string rows, literal tokens, and bounded horizontal geometry.
5. When deterministic geometry is retained, the two full-line readers need exact execution agreement; pinned per-cell Apple Vision evidence remains authoritative for tab tokens.
6. The score-only readers may establish any bounded source count without seeing or being censored by tablature geometry. Score and tab counts are reconciled only after both captures complete.
7. Synthetic candidate geometry created by full-line consensus is explicit and provenance-labelled; it does not silently overwrite the source detector.
8. The validation recapture contract advances from v6 to v7.

No validation correction was applied in this implementation slice. Validation remains evaluation-only, may not train, and the sealed test remains unopened.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-0232-20-validation-count-and-localization-consensus-v7.md`

No source image, reviewed discovery record, validation page record, training record, model, runtime product file, embedding, vector store, auth configuration, deployment configuration, or sealed-test artifact was modified.

## Tests and checks

- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_extraction.py` — pass.
- Focused validation count/localization/score-consensus tests — 3 passed.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py` — 163 passed.
- `.venv/bin/pytest -q` — 1,390 passed.
- `git diff --check -- steel_guitar_rag/amazing_tablature_extraction.py tests/test_amazing_tablature_extraction.py` — pass.

Skipped in this implementation checkpoint:

- Real validation v7 canary: runs only after this code is committed and the exact challenger is rebuilt from that clean HEAD.
- Main 57-line validation replay: conditional on the six-line licks canary completing without lineage or structural-contract defects.
- Sealed evaluation: prohibited until the exact engine, schemas, copedent, validators, and evaluation contract are frozen.
- Runtime/private-enable comparison: conditional on canonical validation passing fixed gates.

## Integration notes

The next operation is not user review. Lane 01 should exact-path commit the two implementation/test files and this handoff. Lane 20 should then rebuild the exact 21-feature challenger from that clean HEAD, replay validation extraction with the new exact model lineage, and run the six-line licks v7 remediation canary without applying records. If the canary is structurally sound, continue to the 57-line main remediation and canonical challenger evaluation.

The v7 fallback is deliberately conservative. Exact agreement between two seeded full-line reads is required when deterministic event geometry is replaced. A count agreement alone cannot fabricate a tab state.

## Risk assessment

Risk: medium.

The privacy, split, lineage, and fail-closed contracts remain intact, and all tests pass. The principal technical risk is low yield: two full-line readers may disagree often enough that v7 still withholds many lines. That is an acceptable failure mode; it must not be weakened using validation truth. If yield remains zero, canonical transformation-model evaluation needs an independently governed structured-score/tab ground-truth path rather than further conflating OMR accuracy with notes-to-tablature accuracy.

Rollback is the scoped commit containing this v7 implementation. No private record or model depends on it yet.

## Human decision needed

No.

The already approved goal authorizes the clean commit, exact challenger rebuild, discovery-only lineage verification, and validation evaluation. Exact model promotion and sealed-test execution remain separate gates.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-0232-20-validation-count-and-localization-consensus-v7.md`

## Files that must not be staged

- Everything beneath `corpus-private/`.
- `docs/handoffs/task-completions/integration-status.md`.
- All unrelated historical untracked handoffs.
- Raw source images, derivatives, private reports, split manifests, models, caches, validation artifacts, and sealed-test material.

## Recommended next lane

Lane 01 Repo Steward, then Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit.

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the three exact safe paths, verify the cached diff, commit the v7 validation consensus repair, then rebuild the exact challenger and run the non-applying six-line licks validation canary.
