# Isolated VTT Guidance Admin Pilot Implementation

## Task Summary

Lanes: `02 Corpus Pipeline` and `15 QA / Answer Eval`

Implemented the requested removable transcript-derived teaching supplement without blending it into SGF data or source presentation.

The implementation is committed in three separable slices:

- `0ced1e53 feat: add isolated VTT guidance corpus tooling`
- `7aa2be67 feat: gate admin VTT lesson guidance`
- `433669cd feat: style curated lesson guidance`

No deployment, protected-preview activation, embeddings, hosted transcript processing, raw-source mutation, or public/beta access was performed.

## Outcome

- The exact 62-record structured-lesson manifest is generated beneath the ignored v2 private root.
- A resumable local `qwen3.5:27b` generation and `gemma4:12b` privacy-review pipeline is implemented.
- Human approval is mandatory and a partial smoke corpus cannot be approved.
- Only approved E9/general cards can enter a separate checksummed SQLite FTS5 index.
- Runtime retrieval is admin-only and requires all three new default-off flags.
- The legacy 899-row curated-guidance hook is disconnected from `/api/answer`; its old flags no longer activate an answer path.
- Base `answer` and SGF-only `sources` remain unchanged. Guidance is appended only as a distinct `Curated lesson guidance` section.
- Missing, corrupt, unsigned, or mismatched private artifacts fail closed.
- A guarded exact-root purge and full-break runbook are included.

## Corpus and Index Controls

The v2 toolchain implements:

- exact 62-record manifest selection with no recursive ingestion;
- source and overview hashes plus stable source/card/parent identifiers;
- model names, digests, generator version, corpus/privacy/licensing decisions, quote policy, embedding policy, and review state on every card;
- structured strings, frets, pedals, levers, grips, keys, chord functions, and techniques;
- identity/contact/platform/private-path scans;
- normalized ten-word source overlap rejection;
- deterministic E9 string, fret, pedal, and lever validation using the existing copedent model;
- automated privacy/music blocking followed by complete human approve/reject decisions;
- E9/general-only runtime admission;
- atomic FTS database replacement and checksum sidecar;
- runtime verification of checksum, schema, build version, corpus hash/version, table/FTS/source/card counts, and row versions;
- separate overview/detail FTS ranking, source collapse, and a runtime maximum of three cards from two source groups;
- aggregate-only evaluation reports enforcing the 43-detail, 10-broad, human-usefulness, and wrong-instrument thresholds.

No VTT retrieval code reads SGF data, Chroma, vector stores, or embeddings.

## Runtime and UI Controls

All three flags are required:

- `ENABLE_PRIVATE_REVIEW_SOURCES=1`
- `ENABLE_VTT_GUIDANCE_RETRIEVAL=1`
- `ENABLE_VTT_GUIDANCE_IN_ANSWER=1`

The authenticated role must be exactly `admin`. Anonymous, public, beta, developer, dev, and backstage requests cannot open the VTT index.

Eligibility excludes non-steel, gear, entity/history, explicit forum-wisdom, guardrail, and deterministic-fretboard requests. Rendering is deterministic and limited to one concept, three procedure steps, one common mistake, and 1,200 characters.

The UI uses the existing section contract with a dedicated teal guidance treatment. Guidance is never rendered through the SGF source-card loop.

## Current Private Artifact State

Private generated artifacts remain ignored and uncommitted.

- Manifest: 62 records.
- Current local-model smoke: one source, six E9 candidate cards.
- Generator-version matches: 6/6.
- Gemma privacy review passed: 6/6.
- Deterministic music validation passed: 6/6.
- Automated blocked: 0.
- Pending human review: 6.
- Human approved: 0.
- Quote allowed: 0.
- Embedding allowed: 0.
- Approved card file: absent.
- Runtime FTS index: absent.

This partial smoke is intentionally non-promotable. `apply-review` refuses any candidate set that does not cover all 62 manifest sources with exactly one overview per source.

## Tests and Verification

Passed:

