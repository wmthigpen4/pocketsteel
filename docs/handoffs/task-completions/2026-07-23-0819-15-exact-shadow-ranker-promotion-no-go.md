# Lane 15 — Exact Shadow Ranker Promotion No-Go

## Task summary

Implemented and independently checked the fail-closed trainer-to-runtime
boundary for the canonical 21-feature melody ranker, rebuilt the exact
complete-discovery challenger from committed adapter code, and repinned both
opened validation cohorts without opening the sealed test.

The exact challenger is **not approved for beta or stable promotion**. Its
learned weights are byte-identical to the selected configuration and its
discovery diagnostics meet the predeclared floors, but the held-out validation
records cannot satisfy the required independent runtime parity gate:

- 302 held-out decisions contain 1,208 candidate records;
- zero candidate records contain explicit previous and next runtime context;
- missing context was failed, not skipped;
- held-out feature parity, score parity, top-choice accuracy, top-three
  coverage, cohort accuracy, evidence-mode accuracy, and mechanical validity
  are therefore unmeasurable;
- score-image recognition remains incomplete and is reported separately below.

No weights were activated. Public runtime behavior remains
`deterministic-fallback-v1`, `rankerEnabled=false`. Beta and stable channels
remain null.

## Implementation lineage

- Adapter implementation commit:
  `8bd169864f1ad9c1d292de3bfc7d4e8cfa2201d3`
- Commit subject: `Add fail-closed shadow ranker loader`
- Canonical feature schema:
  `melody-ranker-features-v3-phrase-sequence`
- Adapter feature count: 21, in exact trainer order
- Adapter scoring order: previous/current/next, beginning at the second event
- Phrase-end behavior: outgoing features zero-filled
- Tie behavior: conservative; an equal-scoring alternative is not a strict
  top-choice success
- Trained style families:
  - `chord_melody`
  - `harmonized`
  - `lever_driven`
  - `single_note_run`
- Unsupported product styles remain deterministic:
  Best Fit, Singing Steel, and Pocket Playing
- Hard pitch, register, harmony, and mechanical constraints remain absolute
- Artifact loader mode: sanitized, exact-ID, exact-digest, fail-closed,
  shadow-only
- Rollback/failure behavior: any digest, schema, feature-order, style-row,
  numeric-finiteness, privacy, or forbidden-field mismatch returns
  `deterministic-fallback-v1`

## Exact model and artifact

- Exact challenger: `at-e00734bee5dea6fc`
- Status: `challenger`
- Promotion eligible: false
- Artifact SHA-256:
  `1b0aa97b2f3ac0c056619f7065039f271ceab36a1f0d681400662bb1fa0df1ba`
- Parent model: `at-89e3f3cb4ff038ce`
- Authoritative dataset: `atd-b7f27284748b713c`
- Authoritative dataset digest:
  `b7f27284748b713c0fbf64c6a2a6efd279a0436ef6ae96aaa280dadf17623fe4`
- Discovery seed: `ats-566f8d336c230bb0`
- Rules-code digest:
  `623ab0391609bd465894f957b45dac6457faa25651801f1bcaea3d8accceb8c3`
- Model code revision:
  `8bd169864f1ad9c1d292de3bfc7d4e8cfa2201d3`
- Training examples: 702
- Training configuration: 32 epochs, learning rate 0.03, averaged weights,
  base-weight ratio 0.35
- Copendent-neutral artifact: true
- Source content in artifact: false
- Profile snapshots in artifact: false

The plan named `at-ca3af91682513311` as the rebuild parent. Registry lineage
shows that model and the prior exact challenger were both derived from the
actual canonical parent `at-89e3f3cb4ff038ce`. Rebuilding from that canonical
parent reproduced the selected learned rows exactly.

## Learned-weight identity receipt

Canonical JSON SHA-256 of `weightsByStyle`, without emitting weight values:

- selected `at-ca3af91682513311`:
  `91b3cc25c5c60c6d18c5a8f808b9e63f4b3fb1c0e43e6f5e1eac251ea23b970c`
- prior exact `at-b8696bff6c641aa9`:
  `91b3cc25c5c60c6d18c5a8f808b9e63f4b3fb1c0e43e6f5e1eac251ea23b970c`
