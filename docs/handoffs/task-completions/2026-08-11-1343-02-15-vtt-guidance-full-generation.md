# VTT Guidance Full Local Generation and Candidate Audit

## Task Summary

Lanes: `02 Corpus Pipeline` and `15 QA / Answer Eval`

Completed the full local-model generation pass for the isolated VTT guidance pilot and added a reproducible metadata-only candidate corpus audit. Transcript-derived material remains a removable supplement beneath the ignored `corpus-private/vtt-guidance-v2/` tree and has not been blended into SGF.

No deployment, protected-preview activation, embeddings, hosted transcript processing, raw-source mutation, human approval, index construction, or public/beta access was performed.

## Code Changes

This continuation added:

- a longer guarded local-model timeout for larger cleaned lessons;
- bounded deterministic generation of two to four cards per source;
- normalization for word/ordinal number anchors, paired pedal phrases, and the E-to-F lever alias;
- a metadata-only `audit-corpus` command covering manifest, source hashes, checkpoints, card references, privacy markers, normalized ten-word overlap, versions, quote/embedding policy, review consistency, and runtime eligibility;
- focused audit coverage and updated private-corpus runbook instructions.

Continuation commits:

- `a3a63b44 fix: allow larger local VTT lessons to finish`
- `ce889431 fix: bound and normalize VTT card generation`
- `eeb37346 feat: audit private VTT candidate corpus`

The earlier implementation commits remain:

- `0ced1e53 feat: add isolated VTT guidance corpus tooling`
- `7aa2be67 feat: gate admin VTT lesson guidance`
- `433669cd feat: style curated lesson guidance`
- `ab056bef docs: record VTT guidance admin pilot handoff`

## Full Generation Result

The loopback-only batch completed successfully:

- manifest sources: 62;
- processed sources: 62;
- generated in this batch: 60;
- resumed and revalidated: 2;
- candidate cards: 247;
- overview cards: 62, exactly one per source;
- generation model: `qwen3.5:27b`, one consistent local digest;
- privacy model: `gemma4:12b`, one consistent local digest;
- hosted calls: 0;
- embeddings created: 0;
- partial generation: false.

Instrument classification:

- E9: 223;
- general technique: 8;
- unknown: 16;
- C6/non-pedal: 0 in this generated set.

Card types:

- overview: 62;
- procedure: 74;
- transfer: 50;
- concept: 30;
- common mistake: 16;
- setup: 15.

## Candidate Audit Result

`scripts/vtt_guidance.py audit-corpus` passed the candidate integrity gate:

- manifest count: 62;
- candidate source count: 62;
- checkpoint count: 62;
- checkpoint/card mismatch: 0;
- missing source files: 0;
- source hash mismatch: 0;
- card source-reference mismatch: 0;
- manifest policy mismatch: 0;
- generator-version mismatch: 0;
- blocked-status consistency mismatch: 0;
- private-marker or normalized ten-word source overlap hits: 0;
- quote or embedding enabled: 0;
- privacy review passed: 247/247.

The runtime gate remains false by design because no card is human-approved and no index exists.

## Review State and Required Human Gate

- pending human review: 143;
- automated blocked: 104;
- pending and runtime-instrument eligible: 131 (124 E9 and 7 general);
- pending but held offline for unknown instrument: 12;
- approved: 0;
- approved-card file: absent;
- runtime FTS index: absent.

The 104 automated holds are technical-structure holds, not privacy-review failures. Recorded finding totals include unsupported or invalid lever, pedal, grip, key, and numeric-anchor labels. Some are likely ordinary aliases expressed outside the deterministic schema; others are genuinely misplaced anchors. They remain blocked rather than being loosened merely to increase yield.

The complete private human decision ledger must cover all 247 cards. At minimum, the 104 automated-blocked cards and 12 remaining unknown-instrument cards must be rejected. The maximum current runtime-eligible review pool is 131 cards. Automated-blocked cards cannot be overridden without corrected regeneration.

## Tests and Verification

Passed:

```text
.venv/bin/ruff check scripts/vtt_guidance.py tests/test_vtt_guidance.py
  All checks passed
.venv/bin/mypy scripts/vtt_guidance.py steel_guitar_rag/vtt_guidance.py
  Success: no issues found
.venv/bin/pytest -q tests/test_vtt_guidance.py
  15 passed
.venv/bin/python -m pytest tests/test_api_search.py tests/test_frontend_answer_ui.py tests/test_vtt_guidance.py -q
  406 passed
.venv/bin/python -m pytest -q --deselect=tests/test_canonical_frontier_service_deploy.py::CanonicalFrontierLaunchFilesTests::test_installer_render_and_preflight_are_read_only
  1653 passed, 1 deselected
```

The one deselected canonical-frontier preflight remains the previously documented unrelated external-bundle issue. No VTT test or broad regression failed.

## Remaining Gates

1. A human reviews the private queue and completes an approve/reject decision for every one of the 247 cards.
2. Apply the complete ledger; the command rechecks privacy, overlap, instrument, human-approval, quote/embedding, and deterministic E9 gates.
3. Build the separate private FTS5 index from approved cards only.
4. Create the required private retrieval probe ledger and run the enforced detail, broad, usefulness, and wrong-instrument retrieval gates.
5. Run local authenticated admin smoke with all three flags enabled and the approved index present.
6. Obtain separate explicit approval before any protected-preview activation.

Until those steps finish, keep all three feature flags off. The base SGF answer path and SGF source cards remain unchanged.

## Privacy, Isolation, and Rollback

- All generated cards, checkpoints, review files, reports, and future indexes remain ignored beneath `corpus-private/vtt-guidance-v2/`.
- Raw `~/Documents/vtt-test` sources were read only and remain untouched.
- No private content or source metadata was committed.
- No VTT retrieval index exists, so runtime cannot serve generated guidance.
- A full product break still consists of clearing the three VTT flags, restarting, verifying no VTT index access, and optionally running the guarded exact-root purge.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-08-11-1343-02-15-vtt-guidance-full-generation.md`

## Files That Must Not Be Staged

- `corpus-private/`
- anything beneath the external `vtt-test` source tree
- raw transcripts, cleaned transcript bodies, candidate cards, checkpoints, review ledgers, reports, approved cards, or indexes
- the unrelated pre-existing untracked handoff `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`

## Recommended Next Lane

Continue in lane `15 QA / Answer Eval` for the private human card review. Do not build an index or enable runtime flags until the complete human ledger is applied successfully.
