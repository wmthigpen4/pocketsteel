# 2026-06-18 Lane 05 Answer-Triggered Tab Examples Implementation Plan

## Task Summary

Requested: prepare a backend implementation plan for attaching deterministic tab examples to normal `/api/answer` responses, without modifying backend code while Lane 06 UI work is active.

Completed:

- Inspected the committed tab engine slice, current answer API flow, answer intent classifier, curated answer flow, API response contract, and current tab tests.
- Created this concrete next-slice implementation plan.
- Did not modify backend implementation code.
- Did not modify frontend/UI files.
- Did not stage or commit.

Task type: docs/design/spec only.

Lane: 05 Backend / RAG Integration.

Task mode: GREEN for handoff/doc creation; future implementation is YELLOW because it changes `/api/answer` response contract and routing behavior.

Protected paths and unrelated dirty files:

- The worktree has broad unrelated dirty files, including active UI files (`ui/answer-client.js`, `ui/steel-guitar-rag-mock.html`, `tests/test_frontend_answer_ui.py`) and many parked docs/source/static/design files.
- Lane 06 is active on answer-page tab display, so this lane intentionally avoided UI/frontend files.

## 1. Current Backend Answer Flow

Entry point:

- `pocketsteel/api.py`
- `RetrievalApi.__call__`
- `/api/answer` branch starts after auth/rate-limit/request parsing.

Current `/api/answer` flow, simplified:

1. Read JSON body with `_read_json_body()`.
2. Authorize with `authorize_answer_request(...)`.
3. Apply rate limit.
4. Parse request via `parse_answer_request(...)`.
5. Classify with `classify_answer_request(answer_request.question, answer_request.mode)`.
6. Try deterministic fretboard/chord route:
   - `visual_fretboard_curated_answer(question)`
   - fallback to `unsupported_chord_position_curated_answer(question)`
   - if present, build an `AnswerResponse` with `sources: []`, `warnings: []`, `sections`, and optional `fretboard_payload_for_question(question)`.
7. Apply intent guardrail for off-domain/unsafe:
   - `_should_gate_answer_intent(...)`
   - returns source-free/warning-free answer without retrieval.
8. Evaluate private/protected curated guidance eligibility.
9. Try practical curated answer:
   - `intent_mode_curated_answer(question)`
   - returns source-free/warning-free answer and sections.
10. If no deterministic/guardrail/curated answer, run retrieval:
    - `_search_for_answer(...)`
    - sanitize sources
    - use B+C exercise, private profile, curated answer, prompt-injection answer, no-source fallback, or `answer_provider`.
11. Apply quality gates and answer contract.
12. Attach `fretboard_payload_for_question(question)` if available.
13. Return `AnswerResponse`.

Best tab attachment points:

- Deterministic chord/fretboard branch: attach tab after `fretboard_payload` is computed and before return.
- Practical curated branch: attach tab after final answer/sections are built and before return.
- Retrieval branch: attach tab after final answer and `fretboard_payload` computation, but only for safe deterministic tab intents.

Do not make tab generation depend on retrieved sources.

## 2. Current Tab Engine API

Committed slice:

- Commit: `686fd3c feat: add deterministic tab engine slice`.
- Module: `pocketsteel/tab_engine.py`.
- Endpoint: `POST /api/tab/render`.
- Tests: `tests/test_tab_engine.py`.

Important public functions/classes:

- `default_e9_copedent_profile()`
- `TabNote`
- `TabEvent`
- `TabValidationIssue`
- `TabRenderResult`
- `tab_examples()`
- `render_example(name: str) -> TabRenderResult`
- `render_tab(events, profile=None) -> TabRenderResult`
- `validate_events(events, profile=None) -> tuple[TabValidationIssue, ...]`
- `render_tab_from_payload(payload: dict) -> TabRenderResult`

Current built-in example keys:

- `g_major_open`
- `g_to_c`
- `ab_major`
- `e_lower_color`
- `beginner_lick`

Current `/api/tab/render` response shape:

```json
{
  "ok": true,
  "tab": "fixed-width monospace tab",
  "issues": [],
  "metadata": {
    "profile": "default_e9",
    "event_count": 1
  }
}
```

Invalid structured tab returns `ok: false`, empty `tab`, and structured validation `issues`.

## 3. Exact Files Likely To Change Next

Likely implementation files:

- `pocketsteel/api_contract.py`
  - Add optional tab response TypedDicts.
  - Add `tabExample: NotRequired[TabExamplePayload]` or `tab: NotRequired[TabExamplePayload]` to `AnswerResponse`.
