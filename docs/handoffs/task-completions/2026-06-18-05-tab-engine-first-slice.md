# 2026-06-18 Lane 05 Tab Engine First Slice

## Task Summary

Requested: build the first deterministic Steel Guitar RAG tab engine slice for Steel Guitar RAG, guided by the tab-engine/task prompt and the repo protocol.

Completed:

- Added a small rules-layer tab module at `steel_guitar_rag/tab_engine.py`.
- Added structured dataclasses for copedent profile, pedal/lever effects, tab notes, tab events, validation issues, and render results.
- Added the default 10-string E9 profile:
  - Open strings: 1 F#, 2 D#, 3 G#, 4 E, 5 B, 6 G#, 7 F#, 8 E, 9 D, 10 B.
  - Controls: A, B, C, E, F, V, G, D with string-specific affected strings.
  - User-facing mapping: P1=A, P2=B, P3=C, LKL=F, LKR=E, LKV=V, RKL=G, RKR=D.
- Added validation for string range, fret range, note count, duplicate strings, mixed frets, unknown changes, and changes placed on unaffected strings.
- Added fixed-width monospace rendering with exactly 10 string rows, optional chord/lyric rows, event-column alignment, and no filler dashes.
- Added deterministic example events for G open, G-to-C, A+B major, E-lower color, and a short beginner lick.
- Added `POST /api/tab/render` for structured local/API use without wiring it into `/api/answer` or RAG.
- Added focused tests in `tests/test_tab_engine.py`.

Intentionally not changed:

- No `/api/answer` behavior changes.
- No RAG prompt/retrieval changes.
- No UI tab editor or frontend rendering work.
- No Chroma, embeddings, scraping, corpus, auth, DNS, deployment, private source, or design asset changes.
- No slant support.
- No raw x/y UI geometry.

Notes:

- The prompt asked to use `steel_rules_engine.txt` and `steel_tab_rules.txt`. I searched for both exact filenames and related rule filenames with `find`/`rg`; neither file was present in the workspace at task time. The implementation follows the pasted task contract and existing repo conventions.

## Files Changed

Changed:

- `steel_guitar_rag/api.py`
- `steel_guitar_rag/tab_engine.py`
- `tests/test_tab_engine.py`
- `docs/handoffs/task-completions/2026-06-18-05-tab-engine-first-slice.md`

Created:

- `steel_guitar_rag/tab_engine.py`
- `tests/test_tab_engine.py`
- `docs/handoffs/task-completions/2026-06-18-05-tab-engine-first-slice.md`

Deleted:

- None.

Generated artifacts:

- None.

## API Behavior

Added:

- `POST /api/tab/render`

Example successful response shape:

```json
{
  "ok": true,
  "tab": "Ch |G\n 1 |\n ...",
  "issues": [],
  "metadata": {
    "profile": "default_e9",
    "event_count": 1
  }
}
```

Invalid structured tab returns `200 OK` with `ok: false`, an empty `tab`, and structured `issues`. This keeps the API simple for a future UI form that can show validation errors without treating them as server failures.

## Validation Contract Implemented

- Strings must be 1 through 10.
- Frets must be 0 through 24.
- Each event must have 1 through 3 notes.
- Multi-note events must be on one fret until slants are supported.
- Duplicate strings inside one event are rejected.
- Unknown changes are rejected.
- String-affecting changes can appear only on strings they affect.
- A pedal on string 4 is rejected.
- A pedal on string 5 is accepted.
- B pedal on string 6 is accepted.
- F lever on string 4 is accepted.
- Unaffected strings do not display a pedal/lever suffix.
- Chords and lyrics align to the event start column.
- Renderer always produces 10 string rows.
- Renderer uses no filler dashes.

## Tests And Checks

Run:

```bash
git status --short
find . -maxdepth 4 \( -name 'steel_rules_engine.txt' -o -name 'steel_tab_rules.txt' \) -print
rg --files | rg '(^|/)(steel_.*rules|.*tab.*rules|tab_engine|api\.py|test_.*api|copedent|fretboard_examples|AGENTS\.md)$'
.venv/bin/python -m py_compile steel_guitar_rag/tab_engine.py steel_guitar_rag/api.py
.venv/bin/python -m pytest tests/test_tab_engine.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
.venv/bin/python -m pytest tests/test_api_search.py -q
git diff --check
.venv/bin/python -m pytest
git status --short
```

