# Beat-cell Stage-2 R3 implementation

Date: 2026-08-21

## Outcome

The narrow R3 recovery implementation is complete and ready to be committed
for independent immutable-byte audit. It has not run the official R3 command.
R1 and R2 remain closed and may not be retried.

R3 preserves the frozen Stage-A tolerant winner and all 48 feature formulas.
It adds only the preregistered, exact-inventory reconciliation for the one
label-blind product disagreement exposed by the consumed R2 attempt. It does
not change any source data, cell, feature name, estimator input, fold, salt,
weight, grid, threshold, readiness gate, protected-data rule, or one-shot
limit.

## Immutable authority checkpoint

The committed R3 governance authority is at commit:

`3e93d279e2d6308918e4e4df3801520f4211edb6`

It binds:

- authority path:
  `docs/handoffs/task-completions/2026-08-21-0740-20-beat-cell-stage2-r3-recovery-preregistration.json`;
- authority raw-file SHA-256:
  `c738861f164022ce558258b2ecad4ebcbe707394750fe4bdc9cb97df5cd3e305`;
- authority canonical-object SHA-256:
  `1050b7c7f676b04431d04b8009827d8695e7e22896917ad9b39d29f3edf1f761`;
- feature-math projection SHA-256:
  `0735dc64d064f227bf4fcdd698ef1ff16644fbb31e261e7a057c5f021e693602`;
- product-reconciliation SHA-256:
  `b890e178f7039e9de3d4fc68ea885ed3e01faaee1e404c5ef43b599a14442c39`;
- post-freeze label-blind preflight SHA-256:
  `da6ee1c264fc49f946e2fb564d0ff65f45ecdea37a5ed528afc1dbf27fd87aec`;
- pre-commit governance-incident disclosure SHA-256:
  `7db4fdb77a5965ae421bde606ef4e59cb739a2c8f11e7f7fd80276337d2dbe06`.

The unchanged projection receipts remain:

- Stage A:
  `814902fac2550294ce8e336a39b01db6c9012e628c0fdaeb3a1bfc31e13f0688`;
- Stage B:
  `ebf2cf85c1c854a8a9c30d0100bd27343612607b0c3fb440e9512b272cb5ff32`;
- selector core:
  `2c0b541418b6360b2e79945375b4638bcc50eb1733894311dedcb9b566f156cf`;
- readiness:
  `81f58801c789370e06104203117331b8e2d487e3055d14b7a1831e1c22b73b18`;
- one-shot:
  `450413b12835c8ffa5117ceb41e896b0f1168589ea2a6f48a2b601fa09f78796`.

## Narrow reconciliation semantics

The frozen Stage-A winner remains `C7` for
`winterreise-schubert_d911-20_hu33`, cell `75`, while the canonical-equal
Stage1 summary remains `Fm`. The implementation permits that inequality only
when the complete observed reconciliation row equals the single authority row
and the complete observed reconciliation inventory equals the authority set
SHA-256
`964195b1e89c9de88b1073269d3c160cb8874aad9d52868c36b33eac10bdef9d`.

Both products must be members of the same frozen `abs_tol=1e-9` tolerant
winner-candidate set. Both the Stage-A and Stage1 value triples must be
structurally ineligible under Stage1 scoring-policy SHA-256
`acb716b4f278c07a5696bf0166601a154a3a2dfce2ca596b8101543a74d766a9`.
Coverage and dominance retain their original exact-tolerance cross-checks,
and all source-cell, timing, construction, identity, and inventory fields
remain exact. A missing row, extra row, eligible row, non-tied product, stale
identity, changed value, or any other product mismatch fails closed.

At Stage B, the exact row may reconcile only when its Stage1 classification
is `U` or `N`. It then emits no example. If the classification is `C` or `I`,
or if any row or inventory field differs, Stage B fails closed. The Stage-B
reconciliation inventory is independently exact and cannot be used to alter
Stage A.

## Governance-incident disclosure

