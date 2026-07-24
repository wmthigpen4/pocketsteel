# Lane 20 — Validation Source Mode and Ordered Projection v8

## Task summary

Continued the approved validation-repair goal through two non-applying v7 canaries, diagnosed the resulting failure classes, and implemented the next discovery-backed v8 repair.

Exact clean challenger rebuilt after the v7 commit:

- model ID: `at-9ee3c6cb119a6a1a`;
- clean code revision: `cdcf1a8d930cc2602f7af3358d8b3ed5140b298d`;
- discovery examples: 702;
- feature schema: exact 21-feature `melody-ranker-features-v3-phrase-sequence`;
- discovery seed: `ats-74d224b4fc059354`;
- validation training allowed: false;
- sealed test accessed: false.

Validation extraction was replayed for both cohorts at that exact model:

- licks: 3/3 pages, 6 systems, zero extraction-page failures;
- main: 28/28 pages, 57 systems, zero extraction-page failures.

Non-applying v7 canaries:

- licks: 0/6 structurally complete, 6 withheld;
- main: 0/5 structurally complete, 5 withheld;
- applied records: 0;
- review packets: 0;
- training evidence: 0;
- sealed-test access: false.

The canaries established two separate architecture defects.

1. The licks cohort is tab-movement material, not a conventional-score-to-tab cohort. Generic score regions above its tab grids have no reviewed conventional-score facts. Running OMR over those regions produced false 11-, 10-, and 17-event “scores.” Licks must be evaluated as tab-state/movement-sequence evidence, not as score-reader evidence.
2. On genuine score+tab pages, v7 removed the tab-derived score-count cap but then accepted partial Audiveris output as complete. It also invoked an unreliable full-line localizer even when independent score and tab counts already fixed a one-to-one chronological mapping.

Implemented v8:

- two-reader source-only score consensus is now mandatory;
- existing Audiveris MusicXML is diagnostic only and cannot independently authorize a score capture;
- when independent score count equals deterministic visible tab-column count, source order defines correspondence without requiring equal engraving spacing;
- ordered equal-count projection requires every pinned Apple Vision tab cell to be complete and confident;
- any connector, slide, or directional mark blocks the all-picked ordered projection and routes the line to explicit execution recognition;
- the ordered projection records its discovery basis: 24/39 opened, score-audited discovery lines have equal score-event, tab-state, and picked-state counts;
- validation remediation advances to v8.

The licks source-mode separation is a confirmed product/evaluation contract finding. This slice does not yet implement a separate licks evaluator; it prevents further licks score-reader audits from being treated as meaningful validation evidence.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-0249-20-validation-source-mode-and-ordered-projection-v8.md`

Private generated artifacts were refreshed beneath the ignored validation extraction/remediation directories. They remain private and uncommitted.

No raw source, reviewed discovery truth, validation truth, model weights, runtime product file, embedding, vector store, auth setting, deployment setting, or sealed-test artifact was modified.

## Tests and checks

- Python compilation — pass.
- Focused v8 score/count/projection tests — 4 passed.
- Extraction test module — 164 passed.
- Full repository suite — 1,391 passed.
- `git diff --check` on the implementation/test files — pass.
- Both v7 canaries — completed, non-applying, all failures withheld.

Skipped:

- 57-line main v7 run: intentionally stopped after the zero-yield five-line canary.
- Any further licks score audit: invalid for a tab-only source mode.
- v8 real validation canary: runs only after the v8 implementation is committed and the exact challenger is rebuilt from that clean revision.
- Sealed evaluation: remains prohibited.
- Runtime/private enable: remains conditional on a valid transformation-model evaluation.

## Integration notes

The transformation model and the image reader must now be scored separately:

- **Structured score to tablature**: accepts app-composed notes, note names, intervals, MusicXML, or independently approved score facts; evaluates the 21-feature arranger against held-out tab choices.
- **Image to structured score**: evaluates OMR/vision count, pitch, octave, key, and rhythm separately. It must not suppress a good arranger score simply because image recognition failed.
- **Lick movement learning**: evaluates captured tab states, control timing, slides, sustained transitions, chord endpoints, and reusable movement priors. It must not manufacture conventional-score targets where none are printed.

This separation is necessary to answer the user’s actual product goal: typed or composed notes can reach high transformation accuracy now, while image upload remains a separately measured reader feature.

## Risk assessment

Risk: medium.

The v8 rules are conservative, source-only, and discovery-backed. Their likely benefit is higher yield on simple score+tab lines without full-line VLM reconstruction. The remaining risk is that many lines contain movement-only states or connector notation and will still be withheld. That is correct; those lines need deterministic pitch/order mapping or a stronger execution reader, not threshold relaxation.

The licks validation contract remains incomplete until the separate tab-movement evaluator is implemented.

## Human decision needed

No.

The active goal already authorizes continued engineering, clean exact-model rebuilds, and validation evaluation. Model promotion and sealed-test execution remain gated.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-0249-20-validation-source-mode-and-ordered-projection-v8.md`

## Files that must not be staged

- Everything beneath `corpus-private/`.
- `docs/handoffs/task-completions/integration-status.md`.
- All unrelated historical handoffs and parked files.
- Private model artifacts, validation reports, source assets, derivatives, caches, split manifests, and sealed-test material.

## Recommended next lane

Lane 01 Repo Steward, then Lane 20.

## Commit readiness

Safe to commit.

## Suggested next step

Exact-path commit v8, rebuild the exact challenger from the new clean HEAD, replay both validation extractions only to repin lineage, run a five-line main v8 canary, and implement the tab-only licks evaluation contract instead of another licks score audit.
