# Beat-cell Stage-2 R4 split-publication pre-execution supersession

Date: 2026-08-21

## Outcome

Independent integrated release review rejected the committed amended-R4
authority and its prospective implementation handoff before any amended-R4
post-freeze preflight, official command, admitted official-data read, output,
publication, or one-shot consumption.

The Stage-A direct-in-memory complete-tree publisher itself passed its focused,
broad, and adversarial implementation review. The blocker is instead an
authority-scope mismatch: one globally scoped `outputPaths.publication`
string was changed to the Stage-A complete-tree v2 policy even though Stage B,
selector, and readiness publish individual JSON artifacts with the distinct
single-JSON v1 protocol.

This is a transparent additive pre-execution R4 authority correction, not a
new R5 cycle. The same five R4 destination paths and the same frozen data,
math, reconciliation, Stage-A, Stage-B, selector, readiness, protected-access,
and one-shot semantics remain in force. R4 is unconsumed.

## Superseded authority and handoff checkpoint

The authority rejected by this audit remains immutable as historical evidence
at commit:

`d3a2616f12862f7c8d9a7835a1911da19056512f`

It is bound by:

- path:
  `docs/handoffs/task-completions/2026-08-21-0932-20-beat-cell-stage2-r4-amended-recovery-preregistration.json`;
- raw-file SHA-256:
  `ef44670f6378a0cf2c7d2e7c77b85b645e5ffd95288ebbb937879fe32c1bfafd`;
- canonical-object SHA-256:
  `4372283a6ce9dbf7d8ea955545e5cd9e32971a89e4ac1f8da2cc4a8702b88e30`;
- output-path projection SHA-256:
  `07023d0c85ad0cab3614b8d2e0763e2050d8fb3724a52c3a0323a763cfdb9686`;
- feature-math projection SHA-256:
  `bb255a0c61dd99577c07e6caeaed86e215e13cbe8ddc63a1bed1d24351a4c379`;
- readiness projection SHA-256:
  `81f58801c789370e06104203117331b8e2d487e3055d14b7a1831e1c22b73b18`;
- Stage-A implementation module SHA-256:
  `bb73bab25cc609fcfaccea9a4f0f831add890a7156da07a48a5aa3d044b7ea6d`;
- singular rejected publication value:
  `canonical-new-path-only-retained-nofollow-dirfd-input-recheck-failure-atomic-direct-in-memory-exact-rendered-inventory-owned-complete-tree-v2`.

That authority is superseded and explicitly non-authorizing. It must not be
used for an R4 preflight or official invocation.

The prospective final implementation handoff drafted after the direct-memory
QA is retained unchanged at:

- path:
  `docs/handoffs/task-completions/2026-08-21-0949-20-beat-cell-stage2-r4-amended-implementation.md`;
- raw-file SHA-256:
  `c410de83c1d590b2b69c703af18c3ce519352ead71b4c989e04496920ac6e94e`.

It is rejected, stale, uncommitted, and must not be staged. Its `163 passed`
focused and `829 passed`, `4 skipped`, `3 deselected` broad receipts remain
factual for the inspected direct-memory implementation, but they did not
cover the global split-publication authority invariant and authorize no
preflight or execution.

The earlier P1 finding and first transparent R4 amendment remain historical
and are bound by:

- rejection/supersession receipt path:
  `docs/handoffs/task-completions/2026-08-21-0931-20-beat-cell-stage2-r4-implementation-audit-rejection.md`;
- receipt raw-file SHA-256:
  `0b2ed9abb2ba05569685919ee58b16b11bfbd92e6ed5d743d10aa3456b10354f`;
- rejected `0919` implementation handoff raw-file SHA-256:
  `ec2d9baf9e9677f838eb7d4eee7d63012dca5681888d26e3575227fa66acbd8f`;
- original R4 authority commit:
  `543ba2ade048b8408db0bf42e500bca77b370613`.

The consumed R3 failure receipt remains unchanged at
`docs/handoffs/task-completions/2026-08-21-0857-20-beat-cell-stage2-r3-failure.md`
with raw-file SHA-256
`362a17d23a09a2cbed58a050c3495529dfdde81a61a68ac960a7ae0ecaabacee`.
R1, R2, and R3 remain closed and may not be retried.

## Exact integrated-audit finding

