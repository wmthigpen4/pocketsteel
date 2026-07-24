# Lane 20 — Discovery-only source transition decoder

## Task summary

Built a conservative source-cohort decoder for unpicked pedal, lever, and bar
movements. This is an extraction component, not the Amazing Tablature
arrangement ranker. It learns exact transition signatures from approved
discovery records, uses content-unit-grouped cross-validation, and emits only
`movement_only` or an explicit abstention.

The prior experimental ordered score-pitch projection was rejected and removed
because its discovery benchmark was only 85.7% accurate.

No validation rows or sealed-test rows entered decoder training. No model was
promoted or enabled in the app.

## Discovery results

- Main score/tab cohort:
  - 544 transition rows.
  - 8 reviewed movement-only transitions.
  - No signature met the fixed support and grouped-precision floors.
  - Status: `diagnostic_only`.
- Licks cohort:
  - 389 transition rows.
  - 136 reviewed movement-only transitions.
  - Five accepted exact signatures.
  - Leave-one-content-unit-out precision: 100%.
  - Leave-one-content-unit-out recall: 45.59%.
  - True positives: 62.
  - False positives: 0.
  - Status: `source_decoder_eligible`.

The deliberately lower recall is an abstention policy. Unproven repeated states
are not silently labeled as held movements.

## Files changed

- `steel_guitar_rag/amazing_tablature_transition_decoder.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_transition_decoder.py`
- `docs/handoffs/task-completions/2026-07-23-0320-20-source-transition-decoder.md`

Generated private artifacts remain beneath ignored
`corpus-private/melody-decisions/source-transition-decoders/`.

## Tests and checks

- `.venv/bin/pytest -q tests/test_amazing_tablature_transition_decoder.py tests/test_amazing_tablature_training.py`
  - 40 passed.
- `.venv/bin/pytest -q`
  - 1394 passed.
- Built both real discovery-only cohort decoders.
- Validation data used for training: false.
- Sealed-test data used: false.

## Integration notes

The decoder is intentionally pinned to a source cohort. Identical tab states
can mean a repick in one publication and a held movement in another, so this
component must not be treated as a universal arrangement rule. The learned
arrangement ranker remains a separate exact 21-feature model.

Because the rules-code file list now includes the decoder module, the exact
challenger must be rebuilt from a clean commit before any further canonical
evaluation.

## Risk assessment

Low to medium. The decoder is private, abstaining, and not runtime-enabled.
The primary risk is treating source-specific notation conventions as universal;
the API and artifact schema explicitly prevent that.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_transition_decoder.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_transition_decoder.py`
- `docs/handoffs/task-completions/2026-07-23-0320-20-source-transition-decoder.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs.

## Recommended next lane

Lane 20: add a digest-pinned, multi-reader semantic contact-sheet consensus pass
for validation tablature, then rebuild the exact challenger from the clean
commit. Keep sealed-test data closed.

## Commit readiness

Safe to commit.

## Suggested next step

Implement the validation contact-sheet consensus report. It should compare
normalized string/fret/control/sounding-pitch states across distinct local model
artifacts, reconstruct every event column without relying on the undercounting
line localizer, and withhold any cell lacking two-reader agreement.
