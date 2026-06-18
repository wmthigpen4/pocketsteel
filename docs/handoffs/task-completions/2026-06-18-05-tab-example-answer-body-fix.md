# 2026-06-18 Lane 05 Tab Example Answer Body Fix

## Task Summary

Requested: fix safe answer-triggered tab prompts so the answer body contains useful direct prose when a deterministic `tab_example` is attached, instead of generic specificity/no-source fallback text.

Completed:

- Added deterministic answer-body prose to each answer-tab registry entry.
- Updated `/api/answer` tab attachment logic to replace known generic fallback text when a validated `tab_example` is attached.
- Added focused regression tests for safe tab prompts, blocked tab prompts, vague fallback behavior, and selector-level answer text.

Intentionally not changed:

- No frontend/UI files were modified.
- No new tab generation path was added.
- No LLM-generated tab, full song tab, copyrighted arrangement, recording transcription, Chroma, corpus, scraping, auth, DNS, deployment, landing/static, or fretboard-background work was touched.

Lane: 05 Backend / RAG Integration.

Branch: `feature/answer-api`.

HEAD before commit: `af645c9`.

## Files Changed

- `pocketsteel/answer_tab_examples.py`
  - Added deterministic `answer_body` text to safe registry examples.
  - Added `answer_body_for_tab_example(...)`.
- `pocketsteel/api.py`
  - Replaces generic fallback answer text only when a validated `tab_example` exists and the answer body matches known generic fallback markers.
- `tests/test_tab_engine.py`
  - Verifies selector payloads map back to deterministic answer prose.
- `tests/test_api_search.py`
  - Verifies safe tab prompts attach `tab_example` and do not return generic fallback text.
  - Verifies unrelated vague prompts may still use generic fallback when no tab example is attached.
  - Preserves no-tab behavior for copyrighted song tab and full-solo transcription requests.
- `docs/handoffs/task-completions/2026-06-18-05-tab-example-answer-body-fix.md`
  - This handoff.

Deleted files: none.

Generated artifacts: none.

## Cause Of Generic Fallback

The answer-tab selector was already attaching valid `tab_example` payloads after answer text was assembled. For several safe tab prompts, the earlier answer composition path produced a generic fallback such as:

- `I don’t have enough reliable information to answer that confidently...`
- older variants such as `I need a more specific steel-guitar question...`

Because tab attachment happened after answer composition, the UI could show a valid tab card paired with generic prose that implied the app could not answer.

## Fix Summary

The fix keeps the existing deterministic tab attachment model and adds one narrow override:

1. Select and validate `tab_example` as before.
2. Attach the payload as before.
3. If the current answer body is a known generic fallback, replace it with deterministic prose associated with the selected tab example.
4. Rebuild answer sections from the replacement prose.

This does not change retrieval, source cards, warnings, auth, UI, or tab rendering.

## Safe Prompts Covered

Verified safe prompts:

- `Show me a G major grip`
  - `tab_example.id`: `g-major-456-open`
  - answer starts: `Here is a simple G major grip on E9.`
- `Show me a G to C move`
  - `tab_example.id`: `g-to-c-456-beginner`
  - answer starts: `Here is a simple G to C movement on E9.`
- `How do I use A+B pedals?`
  - `tab_example.id`: `a-b-pedal-major-position`
  - answer starts: `Here is a basic A+B pedal example.`
- `Show me an A+B example`
  - `tab_example.id`: `a-b-pedal-major-position`
  - answer starts: `Here is a basic A+B pedal example.`
- `Show me an E-lower move`
  - `tab_example.id`: `e-lower-color-move`
  - answer starts: `Here is a small E-lower color move.`
- `Give me a beginner lick in G`
  - `tab_example.id`: `beginner-g-two-event-lick`
  - answer remains the existing useful beginner-lick prose and does not hit the generic fallback.
- `Show me a 4-5-6 grip`
  - `tab_example.id`: `g-major-456-open`
  - answer starts: `Here is a simple G major grip on E9.`

## Blocked Cases Preserved

- Copyrighted/named song tab requests do not attach `tab_example`.
- Full-solo/recording transcription requests do not attach `tab_example`.
- Unrelated vague prompts do not attach `tab_example` and can still use generic fallback behavior.

## Tests And Checks Run

```bash
git diff --check
# passed

.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py
# passed

.venv/bin/python -m pytest tests/test_tab_engine.py -q
# 20 passed in 0.05s

.venv/bin/python -m pytest tests/test_api_contract.py -q
# 5 passed in 0.05s

.venv/bin/python -m pytest tests/test_api_search.py -q
# 257 passed in 2.05s
```

Frontend checks were not run because no frontend files were touched.

## Limitations

- The override only handles known generic fallback text. It does not rewrite useful existing answer prose.
- The answer remains intentionally short; richer tab coaching can be a later slice.
- This slice does not add new tab examples or transposition.

## Risk Assessment

Risk: low.

Why:

- The change only activates when a valid deterministic `tab_example` is attached and the existing answer is a known generic fallback.
- Non-tab answers remain unchanged.
- Blocked tab cases remain tab-free.

Rollback:

- Revert the `answer_body` additions and `answer_body_for_tab_example(...)`.
- Remove the fallback replacement from `_attach_tab_example_if_available(...)`.
- Revert the added/updated tests.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `pocketsteel/answer_tab_examples.py`
- `pocketsteel/api.py`
- `tests/test_tab_engine.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-18-05-tab-example-answer-body-fix.md`

Do not use `git add .`.

## Files That Must Not Be Staged

Do not stage unrelated parked files, especially:

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
- `ui/steel-guitar-rag-mock.html`
- `ui/brand/`
- `Neon Sign/`
- `public/`
- `source-inbox/provenance.json`
- any `corpus-private/`, `corpus-v2/`, Chroma/vector, embedding, scraping, deployment secret, raw corpus, generated private report, or design asset paths.

## Recommended Next Smoke

Lane 12 or Lane 15 should rerun local API/browser smoke for:

- `Show me a G major grip`
- `Show me a G to C move`
- `How do I use A+B pedals?`
- `Show me an A+B example`
- `Show me an E-lower move`
- `Give me a beginner lick in G`
- `Show me a 4-5-6 grip`

Pass criteria:

- `tab_example` renders where expected.
- Answer body is direct and does not contain generic specificity/no-source fallback text.
- Copyrighted song tab and full transcription requests remain tab-free.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment for local/protected-preview verification if Cloudflare Access login is available. Otherwise Lane 15 can run API fallback smoke and clearly label it as API fallback.

## Commit Readiness

Safe to commit if exact-path staged with only the safe-to-stage files above and the focused checks remain green.
