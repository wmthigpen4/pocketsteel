# Beat-cell Stage-2 R4 implementation-audit rejection and authority supersession

Date: 2026-08-21

## Outcome

Independent release review rejected the prospective R4 Stage-A implementation
bytes before any R4 official-data preflight or official invocation. The
rejected implementation admits a writer-to-reader pathname race between its
external feature-summary scratch tree and its owned complete-tree publisher.
It cannot be committed, preflighted, or executed as the official R4
implementation.

This is a transparent additive pre-execution R4 amendment, not a new R5
cycle. R4 has consumed no preflight run, official invocation, admitted
official data, output namespace, publication, or one-shot authority. The five
R4 output destinations remain fixed and absent, and `consumesR4OneShot`
remains `false`.

The committed R4 authority at commit
`543ba2ade048b8408db0bf42e500bca77b370613` remains immutable as historical
evidence, but it is superseded and explicitly non-authorizing. It must not be
used for an R4 preflight or official command. No existing authority, failure
receipt, implementation handoff, code, or test file is changed by this
receipt.

## Rejected authority and implementation checkpoint

The rejected audit target was:

- authority commit:
  `543ba2ade048b8408db0bf42e500bca77b370613`;
- authority path:
  `docs/handoffs/task-completions/2026-08-21-0858-20-beat-cell-stage2-r4-recovery-preregistration.json`;
- authority raw-file SHA-256:
  `de8c8e40b7579214bffb3f261f7af12c19ce2d589a911eb6e322a079c847b3f3`;
- authority canonical-object SHA-256:
  `2648d6374a4f2aa9d7e1d59111004c841bb5ceeacd583ca22b5d5c44276e8a42`;
- authority output-path projection SHA-256:
  `11187003c95974fb15a9c1837d01e14806aa70dbece62791bae618d55d01097d`;
- authority feature-math projection SHA-256:
  `4e707841105697169dafe16d31edbdaa995fadf2c21435eb9ccaeb1fd2612c1b`;
- rejected publication policy:
  `canonical-new-path-only-retained-nofollow-dirfd-input-recheck-failure-atomic-v1`;
- rejected Stage-A implementation module:
  `steel_guitar_rag/chord_reader/beat_cell_examples.py`;
- rejected Stage-A implementation module SHA-256:
  `e78a08cdca8131200719ff08eda627cf398c58f441f819ef39d693508810430f`.

The rejected draft implementation handoff is retained at:

- path:
  `docs/handoffs/task-completions/2026-08-21-0919-20-beat-cell-stage2-r4-implementation.md`;
- draft raw-file SHA-256:
  `ec2d9baf9e9677f838eb7d4eee7d63012dca5681888d26e3575227fa66acbd8f`.

That handoff is superseded by this rejection. Its green synthetic QA receipts
do not cure the publication race and do not authorize preflight or execution.

The factual R3 predecessor failure remains bound separately at:

- path:
  `docs/handoffs/task-completions/2026-08-21-0857-20-beat-cell-stage2-r3-failure.md`;
- raw-file SHA-256:
  `362a17d23a09a2cbed58a050c3495529dfdde81a61a68ac960a7ae0ecaabacee`.

R3 remains consumed and closed. Nothing in this pre-execution R4 amendment
reopens R3 or permits reuse of an R1, R2, or R3 output namespace.

## Exact implementation-audit finding

The rejected `e78a08cd...` implementation retained all `246` validated
feature summaries as in-memory objects, then performed this publication flow:

1. `_stage_and_publish_official_feature_set` created an external
   `TemporaryDirectory` and constructed a pathname mapping for the summaries;
2. `_atomic_publish_json_set` canonically rendered the summaries and wrote
   them into that external scratch directory;
3. after that helper returned, `_publish_complete_feature_set_with_precommit`
   reopened the scratch directory by pathname, listed its current filenames,
   and read its current file bytes;
4. the second helper copied those captured bytes into the unpublished owned
   hidden complete-tree and atomically renamed that tree into the R4 output
   namespace.

The scratch reader required flat regular `.json` entries and detected an
inode change during each individual read. It did not retain the writer's
directory or file identities across the helper boundary, require the complete
reader inventory to equal the original in-memory summary inventory, or
compare every captured byte string with the original exact canonical render
and manifest binding.

