# Sealed development bar-selector examples

## Task summary

Implemented the development-only join between the frozen uncertainty benchmark,
the Play Along runtime bar-grid manifest, explicit confidence grouping/reference
metadata, and the compact grouped selector API.

The public APIs are:

```python
build_bar_selector_group_manifest(track_descriptors, reference_root=...)

build_bar_selector_examples(
    benchmark_report,
    benchmark_root=...,
    runtime_bar_grid_manifest=...,
    runtime_bar_grid_root=...,
    group_manifest=...,
    group_manifest_root=...,
    summary_output_root=...,
)
```

`build_bar_selector_group_manifest` requires every development descriptor to
state `trackId`, `datasetId`, `role`, `confidenceGroupId`, and `referencePath`.
There is no track-ID, dataset, role, or composition fallback for grouping. The
same explicit group may contain GuitarSet comp/solo/player tracks and known
derivatives from other corpora. All descriptors and all splits are validated
before the reference root or any reference path is resolved or opened. The
builder hashes each reference, emits only a relative path beneath the declared
root, seals every track row, and seals the complete manifest.

`build_bar_selector_examples` accepts already-parsed JSON envelopes so it can
reject calibration, test, heldout, confirmation, training, or any other split
before touching a nested prediction, timing, reference, or output path. It
requires:

- a `chord_benchmark_report_v2` factorized uncertainty report with
  `developmentOnlyExperiment=true`, `promotionEligible=false`, no oracle beat
  grid, and `referenceFree=true` uncertainty;
- an exact `chord_runtime_bar_grid_manifest_v2` whose top level and every
  active track declare `runtimeAttested=true`/`selectorUseAllowed=true` as
  applicable;
- successful validation through the runtime lane's public
  `validate_runtime_bar_grid_manifest(..., artifact_root=...,
  verify_sources=True)` API, including exact current pinned source hashes and
  the actual content-addressed timing artifacts beneath the declared root;
- actual `sourceClass=runtime`, explicit, deployable, reference-free timing
  whose source-contract hash matches the runtime analyzer manifest;
- an exact `chord_bar_selector_group_manifest_v1` with an explicit
  `confidenceGroupId` for every track;
- identical track-ID sets across all three sources;
- exact report, prediction-file, prediction-core, uncertainty, timing,
  timing-contract, runtime-source-contract, reference, per-track, and manifest
  hashes. `summary_output_root` is resolved before writing and must be
  path-disjoint from the benchmark, runtime, and group roots in both
  directions; symlink aliases cannot hide overlap.

For every track, the join calls `summarize_prediction_bars(prediction, timing)`
and validates its canonical seal before any reference is opened. It then writes
the complete prediction-only summary to a content-addressed JSON sidecar. Each
sidecar is individually atomic: a fully written and fsynced temporary inode is
hard-linked into place without overwriting an existing path. Symlinked parent
components are rejected, an exact pre-existing sidecar is safely reused, and a
mismatched existing file is rejected without modification. All tracks have
materialized and re-read summaries, plus compact per-bar hashes, before the
first reference file is opened.

This is intentionally not a set-atomic sidecar transaction. If a later track
fails, earlier content-addressed summaries may remain, but they are immutable,
unreferenced by any returned examples artifact, and safe to reuse after an
exact-content check.

Only after the prediction-only phase completes does the join open references.
It calls `score_bar_product_confidence` with every outcome/eligibility argument
explicitly frozen: score schema `chord_bar_product_confidence_v1`, reference
dominance `0.75`, prediction coverage `0.75`, prediction dominance `0.75`, and
confidence thresholds `[0.0]`. The returned score schema, configuration, curve,
and zero-threshold counts are validated. An example is included only when
`scoreBar.eligible=true` and `scoreBar.correct` is boolean. The reference
contributes exactly `outcome: {correct: boolean}`. Reference labels,
eligibility, dataset, and role never enter `featureValues`.

The runtime v2 duration is the player's integer-millisecond duration while the
frozen prediction may retain more precision. The prediction-only summarizer
first proves the exact equality
`runtimeDuration == floor(predictionDuration*1000 + 0.5)/1000`. The reference
join then uses the full-precision prediction duration only for the final score
bar end, so scored bars and compact summary bars are identical. A nearby value
is rejected; there is no tolerance-based duration substitution. This bar-end
rule is part of the frozen outcome/eligibility contract and its SHA-256.

