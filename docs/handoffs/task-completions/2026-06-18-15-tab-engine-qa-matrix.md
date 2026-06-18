# Pocket Steel Tab Engine QA Matrix

## Task Summary

Lane: 15 QA / Answer Eval

Requested: build a QA plan and adversarial test matrix for the new deterministic Pocket Steel tab engine while Lane 05 builds the first backend slice.

Completed:
- Inspected repo QA/eval structure enough to identify likely future test locations.
- Created this QA matrix with renderer, validation, API, answer-integration, and product-guardrail coverage.
- Included 56 specific test cases, including 26 adversarial cases.
- Recommended which checks should become automated pytest coverage versus manual/browser smoke.

Intentionally not changed:
- No backend tab-engine code.
- No answer routing, `/api/answer`, Chroma, embeddings, corpus, scraper, deployment, DNS, auth, UI, or private/generated outputs.
- No answer-eval fixtures were modified yet; recommendations are included below for future fixture work.

## Intended Behavior Under Test

The tab engine should be deterministic and event based, not an LLM-only ASCII tab generator.

Core tab rules:
- Fixed-width monospace output.
- Always 10 string rows for E9.
- Event-based model where one event equals one pick attack.
- Stacked notes in the same event start in the same column.
- Horizontal offset means a later event.
- No more than 3 strings per event.
- Generated examples use only 2- or 3-string grips.
- Straight bar / single fret per event by default.
- Multi-fret grips require an explicit slant label or must be rejected.
- Pedal/lever annotations are string-aware.
- Strings not affected by a pedal/lever must not show that code.
- Lyrics align directly above the event start column.
- Generated tab must be physically playable.

Default E9 open strings:

| String | Open note |
| --- | --- |
| 1 | F# |
| 2 | D# |
| 3 | G# |
| 4 | E |
| 5 | B |
| 6 | G# |
| 7 | F# |
| 8 | E |
| 9 | D |
| 10 | B |

Supported string-aware change labels:

| Change | Affected strings |
| --- | --- |
| A | 5, 10 |
| B | 3, 6 |
| C | 4, 5 |
| E | 4, 8 |
| F | 4, 8 |
| V | 5, 10 |
| G | 1, 6 |
| D | 2, 9 |

## Test Categories Covered

- Renderer structure
- Event alignment
- String-aware pedal validation
- Lyric alignment
- Chord alignment
- Grip limits
- Impossible combinations
- Example library validation
- API validation if Lane 05 adds an endpoint
- Answer integration risks
- Copyright/product guardrails

## QA Test Matrix

Legend:
- `Auto` means should become deterministic pytest coverage.
- `Browser` means should be verified in UI/browser smoke once rendered in answer UI.
- `A` in the Type column means adversarial or negative case.

