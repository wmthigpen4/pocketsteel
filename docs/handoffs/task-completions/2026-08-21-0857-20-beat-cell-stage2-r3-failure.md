# Beat-cell Stage-2 R3 Stage-A failure receipt

Date: 2026-08-21

## Outcome

The one authorized R3 Stage-A invocation was consumed and failed closed after
all label-blind feature computation and manifest construction, but before the
first staging JSON file or official output path was created. R3 is closed and
must not be retried.

The failure is a code-only staging-path normalization defect. macOS supplied
the temporary root through the lexical `/var` alias, while the JSON publisher
correctly rejects every lexical path containing a symlink component. It is not
source-data drift, feature-math drift, reconciliation drift, label access, a
selector fit, a readiness result, or a protected-surface result. No data,
cell, feature, winner, formula, threshold, fold, salt, weight, grid, dataset,
gate, cutoff, or access rule may be changed in response.

## Consumed authority and invocation

The failed invocation was bound to:

- repository HEAD:
  `c01991e9608c0f53c8299efceb48caf85f5e98d1`;
- R3 authority commit:
  `3e93d279e2d6308918e4e4df3801520f4211edb6`;
- R3 authority:
  `docs/handoffs/task-completions/2026-08-21-0740-20-beat-cell-stage2-r3-recovery-preregistration.json`;
- R3 authority raw-file SHA-256:
  `c738861f164022ce558258b2ecad4ebcbe707394750fe4bdc9cb97df5cd3e305`;
- R3 authority canonical-object SHA-256:
  `1050b7c7f676b04431d04b8009827d8695e7e22896917ad9b39d29f3edf1f761`;
- R3 feature-math projection SHA-256:
  `0735dc64d064f227bf4fcdd698ef1ff16644fbb31e261e7a057c5f021e693602`;
- R3 product-reconciliation projection SHA-256:
  `b890e178f7039e9de3d4fc68ea885ed3e01faaee1e404c5ef43b599a14442c39`;
- R3 post-freeze label-blind preflight SHA-256:
  `da6ee1c264fc49f946e2fb564d0ff65f45ecdea37a5ed528afc1dbf27fd87aec`;
- R3 one-shot projection SHA-256:
  `450413b12835c8ffa5117ceb41e896b0f1168589ea2a6f48a2b601fa09f78796`;
- exact Stage-A implementation module SHA-256:
  `1434b9bb30f34d5ea53599a48f52d96e11cce185fe70a66e7e0dde275b07f994`;
- exact CLI module SHA-256:
  `c0911052883b66eeebae12323c43b33fb35bf204352202e97b4add80e802a7d3`.

The exact authorized shell command was:

```sh
cd '/Users/cory/Documents/Pocket Steel/chord-reader-development'
/usr/bin/env -u PYTHONWARNINGS PYTHONDONTWRITEBYTECODE=1 \
  '/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v4/.venv/bin/python' \
  scripts/chord_beat_cell_features.py
```

It exited with status `1` and the terminal exception:

```text
steel_guitar_rag.chord_reader.selector_development.SelectorDevelopmentError: JSON output may not contain symlinked path components.
```

The exact failing call chain in the consumed HEAD was:

1. `scripts/chord_beat_cell_features.py:22` in `main` called
   `run_official_beat_cell_features()`;
2. `steel_guitar_rag/chord_reader/beat_cell_examples.py:3485` called
   `_atomic_publish_json_set(staged)`;
3. `steel_guitar_rag/chord_reader/selector_development.py:511` called
   `_preflight_new_json(raw_path, "JSON output")` for the first staged path;
4. `steel_guitar_rag/chord_reader/selector_development.py:335` called
   `_reject_symlink_components(absolute.parent, name)`;
5. `steel_guitar_rag/chord_reader/selector_development.py:302` raised the
   terminal exception after detecting the lexical `/var` symlink component.

The CLI never returned an artifact and therefore emitted no success receipt
to standard output.

## Authorized preflight proof

Immediately before the consumed official invocation, the authority-authorized
non-consuming preflight completed with exit `0`. It performed exactly two
complete committed-production-builder sweeps, with `246` builder calls and
`11,234` feature rows per sweep, for `492` total builder calls.

Each sweep retained and rechecked:

- lexical admitted paths: `1,258`;
- unique resolved regular files: `1,255`;
- exact raw bytes: `457,075,017`;
- input projection SHA-256:
  `588572cdb73566cc05b04a32d210b647c9c1b0be002e2250168ee75aa797f58e`.

The two complete summary inventories were canonical-equal with SHA-256
`54c523b7c5ed3489b641256b5e9b8b551abb20b06d22521fb1bb7be95df8da93`.
Each contained exactly the one preregistered reconciliation row, whose exact
set SHA-256 was
`964195b1e89c9de88b1073269d3c160cb8874aad9d52868c36b33eac10bdef9d`.
The preflight created no output or temporary path, invoked no official runner
or CLI, parsed no Stage1 report, opened no outcome, and performed no example,
selector, or readiness work.

## Work completed before the exception

The official runner completed the exact authority, destination-absence,
runtime-manifest, beat-receipt, audio-lineage, prediction-sidecar, and
prediction-leaf admissions. Full reference-free audio-lineage file validation
and fresh extraction completed. The Stage1 report remained opaque and was
retained only as raw bytes, inode identity, and raw SHA-256.