The authority literally records the one pre-commit docs-audit `json.loads`
and canonical traversal of the Stage1 report. Top-level receipt prints
occurred. The attempted path
`aggregate.funnel.counts (failed at aggregate.funnel before any duration expression evaluated)`
raised `KeyError('funnel')` before attempted-path output.

No numeric or protected semantic value was emitted or retained. No track,
outcome, classification, reference, group, or dataset collection was indexed.
The tolerant-winner policy had already been selected and the incident was not
used as a decision input. No further docs-audit parse occurred, and official
and authorized-preflight Stage1-report parse counts remain zero.

## Exact implementation receipts

- `steel_guitar_rag/chord_reader/beat_cell_stage2_contract.py`:
  `129458415d27e422a7a566c5712daf265531bd99e8c049f01fa03473728b3a30`;
- `steel_guitar_rag/chord_reader/beat_cell_examples.py`:
  `1434b9bb30f34d5ea53599a48f52d96e11cce185fe70a66e7e0dde275b07f994`;
- `steel_guitar_rag/chord_reader/beat_cell_readiness.py`:
  `40ef7ba29a2dcbff5063159553db44be5763591a4037a48e61c3e74df3c0338c`;
- `tests/test_chord_reader_beat_cell_examples.py`:
  `8b7a0623f7232a3f7ec14cdf962dfd24a192cca4ac47791cac96b2fe85823180`;
- `tests/test_chord_reader_beat_cell_selector.py`:
  `1d817a5822a847af4b67085b7918ab77b4344917a91ceec95ba6aafcc10189ae`.

The contract loader points to the exact R3 authority, binds its raw,
canonical, and projection receipts, and requires the exact Stage-A
implementation module bytes whenever reconciliation is present. Readiness
binds its implementation-authority head to the immutable R3 governance
commit.

## Effective provenance receipts

The expected effective receipts after the R3 authority binding are:

- selector configuration:
  `d5e29f63d990b57dce68965435e6b1fc4312898a191b4a46f6087fa7a41f1d40`;
- readiness rubric:
  `b38fbf12290a2de69905fcd9182ab77f279357a11b0fdec40d6e7c4ccf7a05b9`.

These effective receipts change through authority/provenance binding. The
selector grid, optimizer, folds, salts, weighting, probability handling,
readiness policy, denominators, and gates remain frozen.

## Verification

- focused Stage A/B/C suite: `149 passed`;
- broad non-browser suite: `815 passed`, `4 skipped`, and the exact `3`
  browser tests deselected;
- Ruff check: pass;
- Ruff format check: pass;
- `py_compile`: pass;
- diff check: pass.

The regression surface covers exact authority/module binding, exact-shape
policy and row validation, tolerant-candidate and dual-ineligibility checks,
missing/extra inventory rejection, Stage-B `U`/`N` no-example handling,
Stage-B `C`/`I` fatal handling, governance-incident invariants, and the
non-consuming two-run preflight contract.

## Access, output, and execution boundary

No official R3 command has run. No official R3 feature row, summary, manifest,
examples artifact, selector artifact, or readiness report exists. The
implementation and tests did not parse the official Stage1 report or open an
official Stage1 outcome, classification, reference, group, dataset, calibration,
test, confirmation, player/public-song, deployment, or Travis surface. No
official selector or readiness fit occurred.

## Next authorized step

Commit exactly the five implementation/test paths above plus this handoff,
then independently verify the clean committed HEAD and every bound byte.
Before any official R3 CLI invocation, perform exactly the two authority-
authorized deterministic in-memory committed-production-builder runs across
all 246 tracks and 11,234 cells.

Each run must capture and recheck the full admitted input bytes, file inodes,
root inodes, and path inventory before and after; produce exactly the one
authorized reconciliation row/set; and agree canonically with the other run.
It may not invoke the official runner or CLI, parse the Stage1 report, open an
outcome, create a temporary or output path, publish, build examples, fit a
selector/readiness model, or access a protected surface. Any delta blocks R3.
Because it invokes no official CLI and performs no publication, this exact
two-run preflight is explicitly non-consuming.