```text
.venv/bin/ruff check steel_guitar_rag/vtt_guidance.py steel_guitar_rag/api.py scripts/vtt_guidance.py tests/test_vtt_guidance.py tests/test_api_search.py tests/test_frontend_answer_ui.py
.venv/bin/mypy steel_guitar_rag/vtt_guidance.py scripts/vtt_guidance.py
.venv/bin/python -m pytest tests/test_vtt_guidance.py -q
  13 passed
.venv/bin/python -m pytest tests/test_api_search.py tests/test_frontend_answer_ui.py tests/test_vtt_guidance.py -q
  398 passed
.venv/bin/python -m pytest -q --deselect=tests/test_canonical_frontier_service_deploy.py::CanonicalFrontierLaunchFilesTests::test_installer_render_and_preflight_are_read_only
  1651 passed, 1 deselected
.venv/bin/python scripts/run_world_class_answer_challenge.py --endpoint <local> --ids fmaj7-deterministic tab-deterministic unrelated-entity-guardrail
  3/3 local, no-cost cases passed
```

Local authenticated browser smoke:

- Opened a separate local test tab without modifying the existing Teachable tab.
- Selected the local admin preview and submitted a teaching question.
- Flags-off base answer rendered successfully.
- VTT status logged `disabled`, card count `0`, and empty corpus version.
- Guidance DOM count was `0`, source-card rendering remained separate, and browser console error count was `0`.

Local model smoke:

- Qwen and Gemma were both resolved from loopback Ollama.
- Final-schema smoke produced six pending cards with zero automated blocks.
- Reported hosted calls: `0`.
- Reported embeddings created: `0`.

Purge dry-run resolved only the v2 derived root and required the exact confirmation token. An attempted index build before human approval failed closed because no approved-card file exists.

## Known Unrelated Test Failure

The unmodified full suite has one environment-dependent failure:

```text
tests/test_canonical_frontier_service_deploy.py::CanonicalFrontierLaunchFilesTests::test_installer_render_and_preflight_are_read_only
```

Cause: the pre-existing locally installed canonical-frontier service bundle resolves a required path outside the verifier's configured service root. This is unrelated to the VTT changes and was not modified. All other 1,651 tests pass when that one preflight is deselected.

## Remaining Gates

The implementation is complete, but the private corpus is not runtime-ready. Required next operations are:

1. Run full 62-source local generation with `scripts/vtt_guidance.py generate`.
2. Human-review every generated card and complete the private decision ledger.
3. Apply review, build the FTS index, and create the private retrieval probe ledger.
4. Run the enforced retrieval evaluation and corpus privacy/overlap review.
5. Run an authenticated local browser smoke with the approved index and all flags enabled.
6. Obtain separate explicit approval before any protected-preview flag activation.

Seven paid world-class challenge cases were not run because no paid-case authorization was provided. The challenge bank and all three no-cost local cases were validated.

## Files Changed

Created:

- `steel_guitar_rag/vtt_guidance.py`
- `scripts/vtt_guidance.py`
- `tests/test_vtt_guidance.py`
- `docs/vtt-guidance-admin-pilot.md`
- `docs/handoffs/task-completions/2026-08-11-1026-02-15-vtt-transcript-depth-pilot.md`
- this handoff

Modified:

- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`

Deleted: none.

## Rollback and Full Break

Runtime rollback requires only clearing the three VTT flags and restarting; no SGF artifact changes are involved. Optional derived-data removal uses the guarded purge command documented in `docs/vtt-guidance-admin-pilot.md`.

The purge removes only `corpus-private/vtt-guidance-v2/`. Raw transcript sources remain untouched. Code rollback can revert the UI, runtime, and corpus commits independently in reverse order.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-08-11-1113-02-15-vtt-guidance-admin-pilot.md`

## Files That Must Not Be Staged

- `corpus-private/`
- anything beneath the external `vtt-test` source tree
- raw transcripts, cleaned transcript bodies, private cards, review ledgers, reports, or indexes
- the unrelated pre-existing untracked handoff `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`

## Recommended Next Lane

Continue in lane `02 Corpus Pipeline` for the full local generation batch, then require independent lane `15 QA / Answer Eval` human review before index construction or any enabled browser smoke.
