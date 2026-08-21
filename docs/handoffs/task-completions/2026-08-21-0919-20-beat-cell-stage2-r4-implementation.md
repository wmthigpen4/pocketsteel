# Beat-cell Stage-2 R4 implementation

Date: 2026-08-21

## Outcome

The narrow R4 recovery implementation is complete and its focused and broad
non-browser verification surfaces are green. It is ready to be committed for
an independent immutable-byte audit. No official R4 command or R4 post-freeze
label-blind preflight has run, and R4 remains unconsumed.

The implementation changes only the private Stage-A feature-summary staging
directory construction needed to canonicalize the trusted macOS temporary
base before the existing strict JSON publisher sees a path. It does not weaken
the publisher's symlink-component rejection and does not change any admitted
source, feature row, feature formula, tolerant-winner reconciliation, Stage-A
or Stage-B policy, selector input, model, fold, salt, weight, grid, threshold,
readiness gate, protected-data rule, publication ownership rule, or one-shot
limit.

R1, R2, and R3 are closed and may not be retried.

## Consumed R3 failure checkpoint

The factual predecessor failure receipt is:

- path:
  `docs/handoffs/task-completions/2026-08-21-0857-20-beat-cell-stage2-r3-failure.md`;
- raw-file SHA-256:
  `362a17d23a09a2cbed58a050c3495529dfdde81a61a68ac960a7ae0ecaabacee`.

It records that the sole authorized R3 Stage-A invocation was consumed at
repository HEAD `c01991e9608c0f53c8299efceb48caf85f5e98d1`. All `246`
validated summaries and all `11,234` feature rows were built in memory, the
exact reconciliation inventory validated, and the manifest was constructed.
Publication then failed before the first staging JSON file or output path was
created because `TemporaryDirectory` retained the lexical macOS
`/var/folders/.../T` spelling while the strict JSON publisher correctly
rejected the `/var` symlink component (`/var` resolves to `/private/var`).

The R3 output root and targeted temporary directories were absent after
unwinding. No manifest or feature summary was visible, the Stage1 report was
not parsed, no outcome or protected surface was opened, and no Stage-B
example, selector fit, or readiness evaluation occurred.

## Immutable R4 authority checkpoint

The committed R4 recovery authority is at commit:

`543ba2ade048b8408db0bf42e500bca77b370613`

It binds:

- authority path:
  `docs/handoffs/task-completions/2026-08-21-0858-20-beat-cell-stage2-r4-recovery-preregistration.json`;
- authority raw-file SHA-256:
  `de8c8e40b7579214bffb3f261f7af12c19ce2d589a911eb6e322a079c847b3f3`;
- authority canonical-object SHA-256:
  `2648d6374a4f2aa9d7e1d59111004c841bb5ceeacd583ca22b5d5c44276e8a42`;
- source-input projection SHA-256:
  `d236e26249cfcf616e4ca95cb199f231b9509c212bdbdb27b947f32028a2c185`;
- output-path projection SHA-256:
  `11187003c95974fb15a9c1837d01e14806aa70dbece62791bae618d55d01097d`;
- Stage-A projection SHA-256:
  `814902fac2550294ce8e336a39b01db6c9012e628c0fdaeb3a1bfc31e13f0688`;
- feature-math projection SHA-256:
  `4e707841105697169dafe16d31edbdaa995fadf2c21435eb9ccaeb1fd2612c1b`;
- product-reconciliation projection SHA-256:
  `15c353cc6b393ffacb46016bcd924382d3b505adc8b15a2ccf77ef04cb024a98`;
- exact expected reconciliation-row/set SHA-256:
  `964195b1e89c9de88b1073269d3c160cb8874aad9d52868c36b33eac10bdef9d`;
- label-blind sweep SHA-256:
  `abc0b3d8965ec450382e30c5d5c6a4612b529cf04401f28f677d983793e0eb1c`;
- Stage-B projection SHA-256:
  `ebf2cf85c1c854a8a9c30d0100bd27343612607b0c3fb440e9512b272cb5ff32`;
- Stage-B reconciliation-admission SHA-256:
  `72ab9e4bb788a7ded91a313436c4cdefbf8b8e8a7d244efa5544351b00adfb81`;
- selector-core projection SHA-256:
  `2c0b541418b6360b2e79945375b4638bcc50eb1733894311dedcb9b566f156cf`;
- readiness projection SHA-256:
  `81f58801c789370e06104203117331b8e2d487e3055d14b7a1831e1c22b73b18`;
- one-shot projection SHA-256:
  `450413b12835c8ffa5117ceb41e896b0f1168589ea2a6f48a2b601fa09f78796`;
- post-freeze label-blind preflight SHA-256:
  `f393c456b112bfe123f75578f547ceec1c7e3599fc1ac4e95e3b4f7aa021e4b`;
- preflight one-shot-consumption SHA-256:
  `ed60c40b199e26cc306ea0d6ce4f67bb8e00a33b4869a7c6dd39703c8275579b`;
- historical governance-incident disclosure SHA-256:
  `7db4fdb77a5965ae421bde606ef4e59cb739a2c8f11e7f7fd80276337d2dbe06`.

The R4 authority preserves the frozen Stage-A, Stage-B, selector-core,
readiness, one-shot, source-input, and reconciliation semantics. Relative to
R3, it changes the five output destinations to the distinct R4 namespace,
binds the corrected Stage-A implementation bytes, advances the active
post-freeze preflight schema and execution phase to R4, and replaces the
active non-consuming `consumesR3OneShot` key with
`consumesR4OneShot=false`. Historical R3 governance-incident literals remain
unchanged.

