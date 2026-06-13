# B9 E-Lower Fretboard Payload

## Task summary
- Requested: fix the remaining exploratory-smoke product failure where `Is 5-7-8 with E lowered a B9 pocket?` returned the correct deterministic, source-free answer text but no top-level `response.fretboard`.
- Completed: added a focused pitch-math fretboard payload for the B9/E-lower diagnostic route while preserving the existing answer text, source suppression, warning suppression, and no-SGF-fragment behavior.
- Intentionally not changed: deployment, DNS, staging, commits, Chroma/vector stores, embeddings, `corpus-private`, `corpus-v2`, `source-inbox`, scraping, provenance/legal files, deployment secrets, `.wrangler`, auth, and design assets.

## Branch and HEAD
- Branch: `feature/answer-api`
- HEAD: `bad18d8`
- Worktree: dirty before this task with many unrelated lane changes. This task did not stage or commit anything.

## Root cause
- Bucket: A. deterministic text route bypassed fretboard construction.
- Details:
  - `visual_fretboard_curated_answer()` already routed the B9 question to `e_lower_578_b9_answer_for_question()`.
  - `/api/answer` correctly attaches `response.fretboard` when `fretboard_payload_for_question()` returns a payload.
  - `fretboard_payload_for_question()` returned `None` for the B9 yes/no diagnostic route, so the correct text answer was returned without visualization data.
  - Schema/API normalization did not strip the payload; the payload was never built for this route.

## Files changed
- Changed files:
  - `pocketsteel/fretboard_examples.py`
  - `tests/test_fretboard_examples.py`
  - `tests/test_api_search.py`
- Created files:
  - `docs/handoffs/task-completions/2026-06-13-0011-05-b9-elower-fretboard-payload.md`
- Deleted files: none.
- Generated artifacts: none.

## Exact behavior before/after
- Before:
  - Prompt: `Is 5-7-8 with E lowered a B9 pocket?`
  - Answer text: correct and source-free; said it is not a full B9 pocket, resolves to D major at fret 3, and can suggest rootless B minor 7 color against B.
  - `sources`: `[]`
  - `warnings`: `[]`
  - `response.fretboard`: missing.
- After:
  - Same answer text is preserved.
  - `sources`: `[]`
  - `warnings`: `[]`
  - `response.fretboard.title`: `5-7-8 E-lower B9 check`
  - `response.fretboard.positions`: one focused pitch-validated card:
    - id: `b9-check-e-lower-5-7-8-3`
    - root: `D`
    - quality: `major`
    - fret: `3`
    - grip: `5-7-8`
    - function: `B9 check`
    - notes: string 5 = `D`, string 7 = `A`, string 8 = `F#`
  - `response.fretboard.sourceContext`: rule source `pocketsteel.fretboard_examples`

## Tests and checks
- Command:
  - `.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_search.py tests/test_api_contract.py`
- Result:
  - `191 passed in 0.64s`
- Command:
  - `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py`
- Result:
  - `43 passed in 0.20s`
- Command:
  - `.venv/bin/python -m pytest`
- Result:
  - `517 passed in 3.88s`
- Command:
  - `git diff --check`
- Result:
  - passed with no whitespace errors.
- Tests added/updated:
  - Updated `tests/test_fretboard_examples.py` so the B9 yes/no prompt now expects a focused deterministic payload instead of `None`.
  - Updated `tests/test_api_search.py` so `/api/answer` for the exact prompt verifies:
    - answer says it is not B9,
    - no SGF source cards,
    - no weak-source warning,
    - top-level `response.fretboard` exists,
    - `response.fretboard.positions` is non-empty,
    - no `[object Object]` risk in answer text,
    - payload conforms to the existing API/schema expectations.

## Local API verification
- Existing `127.0.0.1:8783` process:
  - PID `94037` was still serving stale code and continued to return the old text-only response.
  - I did not stop or modify that existing process.
- Fresh current-code verification server:
  - Started loopback-only server on `127.0.0.1:8784`.
  - Command:
    ```bash
    STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
    STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
    STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
    STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
    STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
    STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
    STEEL_RAG_RETRIEVAL_DEBUG=true \
    .venv/bin/python scripts/serve_v2_rerank_smoke.py \
      --host 127.0.0.1 \
      --port 8784 \
      --v2-chroma-path corpus-v2/vector-stores/chroma \
      --v2-collection steel_guitar_unified_v2 \
      --answer-auth-mode local_dev \
      --auth-provider scaffold
    ```
  - Curl result for `Is 5-7-8 with E lowered a B9 pocket?`:
    - `sources=0`
    - `warnings=[]`
    - `fretboard_title=5-7-8 E-lower B9 check`
    - `position_count=1`
    - `positions=[('b9-check-e-lower-5-7-8-3', 'D', 'major', 3, '5-7-8', 'B9 check')]`
    - `sourceContext=[{'kind': 'rule', 'label': 'Pitch-validated E9 copedent rule', 'sourceId': 'pocketsteel.fretboard_examples'}]`
  - The temporary `8784` server was stopped after verification.

## Integration notes
- Lane 15 should restart the `127.0.0.1:8783` loopback server before rerunning exploratory smoke; the existing process was stale after this code change.
- This fix keeps deterministic B9/E-lower answers source-free and warning-free.
- This fix does not add SGF fallback, source cards, weak-source warnings, raw UI geometry, or private-source exposure.
- The focused payload intentionally visualizes the actual pitch classification at fret 3: D major, not B9.
- The existing answer still mentions that the same 5-7-8 E-lower grip spells B major at frets 0, 12, and 24, but the visual card stays focused on the failed B9 diagnostic claim.

## Safe-to-stage file list
- `pocketsteel/fretboard_examples.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-13-0011-05-b9-elower-fretboard-payload.md`

## Files that must remain unstaged
- `corpus-private/**`
- `corpus-v2/**`
- `source-inbox/**`
- Chroma/vector-store files
- embeddings
- scraper outputs
- provenance/legal source dumps
- deployment secrets
- `.wrangler/**`
- DNS/tunnel/app config
- unrelated dirty worktree files from other lanes

## Risk assessment
- Low.
- Why:
  - The runtime change is a narrow payload-builder addition for one deterministic route.
  - Text answer, source suppression, warning suppression, and existing pitch math are preserved.
  - Focused and full test suites passed.
- Rollback notes:
  - Revert the B9 payload helper and the two test expectation updates if the product decision changes back to text-only diagnostics.

## Commit readiness
Safe to commit

## Suggested next step
- Recommended next lane: Lane 15 QA / Answer Eval.
- Exact recommended task:
  - "Restart the local loopback API on `127.0.0.1:8783` from the current worktree and rerun exploratory answer smoke. Confirm `Is 5-7-8 with E lowered a B9 pocket?` now passes with top-level `response.fretboard`, `sources: []`, and no weak-source warning."
