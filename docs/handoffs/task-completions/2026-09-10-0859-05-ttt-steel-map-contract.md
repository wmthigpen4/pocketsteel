# TTT Steel Map deterministic contract

## Task summary

Added a small, generated, deterministic E9 contract for TTT Steel Map. It
does not change Steel Guitar RAG retrieval, corpus, server, storage, or UI.
The producer uses only the Emmons profile and fretboard grip vocabulary.

## Files changed

- `steel_guitar_rag/ttt_steel_map_contract.py`
- `scripts/export_ttt_steel_map_contract.py`
- `contracts/steel-map-e9-contract-v1.json`
- `tests/test_ttt_steel_map_contract.py`

## Tests and checks

- `python3 scripts/export_ttt_steel_map_contract.py --check` — passed.
- Direct Python deterministic-contract smoke assertion — passed.
- `pytest` is not installed in this checkout, so the new pytest file was not
  executed here.

## Integration notes

The snapshot pins a source revision and SHA-256 content digest. It omits
absolute open-string pitches because the approved #65 boundary retains TTT's
established register convention. It includes 5-6-9 and 3-5-9 as reviewed grip
metadata, not as preapproved seventh voicings.

## Risk assessment

Low. This is an offline data export with no production wiring.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/ttt_steel_map_contract.py`
- `scripts/export_ttt_steel_map_contract.py`
- `contracts/steel-map-e9-contract-v1.json`
- `tests/test_ttt_steel_map_contract.py`
- `docs/handoffs/task-completions/2026-09-10-0859-05-ttt-steel-map-contract.md`

## Files that must not be staged

Corpus, retrieval, deployment, auth, private, and generated runtime files.

## Recommended next lane

TTT Steel Map consumption and verification.

## Commit readiness

Safe to commit

## Suggested next step

Commit the listed source-contract producer files, then vendor the exact
snapshot in TTT with its sync check.
