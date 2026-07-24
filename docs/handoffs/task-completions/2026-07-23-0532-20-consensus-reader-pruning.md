# Lane 20 — Validation Consensus Reader Pruning

## Task summary

Removed the least reliable local vision artifact from validation contact-sheet voting after private main/licks diagnostics showed that it frequently disagreed with clearly legible fret/control glyphs and could form an incorrect two-reader majority.

The private consensus now uses:

- pinned `gemma4:12b` for the full-sheet first pass;
- the independently trained, grouped-CV discovery glyph decoder when eligible for the source cohort;
- pinned `gemma4:latest` together with `gemma4:12b` on focused unresolved cards.

At least two semantic readers must still agree. No threshold was relaxed, no validation item was added to training, and sealed test remained closed.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- this handoff

## Tests and checks

- focused contact-consensus tests: 4 passed
- full `.venv/bin/pytest -q`: 1,400 passed
- `git diff --check`: passed

## Integration notes

This changes validation reader lineage, so discovery-only decoders and the exact challenger must be rebuilt from the resulting clean HEAD before final validation reporting.

## Risk assessment

Low to medium. Removing a weak reader can reduce apparent coverage, but it removes an observed false-agreement path and preserves fail-closed behavior.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-0532-20-consensus-reader-pruning.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- unrelated untracked handoffs

## Recommended next lane

Lane 20: rebuild exact discovery artifacts, rerun shadow/no-rereview accounting, repin validation, and finish the two-reader consensus reports.

## Commit readiness

Safe to commit

## Suggested next step

`Lane 20: Rebuild the exact challenger and validation consensus from the clean reader-pruning commit; keep sealed test closed.`
