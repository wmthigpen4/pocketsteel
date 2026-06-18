# 2026-06-18 Lane 05 Answer-Triggered Tab Examples

## Task Summary

Requested: implement the next narrow backend slice that attaches deterministic tab examples to selected normal `/api/answer` responses.

Completed:

- Added a deterministic answer-tab selector that maps a small set of safe prompt patterns to committed `pocketsteel.tab_engine` examples.
- Added optional `tab_example` support to the answer response contract.
- Wired `/api/answer` to attach a validated `tab_example` in existing deterministic, practical-curated, and normal answer return branches.
- Added selector, contract, and API-level regression tests.

Intentionally not changed:

- No frontend/UI files were modified.
- No `/api/tab/render` behavior was changed.
- No LLM-generated tab, SGF-derived tab, copyrighted song tab, full-song tab, recording transcription, Chroma, embeddings, corpus, scraping, auth, DNS, deployment, landing/static, or fretboard-background work was touched.

Lane: 05 Backend / RAG Integration.

Branch: `feature/answer-api`.

HEAD during implementation: `0bd0780`.

## Files Changed

- `pocketsteel/answer_tab_examples.py`
  - New deterministic selector/registry for answer-triggered tab examples.
- `pocketsteel/api.py`
  - Added passive `_attach_tab_example_if_available(...)` helper and called it after existing answer payloads are assembled.
- `pocketsteel/api_contract.py`
  - Added optional `tab_example` TypedDict shape to `AnswerResponse`.
- `tests/test_tab_engine.py`
  - Added selector tests for safe mappings, blocked prompts, and validation-failure omission.
- `tests/test_api_contract.py`
  - Added optional `tab_example` contract coverage while leaving the existing fixture tab-free.
- `tests/test_api_search.py`
  - Added API-level answer tests for supported tab examples and blocked/no-tab cases.
- `docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples.md`
  - This handoff.

Deleted files: none.

Generated artifacts: none.

## Integration Point

The answer route now imports:

```python
from pocketsteel.answer_tab_examples import tab_example_payload_for_question
```

The helper is called only after an answer payload has already been built. It does not alter retrieval, answer text, source cards, warnings, auth, or fretboard routing.

Attachment points:

- deterministic chord/fretboard answer branch,
- practical-curated answer branch,
- normal retrieval/provider answer branch after final quality/contract handling.

Guardrail/off-domain answers remain tab-free because the guardrail branch does not call the tab helper.

## Matcher And Registry Behavior

The registry uses existing committed tab engine example ids:

- `g_major_open`
- `g_to_c`
- `ab_major`
- `e_lower_color`
- `beginner_lick`

Each selected example is rendered through `render_example(...)`. If validation fails or the engine example is missing, `/api/answer` omits `tab_example` rather than returning invalid tab.

## Examples Supported

Supported prompt classes in this first slice:

- `Show me a G major grip.`
- `G major chord on E9.`
- `Show me a 4-5-6 grip.`
- `Show me a G to C move.`
- `How do I use A+B pedals?`
- `Show me an A+B example.`
- `Show me an E-lower move.`
- `Give me a beginner lick in G.`

Supported response ids:

- `g-major-456-open`
- `g-to-c-456-beginner`
- `a-b-pedal-major-position`
- `e-lower-color-move`
- `beginner-g-two-event-lick`

## Blocked Cases

No `tab_example` is attached for:

- unrelated gear/vendor/history questions,
- copyrighted or named song tab requests,
- full song tab requests,
- whole-solo or full-solo requests,
- recording/video transcription requests,
- unsupported arbitrary tab requests.

The blocked checks are intentionally local to tab attachment. Existing answer guardrails and copyright-aware answer text remain owned by the answer composer.

## Response Payload Summary

Optional top-level answer field:

```json
{
  "tab_example": {
    "id": "g-major-456-open",
    "title": "G major 4-5-6 grip",
    "context": {
      "key": "G",
      "tuning": "E9",
      "profile": "default_e9",
      "difficulty": "beginner",
      "grip": "4-5-6"
    },
    "rendered_tab": "fixed-width tab from pocketsteel.tab_engine",
    "validation": {
      "ok": true,
      "issues": [],
      "profile": "default_e9",
      "eventCount": 1
    },
    "explanation": "A simple G major grip at the 3rd fret on strings 4, 5, and 6.",
    "intervals": [],
    "events": []
  }
}
```

Compatibility:

- Existing responses omit `tab_example`.
- Existing required answer fields are unchanged.
- The existing contract fixture remains tab-free.

## Tests And Checks Run

```bash
.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py pocketsteel/answer_tab_examples.py pocketsteel/api_contract.py
# passed

.venv/bin/python -m pytest tests/test_tab_engine.py -q
# 20 passed in 0.05s

.venv/bin/python -m pytest tests/test_api_contract.py -q
# 5 passed in 0.04s

.venv/bin/python -m pytest tests/test_api_search.py -q
# 255 passed in 1.64s

git diff --check
# passed
```

Full pytest was not run in this slice. The task requested focused checks, and the current project context documents two unrelated full-suite static/UI caveats:

- landing source vs deployed static HTML mismatch,
- missing public fretboard background route.

## Limitations

- This slice attaches only one tab example per answer.
- It does not transpose examples.
- It does not generate arbitrary tab.
- It does not attempt song arrangements or recording transcription.
- It does not expose validation failures in `/api/answer`; invalid examples are silently omitted.
- It uses the current default 10-string E9 tab profile.

## Risk Assessment

Risk: medium-low.

Why:

- The `/api/answer` contract is expanded with an optional field, but required fields and existing payload behavior remain unchanged when no tab is selected.
- Tab data comes only from deterministic engine examples and is validated before attachment.
- No frontend files were touched, but Lane 06 must render the new field correctly.

Rollback:

- Revert `pocketsteel/answer_tab_examples.py`.
- Remove the optional `tab_example` contract types.
- Remove `_attach_tab_example_if_available(...)` calls from `pocketsteel/api.py`.
- Revert the added tests.

## Human Decision Needed

No for this backend slice.

Future decision: whether Lane 06 should render `tab_example` exactly as snake_case or support a client-side alias if earlier plans referenced `tabExample`.

## Safe-To-Stage Exact File List

- `pocketsteel/answer_tab_examples.py`
- `pocketsteel/api.py`
- `pocketsteel/api_contract.py`
- `tests/test_tab_engine.py`
- `tests/test_api_contract.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples.md`

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
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
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

## Recommended Next Lane

Lane 06 UX/UI Design.

Suggested task:

```text
Lane 06: Render the optional /api/answer tab_example payload. Preserve fixed-width monospace spacing from rendered_tab, show validation issues calmly if ever present, keep non-tab answers unchanged, and do not synthesize frontend tab when tab_example is absent.
```

## Commit Readiness

Safe to commit if exact-path staged with only the safe-to-stage files above and the focused checks remain green.