Therefore a same-user concurrent actor could replace the scratch directory or
one or more entries after the writer returned but before the reader captured
them, leave the replacement stable during capture, and cause different bytes
or a different flat inventory to be copied into the official complete-tree.
Mode `0700`, a random temporary name, a nofollow open, and a stable inode
during the later read do not bind those later bytes to the earlier in-memory
objects. The official runner could consequently publish and return success
for bytes that were not the exact validated/rendered inventory. This violates
the frozen canonical, exact-inventory, and failure-atomic publication
contract and is a release-blocking P1.

No such mutation occurred against official data or output. The finding was
demonstrated only with synthetic audit fixtures before execution.

## Required narrow correction

Recovery must eliminate the external scratch writer-to-reader round trip.
The committed production implementation must:

- validate the complete in-memory manifest and all in-memory summaries;
- freeze an exact, unique manifest-bound filename inventory and the exact
  canonical rendered bytes for every summary;
- pass those already-bound in-memory byte strings directly into the existing
  owned hidden complete-tree publisher;
- create the unpublished output sibling using retained nofollow directory
  descriptors and owned inode identities;
- write, link, verify, and `fsync` the exact in-memory bytes within that owned
  tree;
- require the private/published feature-set root name inventory to equal
  exactly `{manifest.json, summaries}` and the summary-root name inventory to
  equal exactly the frozen rendered mapping, with no extra entry, both before
  the rename and after the rename/final source barrier;
- verify immediately before rename that the private source name still denotes
  the invocation-owned root inode and immediately after rename that the final
  destination name denotes that same inode;
- preserve both source-recheck barriers, the sole no-replace directory rename,
  post-publication exact-byte/inode verification, and failure cleanup that
  removes only invocation-owned entries;
- create no external feature-summary scratch directory and perform no
  pathname-based writer-to-reader handoff.

The exact amended publication policy is:

`canonical-new-path-only-retained-nofollow-dirfd-input-recheck-failure-atomic-direct-in-memory-exact-rendered-inventory-owned-complete-tree-v2`

The strict no-symlink, no-overwrite, retained-dirfd, source-recheck,
failure-atomic, output-disjointness, and one-shot policies may not be weakened.
No source input, cell, feature, feature formula, winner, reconciliation,
threshold, fold, salt, weight, model, readiness gate, protected-access rule,
or R4 output destination may change.

## Zero-consumption and access proof

At the governance amendment boundary:

- authorized R4 post-freeze preflight sweeps: `0`;
- official R4 production-builder calls over admitted data: `0`;
- official R4 CLI invocations: `0`;
- official R4 runner invocations: `0`;
- official Stage1 report JSON parses: `0`;
- official Stage1 outcome-object accesses: `0`;
- official group/reference/dataset object accesses: `0`;
- official R4 source-admission or feature-extraction reads: `0`;
- R4 output or publication calls: `0`;
- published R4 feature summaries or manifests: `0`;
- Stage-B examples built from official outputs: `0`;
- selector candidate fits: `0`;
- readiness evaluations or reproduction fits: `0`;
- calibration, test, confirmation, protected player/public-song, deployment,
  or Travis accesses: `0`;
- R4 official invocation consumed: `false`;
- R4 one-shot consumed: `false`.

The R4 output root
`/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage2-r4`
and all five authority destinations remained absent. Argument-guard and
synthetic unit/integration tests were not official R4 invocations, admitted no
official data, and created no official output.

One exact synthetic same-user race probe intentionally stranded a private QA
scratch directory under the active resolved system temporary root. It was
identified by its task-owned random name, directory inode `35874091` and mode
`0700`. Its sole synthetic file was
`db8786b290346fd7261e3e1f4b0d4043662803a3fd141fa9fb22740fb1d0d1ea-1111111111111111111111111111111111111111111111111111111111111111.json`,
with inode `35874092`, mode `0600`, size `146` bytes, SHA-256
`dfe90702045a1f95a3dfde047dba9358f96a2aec1c4fa1eb21cf5ae3308d4a45`,
synthetic `track-1` content, and an all-ones artifact identifier. The cleanup
auditor removed only that exact file and then that exact directory and
confirmed the path absent. It was synthetic QA residue, not an official R4
temporary or output artifact, and its cleanup consumed no preflight or
one-shot authority.

