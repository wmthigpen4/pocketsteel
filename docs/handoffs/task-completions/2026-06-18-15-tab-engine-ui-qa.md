# Tab Engine UI QA Coverage

## Task Summary

Lane: 15 QA / Answer Eval

Requested: prepare and, where safe, implement QA coverage for the committed deterministic tab engine and the in-progress answer-page tab UI. The user explicitly allowed QA/test/doc changes and an exact-path commit if focused checks passed.

Completed:
- Reviewed the committed tab engine tests in `tests/test_tab_engine.py`.
- Reviewed tab-related API/search coverage in `tests/test_api_contract.py`, `tests/test_api_search.py`, `tests/test_answer_eval.py`, and `tests/test_full_answer_quality_eval.py`.
- Reviewed the existing Lane 15 tab-engine QA matrix at `docs/handoffs/task-completions/2026-06-18-15-tab-engine-qa-matrix.md`.
- Added narrow API coverage for `/api/tab/render` string-aware pedal behavior and stable validation issue shape.
- Wrote this QA handoff for the backend tab engine plus Lane 06 answer-page tab rendering smoke criteria.

Intentionally not changed:
- No frontend implementation files were touched while Lane 06 is active.
- No tab engine production logic was changed.
- No static landing, public assets, fretboard background route, corpus, Chroma, embeddings, scraping, deployment, DNS, auth, private corpus, or source data were touched.

Current branch / HEAD reviewed:
- Branch: `feature/answer-api`
- HEAD: `686fd3c`

## Automated Tests Reviewed

Existing `tests/test_tab_engine.py` already covered:
- 10 string rows and E9 labels.
- Same-event vertical alignment.
- Variable-width token spacing.
- Chord and lyric row alignment.
- Maximum 3 notes per event.
- Invalid string numbers.
- Unknown change labels.
- A pedal rejection on string 4.
- String-aware change rendering.
- Built-in example validation.
- `/api/tab/render` happy path and validation failure path.

Existing answer/API tests already include song-tab and copyrighted-tab guardrails in `tests/test_api_search.py`, including coverage that tab mode does not generate copyrighted song tab.

## Automated Tests Added

Added to `tests/test_tab_engine.py`:
- `test_api_tab_render_accepts_string_aware_a_pedal_on_string_five`
  - Verifies `/api/tab/render` accepts A pedal on affected string 5.
  - Verifies A is not copied to unaffected string 4.
  - Verifies metadata and issue shape for the valid response.
- Strengthened `test_api_tab_render_reports_validation_issues`
  - Verifies the invalid A-on-string-4 payload returns `ok: false`, empty tab text, stable metadata, and a stable validation issue object with `code`, `message`, `eventIndex`, and `noteIndex`.

No new test file was needed.

## Manual Browser Smoke Checklist For Lane 06

Run after Lane 06 finishes answer-page tab rendering from `/api/tab/render`.

Required browser prompts or fixtures:
- A valid short tab payload with strings 4-5-6 at one fret.
- A valid A pedal example on string 5.
- An invalid A pedal example on string 4.
- A short multi-event lick with chord labels.
- A short multi-event lick with lyric/syllable labels if the UI supports lyrics.
- A long enough tab block to test horizontal scrolling on mobile.
- A normal non-tab answer.

Pass criteria:
- Tab card appears only when a tab payload is present.
- Tab text is rendered in monospace/preformatted layout.
- Same-event notes align vertically.
- Chord and lyric labels align with event start columns where present.
- Long tab scrolls horizontally on narrow screens instead of wrapping columns.
- Tab block does not dominate the answer page.
- Validation issues appear calmly and do not render broken ASCII tab.
- Normal non-tab answers remain unchanged.
- No fake frontend-generated tab is displayed when the API did not provide tab data.
- If a copy control exists, copied tab preserves spacing.

Regression risks to watch:
- Proportional text or markdown table rendering corrupting alignment.
- Global pedal labels copied onto every string row.
- Validation issue objects leaking as `[object Object]`.
- Frontend inventing tab from answer prose instead of rendering API-provided tab.
- Tab UI appearing for non-tab answers.
- Invalid tab rendering as if it were playable.

## Known Unrelated Failures

The task context reports full pytest currently has two known unrelated failures:
- Landing source vs deployed static HTML mismatch.
- Missing public fretboard background route in the same-origin smoke server.

This Lane 15 task did not run full pytest because the requested focused checks passed and the known failures are outside the tab-engine/API QA scope.

## Post-Lane-06 Recommended QA Commands

After Lane 06 finishes answer-page tab rendering, run:

```bash
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_tab_engine.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
.venv/bin/python -m pytest tests/test_api_search.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Browser smoke should include the checklist above and an explicit Smoke Target block if it tests local or protected-preview UI.

## Tests And Checks Run

```bash
.venv/bin/python -m pytest tests/test_tab_engine.py -q
# 16 passed in 0.06s

.venv/bin/python -m pytest tests/test_api_contract.py -q
# 4 passed in 0.04s

.venv/bin/python -m pytest tests/test_api_search.py -q
# 246 passed in 1.63s
```

`git diff --check` still needs to be run after this handoff is written.

## Risk Assessment

Risk: low.

Reason:
- Changes are limited to QA/test/docs.
- No runtime tab engine or UI implementation was modified.
- New tests exercise existing committed API behavior and validation shape.

Rollback:
- Revert `tests/test_tab_engine.py` and this handoff if needed.

## Human Decision Needed

No.

The user explicitly allowed exact QA/test/doc staging and commit if focused checks passed.

## Safe-To-Stage Exact File List

- `tests/test_tab_engine.py`
- `docs/handoffs/task-completions/2026-06-18-15-tab-engine-ui-qa.md`

Do not use `git add .`.

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files, especially:
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
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `tests/test_frontend_answer_ui.py`
- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `ui/brand/`
- `Neon Sign/`
- `public/`
- `source-inbox/provenance.json`
- any `corpus-private/`, `corpus-v2/`, Chroma/vector, embedding, scraping, deployment secret, generated report, raw corpus, or design asset paths.

## Recommended Next Lane

Lane 06 UX/UI Design.

Suggested next task:

```text
Lane 06: Finish answer-page tab rendering from /api/tab/render. Preserve monospace alignment, handle validation issues without rendering bad tab, avoid fake frontend-generated tab, and run the Lane 15 tab UI smoke checklist in docs/handoffs/task-completions/2026-06-18-15-tab-engine-ui-qa.md.
```

## Commit Readiness

Safe to commit.