The output `chord_bar_selector_examples_v1` is sorted by track and bar index,
seals every compact summary and example, seals the example set and complete
artifact, and binds the exact feature order, uncertainty/model/decoder/member
order, feature specification, observability profile, runtime timing source, and
the canonical bar outcome/eligibility contract plus its SHA-256. Each compact
summary carries its own `trackId` and `sharedBindingsSha256`, preventing a
summary from being silently reassigned to another track or selector binding.

All SHA-256 values in this artifact family are canonical integrity commitments,
not digital signatures and not independent proof of provenance or
authorization. Runtime provenance trust comes from the strict in-process v2
generator/validator boundary and exact pinned-source comparison; the hashes
make subsequent mutation and cross-artifact splicing detectable.

No real corpus, benchmark prediction, generated heldout/calibration artifact,
audio, model, private source, or reference file was opened during this task.
No model was trained and no threshold was selected.

## Files changed

- `steel_guitar_rag/chord_reader/bar_examples.py` (new)
- `tests/test_chord_reader_bar_examples.py` (new)
- `docs/handoffs/task-completions/2026-08-20-1945-20-sealed-development-bar-selector-examples.md` (new)

No benchmark, CLI, current inference, selector, runtime timing, corpus,
production, deployment, auth, UI, or model file was edited by this task.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_bar_examples.py`
  - `37 passed`
- `.venv/bin/python -m pytest -q tests/test_chord_reader_bar_examples.py tests/test_chord_reader_bar_selector.py`
  - `82 passed`
- Runtime/examples/selector/uncertainty integration with the two environment-
  dependent live Chrome launches deselected:
  - `178 passed, 2 deselected`
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/bar_examples.py tests/test_chord_reader_bar_examples.py`
  - passed
- `.venv/bin/python -m py_compile steel_guitar_rag/chord_reader/bar_examples.py tests/test_chord_reader_bar_examples.py`
  - passed
- `git diff --check`
  - passed

Focused coverage includes exact compact selector compatibility; canonical
source/example/shared-binding/artifact hashes; explicit cross-corpus grouping;
no group fallback; descriptor and envelope split rejection before path access;
exact track-set identity; prediction, runtime timing, and reference drift;
strict public v2 validation with real content-addressed timing files;
nonattested-manifest and offline-proxy timing rejection even after all relevant
hashes are resealed;
structurally mixed-bar exclusion under the existing product semantics; complete
and hash-stable feature materialization before the first protected reference
open; exact frozen scoring arguments/schema/configuration/curve and
eligible-plus-boolean inclusion; content-addressed sidecars; source/output
root-disjointness including symlink aliases; symlink-component rejection; and
refusal to overwrite mismatched existing content.

## Risks

Risk is medium-low. The module is additive and has no CLI or production caller.
The runtime v2 consumer contract is now exact and delegates validation to the
runtime lane's public validator. The remaining provenance limitation is that
canonical hashes are integrity commitments rather than signatures; callers
must preserve the trusted local generator/validator execution boundary.

The group descriptor manifest is deliberately explicit and therefore requires
an upstream human/research decision about which tracks are derivatives of the
same musical work. The helper prevents accidental fallback but cannot discover
those relationships.

## Human decision needed

No decision is needed to stage this isolated implementation. Before the real
246-song development run, the research owner must provide the explicit
`confidenceGroupId` assignments, including GuitarSet composition/player groups
and known cross-corpus derivatives. Calibration and heldout data remain sealed.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/bar_examples.py`
- `tests/test_chord_reader_bar_examples.py`
- `docs/handoffs/task-completions/2026-08-20-1945-20-sealed-development-bar-selector-examples.md`

## Files that must not be staged

- Do not stage the concurrently owned `bar_selector.py`, runtime bar-grid
  module/scripts/tests/handoff, core uncertainty files, generated summary
  sidecars, reports, predictions, feature caches, audio, references, corpus
  material, ONNX files, calibration/test artifacts, or private data under this
  handoff.

## Recommended next lane

Lane 15 should run the final runtime-grid -> group-manifest -> sealed examples
-> grouped-selector synthetic round trip after the runtime timing contract is
frozen. Lane 01 may then exact-path stage this three-file slice together with
the separately reviewed selector/runtime slices.

## Commit readiness

Ready for exact-path integrated review. This task was explicitly instructed not
to commit.
