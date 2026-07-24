# Lane 20 — Score-consensus confidence accounting

## Task summary

Replayed the exact challenger and found that two independently seeded
score-pitch readers returned identical key, ordered pitches, scientific
octaves, and horizontal geometry for one withheld validation line. Both
explicitly returned `uncertain: false`, but both omitted the optional scalar
`confidence`; the normalizer had converted the omission to `0.0` and rejected
the otherwise exact consensus.

The contract now distinguishes a missing confidence field from a reported low
confidence:

- a reported confidence below `0.85` still fails closed;
- an omitted confidence is accepted only when the two complete count, key,
  pitch, octave, and geometry reads agree;
- the resulting `0.85` threshold is labeled
  `exact_two_reader_consensus_threshold`, not model-reported confidence;
- raw reported confidences remain recorded as nullable lineage.

Intentionally not changed:

- No validation truth or reviewer answer was opened.
- No validation result was applied under this change yet.
- No sealed-test data was opened.
- No challenger was promoted or enabled.
- No production UI, runtime arrangement, corpus, embedding, vector, auth, or
  deployment behavior changed.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2154-20-score-consensus-confidence-accounting.md`

## Tests and checks

- Python compile — pass.
- Extraction suite — **161 passed**.
- Remaining Lane 20 suite — **46 passed**.
- Total Lane 20 tests — **207 passed**.
- `git diff --check` — pass.
- Exact challenger before this fix: `at-5fba6105f9e7ceda`, built from HEAD
  `8edf31bba99599e490913835b37c5f86772b9ac7`, 702 discovery examples.
- Exact licks validation replay — 3 pages, 6 systems, 0 failed pages,
  `sealedTestAccessed: false`.
- Machine-only v3 preflight before this fix — 1 pass, 4 withheld; no lines
  applied.

## Integration notes

This change fixes evidence accounting rather than relaxing a musical gate.
Count readers still receive no expected count or tab input. Pitch readers still
receive only the independently agreed score count. Exact two-reader agreement
is required before the independent tab/mechanical containment gate runs.

## Risk assessment

Low-to-medium. A model-omitted scalar can no longer nullify otherwise exact
independent evidence, but a reported low confidence, uncertainty flag, count
disagreement, pitch disagreement, key disagreement, geometry disagreement, or
tab/mechanical disagreement still withholds the line.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2154-20-score-consensus-confidence-accounting.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing unrelated untracked handoffs
- `corpus-private/**`
- Raw images, validation artifacts, sealed-test artifacts, or private model
  artifacts

## Recommended next lane

Lane 20: commit this exact slice, rebuild the exact discovery-only challenger,
repin licks validation, and rerun v3 machine preflight.

## Commit readiness

Safe to commit

## Suggested next step

Commit, rebuild, and verify whether the exact score consensus passes the full
independent tab/mechanical containment gate; keep every remaining disagreement
withheld.