| ID | Category | Type | Test input / scenario | Expected result | Recommended coverage |
| --- | --- | --- | --- | --- | --- |
| TAB-001 | Renderer structure | Positive | Render a single event on strings 4-5-6 at fret 3 with no pedals. | Output is fixed-width monospace with exactly 10 string rows, labels 1-10, and aligned fret text at one column. | Auto |
| TAB-002 | Renderer structure | Positive | Render an event on string 10 only. | 10th string row exists and can carry an event without layout drift. | Auto |
| TAB-003 | Renderer structure | A | Renderer output omits string 10. | Validation fails before render or render test fails with "expected 10 string rows." | Auto |
| TAB-004 | Renderer structure | A | Renderer returns Markdown table or proportional HTML instead of preformatted monospace tab. | Fail; tab must be fixed-width text or structured event data rendered into fixed-width/pre UI. | Auto + Browser |
| TAB-005 | Renderer structure | Positive | Render empty/rest columns before first event. | All string rows have equal length; empty columns are represented consistently. | Auto |
| TAB-006 | Renderer structure | Positive | Long tab wraps or scrolls in UI. | Backend emits stable fixed-width lines; UI preserves monospace and does not reflow columns. | Browser |
| TAB-007 | Event alignment | Positive | One event has strings 4, 5, and 6 at fret 3. | All three note tokens start at the same column. | Auto |
| TAB-008 | Event alignment | Positive | Two events: strings 4-5-6 fret 3, then strings 4-5-6 fret 5. | Second event starts later; horizontal offset is identical across rows in that event. | Auto |
| TAB-009 | Event alignment | A | Stacked event renders string 4 at column 8, string 5 at column 9, string 6 at column 8. | Fail; same-event tokens must share start column. | Auto |
| TAB-010 | Event alignment | A | Same pick attack encoded as separate horizontal columns. | Fail if event metadata says one event but renderer offsets notes. | Auto |
| TAB-011 | Event alignment | Positive | Event with a two-digit fret such as 10 on strings 4-5-6. | Token width is handled consistently; stacked notes still start in same column. | Auto |
| TAB-012 | Event alignment | Positive | Event with annotation `10AB` followed by `12`. | Later event column accounts for variable token width without overlap. | Auto |
| TAB-013 | String-aware pedal validation | Positive | A pedal on strings 5 and 10. | A annotation allowed only on rows 5 and 10. | Auto |
| TAB-014 | String-aware pedal validation | Positive | B pedal on strings 3 and 6. | B annotation allowed only on rows 3 and 6. | Auto |
| TAB-015 | String-aware pedal validation | Positive | C pedal on strings 4 and 5. | C annotation allowed only on rows 4 and 5. | Auto |
| TAB-016 | String-aware pedal validation | Positive | E and F levers on strings 4 and 8. | E/F annotations allowed only on rows 4 and 8. | Auto |
| TAB-017 | String-aware pedal validation | Positive | V lever on strings 5 and 10. | V annotation allowed only on rows 5 and 10. | Auto |
| TAB-018 | String-aware pedal validation | Positive | G lever on strings 1 and 6. | G annotation allowed only on rows 1 and 6. | Auto |
| TAB-019 | String-aware pedal validation | Positive | D lever on strings 2 and 9. | D annotation allowed only on rows 2 and 9. | Auto |
| TAB-020 | String-aware pedal validation | A | A pedal shown on string 4. | Validation fails; A does not affect string 4. | Auto |
| TAB-021 | String-aware pedal validation | A | B pedal shown on string 5. | Validation fails; B does not affect string 5. | Auto |
| TAB-022 | String-aware pedal validation | A | F lever shown on string 5. | Validation fails; F does not affect string 5. | Auto |
| TAB-023 | String-aware pedal validation | A | Global `AB` state copied onto every picked string row. | Fail on strings that are not affected by A or B. | Auto |
| TAB-024 | String-aware pedal validation | A | Unknown change label `X` appears in an event. | Validation fails with unsupported change label. | Auto |
| TAB-025 | Lyric alignment | Positive | Lyric syllables `I`, `love`, `you` attached to three events. | Each syllable starts at the same column as its event. | Auto + Browser |
| TAB-026 | Lyric alignment | Positive | One lyric word spans a held note. | Word starts at event column; sustain/continuation may extend but cannot shift start. | Auto |
| TAB-027 | Lyric alignment | A | Lyric centered over multiple events rather than event start column. | Fail; lyric must align to the event start column. | Auto + Browser |
| TAB-028 | Lyric alignment | A | Lyric row length differs from tab row lengths. | Fail or normalize before render so all rows stay aligned. | Auto |
| TAB-029 | Chord alignment | Positive | Chord symbol `G` over fret 3 no-pedals event. | Chord label starts at event start column. | Auto + Browser |
| TAB-030 | Chord alignment | Positive | Chord symbols `G`, `C`, `D` over three events. | Each chord aligns with its event, not with the visual center of the grip. | Auto |
| TAB-031 | Chord alignment | A | Chord label floats between two events. | Fail; each chord label must attach to an event id or be omitted. | Auto |
| TAB-032 | Grip limits | Positive | Generated 2-string grip, strings 4-5. | Valid generated example. | Auto |
| TAB-033 | Grip limits | Positive | Generated 3-string grip, strings 4-5-6. | Valid generated example. | Auto |
| TAB-034 | Grip limits | A | Event contains strings 3-4-5-6. | Validation fails; max 3 strings per event. | Auto |
| TAB-035 | Grip limits | A | Event contains one string in generated example. | Reject or mark non-generated/manual; generated examples should use 2- or 3-string grips. | Auto |
| TAB-036 | Grip limits | A | Same event lists string 5 twice. | Validation fails for duplicate string in one event. | Auto |
| TAB-037 | Impossible combinations | A | Event has strings 4, 5, 6 at frets 3, 4, 3 with no slant label. | Validation fails; no unlabeled multi-fret grip. | Auto |
| TAB-038 | Impossible combinations | A | Event has string 4 fret -1. | Validation fails; negative fret is impossible. | Auto |
| TAB-039 | Impossible combinations | A | Event has string 4 fret 25. | Validation fails; fret above 24 is out of supported range. | Auto |
| TAB-040 | Impossible combinations | A | Event has string 11. | Validation fails; standard E9 tab model has strings 1-10 only. | Auto |
| TAB-041 | Impossible combinations | A | Event applies A and V to same string 5 without conflict policy. | Fail until Lane 05 defines whether simultaneous same-string raise/lower is supported. | Auto |
| TAB-042 | Impossible combinations | A | Render is called without validation. | Test should prove invalid event data cannot bypass validation before rendering. | Auto |
| TAB-043 | Example library validation | Positive | Built-in G major no-pedals example. | Physically playable 2- or 3-string grip, no sources required, 10 rows, no unsupported labels. | Auto |
| TAB-044 | Example library validation | Positive | Built-in A+B major-move example. | Only strings 3/6 show B, only strings 5/10 show A if those strings are picked. | Auto |
| TAB-045 | Example library validation | Positive | Built-in B+C pedal lick. | C appears only on strings 4/5; B appears only on strings 3/6. | Auto |
| TAB-046 | Example library validation | Positive | Built-in E-lower color example. | E appears only on strings 4/8 and tab remains playable. | Auto |
| TAB-047 | Example library validation | A | Example library contains any event with more than 3 strings. | Library validation fails. | Auto |
| TAB-048 | API validation | Positive | If `/api/tab` or answer payload endpoint exists, request "show a simple E9 lick in G". | Response includes structured event model plus rendered fixed-width tab or renderable data; no SGF retrieval required. | Auto API |
| TAB-049 | API validation | A | API receives invalid event payload with unknown label `X`. | 4xx validation error or safe structured failure; no rendered bad tab. | Auto API |
| TAB-050 | API validation | A | API request asks for "full tab for Together Again". | Copyright/product guardrail; no full song tab, no invented full arrangement. | Auto API + Answer Eval |
| TAB-051 | Answer integration risks | Positive | User asks "Show me one original E9 lick in G". | Answer may include short deterministic tab, source-free, plus teaching explanation if product wants. | Auto API + Browser |
| TAB-052 | Answer integration risks | A | LLM answer body contains ASCII tab not produced by tab engine. | Fail once provenance marker exists; generated tab must come from deterministic tab model. | Auto Answer Eval |
| TAB-053 | Answer integration risks | A | Answer includes malformed tab from SGF/source fragment as if generated. | Fail; source snippets cannot become generated tab. | Auto Answer Eval |
| TAB-054 | Answer integration risks | Positive | Non-tab theory question "What is pick blocking?" | No tab payload unless explicitly requested; answer remains teaching text. | Auto Answer Eval |
| TAB-055 | Copyright/product guardrails | A | Prompt: "Generate full song tab for a current copyrighted song." | Refuse full note-for-note tab and offer a short original exercise or approach. | Auto Answer Eval |
| TAB-056 | Copyright/product guardrails | A | Prompt: "Copy the exact Steel Guitar Forum tab from that post." | Refuse copying unreviewed/source tab into generated output; may summarize technique if sources allowed. | Auto Answer Eval |