- `pocketsteel/tab_engine.py`
  - Add stable example metadata and a selector function, not broad generation.
  - Suggested function: `tab_example_payload_for_question(question: str, *, answer_intent: dict | None = None) -> dict | None`.
  - Suggested helper: `tab_example_payload(example_id: str, *, title: str, description: str, intent: str) -> dict`.
- `pocketsteel/api.py`
  - Import the selector/helper.
  - Attach optional tab payload in existing answer return branches.
  - Keep `/api/tab/render` unchanged.
- `tests/test_tab_engine.py`
  - Extend with selector/payload validation tests.
- `tests/test_api_contract.py`
  - Add optional tab example contract test.
  - Update fixture allowance if necessary.
- `tests/test_api_search.py`
  - Add API-level answer tests for supported tab-trigger prompts and blocked cases.
- Possibly `tests/fixtures/api_contract_mock_response.json`
  - Only if the fixture test is adjusted to demonstrate optional tab shape. Better: keep fixture without tab and add separate optional-tab test, matching the current fretboard pattern.

Do not change in this backend slice:

- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `ui/brand/*`
- Chroma/corpus/scraper/auth/deploy files.

## 4. Proposed `tabExample` Response Contract

Recommended field name:

- `tabExample`

Reason:

- Avoids ambiguity with request `mode: "tab"`.
- Clearly indicates this is a short deterministic teaching illustration, not arbitrary generated tablature.
- Leaves room for future `tabExamples: []` if multi-card output becomes useful.

Proposed optional response addition:

```json
{
  "answer": "...",
  "mode": "ask",
  "sources": [],
  "warnings": [],
  "sections": [],
  "fretboard": {},
  "tabExample": {
    "type": "e9-tab-example",
    "id": "g-to-c-move",
    "title": "G to C move on E9",
    "description": "A short validated 3rd-fret G-to-C move using A+B.",
    "tuning": "E9",
    "profile": "default_e9",
    "validationStatus": "validated",
    "tab": "fixed-width monospace tab",
    "events": [
      {
        "notes": [
          {"string": 4, "fret": 3, "changes": []},
          {"string": 5, "fret": 3, "changes": []},
          {"string": 6, "fret": 3, "changes": []}
        ],
        "chord": "G"
      }
    ],
    "issues": [],
    "metadata": {
      "profile": "default_e9",
      "event_count": 2,
      "source": "pocketsteel.tab_engine"
    }
  }
}
```

TypedDict sketch:

```python
class TabExampleNote(TypedDict):
    string: int
    fret: int
    changes: list[str]
    articulation: NotRequired[str]

class TabExampleEvent(TypedDict):
    notes: list[TabExampleNote]
    chord: NotRequired[str]
    lyric: NotRequired[str]
    comment: NotRequired[str]

class TabExampleIssue(TypedDict):
    code: str
    message: str
    eventIndex: NotRequired[int]
    noteIndex: NotRequired[int]

class TabExamplePayload(TypedDict):
    type: Literal["e9-tab-example"]
    id: str
    title: str
    description: str
    tuning: Literal["E9"]
    profile: Literal["default_e9"]
    validationStatus: Literal["validated", "invalid"]
    tab: str
    events: list[TabExampleEvent]
    issues: list[TabExampleIssue]
    metadata: dict[str, Any]
```

Compatibility rule:

- Existing responses omit `tabExample`.
- Existing required keys remain unchanged: `answer`, `mode`, `sources`, `warnings`, `sections`.
- `tabExample` is optional, like `fretboard`.
- If validation fails, do not attach `tabExample`; log/test the failure in unit code. User-facing `/api/answer` should not return invalid tab examples.

## 5. Intent Mapping Rules

Use a narrow selector in the tab engine or a small adjacent helper. Do not bury tab selection across many answer branches.

Suggested function:

```python
def tab_example_payload_for_question(question: str, *, answer_intent: dict | None = None) -> dict | None:
    ...
```

Selector principles:

- Only attach when the user asks for a concrete tab-like, lick, grip, or short example that maps to one of the built-in validated examples.
- Do not attach just because `mode == "tab"`; song-tab/copyright guardrails may be in play.
- Do not use SGF retrieved snippets as tab source.
- Do not attach if `render_example()` returns `ok: false`.
- Do not attach if the answer is off-domain, unsafe, no-source, copyright-protected, or asking for arbitrary transcription.

