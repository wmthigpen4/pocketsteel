# Beat-cell Stage-2 R4 owned-directory capture supersession

Date: 2026-08-21

## Outcome

The prospective split-publication implementation was rejected by its final
independent read-only review before any R4 post-freeze preflight, official
command, admitted official-data read, output, publication, fit, or one-shot
consumption. R4 remains unconsumed.

The rejected implementation created the unpublished feature-set directory
with `os.mkdir`, then reopened that name without proving that the opened
descriptor still named the inode created by this invocation. An adversarial
synthetic test renamed the created directory aside and installed a replacement
immediately before the real `os.open`. The publisher accepted and published
the replacement and stranded the created inode. No official source or output
was involved in that reproduction.

This is a release-blocking P1 ownership defect under the frozen
`owned-complete-tree-v2` publication rule. It is not a feature, label,
selector, readiness, or empirical-result change.

## Rejected checkpoint

The authority commit used by the rejected checkpoint is:

`709b98c3d5a8e2d0a14469cb9f2294d17523cedd`

Its authority is:

`docs/handoffs/task-completions/2026-08-21-0955-20-beat-cell-stage2-r4-split-publication-amended-preregistration.json`

with raw SHA-256
`8374be0d7db38800a59d0d1cd83b77f2e595d90ea0c5d23b5b264177b4211eb4`
and canonical SHA-256
`0ce840f56fcaab9474e73e9eae0ca03d39eb30d53a39a0eb623bfb85b963173f`.

The rejected, uncommitted implementation handoff is:

`docs/handoffs/task-completions/2026-08-21-1009-20-beat-cell-stage2-r4-split-publication-implementation.md`

with raw SHA-256
`93d07fab82819ca10b42db1d9e65cb0df5fe85364fa2a07bc8d179734f8693c3`.
It must not be staged or used to authorize preflight. Its `175 passed` focused
and `841 passed`, `4 skipped`, `3 deselected` broad receipts remain factual
for those rejected bytes only.

The rejected Stage-A implementation module SHA-256 was
`0bd8dde059c29a10838e31b08f2987d94bb358b140a0b0fcba7c899364f29dc5`.

## Exact correction

The only permitted operational correction is to bind each newly created
private directory before it is populated:

- capture its regular directory inode through the retained parent descriptor
  immediately after exclusive creation;
- open it with the existing no-follow directory flags;
- require the opened descriptor inode and the current retained-parent name to
  equal that captured inode;
- retain the captured inode for all-name owned-only cleanup;
- apply the same rule to both the hidden feature-set root and its summaries
  directory;
- preserve a foreign replacement and remove every discoverable alias of the
  captured owned inode on failure.

The corrected Stage-A implementation module SHA-256 is
`b1e3153b0c7c27548eda35ceb65bf01782cac50ad6ed9e7d9450eb525660bff1`.
No feature formula, row, summary, manifest schema, source input, output path,
reconciliation rule, Stage-B rule, selector policy, readiness gate, protected
access rule, or one-shot count changes.

## Final source-hash authority amendment

The replacement non-executable authority is:

`docs/handoffs/task-completions/2026-08-21-1019-20-beat-cell-stage2-r4-final-source-amended-preregistration.json`

Its receipts are:

- raw-file SHA-256:
  `329bb235e760a9c665945817b21d4ea0e9d824a26251a668cad4d47fa5b7e2a1`;
- canonical-object SHA-256:
  `a606cfefb1026bc29d335aeb9e73f0adead459a6e789e550aaff35bca214e7c9`;
- output-path projection SHA-256:
  `a8b3d76cd0adc5e656ce3f53466d352e83a3b048e78a645e72db0482413981ce`;
- feature-math projection SHA-256:
  `4b450d74df5314d68e7a8034d488b8d727144c2847e0ae628ba351c69d4ddfb0`;
- Stage-A projection SHA-256:
  `814902fac2550294ce8e336a39b01db6c9012e628c0fdaeb3a1bfc31e13f0688`;
- Stage-B projection SHA-256:
  `ebf2cf85c1c854a8a9c30d0100bd27343612607b0c3fb440e9512b272cb5ff32`;
- selector-core projection SHA-256:
  `2c0b541418b6360b2e79945375b4638bcc50eb1733894311dedcb9b566f156cf`;
- readiness projection SHA-256:
  `81f58801c789370e06104203117331b8e2d487e3055d14b7a1831e1c22b73b18`;
- one-shot projection SHA-256:
  `450413b12835c8ffa5117ceb41e896b0f1168589ea2a6f48a2b601fa09f78796`.

The recursive object diff from `0955` to `1019` is exactly one value:
`featureMath.sourceStageAImplementationModuleFileSha256`, changing from
`0bd8dde059c29a10838e31b08f2987d94bb358b140a0b0fcba7c899364f29dc5`
to
`b1e3153b0c7c27548eda35ceb65bf01782cac50ad6ed9e7d9450eb525660bff1`.

The split publication object remains exact: Stage A binds `featureSet` to the
direct-memory complete-tree v2 mode, while Stage B, selector, and readiness
bind `singleJson` to the atomic v1 mode.

## Zero-consumption boundary

- R4 post-freeze preflight sweeps: `0`;
- R4 official feature invocations: `0`;
- R4 Stage-B invocations: `0`;
- R4 selector fits: `0`;
- R4 readiness evaluations: `0`;
- admitted official-data reads under R4: `0`;
- official R4 outputs or publications: `0`;
- R4 one-shot consumed: `false`.

The `1019` authority does not authorize execution by itself. It remains
blocked until exact implementation/test bytes are committed at one clean
HEAD, local QA passes, the injected pre-open swap fails closed with owned-only
cleanup, and the single independent correction recheck reports no P0/P1.

After that implementation commit, work must pause before the authorized
two-sweep label-blind preflight. No preflight or official command may be run
without the user's next explicit approval.
