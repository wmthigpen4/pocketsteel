# 2026-06-18 Lane 05 - Tab Example Fretboard Payload And Lick Fix

## Task Summary

Requested: fix deterministic answer-triggered tab examples so safe tab prompts attach both `tab_example` and `fretboard` payloads, and correct the beginner G lick so the A+B press event does not imply unchanged strings are affected by the pedals.

Completed:

- Added a tab-derived fretboard payload builder in `steel_guitar_rag.answer_tab_examples`.
- Wired `/api/answer` to attach that fretboard payload when a validated deterministic tab example is attached and no earlier fretboard exists.
- Revised the beginner G lick A+B press event to only include strings 5 and 6, the strings actually changed by A+B in the compact partial move.
- Revised the G-to-C tab example to label the A+B event as a `C partial`.
- Corrected the A+B major tab example from strings `3-5-6` to `3-4-5`, so notes/intervals resolve to G major as claimed.
- Narrowed tab-example matching so broad teacher/concept prompts mentioning A+B, grips, or E-lower do not unexpectedly attach tab/fretboard payloads.

Intentionally not changed:

- No UI files.
- No public response schema changes.
- No LLM-generated tab.
- No full-song/copyrighted tab behavior.
- No Chroma, embeddings, SGF scraper, corpus, auth, DNS, deployment, or private data.

## Files Changed

- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/tab_engine.py`
- `tests/test_api_search.py`
- `tests/test_tab_engine.py`
- `docs/handoffs/task-completions/2026-06-18-05-tab-example-fretboard-payload-and-lick-fix.md`

## Behavior Notes

Safe prompts now attach both `tab_example` and `fretboard`:

- `Show me a G major grip.`
- `Show me a 4-5-6 grip.`
- `Show me a G to C move.`
- `How do I use A+B pedals?`
- `Show me an A+B example.`
- `Show me an E-lower move.`
- `Give me a beginner lick in G.`

The tab-derived fretboard payload:

- uses existing `e9-fretboard-diagram` shape,
- includes `positions` and `highlights`,
- uses `sourceContext.sourceId = steel_guitar_rag.answer_tab_examples`,
- emits no raw UI geometry,
- derives frets/strings/pedals/levers from validated tab events.

Corrected tab semantics:

- Beginner G lick press event is now strings `5` and `6` only with `A` and `B`.
- Beginner G lick prose says to press A+B only on strings 5 and 6.
- A+B example now uses fret 10 strings `3-4-5`: notes `G-D-B`, intervals `1-5-3`.

Blocked/unsupported prompts still do not attach tab/fretboard:

- copyrighted song tab requests,
- full-solo transcription requests,
- unrelated non-tab questions.

## Tests And Checks

Run and passed:

- `git diff --check`
- `.venv/bin/python -m py_compile steel_guitar_rag/tab_engine.py steel_guitar_rag/api.py steel_guitar_rag/answer_tab_examples.py`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - `22 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - `5 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - `257 passed`

Skipped:

- Full pytest was not requested for this narrow tab/API slice. The required focused suites passed.

## Integration Notes

- `response.fretboard.positions` is now present for deterministic tab examples when the tab selector fires.
- The payload is rule-derived from the tab example and does not depend on retrieval.
- Existing deterministic fretboard payloads are not overwritten; the tab-derived fretboard only attaches when no fretboard is already present.
- Tab selector matchers were narrowed to avoid changing broad teacher-first answers.

## Risk Assessment

Risk: low to medium.

Why:

- The API now adds a `fretboard` payload for safe tab prompts, which is an intentional response extension.
- Overmatching risk was reduced after `tests/test_api_search.py` caught broad A+B/E-lower/lick prompts that should not attach fretboard.
- The tab-derived payload uses the existing fretboard validator to reduce schema/render risk.

Rollback:

- Revert the exact commit or remove the `fretboard_payload_for_tab_example` attachment in `_attach_tab_example_if_available`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/tab_engine.py`
- `tests/test_api_search.py`
- `tests/test_tab_engine.py`
- `docs/handoffs/task-completions/2026-06-18-05-tab-example-fretboard-payload-and-lick-fix.md`

## Files That Must Not Be Staged

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
- all untracked private/corpus/source/design/deploy/generated paths shown by `git status --short`

## Recommended Next Lane

Lane 12 protected-preview/local browser smoke for tab cards plus fretboard rendering, if the user wants UI verification next.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 prompt:

```text
Lane 12: Smoke test answer-triggered tab examples and fretboard cards for the committed tab-example payload fix. Verify "Show me a G major grip", "Show me a G to C move", "How do I use A+B pedals?", "Show me an E-lower move", and "Give me a beginner lick in G" render both tab cards and fretboard cards without unrelated source cards or generic fallback text.
```
