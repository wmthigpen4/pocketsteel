# Lane 20 — Validation structural preflight stop gate

## Task summary

The user reported that the active main and licks validation audits exposed blank machine score captures, unequal event counts across score/tab representations, and incomplete ten-string tablature. This was a smoke-blocking Lane 20 bug.

Completed:

- Added fail-closed validation preflight `validation-line-structural-preflight-v1`.
- A validation audit is not published unless every detected line has nonblank score events, nonblank tab movements, equal score/tab event counts, complete ordered comparison columns, complete string/fret payloads, a captured key signature, mechanically valid tab, and no blocking reader issue.
- Withdrew both active validation audits and replaced their canonical pages with static “Not ready for human review” pages that contain no review or submit controls.
- Rejected legacy/incomplete validation packets at both submission and scoring boundaries.
- Kept validation decisions prohibited from challenger training.
- Used strict ordered columns for any future validation rendering so score, calculated tab pitch, event comparison, and ten-string tablature share one cardinality.

Intentionally not changed:

- No validation facts were manually reconstructed.
- No challenger was retrained.
- No validation review was converted to training evidence.
- No sealed-test imagery, membership, ground truth, or failures were opened or used.
- No raw source image, split, embedding, vector store, runtime product surface, auth, deployment, or Cloudflare setting changed.

## Current preflight result

- Main validation: 57 detected lines, 56 blocked, 1 structurally ready, and 3 pages with no paired complete line. Audit publication is false. Readiness digest: `2dae98c73d5177f937c91b41e9c222da16623a8a4297acfb69a051bc49ae6e26`.
- Licks validation: 6 detected lines, 5 blocked, 1 structurally ready, and 0 no-line pages. Audit publication is false. Readiness digest: `b2f2e995aa20fa255573c26df226cdb274680d8e9c00a872eaf909235a3a9ffd`.
- Both generated readiness artifacts report `sealedTestAccessed: false` and `validationGroundTruthMayTrain: false`.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
- `pocketsteel/amazing_tablature_training.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- This handoff.

Generated private artifacts changed beneath ignored `corpus-private/melody-decisions/`:

- Main and licks validation readiness JSON.
- Main and licks static canonical not-ready pages.

No files were deleted.

## Tests and checks

- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py` — **167 passed**.
- `git diff --check` on the four implementation/test files — **passed**.
- Re-ran `prepare-validation-line-audit` for both batches — both returned `blocked_before_human_review` and `auditPublished: false`.
- HTTP smoke on both canonical pages — both contained the withdrawn/not-ready copy and did not contain the submit control.
- In-app browser smoke on the main and licks canonical pages — both displayed the static withdrawn/not-ready state.
- Implementation commit: `af316908112729ad04b530be755d5c70bfa79f0e`.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8766/atb-20260716-training-278-semantic-v2/extraction/validation/review/validation-line-audit/validation-line-audit-console.html?v=2dae98c7` and `http://127.0.0.1:8766/atb-20260716-licks-34/extraction/validation/review/validation-line-audit/validation-line-audit-console.html?v=b2f2e995`
- Cache-busted URL tested: same URLs above
- Exact URL the user should use: none; there is currently no validation audit to review
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8766`
- Expected backend port: `8766`
- Expected git HEAD: `af316908112729ad04b530be755d5c70bfa79f0e`
- Version endpoint: not applicable to the private review server
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: committed implementation hash plus readiness digests
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: no; only the private review paths are in scope
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant
- Who should test this URL: Codex
- Do not test these URLs: no human review URL should be issued until every validation line passes preflight
- Known caveats: the private validation server must remain running for local status pages to resolve

## Integration notes

The preflight is a publication boundary, not an accuracy claim. It prevents review burden and invalid metrics; it does not repair the score or tab readers. The next Lane 20 work should be offline remediation and automatic replay. No reviewer packet should be produced until the full candidate set passes structural preflight and a confidence report is available.

### Sealed-test access incident

During diagnosis, a repo-wide text search unintentionally traversed two sealed manifest files and displayed only generic `sourceCopedentId` metadata. It did **not** display or use asset names, membership, images, ground truth, annotations, predictions, or failure details. Pipeline commands did not open sealed test data and still report `sealedTestAccessed: false`. This is nevertheless a protocol-level path-access incident and should be recorded for Lane 15. The unbiased holdout composition was not disclosed by the output observed.

## Risk assessment

**Medium.** The immediate human-review failure is contained, but current machine extraction is structurally far below validation readiness. The sealed-test path-access incident above requires independent Lane 15 acknowledgment even though no holdout membership or truth was revealed.

Rollback: revert commit `af316908112729ad04b530be755d5c70bfa79f0e`; doing so is not recommended because it would restore publication of incomplete audits.

## Human decision needed

No decision is needed to keep validation audits withdrawn. Lane 15 should independently record whether the limited generic sealed-manifest metadata access requires any action beyond an incident note; it did not reveal test composition or ground truth.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-22-1305-20-validation-structural-preflight-stop-gate.md`

The implementation and tests were already committed exactly in `af316908112729ad04b530be755d5c70bfa79f0e`.

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing parked change)
- All unrelated untracked historical handoffs
- Everything beneath `corpus-private/`
- Raw images, manifests, review submissions, readiness artifacts, extraction outputs, models, embeddings, and vector stores

## Recommended next lane

Lane 20 for offline reader remediation and full structural replay; Lane 15 only for the independent sealed-access incident note and later validation acceptance review.

## Commit readiness

Safe to commit

## Suggested next step

Lane 20: repair the score and tab capture pipeline offline using discovery evidence and existing correction-derived regressions, rerun the structural preflight across both validation batches, and publish nothing until every line has complete equal-cardinality representations and the automatic confidence report passes.
