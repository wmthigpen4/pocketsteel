# Lane 20 — Score-constrained tab hypothesis selection

## Task summary

Replaced the remaining full-line row-vote dependency in validation remediation with a bounded machine-evidence hypothesis gate.

The gate now:

- Uses independently captured, hash-pinned per-cell tab tokens.
- Enumerates only five possible system-wide row-origin offsets (`-2` through `+2`).
- Requires every cell to be confident and mechanically valid under the exact source copedent.
- Requires the complete resulting tab state sequence to be contained in the independently captured MusicXML score under one explicit line-wide notation-octave convention.
- Accepts only one unique semantic hypothesis; zero or multiple hypotheses remain withheld.
- Records the tested offsets, eligible hypothesis count, selected offset, and evidence contract.

This is designed to resolve machine-reader row disagreements without validation truth or reviewer reconstruction.

Intentionally not changed:

- No validation truth was opened or used.
- No sealed-test data was opened.
- No validation result was applied under this new gate yet.
- No production model, source asset, embedding, vector, auth, deployment, or UI behavior was changed.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2127-20-score-constrained-tab-hypothesis-selection.md`

## Tests and checks

- Python compile checks — pass.
- Focused extraction suite: **159 passed**.
- Lane 20 suite: **205 passed**.
- `git diff --check` — pass.

## Integration notes

- The independent score reader remains unconstrained by tab counts or pitches during recognition.
- Score containment is used only after both score and tab hypotheses exist.
- Candidate string rows can move only by one uniform bounded system offset, never event-specific invention.
- Multiple mechanically and musically valid hypotheses are explicitly ambiguous and cannot auto-apply.
- The exact challenger must be rebuilt and validation extraction replayed from the new commit before this gate is used for official validation accounting.

## Risk assessment

Medium. Score containment is now part of post-recognition hypothesis selection, but it cannot generate tokens, rows, or pitches and requires uniqueness across the entire line. Raw score and tab evidence remain preserved.

## Human decision needed

No immediate decision.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2127-20-score-constrained-tab-hypothesis-selection.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Unrelated handoffs
- `corpus-private/**`
- Raw images, models, validation artifacts, or sealed-test artifacts

## Recommended next lane

Lane 20: exact-path commit, rebuild the exact challenger, replay licks validation, and run this unique-hypothesis gate on the four remaining withheld lines.

## Commit readiness

Safe to commit

## Suggested next step

Commit this three-file slice, rebuild from the exact code revision, and measure how many of the four remaining licks validation lines become machine-complete without human input.