## Minimum Automated Pytest Recommendations

Create focused backend tests once Lane 05 has concrete module names. Suggested test files:

- `tests/test_tab_engine_model.py`
- `tests/test_tab_engine_renderer.py`
- `tests/test_tab_engine_validation.py`
- `tests/test_api_tab_engine.py` if an endpoint or answer payload hook is added
- existing `tests/test_api_search.py` or `tests/test_full_answer_quality_eval.py` only for answer-integration and guardrail rows

Highest-priority automated tests:
- `TAB-001` through `TAB-012` for renderer structure and event alignment.
- `TAB-013` through `TAB-024` for string-aware pedal/lever validation.
- `TAB-025` through `TAB-031` for lyric and chord alignment.
- `TAB-034`, `TAB-036`, `TAB-037`, `TAB-038`, `TAB-039`, `TAB-040`, `TAB-042` for hard validation failures.
- `TAB-043` through `TAB-047` for example-library validation.
- `TAB-048` through `TAB-050` if Lane 05 adds an endpoint.
- `TAB-052`, `TAB-053`, `TAB-055`, `TAB-056` in answer eval/scorer once tab appears in answer responses.

Suggested assertions for automated renderer tests:
- Rendered tab is plain fixed-width text in a code/pre-compatible format.
- Exactly 10 string rows.
- All rows have equal display width after render.
- Same-event tokens share start column.
- Later event columns strictly increase.
- Chord and lyric start columns match event start columns.
- Annotation letters only appear on affected strings.
- Invalid input raises a structured validation error before render.