Results:

- `py_compile`: passed.
- `tests/test_tab_engine.py -q`: 15 passed.
- `tests/test_api_contract.py -q`: 4 passed.
- `tests/test_api_search.py -q`: 246 passed.
- `git diff --check`: passed.
- Full pytest: 735 passed, 2 failed.

Full pytest failures were unrelated to this tab-engine slice and came from existing dirty static/UI state:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

## Integration Notes

- The new tab engine is independent of SGF retrieval and source cards.
- `/api/tab/render` is deterministic and does not use private data.
- Future Lane 06 UI can call `/api/tab/render` with structured events, then show the raw `tab` plus validation `issues`.
- Future Lane 18/Product may decide whether example endpoints should be added. This slice keeps examples available in Python only via `tab_examples()` / `render_example()`.
- The renderer is deliberately conservative: it rejects mechanically invalid “fake tab” where a global A+B change is stamped onto strings 4, 5, and 6. The corrected string-aware version uses no change on string 4, A on string 5, and B on string 6.

## Risk Assessment

Risk: Low to medium.

Why:

- The tab engine itself is isolated.
- The only existing runtime file touched is `steel_guitar_rag/api.py`, where a new route was added before `/api/answer`.
- Focused API tests passed, which lowers risk of answer/search regression.
- Full-suite failure prevents commit readiness, even though failures appear unrelated.

Rollback notes:

- Revert only `steel_guitar_rag/tab_engine.py`, `tests/test_tab_engine.py`, and the `/api/tab/render` import/route in `steel_guitar_rag/api.py`.

## Human Decision Needed

Yes.

Decision:

- Full pytest is not green due unrelated static/UI failures. A human or Repo Steward should decide whether this backend slice may proceed after those known blockers are resolved or explicitly exempted.

## Safe-To-Stage Exact File List

If the unrelated full-suite blockers are accepted/resolved and QA approves this slice, safe-to-stage files are:

- `steel_guitar_rag/api.py`
- `steel_guitar_rag/tab_engine.py`
- `tests/test_tab_engine.py`
- `docs/handoffs/task-completions/2026-06-18-05-tab-engine-first-slice.md`

## Files That Must Not Be Staged

- Any existing unrelated dirty files shown by `git status --short`, especially:
  - `README.md`
  - `corpus_metadata/source_policies/README.md`
  - `corpus_metadata/source_registry.json`
  - `deploy/landing/index.html`
  - `docs/answer-eval-report.md`
  - `docs/cloudflare-pages-landing.md`
  - `docs/copyright-provenance.md`
  - `docs/corpus-license-policy.md`
  - `docs/current-commands.md`
  - `docs/handoffs/task-completions/integration-status.md`
  - `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
  - `docs/source-inbox-inventory.md`
  - `rag_answer.py`
  - `rag_build_clean_corpus.py`
  - `rag_chunk_corpus.py`
  - `rag_embed_chroma.py`
  - `source-inbox/inventory.json`
  - `tests/test_frontend_answer_ui.py`
  - `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
  - `ui/steel-guitar-rag-mock.html`
  - `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, raw source data, generated reports, deployment secrets, auth files, and design assets.

## Recommended Next Lane

Lane 15 QA / Answer Eval.

Suggested prompt:

```text
Lane 15: QA the first deterministic tab-engine backend slice using docs/handoffs/task-completions/2026-06-18-05-tab-engine-first-slice.md. Verify /api/tab/render contract, validation issues, fixed-width rendering, and the fake-tab string-aware regression. Note that full pytest currently has unrelated static/UI failures; confirm whether those are already tracked or need Lane 06/12 cleanup before Repo Steward commit.
```

## Commit Readiness

Not ready to commit.

Reason:

- Scoped tests passed, but full pytest failed on two unrelated static/UI tests.
- No commit was made.

## Suggested Next Step

Have Lane 15 QA review this backend slice, and have Lane 06/12 or Repo Steward resolve/confirm the unrelated full-suite static/UI blockers before committing the tab-engine slice.