- rebuilt exact `at-e00734bee5dea6fc`:
  `91b3cc25c5c60c6d18c5a8f808b9e63f4b3fb1c0e43e6f5e1eac251ea23b970c`

All three artifacts contain 21 ordered features, four style rows, and 702
training examples. The exact sanitized artifact loads successfully as
shadow-eligible while still returning `rankerEnabled=false`; public metadata
simultaneously remains the deterministic fallback.

An initial literal-parent rebuild, `at-6f1d0365bdd89c9f`, was excluded from
consideration because it did not reproduce the selected weights and did not
carry an exact code revision. It remains private, inactive, and unpromoted.

## Discovery diagnostics

- Shadow report:
  `c0fdd6d0379e93478366208b7d541d35381d4e5ff1402073dab8f3bc2bc003ea`
- Decisions scored: 1,060
- Source agreements: 964
- Source agreement rate: 0.909434
- Expert-acceptable decisions: 966
- Expert-acceptable rate: 0.911321
- Known preference failures: 1
- Reviewed preferences: 16
- Training preferences: 6
- Co-valid preferences: 10
- Review-ready lines: 0
- Selected review lines: 0
- Validation accessed by discovery shadow: false
- Sealed test accessed: false
- Accuracy claim allowed: false

These diagnostics meet the rebuild requirements but are discovery evidence,
not held-out accuracy.

## Independent held-out runtime parity

The independent check inspected the exact repinned validation pages and did
not use the trainer's stored aggregate as validation truth.

| Cohort | Decisions | Candidates | Candidates with explicit previous context | Candidates with explicit next context |
|---|---:|---:|---:|---:|
| Licks | 30 | 120 | 0 | 0 |
| Main | 272 | 1,088 | 0 | 0 |
| Total | 302 | 1,208 | 0 | 0 |

The runtime adapter requires previous/current/next context to reconstruct the
exact second-order vector. Because context is absent for every held-out
candidate, the required parity result is:

- feature parity coverage: 0 of 1,208
- feature parity requirement: 100%
- score parity coverage: 0 of 1,208
- score parity requirement: 100%
- missing-context disposition: fail, never skip
- independent ranker gate: not passed

Consequently, the following gates are **unmeasurable**, not zero and not
passed:

- overall top-choice accuracy strictly greater than 95%
- top-three coverage at least 99%
- each cohort top-choice accuracy at least 90%, minimum 10 decisions
- each evidence mode top-choice accuracy at least 90%, minimum 20 decisions
- approved-source mechanical validity 100%
- predicted-top mechanical validity 100%

Runtime/trainer golden fixtures do provide exact 21-feature and score parity
for complete synthetic triples, including sustain, repick, cadence, direction
reversal/continuation, and phrase-end zero filling. Those fixtures prove the
adapter contract; they do not replace held-out parity.

## Score-image recognition, reported separately

### Main score/tab cohort

- Consensus report:
  `84cf8d667c8b6f24309fbe567b3a8e2cc3f8b2866eb79837a86e73d00726928f`
- Validation run:
  `0e012f3d899c9185e30232e36fc9c1ec1b12aadc1323e236868227f22f40b696`
- Validation pages: 28
- Lines: 57
- Complete machine candidates: 1
- Withheld incomplete lines: 56
- Event columns: 889
- Reconstructed events: 396
- Event-column reconstruction: 44.5444%
- Unresolved cells: 1,023
- Non-activated line-audit readiness:
  `e5598df7b190fbfa7a0c2580a96f21d287722e660a140c4d6b3d31e86700a803`
- Review-ready lines: 1
- Blocked lines: 56

### Licks cohort

- Consensus report:
  `6f1c70d7c23b59f94d9056cafe4c767b3a8e2e835ae15b609d12f383c8b01c0c`
- Validation run:
  `8b206bab147c724147652d35040165dfad778dc5328bb8ef4a7b8f269be09da0`
- Validation pages: 3
- Lines: 6
- Complete machine candidates: 4
- Withheld incomplete lines: 2
- Event columns: 85
- Reconstructed events: 81
- Event-column reconstruction: 95.2941%
- Unresolved cells: 6
- Non-activated line-audit readiness:
  `f290c75e5425b520016958df4b7f0e816809ec4028d0248040dc1cfa665dff23`
- Review-ready lines: 1
- Blocked lines: 5