Suggested assertions for automated model tests:
- Every event has a stable id.
- Every event has 1 pick attack and 2-3 strings for generated examples.
- Every event has one fret unless a supported slant object/label exists.
- Strings are unique within an event.
- String numbers are integers 1-10.
- Frets are integers 0-24.
- Change labels are a subset of `A`, `B`, `C`, `E`, `F`, `V`, `G`, `D`.
- Validation runs before renderer entry points.

## Manual Browser Smoke Recommendations

Manual/browser smoke should start only after Lane 05 exposes tab output through an API or answer payload and Lane 06 renders it.

Smoke prompts:
- "Show me one original E9 lick in G."
- "Show me a B+C pedal lick."
- "Show me a simple G to C move with tab."
- "Add lyrics `I love you` over three E9 tab events."
- "Show me full tab for Together Again."
- "Show me tab with A pedal on string 4."

Browser/UI checks:
- The tab renders in monospace and preserves alignment on desktop and mobile.
- The UI uses `<pre>` or equivalent fixed-width presentation, not a Markdown table.
- Horizontal scroll is available if a tab is wider than the viewport.
- No line wrapping corrupts event columns.
- Lyrics and chord labels align above event starts.
- Invalid/adversarial prompts show a validation/guardrail response, not a malformed tab.
- Generated tab is visibly short and pedagogical, not a fake full-song transcription.
- Copy-to-clipboard, if added, copies fixed-width tab exactly.

## Answer Eval Fixture Recommendations

The repo already has:
- `tests/answer_eval/question_bank.jsonl` for broad planning prompts.
- `tests/answer_eval/expected_behaviors.md` for manual/evaluator interpretation.
- `tests/fixtures/user_question_bank.json` used by existing answer-quality runners.
- `tests/test_api_search.py`, `tests/test_answer_eval.py`, and `tests/test_full_answer_quality_eval.py` for current answer contract checks.

Recommended future fixture approach:
- Add a new `Tab/engine-generated examples` bucket to `tests/answer_eval/question_bank.jsonl` only after Lane 05 defines the response schema.
- Keep tab rows expectation-based, not snapshot-based. Avoid brittle full ASCII snapshots in broad answer eval.
- Use structured expectations such as:
  - `expected_intent: tab_engine_example`
  - `retrieval_allowed: false`
  - `sources_required: false`
  - `fretboard_allowed: false` unless a combined fretboard+tab answer is explicitly supported
  - `expected_answer_shape: deterministic tab-engine output with structured events and rendered fixed-width tab`
  - `must_include: ["E9", "strings", "fret"]`
  - `must_not_include: ["source support was weak", "retrieved material", "full copyrighted tab"]`
- Put exact alignment and pedal/string validation in dedicated tab-engine unit tests, not in high-level answer-quality JSON fixtures.
- In `tests/fixtures/user_question_bank.json`, add only a few non-brittle rows once the engine is wired:
  - "Show me one original E9 lick in G."
  - "Show me a B+C pedal lick."
  - "Show me full tab for a current copyrighted song."
  - "Explain this tab: 3rd fret strings 4-5-6 with A+B."
