# Lane 20 — Validation score independence and written-octave contract

## Task summary

Repaired the validation-only score/tab comparison after the first unpublished validation replay exposed two problems: a tab-count-constrained score vision pass was not independent evidence, and standard guitar-family notation written an octave above sounding pitch was being rejected as a scientific-octave error.

Completed:

- Validation score reuse now requires an existing, hash-pinned `audiveris-musicxml-v1` capture with a complete independent event count, nonblank pitches, and an explicit key signature.
- Removed guided score vision from validation remediation; tablature or expected pitches are never supplied to the validation score reader.
- Added a fail-closed, whole-line written-versus-sounding octave contract. Raw written score pitches and raw sounding tab pitches remain unchanged; the accepted line-wide offset is stored explicitly as `scoreNotationTranspositionSemitones`.
- Added bounded semantic retries to guided tab localization and required one visual cell per deterministic candidate cell at every numbered guide.
- Bumped the private validation remediation schema to `validation-machine-recapture-v2`.

Intentionally not changed:

- No validation ground truth was opened or used.
- No sealed-test data was opened.
- No validation audit was published to the user.
- No challenger was promoted or enabled in production.
- No source image, corpus record, embedding, vector index, auth, deployment, or runtime product behavior was changed.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2059-20-validation-score-independence-and-octave-contract.md`

No files were deleted. Private replay artifacts remain beneath ignored `corpus-private/melody-decisions/`.

## Tests and checks

- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_extraction.py tests/test_amazing_tablature_extraction.py` — pass.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py -x` — **156 passed**.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_input_parity.py tests/test_amazing_tablature_score_sequence.py tests/test_amazing_tablature_sealed_test.py tests/test_amazing_tablature_training.py` — **202 passed**.
- `git diff --check` — pass.

## Integration notes

- A valid offset does not mean two raw scientific octaves are equal. Example: written `E5` and sounding `E4` remain `E5` and `E4`; the record carries `scoreNotationTranspositionSemitones: 12` and a separate raw relationship.
- The offset is accepted only when one bounded line-wide octave displacement preserves every ordered score pitch set inside the independently captured tab state. A mixed or inconsistent displacement remains blocked.
- Validation remediation may use tab geometry to demand complete tab cells, but it may not constrain the score reader's count or pitch answer.
- The exact challenger must be rebuilt after this commit so code lineage and evaluation lineage match before the next validation replay.

## Risk assessment

Medium. The comparison contract changes validation eligibility for standard octave-transposing notation, but it is bounded, explicit, preserves raw evidence, and is covered by fail-closed tests. Lines without complete independent OMR lineage remain withheld.

Rollback: revert this scoped commit. Private validation artifacts can be regenerated from immutable source assets.

## Human decision needed

No. Continue the approved discovery/validation workflow automatically. Human review remains reserved for complete, genuinely ambiguous lines only.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2059-20-validation-score-independence-and-octave-contract.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs
- `corpus-private/**`
- Any raw images, review exports, extraction output, models, validation artifacts, or sealed-test artifacts

## Recommended next lane

Lane 20 Amazing Tablature Training: exact-path commit this green slice, rebuild the discovery-only challenger from the new clean HEAD, replay validation extraction, and run machine-only remediation/preflight without publishing incomplete audits.

## Commit readiness

Safe to commit

## Suggested next step

Commit these exact three paths, rebuild the exact challenger, replay the licks validation partition first, and measure how many lines pass the independent score + complete tab + explicit octave contract before opening the main validation partition.