Both consensus reports record `humanTruthUsed=false`,
`validationMayTrain=false`, and `sealedTestAccessed=false`. Recognition
failures do not count as ranker errors, but score-image runtime support remains
disabled.

## Promotion decision

**NO-GO.**

- Exact beta model: null
- Exact stable model: null
- Beta channel: null
- Stable channel: null
- Deterministic runtime active: yes
- Learned runtime ranker active: no
- Rules freeze allowed: no
- Sealed test allowed: no
- Sealed test opened in this task: no
- Public/API/UI behavior changed: no
- Deployment or protected-preview action: none

The validation cohort was previously opened, so even a later complete
evaluation can support only a disclosed beta decision, not a fresh unbiased
accuracy claim. The unopened one-shot sealed test remains reserved for a
separate explicit decision.

## Files changed

Implementation commit:

- `pocketsteel/amazing_tablature_model.py`
- `pocketsteel/melody_arranger.py`
- `tests/test_amazing_tablature_model.py`
- `tests/test_melody_arranger_decision_fixtures.py`
- `docs/handoffs/task-completions/2026-07-23-0733-05-shadow-ranker-artifact-loader.md`

This closeout adds:

- `docs/handoffs/task-completions/2026-07-23-0819-15-exact-shadow-ranker-promotion-no-go.md`

No files were deleted. Private models, extractions, caches, readiness receipts,
and metrics remain ignored under `corpus-private/melody-decisions/`.

## Tests and checks

- Focused loader/arranger tests: 21 passed
- Focused ranker, arranger, input-parity, training, sealed-contract,
  copedent-transfer, and melody suites:
  `116 passed in 13.02s`
- Full test suite:
  `1422 passed in 88.73s`
- Python compile checks: passed
- `git diff --check`: passed before the implementation commit
- `git diff --cached --check`: passed before the implementation commit
- Exact main validation extraction: 28 pages, 0 page failures
- Exact licks validation extraction: 3 pages, 0 page failures
- Both independent consensus passes: completed
- Both non-activated line-audit preflights: blocked before human review
- Browser/protected-preview smoke: intentionally not run because activation,
  deployment, HTTP, UI, and public behavior were out of scope

## Integration notes

- Do not wire `at-e00734bee5dea6fc` into runtime.
- Do not promote `at-e00734bee5dea6fc`.
- Do not run the sealed test from this packet.
- Do not treat discovery diagnostics or synthetic adapter fixtures as
  held-out ranker accuracy.
- Do not treat score-image recognition as normalized-event ranker quality.
- Do not synthesize mappings for unsupported product styles.
- A later evaluation must provide explicit previous/current/next candidate
  context for every held-out record and rerun the independent parity and
  ranking gates from scratch.

## Risk assessment

Risk is low for public behavior because learned ranking remains disabled and
all artifact failures fall back deterministically.

Promotion risk is high because the exact held-out parity and accuracy gates
are unmeasurable. The primary unresolved risks are attack/sustain semantic
drift in real held-out sequences, second-order path-scoring disagreement on
real candidates, incomplete score-image recognition, and overstating evidence
from an already opened validation cohort.

Rollback is immediate and already active:
`deterministic-fallback-v1`, `rankerEnabled=false`, beta/stable null.

## Human decision needed

Yes, but not for promotion.

Promotion approval is not supportable from this evidence. A separate product
decision is needed before expanding scope to create a context-complete,
structured-input blind validation set or to continue discovery-only
score-image recognition remediation. Either path must keep validation
non-training and the sealed test closed.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-23-0819-15-exact-shadow-ranker-promotion-no-go.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- unrelated historical handoffs
- existing dirty extraction, glyph-decoder, training, CLI, and test work
- private models, registries, validation reports, reader caches, source images,
  weights, or derived private artifacts

## Recommended next lane

Lane 18, only after explicit approval, should define a context-complete
structured-input blind comparison contract. Lane 15 should then independently
score the exact immutable candidate triples. Lane 20 remains responsible for
private candidate preparation; Lane 05 runtime integration remains blocked.

## Commit readiness

Safe to commit

## Suggested next step

`Lane 18: Design a private context-complete structured-input blind comparison for the exact deterministic and challenger candidate triples, keep validation non-training, and keep the sealed test closed.`