The original Stage-2 preregistration states that every publication is
new-path-only, canonical, retained-directory-fd based, source-rechecked, and
failure-atomic. The machine authority represented that global rule with the
single `outputPaths.publication` value shared by all five destinations.

The superseded amended authority replaced that singular value with a protocol
that additionally asserts direct in-memory exact-rendered-inventory and an
owned complete-tree. Those additional properties are true for the corrected
Stage-A feature set only:

- Stage A freezes the complete validated manifest/summary inventory to exact
  in-memory bytes and publishes one owned hidden directory tree by a single
  no-replace rename;
- Stage B publishes its one examples JSON through
  `_publish_new_json_with_precommit` and the single-JSON v1 link protocol;
- the selector publishes its one artifact JSON through the single-JSON v1
  protocol;
- readiness emits and validates `PUBLICATION_MODE` as the single-JSON v1
  protocol for its one report JSON.

The prospective implementation consumed the singular authority field only in
the Stage-A output preflight. Stage B, selector, and readiness neither
consumed that v2 value nor could truthfully claim its complete-tree behavior.
Changing their publication literals to v2 would falsely attest a complete-
tree protocol they do not perform; leaving them at v1 while retaining one
global v2 authority value makes the authority false and leaves three official
phases without an exact authority-mode binding.

This is a release-blocking P1 authority/provenance defect. No official
publication was attempted, so no official artifact was exposed or corrupted.

## Frozen split-publication policy

The replacement authority must use this exact object at
`outputPaths.publication`:

```json
{
  "schemaVersion": "chord_runtime_beat_cell_stage2_publication_policy_v2",
  "featureSet": "canonical-new-path-only-retained-nofollow-dirfd-input-recheck-failure-atomic-direct-in-memory-exact-rendered-inventory-owned-complete-tree-v2",
  "singleJson": "canonical-new-path-only-retained-nofollow-dirfd-input-recheck-failure-atomic-v1"
}
```

The meanings are disjoint and exact:

- `featureSet` governs only the Stage-A manifest plus all summaries published
  as one owned complete directory tree;
- `singleJson` governs the Stage-B examples artifact, selector artifact, and
  readiness report, each published as one canonical new-path-only JSON file.

Before any source or output access, the corrected implementation must validate
the exact publication object key set and schema, then bind:

- Stage A to `publication.featureSet`;
- Stage B to `publication.singleJson`;
- the selector CLI to `publication.singleJson`;
- readiness to `publication.singleJson`.

A missing, extra, stale, scalar, wrong-schema, swapped, cross-bound, or altered
publication field must fail before input or output access. Tests must cover
every phase and retain the existing direct-memory inventory, inode,
concurrency, and ownership-cleanup adversarial surface.

The Stage-A and Stage-B implementations share
`steel_guitar_rag/chord_reader/beat_cell_examples.py`; its final post-fix hash
is
`0bd8dde059c29a10838e31b08f2987d94bb358b140a0b0fcba7c899364f29dc5`
and is sealed by the replacement feature-math source binding. Binding
`singleJson` in readiness changes
`steel_guitar_rag/chord_reader/beat_cell_readiness.py`, whose final bytes and
effective rubric must be pinned in the implementation handoff.
It does not change the authority's `readiness.sourceModule`, which is the
unchanged `steel_guitar_rag/chord_reader/selector_readiness.py` at SHA-256
`464c918d9e579ce98ddce7a98f2ef35fe58e57dce2cff9b0d77af1548335b291`.
The selector CLI implementation bytes must likewise be pinned in the final
implementation handoff; they are not the `selectorCore.sourceModule` named by
the machine projection and therefore do not change that frozen selector-core
source binding.

## Zero-consumption and access proof

At this pre-execution supersession boundary:

- authorized R4 post-freeze preflight sweeps: `0`;
- official R4 production-builder calls over admitted data: `0`;
- official R4 CLI invocations: `0`;
- official R4 runner invocations: `0`;
- official Stage1 report JSON parses: `0`;
- official Stage1 outcome-object accesses: `0`;
- official group/reference/dataset object accesses: `0`;
- official R4 source-admission or feature-extraction reads: `0`;
- official R4 output or publication calls: `0`;
- published R4 feature summaries or manifests: `0`;
- Stage-B examples built from official output: `0`;
- selector candidate fits: `0`;
- readiness evaluations or reproduction fits: `0`;
- calibration, test, confirmation, protected player/public-song, deployment,
  or Travis accesses: `0`;