The sorted production-builder comprehension returned all `246` validated
feature summaries containing all `11,234` feature rows. The complete
product-reconciliation inventory then validated as exactly one row with set
SHA-256
`964195b1e89c9de88b1073269d3c160cb8874aad9d52868c36b33eac10bdef9d`.

`build_beat_cell_feature_set_manifest` next revalidated every summary and row,
built the complete manifest in memory, and returned successfully. The
following official guard passed exact `trackCount=246`, `cellCount=11234`, and
the frozen covered-duration total. No manifest artifact hash was emitted or
retained after process exit.

The publication `precommit` closure was defined but never invoked. One
`beat-cell-stage2-features-*` temporary directory was then created, and an
in-memory `staged` mapping associated all `246` summaries with their intended
temporary JSON filenames. “Staged” here names only that Python mapping; no
staging JSON file existed.

## Exact staging-path defect

`tempfile.TemporaryDirectory(prefix="beat-cell-stage2-features-")` used the
active macOS temporary root through its lexical `/var/folders/.../T` spelling.
On this host, `/var` is a symlink to `/private/var`.

`Path(temporary)` retained the lexical `/var` spelling, and the publisher's
`_absolute` helper uses `os.path.abspath`, which normalizes syntax but does not
resolve symlinks. On the first `_atomic_publish_json_set` normalization
iteration, `_preflight_new_json` inspected the target parent and
`_reject_symlink_components` correctly rejected `/var`.

The exception occurred before the first path was added to the publisher's
`normalized` mapping and before its `parents`, `temporary_entries`, or
`linked` ownership collections received an entry. Consequently the publisher
never opened or created a staging parent, rendered a summary JSON payload,
called `_create_temporary_json`, linked a destination name, called `fsync`, or
entered `_publish_complete_feature_set_with_precommit`.

The independently validated audio-lineage path already avoids the same host
alias by resolving the trusted temporary base before creating each private
snapshot. Recovery must use that narrow established pattern for the Stage-A
feature staging directory. The no-symlink publisher policy must not be
weakened.

## Zero-publication, cleanup, and protected-access proof

The official R3 root and every descendant remained absent. No feature summary,
feature-set manifest, examples artifact, selector artifact, or readiness
report was published or visible. No partial or hidden R3 output sibling was
created.

The `TemporaryDirectory` context manager removed its empty feature-staging
directory while unwinding the exception. Independent post-failure inspection
found absent every `beat-cell-stage2-features-*`,
`chord-audio-lineage-*`, and `chord-runtime-beat-runner-*` directory under the
active system temporary root. No manual cleanup was performed or required.

Repository HEAD remained
`c01991e9608c0f53c8299efceb48caf85f5e98d1`; the index and worktree remained
clean immediately after the failed attempt and independent forensic trace.

Exact protected and downstream counts are:

- Stage1 report JSON parses: `0`;
- Stage1 outcome-object accesses: `0`;
- group/reference-object accesses: `0`;
- published feature summaries or manifests: `0`;
- Stage-B examples artifacts built: `0`;
- selector candidate fits: `0`;
- readiness evaluations or reproduction fits: `0`;
- calibration, test, confirmation, protected player/public-song artifact or
  surface accesses, deployment, or Travis accesses: `0`.

The strict reference-free beat-receipt validation did open its exact admitted,
receipt-bound player repository resources and documentation as source-evidence
bytes. Those reads were part of source-identity validation; no protected player
artifact or evaluation surface was opened.

## Recovery boundary

R3 is terminal. The consumed official CLI invocation is the one R3 feature-set
attempt even though publication did not occur. Same-cycle retry, an environment
override, manual publication of the lost in-memory objects, and reuse of the
R3 output namespace are forbidden.

A further attempt requires a distinct R4 namespace, a new machine authority,
the narrow trusted-temporary-base code fix, final implementation and authority
hashes, a clean committed HEAD, independent immutable-byte audit, and a fresh
two-sweep label-blind preflight before the sole R4 official invocation.

The prospective code-only fix is to resolve `tempfile.gettempdir()` once as an
existing trusted directory and pass that resolved directory explicitly to the
Stage-A `TemporaryDirectory`, matching the established audio-lineage pattern.
It must not change `_reject_symlink_components`, publication ownership,
atomicity, any source input, any feature or reconciliation rule, or any
downstream policy.

The R4 machine authority must be a full R3 copy with only five R3-to-R4 output
namespace substitutions, the active post-freeze-preflight schema bump from v1
to v2, the two active cycle updates (`executionPhase` R3-to-R4 and
`consumesR3OneShot` renamed to `consumesR4OneShot=false`), plus the final corrected
`featureMath.sourceStageAImplementationModuleFileSha256`. Historical R3
literals in the governance-incident disclosure remain unchanged. The failure
and predecessor binding remain in this separate receipt because the exact
machine authority schema has no recovery field. Until the final implementation
hash is inserted and all derived hashes are independently audited, the R4
draft authorizes no execution.

Because the final Stage-A implementation hash changes the complete
feature-math projection hash, every R4 feature summary will carry new
provenance and therefore have a new artifact hash and filename even when all
feature-row values remain identical. The R3 canonical summary-inventory hash
above is historical evidence only and must not be pinned as an R4 expected
digest. The fresh R4 preflight must require run-one/run-two canonical equality
and report its newly observed summary-inventory digest, while the exact
reconciliation row-set SHA-256 remains
`964195b1e89c9de88b1073269d3c160cb8874aad9d52868c36b33eac10bdef9d`.

No code, test, contract, readiness, source, or existing authority file was
changed while preparing this receipt.