## Amended R4 authority draft

The replacement machine-authority draft is:

`docs/handoffs/task-completions/2026-08-21-0932-20-beat-cell-stage2-r4-amended-recovery-preregistration.json`

It is an exact object copy of the committed R4 authority except for:

1. `outputPaths.publication`, which changes from the rejected v1 policy to
   the exact direct-in-memory v2 policy above; and
2. `featureMath.sourceStageAImplementationModuleFileSha256`, which is
   `bb73bab25cc609fcfaccea9a4f0f831add890a7156da07a48a5aa3d044b7ea6d`,
   the exact frozen corrected production module.

Its current candidate receipts are:

- raw-file SHA-256:
  `ef44670f6378a0cf2c7d2e7c77b85b645e5ffd95288ebbb937879fe32c1bfafd`;
- canonical-object SHA-256:
  `4372283a6ce9dbf7d8ea955545e5cd9e32971a89e4ac1f8da2cc4a8702b88e30`;
- output-path projection SHA-256:
  `07023d0c85ad0cab3614b8d2e0763e2050d8fb3724a52c3a0323a763cfdb9686`;
- feature-math projection SHA-256:
  `bb255a0c61dd99577c07e6caeaed86e215e13cbe8ddc63a1bed1d24351a4c379`.

The amended authority is still uncommitted and non-executable. The committed
v1 authority is superseded and non-executable. No R4 preflight or official
command is authorized until all amended-authority receipts are independently
audited, the corrected code/tests/contract/readiness and their implementation
handoff are committed at one clean HEAD, and the exact authority-bounded
two-sweep preflight returns an independent GO.

## Validator and provenance handoff

Before the amended authority and implementation can be executed, the
implementation slice must:

- independently verify the final raw-file SHA-256 of
  `steel_guitar_rag/chord_reader/beat_cell_examples.py` and the amended
  authority raw, canonical, output-path, and feature-math receipts;
- update the central contract to bind the amended authority path, raw hash,
  canonical hash, output-path projection, and feature-math projection;
- validate the exact `outputPaths` key set and consume the exact v2
  `outputPaths.publication` literal in the production Stage-A guard, rejecting
  the superseded v1 literal and any extra, missing, or stale key;
- update or authority-bind the readiness publication mode to the exact v2
  policy, rejecting the superseded v1 mode;
- recompute and bind the effective selector-configuration and readiness-rubric
  receipts after all final authority and implementation provenance changes;
- treat every R4 summary inventory digest, summary artifact hash, manifest
  hash, and summary filename as newly observed provenance. No R3 or prior R4
  summary digest may be pinned, although the exact reconciliation row/set
  SHA-256 remains unchanged.

The machine authority and artifact schema versions may remain v1 because the
amendment adds no machine field and changes no schema shape. The historical
supersession facts remain in this companion receipt; adding them to the
machine JSON would require a separately reviewed schema/key-set change.

## Task-finish metadata

- files created by this governance task: this rejection/supersession receipt
  and the amended R4 authority draft named above;
- existing evidence retained unchanged: the committed R3 failure receipt, the
  committed R4 v1 authority, and the rejected `0919` implementation handoff at
  raw SHA-256
  `ec2d9baf9e9677f838eb7d4eee7d63012dca5681888d26e3575227fa66acbd8f`;
- checks completed: strict JSON parse, duplicate-key rejection, finite-number
  traversal, recursive exact-object diff, raw/canonical/projection hashing,
  diff check, R4-root absence, synthetic-residue ownership/cleanup audit, and
  targeted feature-temp-prefix absence;
- current docs commit readiness: pending independent immutable-byte audit;
  neither uncommitted draft authorizes preflight or execution;
- must not stage as part of this docs draft: code, tests, contract, readiness,
  generated outputs, temporary artifacts, or any edit to the committed v1
  authority and existing failure receipts;
- remaining human decision: freeze and independently audit the corrected v2
  publisher, insert its final module hash, refresh all derived receipts, and
  approve the exact docs/implementation commit sequence;
- recommended next lane: implementation and adversarial publication audit,
  followed by Lane 20 final authority resealing and clean-HEAD preflight
  review.