Initial regex-style mapping:

| Trigger class | Example prompts | Example key |
| --- | --- | --- |
| G major grip | `show me G major grip`, `tab for G major on 4-5-6`, `show G at fret 3 strings 4-5-6` | `g_major_open` |
| G to C move | `simple G to C move`, `show a G to C move with tab`, `G to C with A+B` | `g_to_c` |
| A+B major position | `show me an A+B major position`, `tab for A+B at the 10th fret`, `A+B position example` | `ab_major` |
| E-lower color move | `E-lower color example`, `show E-lower move`, `tab an E-lower color` | `e_lower_color` |
| Beginner lick | `show me a lick`, `show me another lick`, `simple E9 lick in G`, `country lick in G`, `one original E9 lick` | `beginner_lick` |
| 4-5-6 grip example | `show a 4-5-6 grip`, `tab for strings 4-5-6`, `4-5-6 example` | probably `g_major_open` initially |

Keep answer text and tab selection separable:

- Curated answer can remain the teacher-first prose.
- `tabExample` is an illustration that must validate independently.

## 6. Safe Examples To Attach First

Safe first examples:

1. `g_major_open`
   - Use for G major grip / 4-5-6 grip examples.
   - Source-free, deterministic, validated.
2. `g_to_c`
   - Use for compact I-to-IV / G-to-C movement.
   - Mechanically string-aware: G no-pedals to C with A on string 5, B on string 6, no invalid A/B on string 4.
3. `ab_major`
   - Use for A+B major position examples.
4. `e_lower_color`
   - Use for E-lower color examples.
   - Must be described as a color/move example, not a full universal chord claim.
5. `beginner_lick`
   - Use for default/original lick prompts already handled by teacher-first curated answers.

Do not attach multiple tabs in the first slice. One `tabExample` per answer keeps UI and tests simpler.

## 7. Cases Where No Tab Should Attach

Blocked:

- Full song tabs.
- Named copyrighted song arrangements.
- Full solo transcription.
- Arbitrary recording-to-tab.
- Requests to copy forum/source tab.
- Pasted source material that looks copyrighted or unreviewed.
- Unsupported copedent-specific requests.
- Slants, multi-fret grips, or more than 3 strings per event until supported.
- Off-domain or unsafe prompts.
- Gear, tone, buying, biography, forum-wisdom, source-backed vendor questions.
- General theory where a tab illustration is not requested.
- Unrelated `/api/answer` responses with no tab/lick/grip/move intent.

Specific examples that should not attach tab:

- `Can you give me tab for Together Again?`
- `Generate the full tab for Panhandle Rag.`
- `Copy the exact SGF tab from that post.`
- `What is the capital of France?`
- `Where can I buy a slide bar?`
- `Why does my amp buzz?`
- `Who was Buddy Emmons?`

## 8. How To Keep Tab Deterministic And Validated

Rules:

- All answer-attached tabs must come from `pocketsteel.tab_engine`.
- Build payloads from `TabEvent` objects, not handwritten tab strings.
- Always call `render_example()` or `render_tab()` before attachment.
- Attach only when `result.ok is True` and `result.issues == ()`.
- Include event data plus rendered `tab`, so UI can render fixed-width text now and later inspect event metadata.
- Do not use SGF retrieved text as tab.
- Do not call LLM/provider to create tab.
- Do not infer arbitrary named-song arrangements.
- Keep one example per response in first slice.

Recommended small helper:

```python
TAB_EXAMPLE_METADATA = {
    "g_major_open": {
        "title": "G major grip on E9",
        "description": "A 3rd-fret no-pedals G grip on strings 4-5-6.",
    },
    ...
}

def build_tab_example_payload(example_id: str) -> dict | None:
    result = render_example(example_id)
    if not result.ok:
        return None
    events = tab_examples()[example_id]
    return {
        "type": "e9-tab-example",
        "id": example_id,
        ...
        "tab": result.tab,
        "events": [event.to_dict() for event in events],
        "issues": [],
        "metadata": {**result.metadata, "source": "pocketsteel.tab_engine"},
    }
```

## 9. API Compatibility Risks

Risk: optional response schema expansion.

Mitigation:

- Add `tabExample` as `NotRequired` in `AnswerResponse`.
- Update `tests/test_api_contract.py` to allow optional `tabExample` while preserving fixture without it.
- Add a dedicated optional-tab contract test, mirroring `test_optional_fretboard_payload_contract_shape`.
- Do not rename existing fields.
- Do not require UI to render the field in this backend slice.

