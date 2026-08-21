# Beat-cell Stage-2 R4 final implementation

Date: 2026-08-21

## Outcome

The final pre-execution R4 implementation is frozen against the split
publication authority and the owned-directory capture correction. Stage A
publishes one exact validated in-memory feature-set inventory as an owned
complete tree. Stage B, selector, and readiness remain bound to their exact
single-JSON publication protocol.

No R4 post-freeze preflight, official command, admitted official-data read,
output, publication, examples join, selector fit, readiness evaluation, or
one-shot consumption has occurred. R4 remains unconsumed. This handoff does
not authorize execution; work must pause after the implementation commit.

## Governance chain

- consumed R3 failure receipt:
  `docs/handoffs/task-completions/2026-08-21-0857-20-beat-cell-stage2-r3-failure.md`;
- initial R4 authority commit:
  `543ba2ade048b8408db0bf42e500bca77b370613`;
- first R4 implementation-audit rejection:
  `docs/handoffs/task-completions/2026-08-21-0931-20-beat-cell-stage2-r4-implementation-audit-rejection.md`;
- split-publication supersession receipt:
  `docs/handoffs/task-completions/2026-08-21-0954-20-beat-cell-stage2-r4-split-publication-supersession.md`;
- final owned-directory capture supersession receipt:
  `docs/handoffs/task-completions/2026-08-21-1018-20-beat-cell-stage2-r4-owned-directory-capture-supersession.md`;
- final authority commit:
  `0933007489656500ec17fec1f64628031564214f`.

The rejected prospective `1009` handoff is raw-bound in the `1018` receipt
and is not part of this commit.

## Final authority receipts

Authority path:

`docs/handoffs/task-completions/2026-08-21-1019-20-beat-cell-stage2-r4-final-source-amended-preregistration.json`

- raw-file SHA-256:
  `329bb235e760a9c665945817b21d4ea0e9d824a26251a668cad4d47fa5b7e2a1`;
- canonical-object SHA-256:
  `a606cfefb1026bc29d335aeb9e73f0adead459a6e789e550aaff35bca214e7c9`;
- output-path projection SHA-256:
  `a8b3d76cd0adc5e656ce3f53466d352e83a3b048e78a645e72db0482413981ce`;
- Stage-A projection SHA-256:
  `814902fac2550294ce8e336a39b01db6c9012e628c0fdaeb3a1bfc31e13f0688`;
- feature-math projection SHA-256:
  `4b450d74df5314d68e7a8034d488b8d727144c2847e0ae628ba351c69d4ddfb0`;
- Stage-B projection SHA-256:
  `ebf2cf85c1c854a8a9c30d0100bd27343612607b0c3fb440e9512b272cb5ff32`;
- selector-core projection SHA-256:
  `2c0b541418b6360b2e79945375b4638bcc50eb1733894311dedcb9b566f156cf`;
- readiness projection SHA-256:
  `81f58801c789370e06104203117331b8e2d487e3055d14b7a1831e1c22b73b18`;
- one-shot projection SHA-256:
  `450413b12835c8ffa5117ceb41e896b0f1168589ea2a6f48a2b601fa09f78796`.

The exact split publication policy is:

- `featureSet`:
  `canonical-new-path-only-retained-nofollow-dirfd-input-recheck-failure-atomic-direct-in-memory-exact-rendered-inventory-owned-complete-tree-v2`;
- `singleJson`:
  `canonical-new-path-only-retained-nofollow-dirfd-input-recheck-failure-atomic-v1`.

## Implementation receipts

- `steel_guitar_rag/chord_reader/beat_cell_stage2_contract.py`:
  `3eb25a03fadfbff2f294375d5399fb186d7973abc5f4bc9b2730dfebb1503583`;
- `steel_guitar_rag/chord_reader/beat_cell_examples.py`:
  `b1e3153b0c7c27548eda35ceb65bf01782cac50ad6ed9e7d9450eb525660bff1`;
- `steel_guitar_rag/chord_reader/beat_cell_readiness.py`:
  `505da80afea102a7d66c4655b2f11865ac154915895d1d1f32ea4d3c06ffa18a`;
- `scripts/chord_beat_cell_selector.py`:
  `48d4de5af7225ad082fe96e459c55fcb58cad1a774281eaacbc363e9b8e130c7`.

Test receipts:

- `tests/test_chord_reader_beat_cell_examples.py`:
  `05ece0e2acd7f34c4b6e5b97efb17f5f62d7f884871a0af0647b4ef449b4298c`;
- `tests/test_chord_reader_beat_cell_selector.py`:
  `c48c19d4b3b32936870f0b6d7339fc7ddb3d7dcfd5970502903474e9565fa6`;
- `tests/test_chord_reader_beat_cell_readiness.py`:
  `03dcc2dc8fbb05bf6c9eee0decad4467a244e4ed948eec79fc6cbc7e5669da5b`.

Effective provenance receipts:

- selector configuration:
  `263b8fd5c0e06c1348adcd372b1101ba090c49a8053abbe1c1ba4979607d7dc9`;
- readiness rubric:
  `5b5d25fae2271eed1283e2a5c17a3f77b1b0508a2ff330c85bdf1efc9c7a7236`.

## Publication closure

The feature-set runner validates the complete manifest and summaries before
creating an output parent, freezes each deterministic filename to exact
canonical bytes, builds exactly those bytes under one hidden sibling, and
uses a single no-replace directory rename. Source barriers run immediately
before and after that rename.

The hidden feature-set root and its summaries directory are each captured
through the retained parent descriptor immediately after exclusive creation.
Their opened descriptors and visible names must equal the captured inode
before any artifact byte is written. All success checks bind exact names,
inodes, inventories, and bytes. Failure cleanup searches by captured owned
inode and preserves foreign replacements.

Stage B validates `publication.singleJson` before output access. The selector
CLI validates it before destination preflight or examples access. Readiness
validates and emits that same authority mode before artifact access. Any
missing, extra, stale, or cross-mode publication field fails closed.

## Verification

- exact focused Stage A/B/C suite: `176 passed`;
- broad non-browser suite with warnings treated as errors: `842 passed`,
  `4 skipped`, and exactly `3` real-browser tests deselected;
- injected private-root replacement immediately before the real `os.open`:
  rejected, zero publication, foreign replacement preserved, captured owned
  inode removed;
- Ruff check: pass;
- Ruff format check: pass;
- in-memory compile: `7 passed`;
- diff check: pass;
- feature and examples CLIs reject `--help` with exit `1` and no alternate
  path/policy surface;
- selector and readiness help surfaces exit `0` and expose no weakening path.

No official Stage-1 report, protected label surface, benchmark report, group
manifest, feature output, examples artifact, selector artifact, or readiness
report was opened or created by this implementation verification.

## Mandatory pause

After these exact files are committed at one clean HEAD, stop. Do not run the
R4 two-sweep label-blind preflight, an official CLI, Stage B, selector
training, or readiness evaluation without the user's next explicit approval.
Any future nonzero official command remains terminal for its one-shot cycle.
