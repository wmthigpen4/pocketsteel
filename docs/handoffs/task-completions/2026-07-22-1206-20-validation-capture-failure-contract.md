# Lane 20 — Validation Capture-Failure Contract

Date: 2026-07-22 12:06 America/Chicago

## Task summary

Corrected a validation-audit contract defect that presented incomplete machine score/tab extraction as candidate ground truth. Validation reviewers can now reject an entire line with one `capture_failed` decision when the event count, score note, fret, string, pedal, lever, or octave was missed. No event-by-event reconstruction or false tablature confirmation is required.

The scoring contract records these as recognition failures, excludes them from arranger-ranking evidence, and preserves the existing rule that validation ground truth never enters challenger training. Both current validation audit consoles were regenerated from their existing packets; the packet digests remained unchanged and the sealed test remained closed.

Implementation commit: `edf70968efb53f5919c232ca0c99a4b22e80342a`.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- This handoff.

Ignored private artifacts regenerated but not staged:

- Current validation-audit HTML for both authorized batches.
- Digest-versioned validation-audit HTML summaries for the existing packet digests.

No source image, page record, split manifest, extraction hypothesis, model artifact, embedding, validation submission, or sealed-test artifact was modified.

## Behavioral contract

- `capture_failed` is a valid complete-line validation outcome.
- It does not require a comment or confirmation that the machine tab matches the source.
- It increments `captureFailedLineCount` and remains in the denominator for recognition accuracy.
- It does not increment resolved-line, score-reader-correct, or exact-pitch-match counts.
- It cannot produce an arranger-ranking record.
- It remains `trainingEligible: false` and cannot enter accepted discovery decisions.
- Audit labels now distinguish machine-captured tab from ground truth and distinguish deterministic pitch calculation from source-reading accuracy.
- Obvious zero-count or severe score/tab count mismatches receive a prominent whole-line failure instruction.

## Tests and checks

- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py` — PASS, `164 passed`.
- `git diff --check` — PASS.
- Exact-path cached-diff check before implementation commit — PASS.
- Both current validation audit preparation commands — PASS.
- Both regenerated audit URLs returned HTTP `200`.
- Browser smoke — PASS for honest labels, obvious-incomplete warning, whole-line failure control, progress completion without tab confirmation, and preserved no-training copy.
- Both preparation summaries reported `sealedTestAccessed: false` and `validationGroundTruthMayTrain: false`.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8766/atb-20260716-training-278-semantic-v2/extraction/validation/review/validation-line-audit/validation-line-audit-console.html?v=4663b12e` and `http://127.0.0.1:8766/atb-20260716-licks-34/extraction/validation/review/validation-line-audit/validation-line-audit-console.html?v=aafa20b9`
- Cache-busted URL tested: same URLs; packet digest query strings are the cache busters
- Exact URL the user should use: the two URLs above
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8766`
- Expected backend port: `8766`
- Expected git HEAD: `edf70968efb53f5919c232ca0c99a4b22e80342a`
- Version endpoint: none for this private local review server
- Version endpoint result: not available
- If version endpoint missing, how version is inferred: exact implementation commit plus regenerated HTML containing the new capture-failure contract
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this private review server
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant
- Who should test this URL: both
- Do not test these URLs: protected preview and public production; this change is private Lane 20 review tooling
- Known caveats: the interactive licks smoke saved one unsubmitted `capture_failed` choice in local browser state; it did not create a validation receipt or submission

## Integration notes

The packet and validation-run digests did not change because the extracted evidence did not change. This avoids invalidating saved review work. The new decision is captured in the submission digest and the committed scorer contract.

Current aggregate audit state after regeneration:

- Main cohort: `28` validation pages, `57` reviewable lines, `3` automatic no-line failures, `0` machine-passing lines.
- Licks cohort: `3` validation pages, `6` reviewable lines, `0` automatic no-line failures, `0` machine-passing lines.

These figures explain why the existing UI was misleading: current validation extraction quality is below the threshold for an arranger-quality claim. They do not open or describe sealed-test membership.

## Risk assessment

Risk: **medium**. The change fixes evaluation honesty and reviewer burden, but it does not improve the underlying score/tab readers. Validation accuracy remains to be measured after complete receipts. Rollback is the implementation commit, but rollback would reintroduce false source-confirmation pressure and should not be used for active review.

## Human decision needed

No. The reviewer can continue both validation audits and use whole-line failure wherever capture is materially wrong.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-22-1206-20-validation-capture-failure-contract.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- Unrelated historical untracked handoffs
- Validation submissions, extracted page records, private audit HTML, model artifacts, and sealed-test material

## Recommended next lane

Lane 20: complete the two validation receipts using pass or whole-line failure decisions. Then score the exact frozen challenger once against those receipts, reporting recognition and arranger-ranking metrics separately without training from validation.

## Commit readiness

Safe to commit

## Suggested next step

`Lane 20: Continue the current main and licks validation audits. Treat materially incomplete score/tab capture as capture_failed without event-by-event repair. After both exact packet receipts exist, score the frozen challenger once, keep sealed test closed, and return the cohort-separated recognition and arranger-ranking report.`