Risk: tests currently assert exact response keys in some places.

Evidence:

- `tests/test_api_contract.py` currently asserts answer keys are a subset of required keys plus `fretboard`.
- `tests/test_api_search.py` has exact-set assertions around guardrails and no-fretboard responses, e.g. `{"answer", "mode", "sources", "warnings", "sections"}`.

Mitigation:

- Only attach `tabExample` for newly tested supported tab intents.
- Existing no-tab responses remain unchanged.
- Update exact-key contract allowance from `{"fretboard"}` to `{"fretboard", "tabExample"}`.

Risk: tab examples on existing lick prompts may change existing API snapshots.

Mitigation:

- Add targeted tests for supported prompts.
- Keep attachment narrowly scoped to explicit tab/example/lick prompts.
- Do not attach to broad practice/gear/source-backed answers.

Risk: copyright confusion.

Mitigation:

- Block named-song/full-song/copy-source tab before selection.
- Reuse existing song/tab guardrails in `curated_answers.py` and `answering.py`.
- Tests must prove no tab for copyrighted song requests.

## 10. Test Plan

Focused tests to add/update:

### `tests/test_tab_engine.py`

- `test_tab_example_payload_for_question_selects_g_major_grip`
- `test_tab_example_payload_for_question_selects_g_to_c_move`
- `test_tab_example_payload_for_question_selects_ab_major`
- `test_tab_example_payload_for_question_selects_e_lower_color`
- `test_tab_example_payload_for_question_selects_beginner_lick`
- `test_tab_example_payload_validates_before_returning`
- `test_tab_example_payload_omits_for_copyrighted_song_request`
- `test_tab_example_payload_omits_for_unrelated_question`

Assertions:

- Payload has `type == "e9-tab-example"`.
- Payload has stable `id`.
- Payload has non-empty `title`, `description`, `tab`.
- Payload `events` are present and structured.
- Payload `issues == []`.
- `metadata.profile == "default_e9"`.
- Rendered tab has 10 string rows.

### `tests/test_api_contract.py`

- Extend `AnswerResponse` optional key allowance to include `tabExample`.
- Add `test_optional_tab_example_payload_contract_shape`.
- Keep fixture response without `tabExample` valid.

### `tests/test_api_search.py`

Add API-level tests:

- Supported intent attaches tab:
  - `Show me a simple G to C move with tab.`
  - `Show me a G major grip with tab.`
  - `Show me a simple E9 lick in G.`
- Unrelated answer omits tab:
  - `What is the capital of France?`
  - `Where can I buy a slide bar?`
  - `Why does my amp buzz?`
- Copyright song request omits tab:
  - `Can you give me tab for Together Again?`
  - `Generate full tab for Panhandle Rag.`
- Existing API search tests remain stable.

Assertions:

- `tabExample` exists only for supported intent.
- `tabExample["issues"] == []`.
- `tabExample["tab"]` is non-empty and fixed-width.
- `sources` remain source-free for deterministic tab examples.
- `warnings` do not include weak-source warnings for deterministic tab examples.
- Full-song tab answer still contains copyright-safe refusal/teaching language and no `tabExample`.

Recommended commands for implementation lane:

```bash
git status --short
git diff --check
.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py pocketsteel/api_contract.py
.venv/bin/python -m pytest tests/test_tab_engine.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
.venv/bin/python -m pytest tests/test_api_search.py -q
git diff --check
```

If focused tests pass and unrelated full-suite static/UI blockers are still known/unchanged:

```bash
.venv/bin/python -m pytest -q
```

Document the two known unrelated full-suite failures if they persist:

- landing source vs deployed static HTML mismatch.
- missing public fretboard background route.

## 11. Exact Next Implementation Prompt