## Exact implementation receipts

- `steel_guitar_rag/chord_reader/beat_cell_stage2_contract.py`:
  `fe4379d3ad2766dad91836c2b8e86fecd7c1e739c61f84916917bf8d6b843471`;
- `steel_guitar_rag/chord_reader/beat_cell_examples.py`:
  `e78a08cdca8131200719ff08eda627cf398c58f441f819ef39d693508810430f`;
- `steel_guitar_rag/chord_reader/beat_cell_readiness.py`:
  `2dca846080d859c722e9b1e2704568f8e4046b51e245182ab9073989ba24d5ab`;
- `tests/test_chord_reader_beat_cell_examples.py`:
  `eecbff12575303405f7b0ae1df035894432fc7520c73389653b5e03ce7f0adf1`.

The contract loader points to the exact committed R4 authority and binds its
raw, canonical, and feature-math projection receipts. Readiness binds its
implementation-authority head to the R4 authority commit. The production
guard requires the R4 post-freeze preflight schema, execution phase, exact
one-shot-consumption key shape, and rejects stale R3 active-preflight fields.

The new `_stage_and_publish_official_feature_set` helper resolves
`tempfile.gettempdir()` with `strict=True`, requires the resolved base to be an
existing directory, and passes that canonical base explicitly to
`TemporaryDirectory`. It then delegates to the unchanged strict staging and
complete-set publication helpers. Resolution, nondirectory, and temporary-
directory construction failures fail before publication and leave zero
output. A precommit failure removes the private staging tree and leaves no
visible feature set or scratch sibling.

## Effective provenance receipts

The exact effective receipts after the R4 authority binding are:

- selector configuration:
  `79a95d41bd6952eea881dc1795460fa4dd22105c7507bc40808ba07bde5b1047`;
- readiness rubric:
  `12bab08e497d4231cbb0b67c9caa544936ce4ccc523a38f42687e61f19cbedd4`.

These receipts change only through authority and implementation provenance.
The selector grid, optimizer, folds, salts, weighting, probability handling,
readiness policy, denominators, and gates remain frozen.

## Verification

- focused Stage A/B/C suite: `158 passed`;
- broad non-browser suite with warnings treated as errors: `824 passed`,
  `4 skipped`, and exactly `3` browser tests deselected;
- Ruff check: pass;
- Ruff format check: pass;
- `py_compile`: pass;
- diff check: pass;
- CLI surface guards: Stage-A features and Stage-B examples reject `--help`
  with exit `1`; selector and readiness help surfaces exit `0`.

The regression surface covers exact R4 authority and module binding; rejection
of stale R3 preflight schema, execution phase, and one-shot keys; canonical
resolution of a symlinked temporary base; continued rejection of a symlinked
output parent; zero-write failure on broken or nondirectory temporary bases
and private-directory construction; private-tree cleanup on precommit failure;
and existing complete-set atomic-publication safeguards.

## Access, output, and execution boundary

No official R4 command has run. The authority-authorized R4 two-sweep
label-blind in-memory preflight has not run. No R4 feature summary, feature-set
manifest, examples artifact, selector artifact, or readiness report exists.
The implementation and tests did not parse the official Stage1 report or open
an official Stage1 outcome, classification, reference, group, dataset,
calibration, test, confirmation, player/public-song, deployment, or Travis
surface. No official selector or readiness fit occurred.

The CLI surface checks above exercised argument guards only; they did not run
an official Stage-A or Stage-B workflow, access admitted official data, create
an output or targeted temporary path, publish, or consume the R4 one-shot.

## Next authorized step

Commit exactly the four implementation/test paths above plus this handoff at
one clean HEAD, then independently verify the committed implementation,
authority, failure receipt, effective receipts, source bytes, and complete
destination/temp absence.

Before any official R4 CLI invocation, perform exactly the two
authority-authorized deterministic in-memory committed-production-builder
sweeps across all `246` tracks and `11,234` cells. Each sweep must retain and
recheck every admitted raw byte, file inode, root inode, and root/path
inventory before and after; validate every summary and row; produce exactly
the one authorized reconciliation row/set; and agree canonically with the
other sweep. It may not invoke an official runner or CLI, parse the Stage1
report, open an outcome, create a temporary or output path, publish, build
examples, fit a selector/readiness model, or access a protected surface. Any
delta blocks R4. Because the two-sweep proof invokes no official CLI and
performs no publication, it is explicitly non-consuming.

The R4 feature-math provenance differs from R3, so the R3 canonical summary-
inventory SHA-256 is historical evidence only. R4 must report a new observed
summary-inventory digest and require exact run-one/run-two equality; it must
not pin the R3 digest. The reconciliation row/set SHA-256 remains exactly
`964195b1e89c9de88b1073269d3c160cb8874aad9d52868c36b33eac10bdef9d`.

Only after that clean-HEAD preflight and an independent GO may the sole R4
official Stage-A command be authorized. No official execution is authorized
by this implementation handoff alone.

## Task-finish metadata

- files changed by this documentation task: this handoff only;
- safe implementation commit set: the four exact implementation/test paths
  above plus this handoff;
- must not stage: generated outputs, temporary artifacts, unrelated worktree
  changes, or any R1/R2/R3 authority or receipt;
- remaining human decision: independent immutable-byte audit and explicit R4
  preflight/official-execution authorization;
- recommended next lane: Lane 01 exact commit, followed by independent Lane
  20/15 clean-HEAD audit and the authority-bounded R4 two-sweep preflight.
