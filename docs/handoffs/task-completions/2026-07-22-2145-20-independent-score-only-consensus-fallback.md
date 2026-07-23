# Lane 20 — Independent score-only consensus fallback

## Task summary

Added a fail-closed validation fallback for lines whose pinned Audiveris
MusicXML is incomplete.

The fallback:

- runs two score-only readers with different deterministic seeds;
- gives neither count reader an expected count, tablature, validation truth,
  or reviewer correction;
- requires both count readers to agree on visible columns, attack count, and
  continuation classification;
- compares that independently established attack count with the complete
  machine timeline only after recognition;
- gives the two pitch readers only the agreed score-only count;
- requires exact agreement on ordered scientific pitches and key signature;
- requires their independently reported note positions to remain within a
  bounded delta;
- preserves score-reader geometry rather than borrowing tablature positions;
- records crop, reader, prompt, seed, count, pitch, and disagreement lineage;
- withholds every disagreement instead of manufacturing a score–tab match.

The recapture contract was advanced to `validation-machine-recapture-v3`, so
older machine-candidate caches cannot silently satisfy the new gate.

Intentionally not changed:

- No validation truth or reviewer answer was opened.
- No validation result was applied yet.
- No sealed-test data was opened.
- No private challenger was promoted or enabled.
- No runtime arrangement, UI, corpus, embedding, vector, auth, or deployment
  behavior changed.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2145-20-independent-score-only-consensus-fallback.md`

## Tests and checks

- `.venv/bin/python -m py_compile pocketsteel/amazing_tablature_extraction.py tests/test_amazing_tablature_extraction.py` — pass.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py` — **161 passed**.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_input_parity.py tests/test_amazing_tablature_score_sequence.py tests/test_amazing_tablature_sealed_test.py tests/test_amazing_tablature_training.py` — **207 passed**.
- `git diff --check` — pass.

## Integration notes

This fallback is narrower than ordinary score recapture. Two score-only readers
must independently agree before the tab hypothesis is consulted. The tab may
confirm or reject a finished score hypothesis, but it cannot supply its count,
pitches, octave, key, or horizontal geometry.

Grace-note systems whose visible score-note count legitimately exceeds the tab
state count remain withheld. Missing-key or conflicting-count cases also remain
withheld. These are the appropriate candidates for a compact ambiguity review
only after automatic options are exhausted.

## Risk assessment

Medium. The new path consumes local vision output, but it requires two-reader
agreement, exact key/pitch consensus, bounded geometry agreement, independent
tab containment, mechanical validity, and final structural preflight. Rollback
is the exact three-file commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2145-20-independent-score-only-consensus-fallback.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing unrelated untracked handoffs
- `corpus-private/**`
- Raw images, validation artifacts, sealed-test artifacts, or private model
  artifacts

## Recommended next lane

Lane 20: exact-path commit, rebuild the exact discovery-only challenger, replay
the licks validation extraction, and measure which previously withheld lines
now satisfy the complete independent preflight.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact three-file slice, rebuild from that exact HEAD, and run
`validation-machine-recapture-v3` against the six licks validation systems
without opening validation truth.
