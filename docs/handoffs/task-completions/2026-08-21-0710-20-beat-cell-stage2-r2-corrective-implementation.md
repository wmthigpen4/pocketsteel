# Beat-cell Stage-2 R2 corrective implementation

Date: 2026-08-21

## Outcome

The code-only recovery for the consumed beat-cell Stage-2 R1 attempt is
implemented and ready for an independent immutable-byte audit. It has not
been committed or executed against the official R2 sources yet.

R1 remains closed. This implementation points every official command to the
separately committed R2 authority and its distinct `beat-cell-stage2-r2`
output root. It does not authorize reuse of the R1 authority or output path.

## Governance checkpoint

The immutable governance commit is:

`6152b67139fe2e4bdc29bf69e31bb6710f7400a4`

It contains only:

- the factual R1 failure receipt, whose SHA-256 is
  `a9428f6755a80c9c3b01996408e17a6a603be95b0b7bbf88a52b5a2271acaa8f`;
- the full R2 machine authority, whose raw-file and canonical-object SHA-256
  receipts are
  `7fd598ec952c22ae3a59d4d28d66333f75cb88cdc9348e46566063d7d1709b34`
  and
  `33e74034f0bab7b9a8f146188835306f535a158f68bb5bcf66bb0d265d69dd2a`.

The R2 authority differs from R1 in exactly five values: the five official
output paths use `beat-cell-stage2-r2`. Source inputs and all six semantic
projections are object-identical.

## Exact correction

The failed guard read the nonexistent top-level runtime-manifest field
`analyzerContractSha256`. The corrected guard requires the real schema:

`runtime["analyzerContract"]["contractSha256"]`

The nested value must be an object and must equal the exact frozen digest.
There is no fallback to the obsolete top-level alias. The real-shape
regressions prove:

- a nested analyzer contract with no top-level alias passes the guard;
- a missing, non-object, or mismatched nested contract fails closed;
- a correct-looking top-level alias cannot rescue an invalid nested value;
- the valid nested guard advances to the existing audio-lineage admission
  barrier, preserving the original access order.

No runtime artifact, source receipt, feature formula, example mapping,
selector algorithm, readiness rule, gate, threshold, fold, salt, weight,
dataset, cell grid, publication primitive, or protected-data policy changed.

## Frozen semantic receipts

- Stage A:
  `814902fac2550294ce8e336a39b01db6c9012e628c0fdaeb3a1bfc31e13f0688`
- feature math:
  `65fc42417c1b45201e02fe35f140fee541f20608f08fbe6f2d92c127e4009ef2`
- Stage B:
  `ebf2cf85c1c854a8a9c30d0100bd27343612607b0c3fb440e9512b272cb5ff32`
- selector core:
  `2c0b541418b6360b2e79945375b4638bcc50eb1733894311dedcb9b566f156cf`
- readiness:
  `81f58801c789370e06104203117331b8e2d487e3055d14b7a1831e1c22b73b18`
- one-shot:
  `450413b12835c8ffa5117ceb41e896b0f1168589ea2a6f48a2b601fa09f78796`

The readiness implementation now binds its implementation-authority head to
the R2 governance commit `6152b67139fe2e4bdc29bf69e31bb6710f7400a4`.
The expected provenance-only effective receipts are:

- selector configuration:
  `9be2bb559e4c24842a8c221bb9d4d3e5e39ba1acccdc9f54f7cb2a6776f69da1`;
- readiness rubric:
  `f98c267277f87fbd01ba93b2325fbd1ea3d05479838fd46f54ac0cc224e24ba0`.

Those hashes change only because the R2 authority receipt and authority-head
binding changed; their frozen mathematical and policy projections did not.

## Exact implementation receipts

- `steel_guitar_rag/chord_reader/beat_cell_stage2_contract.py`:
  `955d6d929dabffe849aca960dd06f40fbb7c9a12e32d254e2f05ee5dfca4d64e`
- `steel_guitar_rag/chord_reader/beat_cell_examples.py`:
  `844e12d1bbc78bf3b3f6ca007a4d8440c1b1ca238d2360bca91c32487988417b`
- `steel_guitar_rag/chord_reader/beat_cell_readiness.py`:
  `b73bd060fccff0b548635f7237c9d755fd76cd155b04995ea0aebcdc0ec33cf6`
- `tests/test_chord_reader_beat_cell_examples.py`:
  `299b0b3994022c490cf26f848a45e3e3c295d82e3bc6ce3d716d16cef3d8fe7f`

Unchanged selector and command-line hashes were rechecked:

- selector core module:
  `689a31d0eac1f07ec870333fb2994b47eb005ac907c23d14ce7e6a822fb16576`
- features CLI:
  `c0911052883b66eeebae12323c43b33fb35bf204352202e97b4add80e802a7d3`
- examples CLI:
  `a841485267f384c6b2568a07fc61be2defd8e8abecf17e095ad0a3b33c2cd338`
- selector CLI:
  `37bdf4c156495eb6d4d8293fd1201f23db1299c6d397c8e347c00e242f007048`
- readiness CLI:
  `cc0c68ff11b654f8e17f4dc9c8a746c88e543be14d8188e2cf1189304e9b77dd`

## Verification

- focused Stage A/B/C: `117 passed` with warnings treated as errors;
- full chord-reader non-browser suite: `783 passed`, `4 skipped`, and the
  exact `3` real-browser tests deselected, with warnings treated as errors;
- Ruff check and format: pass on the changed Python files;
- `py_compile`: pass on all changed Python files;
- diff check: pass.

The final exact hash recheck and independent P0/P1 verdict remain required
before the implementation commit.

## Boundaries and next action

No R2 official command was run. Neither the R1 nor R2 output root exists.
The correction and tests opened no official Stage-1 outcome object,
reference, prediction, feature output, calibration, test, confirmation,
player/public-song, or Travis surface.

After an independent no-P0/P1 verdict, the exact corrected paths plus this
handoff may be committed. A fresh clean-HEAD metadata preflight must then
revalidate unchanged sources and absent R2 destinations. Only after that
preflight may the distinct R2 Stage-A command be invoked once. It must again
stop for independent label-blind feature-set audit before Stage B.
