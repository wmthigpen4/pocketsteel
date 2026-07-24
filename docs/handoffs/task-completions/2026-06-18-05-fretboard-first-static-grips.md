# 2026-06-18 Lane 05 - Fretboard-First Static Grips

## Task Summary

Requested: reclassify answer-triggered tab examples so static grip/chord prompts use fretboard-first output, while tab remains reserved for movement/sequence examples.

Completed:

- Split deterministic tab-example routing into static fretboard-only examples and movement tab examples.
- Static G/4-5-6 grip prompts now attach a fretboard payload and omit `tab_example`.
- Movement prompts still attach both `tab_example` and a matching fretboard payload.
- Added metadata to internal tab examples:
  - `kind`
  - `display_mode`
  - `display_tab`
  - `preferred_display`
- Preserved blocked tab behavior for full song, copyrighted arrangement, full solo, and transcription requests.

Intentionally not changed:

- No UI files.
- No tab engine removal.
- No LLM-generated tab.
- No broad example generation.
- No schema-breaking response changes.
- No Chroma, embeddings, corpus, SGF scraper, auth, deployment, DNS, or private data.

## Files Changed

- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `tests/test_tab_engine.py`
- `docs/handoffs/task-completions/2026-06-18-05-fretboard-first-static-grips.md`

## Product Correction

The tab engine is now treated as a movement/sequence engine. Static grips and static chord locations are owned by the SVG/fretboard payload.

Static grip/chord prompts should not show redundant tab by default because the tab duplicates the fretboard state without adding time-based information.

## Static vs Movement Routing Rules

Static / fretboard-first:

- `Show me a G major grip`
- `Show me a 4-5-6 grip`
- `Where is G on E9?`
- `Show me a G chord on strings 4-5-6`

Response behavior:

- direct prose,
- `fretboard` payload,
- no `tab_example`.

Movement / tab-worthy:

- `Show me a G to C move`
- `How do I use A+B pedals?`
- `Show me an A+B example`
- `Show me an E-lower move`
- `Give me a beginner lick in G`
- `Show me a walk from G to C` when it matches the supported G-to-C movement route.

Response behavior:

- direct prose,
- `tab_example`,
- matching `fretboard` payload.

Blocked:

- full song tab requests,
- copyrighted song arrangements,
- full solo transcription,
- recording transcription,
- unrelated gear/history questions.

## Response Shape Changes

For movement examples, `tab_example` now includes internal display metadata:

- `kind`
- `display_tab`
- `preferred_display`

For static examples, the public response omits `tab_example` and attaches only `fretboard`.

The `fretboard` payload remains the existing `e9-fretboard-diagram` shape. No raw UI geometry is emitted.

## Tests And Checks

Run and passed:

- `git diff --check`
- `.venv/bin/python -m py_compile steel_guitar_rag/tab_engine.py steel_guitar_rag/api.py steel_guitar_rag/answer_tab_examples.py`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - `23 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - `5 passed`
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - `259 passed`

Skipped:

- Full pytest was not requested for this narrow routing slice. Required focused checks passed.

## Limitations

- Static fretboard-first support in this slice is limited to the known G/4-5-6 examples and existing deterministic chord-position routes.
- Movement tab support remains limited to the existing deterministic examples.
- No frontend changes were made; Lane 06 can decide whether to use `display_tab` / `preferred_display` for future UI affordances.

## Lane 06 Follow-Up Needs

Optional:

- Verify that when `tab_example` is absent, the frontend clears any previous tab display state.
- Verify static grip answers visually prioritize the fretboard card.
- Verify movement examples show both tab and fretboard states.

## Risk Assessment

Risk: low.

Why:

- The change is scoped to deterministic answer-tab routing and tests.
- Static prompts now emit less structured output, not more.
- Movement prompts preserve the previous tab-plus-fretboard behavior.

Rollback:

- Revert this commit to restore static tab examples.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/api.py`
- `tests/test_api_search.py`
- `tests/test_tab_engine.py`
- `docs/handoffs/task-completions/2026-06-18-05-fretboard-first-static-grips.md`

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

Lane 12 or Lane 06 smoke/verification of static grip UI behavior and tab clearing behavior.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 prompt:

```text
Lane 12: Verify protected-preview answer behavior for static grip and movement tab prompts after `fix: prefer fretboard for static grip examples`. Confirm static G/4-5-6 prompts show fretboard without tab, movement prompts show tab plus fretboard, and previous tab cards do not persist across answers.
```