- R4 official invocation consumed: `false`;
- R4 one-shot consumed: `false`.

The complete R4 output root and all five destination paths are absent. The
active resolved temporary root contains no `beat-cell-stage2-features-*`,
`chord-audio-lineage-*`, or `chord-runtime-beat-runner-*` entry. No cleanup
was required for this integrated audit. The review inspected committed
authority, code, tests, and synthetic QA receipts only; it did not open or
parse official data.

## New non-executable authority draft

The split-publication replacement draft is:

`docs/handoffs/task-completions/2026-08-21-0955-20-beat-cell-stage2-r4-split-publication-amended-preregistration.json`

It is an exact object copy of the committed amended-R4 authority except for
two paths:

1. `outputPaths.publication` changes from the singular feature-set-only v2
   string to the exact split-policy object above;
2. `featureMath.sourceStageAImplementationModuleFileSha256` changes from the
   superseded implementation hash to final SHA-256
   `0bd8dde059c29a10838e31b08f2987d94bb358b140a0b0fcba7c899364f29dc5`.

Its final candidate receipts are:

- raw-file SHA-256:
  `8374be0d7db38800a59d0d1cd83b77f2e595d90ea0c5d23b5b264177b4211eb4`;
- canonical-object SHA-256:
  `0ce840f56fcaab9474e73e9eae0ca03d39eb30d53a39a0eb623bfb85b963173f`;
- output-path projection SHA-256:
  `a8b3d76cd0adc5e656ce3f53466d352e83a3b048e78a645e72db0482413981ce`;
- feature-math projection SHA-256:
  `5b63fbbda06d2c5b250e5a7b51adb971c3d5ebdac4a38c706e2625574792d766`.

The source-input, Stage-A, Stage-B, selector-core, readiness, one-shot,
reconciliation, label-blind-sweep, Stage-B-admission, post-freeze-preflight,
preflight-one-shot-consumption, and historical-incident projections remain
byte-identical to the committed amended-R4 authority. The unchanged readiness
projection SHA-256 is
`81f58801c789370e06104203117331b8e2d487e3055d14b7a1831e1c22b73b18`.

There is no pending marker. The exact split policy and final Stage-A source
hash are sealed in this docs-only candidate. It remains non-executable because
the replacement authority is not yet committed and the corresponding
contract, phase consumers, tests, readiness wrapper, selector CLI, and final
implementation handoff are not yet committed and independently audited at one
clean HEAD. The final handoff must separately pin the changed readiness-
wrapper and selector-CLI bytes. The output-path projection above is final
while the exact split-policy object remains unchanged.

Neither the superseded committed authority nor this uncommitted draft
authorizes preflight or official execution. A new authority commit, final
implementation/test commit, clean-HEAD immutable-byte audit, and fresh exact
two-sweep label-blind preflight are required before the sole R4 Stage-A
invocation can be considered.

## Task-finish metadata

- files created by this supersession task: this receipt and the split-
  publication amended authority draft named above;
- rejected evidence retained unchanged: the uncommitted `0949` handoff at
  SHA-256
  `c410de83c1d590b2b69c703af18c3ce519352ead71b4c989e04496920ac6e94e`;
- checks completed: strict JSON parse, duplicate-key rejection, finite-number
  traversal, recursive exact-object diff, raw/canonical/projection hashing,
  diff check, output-root absence, and targeted temporary-prefix absence;
- current docs commit readiness: ready for an exact docs-only commit of this
  receipt and the `0955` authority after independent immutable-byte review;
  the authority remains non-executable after that docs commit by itself;
- must not stage: the rejected `0949` handoff, code, tests, contract,
  readiness, generated outputs, temporary artifacts, or edits to any committed
  authority/failure/supersession document;
- remaining human decision: independently audit and commit these exact docs,
  then freeze and audit the exact split-policy consumers in every official
  phase, bind the wrapper/CLI implementation bytes, and approve the separate
  implementation commit;
- recommended next lane: implementation and adversarial cross-phase policy
  audit, followed by Lane 20 final authority resealing and clean-HEAD
  preflight review.