- Do not test raw copied tab from private/source material in answer fixtures.

## Lane 05 Implementation Notes

Lane 05 should account for:
- Separate structured event model from rendered ASCII.
- Make validation a required pre-render step.
- Return validation errors as structured, user-safe messages.
- Preserve deterministic provenance for generated tab so answer QA can tell engine output from LLM prose.
- Keep initial examples small: 1-4 events, 2- or 3-string grips, standard E9 only.
- Add explicit schema fields for event ids, event column/order, strings, fret, changes, lyric syllable, chord label, and optional slant metadata.
- Do not support full-song tab generation in the first slice.
- Do not infer multi-fret grips as playable unless slant support is deliberately designed.
- Do not copy tab from SGF/forum snippets into generated tab output.
- Do not wire to Chroma, corpus, private lesson data, or source-inbox for the first deterministic engine slice.

## Safe-To-Stage Exact File List

Safe to stage for this docs-only QA task:
- `docs/handoffs/task-completions/2026-06-18-15-tab-engine-qa-matrix.md`

Do not use `git add .`.

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files, especially:
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- SGF scraper outputs
- `source-inbox/` raw data or provenance
- `.wrangler/`
- DNS/deployment secrets
- `public/`
- `ui/brand/`
- `Neon Sign/`
- generated/private reports or raw design assets
- unrelated README, corpus metadata, landing, runtime, UI, or test files already dirty in the worktree

## Tests And Checks

Commands run:

```bash
git status --short
```

Result:
- Passed. Worktree is broadly dirty with many unrelated changes; this task only created the tab-engine QA matrix handoff.

```bash
find tests -maxdepth 3 -type f | sort | sed -n '1,220p'
```

Result:
- Passed. Confirmed existing test/eval structure.

```bash
sed -n '1,220p' tests/answer_eval/README.md
sed -n '1,220p' tests/answer_eval/expected_behaviors.md
```

Result:
- Passed. Confirmed answer-eval fixture guidance and browser smoke conventions.

```bash
rg -n "tab|tablature|lick|song|copyright|fretboard" tests/test_answer_eval.py tests/test_full_answer_quality_eval.py tests/test_api_search.py tests/answer_eval tests/fixtures/user_question_bank.json | head -200
```

Result:
- Passed. Confirmed existing tab/song/copyright and fretboard coverage areas.

```bash
git diff --check
```

Result:
- Passed.

```bash
git status --short -- docs/handoffs/task-completions/2026-06-18-15-tab-engine-qa-matrix.md
```

Result:
- Passed. Shows only the new untracked handoff file in this task scope.

```bash
git status --short
```

Result:
- Passed. Broad unrelated dirty worktree remains; this task only created the tab-engine QA matrix handoff.

## Risk Assessment

Risk level: low.

Why:
- This is a docs-only QA matrix.
- No app logic, tests, corpus, Chroma, scraper, UI, auth, deployment, or private data were modified.

Rollback notes:
- Delete this handoff file if the matrix is superseded.

## Human Decision Needed

No for this QA plan.

Yes before:
- adding a new endpoint,
- wiring generated tab into `/api/answer`,
- adding UI rendering,
- expanding answer-eval fixtures in a way that changes release gates,
- allowing any source-derived or copyrighted tab output.

## Commit Readiness

Safe to commit as a docs-only QA artifact, if Repo Steward stages only the exact handoff path.

## Recommended Next Lane

Recommended lane: `05 Backend / RAG Integration`.

Suggested next prompt:

```text
Lane 05: Build the first deterministic Pocket Steel tab-engine slice using docs/handoffs/task-completions/2026-06-18-15-tab-engine-qa-matrix.md as the QA contract. Implement a structured event model, validation before rendering, string-aware pedal/lever annotation checks, fixed-width monospace rendering, and a tiny standard E9 example library. Do not wire into Chroma, SGF retrieval, corpus-private, source-inbox, deployment, DNS, or public UI. Add focused pytest coverage for renderer structure, event alignment, string-aware pedals/levers, grip limits, impossible combinations, and example-library validation.
```
