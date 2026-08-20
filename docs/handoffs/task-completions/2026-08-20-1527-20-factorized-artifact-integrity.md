# Factorized artifact integrity seal

## Task summary

Added a tamper-evident integrity layer for factorized training artifacts. `seal_factorized_artifact_manifest()` validates and hashes every selected feature NPZ and factorized-label NPZ, records each file's SHA-256 and byte count, and freezes the canonical artifact set under `artifactSetSha256`. `validate_factorized_artifact_manifest()` validates metadata-only or rehashes/revalidates every selected file.

The validator rejects symlinked paths (including symlinked parent components), non-absolute/unsafe paths, rogue or duplicate ZIP members, encrypted/non-DEFLATE members, object arrays, non-finite features, incorrect feature contracts, frame/feature/label misalignment, invalid label class ranges, duplicate IDs, unsupported splits, path swaps, and changed file bytes. It reads no audio or reference path.

Strict split-protocol training now requires and verifies this seal before importing/building the model. Legacy manifests without a split protocol remain supported; an unsigned legacy seal, when present, is also verified. Training provenance records the artifact-set hash.

Added `seal-factorized-artifacts INPUT OUTPUT`. The CLI writes the sealed manifest via flush/fsync plus atomic replace. Sealing a manifest that already contains `splitProtocol` fails with instructions to seal the source manifest and then refreeze, preserving the split-protocol hash chain.

## Files changed

- `steel_guitar_rag/chord_reader/artifact_integrity.py`
- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_artifact_integrity.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1527-20-factorized-artifact-integrity.md`

## Tests/checks run

- Artifact-integrity, factorized, and split-protocol tests: 58 passed, 1 skipped.
- Ruff on all owned implementation/test files: passed.
- Python compile check: passed.
- A broader 200-test chord-reader run reached 197 passed and 2 skipped, with one unrelated concurrent failure in `test_promotion_gate_requires_material_gain_and_runtime`: the updated promotion dispatcher now requires an explicit report schema, while that older test fixture supplies none.
- No real corpus scan or model training was run.

## Risks

- Browser feature NPZs do not embed track IDs; pre-seal identity comes from the manifest path. Once sealed, path swaps and byte swaps are detected. Dasheng NPZs additionally verify their embedded track ID.
- Validation intentionally scans every selected artifact in strict training. On the full corpus this is I/O-heavy but occurs before model construction and is the required integrity gate.
- Direct benchmark-function callers remain outside this scope; no benchmark implementation was edited.

## Human decision needed

None. The required operational order is now explicit: factorized-label cache, artifact seal, split-protocol freeze, strict training.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/artifact_integrity.py`
- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_artifact_integrity.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1527-20-factorized-artifact-integrity.md`

## Files that must not be staged

- Generated sealed manifests, NPZ caches, model weights, benchmark outputs, audio, and unrelated dirty files.

## Recommended next lane

Lane 20 can seal the real training source manifest as a separately reviewed I/O operation, then rebuild and validate the split protocol before any challenger training.

## Commit readiness

The implementation is focused-test ready for parent integration. Nothing was staged or committed.