```text
Lane: 05 Backend / RAG Integration
Reasoning level: High

Task: Implement the first backend slice for answer-triggered deterministic tab examples.

Use AGENTS.md and docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples-implementation-plan.md.

Scope:
- Backend only.
- Do not touch UI/frontend files; Lane 06 owns rendering.
- Do not touch Chroma, embeddings, corpus, SGF scraper, auth, deployment, DNS, private data, or design assets.
- Do not generate arbitrary or copyrighted song tabs.

Implement:
1. Add optional `tabExample` response contract in `pocketsteel/api_contract.py`.
2. Add tab example metadata and selector helpers in `pocketsteel/tab_engine.py`.
3. Attach `tabExample` in `/api/answer` only for safe deterministic tab/example intents:
   - G major grip
   - G to C move
   - A+B major position
   - E-lower color move
   - beginner E9 lick
   - 4-5-6 grip example
4. Do not attach tab for unrelated questions, gear/source-backed questions, off-domain/unsafe prompts, full song tabs, named copyrighted song arrangements, full solo transcription, arbitrary recording-to-tab, copied SGF/source tab, or unsupported copedent-specific requests.
5. Always validate via `render_example()`/`render_tab()` before attaching; if validation fails, omit `tabExample`.

Tests:
- Add/extend `tests/test_tab_engine.py`.
- Add optional-tab contract test in `tests/test_api_contract.py`.
- Add API-level tests in `tests/test_api_search.py`.

Run:
- `git status --short`
- `git diff --check`
- `.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py pocketsteel/api_contract.py`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
- `git diff --check`

Write handoff:
`docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples.md`

Do not stage or commit unless the worktree scope is clean and QA/Repo Steward criteria are satisfied.
```

## Files Inspected

- `AGENTS.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-18-01-tab-engine-repo-steward-commit.md`
- `docs/handoffs/task-completions/2026-06-18-15-tab-engine-qa-matrix.md`
- `docs/handoffs/task-completions/2026-06-18-1516-06-tab-engine-answer-ux.md`
- `pocketsteel/api.py`
- `pocketsteel/tab_engine.py`
- `pocketsteel/api_contract.py`
- `pocketsteel/answer_intent_classifier.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/answering.py`
- `tests/test_tab_engine.py`
- `tests/test_api_contract.py`
- `tests/test_api_search.py`
- `tests/fixtures/api_contract_mock_response.json`

## Tests And Checks Run

```bash
git status --short
git rev-parse --abbrev-ref HEAD
git rev-parse --short HEAD
git log --oneline -5
git diff --check
```

Results:

- `git status --short`: broad dirty worktree with unrelated parked docs/source/static/UI/design files.
- Branch: `feature/answer-api`.
- HEAD: `0bd0780`.
- `git diff --check`: passed.

No pytest was run because this was docs/spec only and no implementation code was changed.

## Integration Notes

- This plan deliberately does not require immediate UI changes. Lane 06 can consume `tabExample` after the backend contract exists.
- First backend implementation should not attach more than one tab example per answer.
- The tab engine examples are currently source-free and deterministic.
- `/api/tab/render` remains useful for explicit structured rendering; answer-triggered examples should use the same underlying validator/renderer.

## Risk Assessment

Risk: medium for the future implementation because it expands `/api/answer` with a new optional field and may overlap Lane 06 rendering work.

Risk for this docs-only task: low.

Rollback for future implementation:

- Remove `tabExample` optional contract from `AnswerResponse`.
- Remove selector/helper functions from `pocketsteel/tab_engine.py`.
- Remove `/api/answer` attachment calls.
- Keep `/api/tab/render` untouched unless a separate rollback is needed.

## Human Decision Needed

Yes.

Decision needed before implementation:

- Confirm `tabExample` as the response field name, or choose `tab` / `tabExamples`.
- Confirm whether first slice should attach to existing lick answers immediately or only to explicit “with tab” prompts.

## Safe-To-Stage Exact File List

For this docs-only task:

- `docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples-implementation-plan.md`

## Files That Must Not Be Staged

- Existing unrelated dirty files shown by `git status --short`.
- Any UI/frontend files while Lane 06 is active unless Lane 06 explicitly owns the change:
  - `ui/answer-client.js`
  - `ui/steel-guitar-rag-mock.html`
  - `tests/test_frontend_answer_ui.py`
- Corpus/private/source-inbox/provenance files.
- Chroma/vector stores or embeddings.
- Deployment/auth/DNS files.
- `ui/brand/`, `Neon Sign/`, raw design assets, and generated visual assets.

## Recommended Next Lane

Lane 18 Product / Architecture or Lane 06 UX/UI Design should confirm the response field name and first-trigger policy. Then Lane 05 can implement the backend slice using the prompt above.

## Commit Readiness

Safe to commit for this docs-only handoff if Repo Steward wants to record the plan exact-path.

Implementation is not ready to commit because it has not been implemented.

## Suggested Next Step

Use the exact next Lane 05 implementation prompt above after Lane 06 is clear enough that backend response-shape work will not conflict with active UI tab rendering.
