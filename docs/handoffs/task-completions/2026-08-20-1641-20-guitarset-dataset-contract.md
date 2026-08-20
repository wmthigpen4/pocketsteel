# GuitarSet dataset contract repair

## Task summary

Repaired the GuitarSet adapter so chord annotation meaning is explicit and
deterministic. The parser now selects the instructed lead-sheet annotation by
role metadata rather than array position, preserves the note-derived performed
annotation as a separate reference, records `performanceRole` as `comp` or
`solo`, and fails closed when chord roles or performance identity are missing,
duplicated, or contradictory. Chord observations now retain their explicit
half-open JAMS intervals, preserve gaps, avoid joining equal labels across a
gap, and reject invalid or overlapping intervals.

The existing Play Along contract remains backward-compatible: `referencePath`
and `labelSource: ground_truth` still point to the normalized instructed
lead-sheet harmony. The new performed reference retains GuitarSet's native
Harte labels and declares both that encoding and its hybrid provenance: quality
evidence comes from separate-string note transcriptions, while segmentation and
root come from the instructed chord sheet.

No model, trainer, cache, generated corpus, sealed protocol, calibration/test
material, production runtime, or UI was changed.

## Files changed

- `steel_guitar_rag/chord_reader/datasets.py`
- `tests/test_chord_reader_dataset_timing.py`
- `tests/test_chord_reader.py`
- `docs/handoffs/task-completions/2026-08-20-1641-20-guitarset-dataset-contract.md`

No files were deleted and no generated artifacts were retained.

## Tests and checks

- `.venv/bin/pytest -q tests/test_chord_reader_dataset_timing.py tests/test_chord_reader.py -k 'guitarset'`
  - Passed: 10; deselected: 76.
- `.venv/bin/pytest -q tests/test_chord_reader_dataset_timing.py tests/test_chord_reader.py`
  - Passed: 86.
- `.venv/bin/pytest -q tests/test_chord_reader_harmonic_prior.py tests/test_chord_reader_artifact_integrity.py tests/test_chord_reader_split_protocol.py tests/test_chord_reader_dataset_timing.py tests/test_chord_reader.py`
  - Passed: 124.
- `.venv/bin/pytest -q tests/test_chord_reader*.py`
  - Passed: 273; dependency-gated skips: 4.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/datasets.py tests/test_chord_reader.py tests/test_chord_reader_dataset_timing.py`
  - Passed.
- `git diff --check`
  - Passed for the shared worktree.
- No raw-corpus smoke was run for the interval/provenance repair. Only synthetic
  fixtures were opened.

Focused tests cover annotation-order reversal, missing and duplicated chord
roles, missing and conflicting comp/solo identity, performed-reference
preservation, hybrid provenance fields, explicit gaps, same-label gaps,
overlap rejection, and the unchanged contiguous instructed primary output.

## Held-out access process note

An earlier revision of this handoff recorded a read-only parser smoke across all
360 public-release JAMS files. That run reported aggregate parse/role counts and
did not display chord labels, score a model, or tune a decision. It nevertheless
means any identities in that set which later map to development, calibration,
or test partitions must not be described as literally "never opened." This
repair did not repeat that smoke. Future adapter iteration must use synthetic
fixtures or an explicitly train-only projection, and strict confirmation claims
must carry this access note or use a separately pristine identity set.

## Integration notes

Prepared GuitarSet tracks now add:

- `performanceRole` (`comp` or `solo`);
- `performedReferencePath`;
- `labelSourceDetail` and `labelSourceProvenance` for the instructed primary;
- performed-label source detail/provenance;
- `chordProvenance` for both semantic targets;
- timing provenance naming the `chord` and `beat_position` namespaces and both
  chord annotation roles.

The primary reference JSON retains the existing `chord_reference_v1` shape and
normalized instructed segments. The secondary reference also uses the reference
envelope but carries a `provenance` object with `annotationRole: performed`,
`sourceNamespace: chord`, `labelEncoding: guitarset-harte`, sheet-derived root
and segmentation fields, and separate-string note-transcription quality
evidence.

Both references use the observation's explicit `[time, time + duration)`
interval. Gaps remain gaps. Contiguous equal labels may be coalesced without
changing their covered interval, but equal labels separated by any gap remain
separate. Overlapping or nonpositive chord observations fail closed.

Performed labels such as `C:maj7/1` are intentionally preserved exactly. They
must not be passed directly to the current generic normalizer; a future
performed-label training experiment needs an explicit, tested GuitarSet-Harte
projection. Regenerating manifests under this additive contract will change
artifact hashes and therefore requires a new protocol version rather than
mutating any sealed artifact.

## Risk assessment

Risk is medium. The primary semantic target remains unchanged, but explicit
source gaps are no longer fabricated into continuous chord coverage. Consumers
opting into `performedReferencePath` must understand its native label encoding
and hybrid chord-sheet/note evidence. The instructed role is inferred only under
the official release contract: exactly one unmarked chord annotation paired
with exactly one metadata-identified note-transcription annotation. Any
different or ambiguous shape fails closed.

Rollback is limited to the additive GuitarSet parser/preparer changes and the
focused fixtures; no data migration or generated-output cleanup is required.

## Human decision needed

No decision is needed to accept this dataset-contract repair. A separate product
decision remains for a later challenger: whether to train the acoustic reader
on comp performances only and whether/how to project performed Harte labels into
an auxiliary quality target.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/datasets.py`
- `tests/test_chord_reader_dataset_timing.py`
- `tests/test_chord_reader.py`
- `docs/handoffs/task-completions/2026-08-20-1641-20-guitarset-dataset-contract.md`

## Files that must not be staged

Parallel architecture work currently visible in the shared worktree is outside
this task and must not be staged with this slice:

- `steel_guitar_rag/chord_reader/benchmark.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/harmonic_prior.py`
- `tests/test_chord_reader_factorized.py`
- `tests/test_chord_reader_harmonic_prior.py`
- all `tmp/` artifacts, caches, reports, prepared manifests, references, and
  sealed protocols.

## Recommended next lane

Lane 15 should review the additive manifest/reference contract and rerun the
focused dataset suite after the parallel architecture changes settle. Lane 20
can then create a new train/development-only comp-role ablation without touching
the existing sealed protocol.

## Commit readiness

Safe to commit by exact path after shared-worktree integration review.

## Suggested next step

`Lane 15: Review the GuitarSet dataset contract in
docs/handoffs/task-completions/2026-08-20-1641-20-guitarset-dataset-contract.md,
verify the four exact files only, and run the focused chord-reader dataset
tests. Do not regenerate sealed artifacts.`
