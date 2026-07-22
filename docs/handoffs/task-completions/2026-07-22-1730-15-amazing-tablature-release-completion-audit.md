# Amazing Tablature release goal completion audit

## Task summary

Audited the active bounded release goal against current repository, private-registry, discovery-shadow, test, local-browser, and protected-preview evidence. The training and frontend requirements are complete. Exact protected-preview activation and authenticated smoke remain incomplete because macOS administrator authentication is required.

No validation imagery, validation ground truth, sealed-test membership, sealed-test imagery, or sealed-test ground truth was opened during this audit.

## Requirement-by-requirement evidence

| Requirement | Evidence | Result |
| --- | --- | --- |
| Use only authoritative 278 main + 34 licks batches | Active dataset `atd-b7f27284748b713c` contains only `atb-20260716-training-278-semantic-v2` and `atb-20260716-licks-34`; counts are 278 and 34 | PASS |
| Exclude superseded 51 images | `atb-20260714-photos-1-001` is `superseded`; model `at-44c59f08724d501e` is `retired`, `historical_superseded`, and ineligible for comparison | PASS |
| Preserve held-out integrity | Both partitions report `sealed_unopened`, `membershipExposedInStatus=false`; current canonical readiness and shadow report report `validationAccessed=false`, `sealedTestAccessed=false` | PASS |
| Limit challenger search | One existing baseline plus two distinct new configurations were compared: conservative `at-7c4532776b95c51a` and averaged `at-1ccbd05b5b157759`; later artifacts are exact selected-configuration lineage rebuilds, not additional configuration evaluations | PASS |
| Respect rights/copedents | Both active batches are approved for private extraction/evaluation, model training, and runtime product use; rights digests and exact source-copedent revisions are pinned | PASS |
| Preserve preference/no-rereview accounting | Canonical readiness reports exact expected/actual `16 reviewed`, `6 training`, `10 co-valid`; final shadow suppresses four prior-reviewed lines, including two with current disagreements, and selects zero review lines | PASS |
| Prepare expert checkpoint only if structurally complete and necessary | Validation structural preflight blocks 56/57 main lines and 5/6 licks lines; no 24-comparison packet was generated and no additional user repair work was requested | PASS (checkpoint correctly omitted) |
| Promote only if fixed gates pass | `at-ca3af91682513311` remains `challenger`, `promotionEligible=false`; beta and stable channels are null | PASS |
| Otherwise use deterministic fallback | Runtime policy is `deterministic-fallback-v1`, `rankerEnabled=false`, `scoreImageRecognitionIncluded=false`, with separate review required | PASS |
| Integrate selected engine into Melody Studio | Result UI reads runtime metadata and displays the verified E9 rules/future trained-ranker method; imported score images are identified as review-first | PASS |
| Tests and local browser verification | `1375 passed`; JavaScript syntax passed; local same-origin browser smoke rendered four synchronized score/fretboard/tab events and the deterministic engine status | PASS |
| Exact-path commits | Runtime/training/frontend changes are committed through `4b443c7`; deployment-blocker handoff is committed at `107829b`; unrelated dirty coordination/history files remain parked | PASS |
| Protected-preview activation and browser smoke | Exact detached release `4b443c7` passed preflight, but activation required the macOS administrator password. Live preview is healthy but stale at `3cb63c3` | INCOMPLETE — external administrator action required |

The earlier Lane 20 handoff documented an accidental repo-wide text traversal that displayed only generic source-copedent metadata from sealed manifest paths. It disclosed no membership, images, annotations, truth, predictions, or failures. The current status continues to report the sealed cohorts unopened; the event remains an audit note rather than evidence of holdout-content leakage.

## Final discovery challenger evidence

- Model ID: `at-ca3af91682513311`
- Artifact SHA-256: `7a815d7cd7a8d8a7ffc5cb48c5cd2ad950ee5c72c856e505d3ec87bb0cdbcbf1`
- Complete-discovery examples: `702`
- Feature schema: `melody-ranker-features-v3-phrase-sequence`
- Discovery decisions: `1060`
- Source agreements: `964` (`0.909434`)
- Expert-acceptable decisions: `966` (`0.911321`)
- Known preference failures: `1`
- Selected review lines: `0`
- Validation accessed: `false`
- Sealed test accessed: `false`
- Accuracy claim allowed: `false`

These are discovery diagnostics, not held-out accuracy and not a production model claim.

## Files changed

- `docs/handoffs/task-completions/2026-07-22-1730-15-amazing-tablature-release-completion-audit.md`

Private discovery-shadow metadata was refreshed beneath ignored `corpus-private/melody-decisions/`. It must not be staged.

## Tests and checks

- `.venv/bin/python scripts/amazing_tablature.py status` — active authoritative dataset and channels audited.
- `batch-status` for both active cohorts — counts, split status, rights, and copedents audited.
- `canonical-readiness --base-model-id at-ca3af91682513311` — no discovery blocker, exact preference accounting, no held-out access.
- `shadow-test-discovery at-ca3af91682513311 --max-review-lines 1` — final lineage report regenerated; zero review lines selected; no held-out access.
- `curl` against loopback live/ready/version — live and ready; version remains stale `3cb63c3`.
- Previously completed full suite — `1375 passed`.
- Previously completed local browser smoke — passed.

## Integration notes

The exact detached release at `~/.steel-rag/releases/4b443c7` is ready. The only remaining objective item is the canonical administrator-authorized activation followed by health/version and authenticated browser smoke. `docs/handoffs/task-completions/integration-status.md` remains pre-existing dirty coordination work and was not edited.

## Risk assessment

Low release risk, medium future-model risk. Structured score/notes input is safe on deterministic validation. Score-image recognition is not production-ready and the trained discovery challenger must remain disabled until a canonical runtime feature adapter and valid independent held-out comparison exist.

## Human decision needed

Yes, operational only: enter the macOS administrator password when running the exact activation command in `2026-07-22-1728-12-amazing-tablature-preview-activation-blocker.md`. No musical validation or product decision is required.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-22-1730-15-amazing-tablature-release-completion-audit.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated historical untracked handoffs
- Everything under `corpus-private/`
- Raw images, validation data, sealed-test data, embeddings, vector stores, credentials, environment files, logs, and generated reports

## Recommended next lane

Lane 12 Self-Hosted Deployment immediately after administrator-authorized activation.

## Commit readiness

Safe to commit

## Suggested next step

Activate exact release `4b443c7`, then have Lane 12 verify `/health/live`, `/health/ready`, `/api/version`, root, the home UI, and authenticated Melody Studio at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=arrangement-engine-4b443c7-20260722`.
