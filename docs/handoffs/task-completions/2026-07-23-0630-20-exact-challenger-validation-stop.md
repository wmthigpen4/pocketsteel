# Lane 20 — Exact Challenger Validation Stop Report

## Task summary

Rebuilt the discovery-only Amazing Tablature artifacts from clean HEAD, verified exact trainer/runtime lineage and no-rereview accounting, repinned both validation cohorts, and completed independent tab-cell consensus without opening sealed-test data.

The validation result is a hard recognition stop. The exact challenger cannot be scored honestly against the main image validation cohort because the image-to-structured-tab comparison is incomplete. The challenger was not promoted or enabled.

## Exact lineage

- Git HEAD: `2c5e1b6a693bcd34bd1ea53db596bc7c97567386`
- Challenger: `at-b8696bff6c641aa9`
- Challenger artifact SHA-256: `331182523c78ec5af648ad6616401968736235d41089bcab2eb397dcc7680aba`
- Discovery seed: `ats-77c4d1cc90e0b51b`
- Training examples: 702
- Feature count: 21 exact trainer/runtime features
- Reviewed preferences: 16
- Training preferences: 6
- Co-validation preferences: 10
- Promotion eligible: false

## Discovery shadow and no-rereview accounting

- Shadow report digest: `5a061dcc1917d9a0ed8b39cef5089cc8eb2d55fb557fe4e5df7f865db5d537f3`
- Pages considered: 173
- Decisions scored: 1,060
- Review-ready lines: 0
- Selected review lines: 0
- Previously reviewed lines suppressed: 4
- Suppressed lines with a current disagreement: 2
- Validation accessed by shadow: false
- Sealed test accessed: false
- Shadow code revision: exact HEAD `2c5e1b6a693bcd34bd1ea53db596bc7c97567386`

## Discovery-only recognition aids

### Main glyph decoder

- Decoder: `atg-c0fe5b851780f9e9`
- Training examples: 1,245
- Content-unit folds: 17
- Selected confidence: 0.80
- Grouped discovery CV precision: 95.2542%
- Grouped discovery CV coverage: 23.6948%
- Automation eligible: true
- Validation used for training: false
- Sealed used for training: false

### Licks transition decoder

- Decoder: `atx-78e4839c72e7a5ed`
- Grouped discovery CV precision: 100%
- Grouped discovery CV recall: 45.5882%
- False positives: 0
- Automation eligible: true
- Validation used for training: false
- Sealed used for training: false

The main transition decoder and licks glyph decoder remained diagnostic-only.

## Validation results

### Main score/tab cohort

- Report digest: `55c534b340e1e934d8e8b91872ac5d4c9af258c593c374e2239e7e921118b3b3`
- Lines: 57
- Complete machine candidates: 1
- Withheld incomplete lines: 56
- Candidate event columns: 900
- Reconstructed events: 511
- Event-column reconstruction: 56.7778%
- Unresolved candidate cells: 889
- Complete line: `input-0098`, system 2, 10 events
- Human truth used: false
- Validation may train: false
- Sealed test accessed: false

### Licks cohort

- Report digest: `6e6745e439f6fc719ad620cdb32942a70d3f2f297d3254ff3f124bf5b425b9de`
- Lines: 6
- Complete machine candidates: 4
- Withheld incomplete lines: 2
- Candidate event columns: 85
- Reconstructed events: 81
- Event-column reconstruction: 95.2941%
- Unresolved candidate cells: 6
- Source-specific movement events classified: 17
- The known 14-event validation line is complete
- Human truth used: false
- Validation may train: false
- Sealed test accessed: false

## Decision

The fixed validation gates do not pass. Specifically:

- main complete-line rate is 1.7544%, not sufficient for scoring;
- main event-column reconstruction is 56.7778%, far below the 98% tab confirmation target;
- conventional score recognition still lacks complete independent truth;
- therefore challenger preference accuracy cannot be measured without conflating image-recognition failures with arrangement quality.

The exact challenger remains private and disabled. The sealed test remains closed.

## Recommended product pivot

Do not spend more user time auditing hundreds of image cells before testing the product value that matters most.

The recommended next slice is a structured-input blind comparison:

1. keep image upload experimental and separate;
2. use typed note names, intervals, or in-app composed single-note melodies, where score OCR is not involved;
3. generate deterministic and learned candidate arrangements from the same normalized events;
4. enforce mechanical and sounding-pitch validity automatically;
5. present a compact blind A/B choice for 25 short, original or authorized phrases;
6. record arrangement preference separately from image-recognition metrics;
7. require the predeclared >95% ranker gate before private enablement;
8. return to image recognition as an independent workstream using discovery-only evidence.

This directly tests the desired product—adding slides, harmonies, grips, and voice leading to known notes—without letting weak photography/OCR block or falsely validate the arrangement engine.

## Files changed

No runtime files changed after HEAD `2c5e1b6`. This handoff is the only new repository file in this task closeout. All models, caches, validation candidates, and reports remain private and ignored.

## Tests and checks

- focused contact-consensus tests: 4 passed
- glyph/consensus focused tests: 7 passed
- full `.venv/bin/pytest -q`: 1,400 passed
- Python compile checks: passed
- `git diff --check`: passed before the exact commits
- both validation extraction runs: 0 failed pages
- exact discovery shadow: passed lineage and no-rereview checks

## Integration notes

- Do not wire `at-b8696bff6c641aa9` into runtime.
- Do not run sealed test.
- Do not describe the main validation result as model accuracy; it is an input-recognition failure.
- Licks recognition is materially stronger but is not enough to validate the score-to-tab arrangement ranker.
- A structured-input evaluation can proceed without OCR, OMR, embeddings, scraping, deployment, auth, or source publication.

## Risk assessment

High if the image result is treated as arrangement accuracy or the challenger is enabled now. Low for the recommended structured-input blind comparison because inputs are normalized, mechanics are deterministic, and the learned ranker remains feature-gated/private.

## Human decision needed

Yes. Approve the recommended structured-input blind comparison as the next validation path, or explicitly choose to continue discovery-only image-recognition engineering first.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-23-0630-20-exact-challenger-validation-stop.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- unrelated historical handoffs
- private models, registries, validation reports, reader caches, source images, and derivatives

## Recommended next lane

Lane 18 defines the compact structured-input blind-comparison contract, then Lane 20 prepares exact private candidates and Lane 15 owns independent scoring. Runtime integration remains with Lanes 05/06 only after the fixed gate passes.

## Commit readiness

Safe to commit

## Suggested next step

`Approve a private 25-phrase structured-input blind comparison of deterministic versus challenger arrangements, with image upload explicitly out of scope and sealed test still closed.`
