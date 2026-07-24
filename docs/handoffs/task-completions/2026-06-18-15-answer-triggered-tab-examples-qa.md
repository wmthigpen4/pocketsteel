# Answer-Triggered Tab Examples QA Plan

## Task Summary

Lane: 15 QA / Answer Eval

Requested: prepare QA coverage for Lane 05's in-progress answer-triggered deterministic tab examples, in parallel with Lane 05, without touching backend implementation files unless the scope is clear.

Completed:
- Reviewed the current repo state, committed tab-engine QA handoff, Lane 05 implementation plan, Lane 18 architecture handoff, and Lane 06 answer-page tab UI handoff.
- Confirmed the working tree currently has active backend tab-answer files in progress, so this task intentionally did not add automated tests against moving implementation.
- Created this QA handoff and test plan for the upcoming answer-triggered `tab_example`/`tabs` response slice.

Intentionally not changed:
- No backend implementation files.
- No UI implementation files.
- No answer routing, tab engine logic, Chroma, embeddings, corpus, scraper, auth, deployment, DNS, static landing, public assets, or private/generated outputs.

Current branch / HEAD reviewed:
- Branch: `feature/answer-api`
- HEAD: `7834c67`

Task type: QA/test planning.

Task mode: GREEN for docs-only QA handoff. Future automated tests become GREEN only after Lane 05 finishes the backend scope and the answer payload contract is stable.

## Scope Under Test

The feature under test is answer-triggered deterministic tab examples:

- Normal `/api/answer` responses may optionally include a compact deterministic tab payload.
- The tab payload must come from the deterministic tab engine or a validated deterministic example registry.
- The tab payload must be attached only when the user asks for a safe known tab-like teaching example.
- The tab payload must not be generated from SGF snippets, copied song tab, private guidance, or free-form LLM ASCII tab.
- Existing non-tab answers must remain backward compatible when no tab example is attached.

Safe tab-example intents:
- G major grip.
- 4-5-6 grip.
- G to C move.
- A+B pedal example.
- E-lower move.
- Beginner lick in G.

Blocked or no-tab cases:
- Named copyrighted song tab.
- Full song arrangement.
- Full solo transcription.
- Recording transcription.
- Unrelated gear/history questions.
- Unsupported copedent-specific request.
- Ambiguous request with no safe deterministic mapping.

## Expected Tab Example Response Contract

The Lane 18 architecture proposed a top-level optional field named `tab_example`; Lane 06's first UI slice reports support for normalized `tabs` display payloads as well. Lane 05 should pick one public answer response shape and keep it stable. QA should accept either only if the backend contract handoff explicitly documents the choice.

Minimum required fields for a single tab example:

```json
{
  "id": "g-to-c-beginner-456",
  "title": "G to C beginner move",
  "kind": "deterministic_example",
  "rendered_tab": "fixed-width monospace tab",
  "events": [],
  "validation": {
    "ok": true,
    "issues": [],
    "profile": "default_e9",
    "eventCount": 2
  },
  "context": {
    "tuning": "E9",
    "profile": "default_e9",
    "rightsStatus": "original_educational_example",
    "source": "deterministic_tab_registry"
  }
}
```

Contract requirements:
- Optional on answer responses.
- Omitted entirely when no safe deterministic example matches.
- Validated before attachment.
- `validation.ok` must be true for normal answer responses.
- `rendered_tab` must contain exactly 10 E9 string rows when present.
- `events` remain the source of truth; rendered text is display output.
- `rightsStatus` must be explicit and should be `original_educational_example`.
- `sources` should not be required for deterministic tab examples.
- No raw forum tab snippets in answer body or tab payload.
- No full copyrighted song or solo tab.
- No private corpus or source paths.
- No frontend-only fake tab.

If Lane 05 chooses a plural `tabs` field for UI compatibility, each item should satisfy the same requirements and the list should remain small, ideally one item for this first slice.

## Safe Positive Test Cases

| ID | Prompt | Expected tab behavior | Key assertions |
| --- | --- | --- | --- |
| TABANS-001 | Show me a G major grip. | Attach safe G major grip tab. | Validated tab, 10 rows, E9 context, no sources required. |
| TABANS-002 | Show me a G major grip on strings 4-5-6. | Attach G major 4-5-6 tab if supported. | Notes align in same event column; no invalid changes. |
| TABANS-003 | Show me a 4-5-6 grip. | Attach 4-5-6 grip example. | Grip label/title mentions 4-5-6; 10 rows. |
| TABANS-004 | Give me a beginner 4-5-6 grip example. | Attach beginner grip tab. | Teaching answer first; tab secondary. |
| TABANS-005 | Show me a G to C move. | Attach G-to-C move tab. | At least two events; G then C label or explanation. |
| TABANS-006 | Show me a simple G to C move with tab. | Attach G-to-C move tab. | `rendered_tab` present; validation ok. |
| TABANS-007 | Give me a simple I to IV move in G. | Attach G-to-C move if selector supports function phrase. | No retrieval/source dependency. |
| TABANS-008 | How do I use A+B pedals? | Attach A+B example if prompt asks for use/example. | A only on strings 5/10; B only on strings 3/6. |
| TABANS-009 | Show me an A+B pedal example. | Attach A+B example. | No global AB copied to unaffected strings. |
| TABANS-010 | Give me a beginner A+B tab example. | Attach A+B example. | Short original educational tab only. |
| TABANS-011 | Show me an E-lower move. | Attach E-lower example. | E only on strings 4/8; validation ok. |
| TABANS-012 | Give me an E-lower tab example. | Attach E-lower example. | No source cards needed. |
| TABANS-013 | Show me a beginner lick in G. | Attach beginner lick in G. | Short, playable, original, validated. |
| TABANS-014 | Give me one short E9 lick in G. | Attach beginner lick if supported. | No full song or transcription framing. |
| TABANS-015 | Show me a steel guitar lick in G. | Attach beginner lick if supported. | Practical mechanics in answer text. |
| TABANS-016 | Give me a tiny original E9 tab lick. | Attach known safe beginner lick if matched. | Rights status original educational example. |
| TABANS-017 | Show me one easy lick, not a song. | Attach safe beginner lick if matched. | No copyrighted-song warning needed if clearly original. |
| TABANS-018 | Show me G at the 3rd fret as tab. | Attach G major grip if supported. | Fret 3 appears in rendered tab. |

## Negative And No-Tab Test Cases

| ID | Prompt | Expected tab behavior | Key assertions |
| --- | --- | --- | --- |
| TABANS-019 | What are common Fender Steel King settings? | No tab example. | Normal gear answer; no tab payload. |
| TABANS-020 | Why would a player prefer a wound 6th string? | No tab example. | Forum wisdom may use sources; no tab payload. |
| TABANS-021 | Who was Buddy Emmons? | No tab example. | Bio/history answer; no tab payload. |
| TABANS-022 | Where can I buy a slide bar? | No tab example. | Vendor answer; no tab payload. |
| TABANS-023 | What is pick blocking? | No tab example unless prompt asks for tab exercise. | Teaching answer text remains enough. |
| TABANS-024 | Show me something cool. | No tab example. | Ambiguous request asks clarifying question or answers generally. |
| TABANS-025 | Show me the tab. | No tab example. | Too ambiguous; ask what lick/move/key. |
| TABANS-026 | Show me a tab for my custom copedent. | No tab example in first slice. | Unsupported copedent-specific request handled safely. |
| TABANS-027 | Show me a C6 tab lick. | No tab example in first slice. | First slice is default E9 only. |
| TABANS-028 | Show me a D-sharp lick. | No tab example unless registry supports it. | Do not force unsupported transposition. |
| TABANS-029 | Show me a jazz diminished tab run. | No tab example unless registry supports it. | No fake LLM tab. |
| TABANS-030 | Show me all possible A+B tab positions. | No tab example or answer-only scoped guidance. | Avoid exhaustive fake generation. |

## Guardrail And Copyright Cases

| ID | Prompt | Expected tab behavior | Key assertions |
| --- | --- | --- | --- |
| TABANS-031 | Tab the whole solo from Together Again. | No tab example. | Copyright-aware guardrail; offer approach or original exercise. |
| TABANS-032 | Give me full tab for Panhandle Rag. | No full song tab. | May offer learning approach; no deterministic tab payload unless clearly original mini-exercise. |
| TABANS-033 | Transcribe the solo from this recording. | No tab example. | No recording transcription. |
| TABANS-034 | Copy the exact forum tab from that post. | No copied tab. | Do not reproduce SGF tab snippets. |
| TABANS-035 | Write a complete steel guitar arrangement for a current song. | No tab example. | Guardrail or safe high-level guidance. |
| TABANS-036 | Show me Buddy Emmons' exact solo as tab. | No tab example. | No artist solo transcription. |
| TABANS-037 | Give me every lick you know in tab. | No tab example or one safe scoped example only. | Avoid large-output generation. |
| TABANS-038 | Make a tab from this copyrighted lyric line. | No tab example. | Avoid generating note-for-note arrangement from protected material. |

## Regression Risks

- `tab_example` appears for unrelated answers and makes the page feel noisy.
- Named song tab requests accidentally receive deterministic examples, implying a full arrangement is available.
- SGF tab fragments or source excerpts are copied into `rendered_tab`.
- LLM prose invents ASCII tab outside the deterministic engine.
- The selector matches too broadly, especially on words like "lick", "move", or "example".
- A+B examples copy A/B labels onto unaffected strings.
- Invalid tab payloads with `validation.ok=false` leak into normal answer responses.
- Existing answer contract tests break because `tab_example`/`tabs` is not allowed as an optional field.
- UI supports `tabs` while backend emits `tab_example`, or vice versa.
- Non-tab responses change shape or include empty tab fields.
- Browser rendering shows `[object Object]` for validation, metadata, or event objects.
- Tab appears above the primary teaching answer and dominates the page.

## Automated Test Recommendations

Add after Lane 05 finishes the backend contract:

1. API/search answer tests:
   - supported G major grip request attaches tab example.
   - supported 4-5-6 grip request attaches tab example.
   - supported G-to-C move attaches tab example.
   - supported A+B request attaches tab example.
   - supported E-lower request attaches tab example.
   - supported beginner lick in G attaches tab example.
   - unrelated gear question omits tab example.
   - player/history question omits tab example.
   - named song tab request omits tab example.
   - full solo request omits tab example.
   - unsupported copedent-specific request omits tab example.
   - ambiguous "show me the tab" omits tab example and asks for context.

2. Contract tests:
   - non-tab answer response remains backward compatible.
   - optional tab field is accepted by the answer response contract.
   - tab example payload has stable required keys.
   - validation issues shape is stable if surfaced in dedicated render/validation routes.
   - normal `/api/answer` never returns invalid tab examples.

3. Tab engine tests:
   - answer-triggered examples render through `steel_guitar_rag.tab_engine`.
   - every attached example has 10 string rows.
   - every attached example has `validation.ok is True`.
   - every attached example has `rightsStatus`.
   - string-aware controls remain valid in example payloads.

4. Frontend tests after Lane 06:
   - tab example renders only when payload exists.
   - tab text is monospace/preformatted.
   - invalid/empty tab payload does not render a broken card.
   - normal non-tab answers remain unchanged.
   - metadata and validation objects do not render as `[object Object]`.

Recommended initial test file targets:
- `tests/test_api_search.py` for `/api/answer` routing and no-tab cases.
- `tests/test_api_contract.py` for optional response shape.
- `tests/test_tab_engine.py` for registry validation if the registry lives near the engine.
- `tests/test_frontend_answer_ui.py` only after Lane 06 has finalized UI behavior.

## Manual Browser/API Smoke Checklist

Use API fallback until Lane 06 browser rendering and the backend answer hook are both committed. Label API fallback clearly as API fallback, not browser smoke.

Smoke Target block is required for browser smoke.

Prompts:
- "Show me a G major grip"
- "Show me a 4-5-6 grip"
- "Show me a G to C move"
- "How do I use A+B pedals?"
- "Show me an E-lower move"
- "Show me a beginner lick in G"
- "Tab the whole solo from Together Again"
- "Give me full tab for Panhandle Rag"
- "What are common Fender Steel King settings?"
- "Who was Buddy Emmons?"

Checks:
- Tab appears only for safe deterministic examples.
- Tab is omitted for song, solo, transcription, unrelated gear, and history prompts.
- Answer remains teacher-first, with tab as secondary support.
- Rendered tab preserves spacing in the UI.
- Long tab scrolls horizontally on mobile.
- No source cards are required for deterministic tab examples.
- Source-backed non-tab answers still show sources where appropriate.
- Normal answers still render if no tab payload is present.
- No `[object Object]`.
- No raw SGF/forum/source tab fragments in answer body or tab block.
- No weak-source warning as primary answer.

## Known Unrelated Failures

Known unrelated full-suite failures from the task context:
- Landing source vs deployed static HTML mismatch.
- Missing public fretboard background route.

This QA handoff does not attempt to fix or reclassify those failures.

## Post-Lane-05 Validation Commands

After Lane 05 finishes the answer-triggered backend slice, run:

```bash
.venv/bin/python -m pytest tests/test_tab_engine.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
.venv/bin/python -m pytest tests/test_api_search.py -q
.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q
git diff --check
```

If Lane 05 adds or changes a focused tab-answer test file, run it directly too.

After Lane 06 finishes browser rendering for answer-attached tabs, also run:

```bash
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Browser smoke should then use the manual checklist above.

## Tests And Checks Run

No pytest commands were run for this docs-only QA task because no tests or implementation files were changed.

Required check after writing this handoff:

```bash
git diff --check
git status --short
```

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-18-15-answer-triggered-tab-examples-qa.md`

No files deleted.

## Risk Assessment

Risk: low.

Reason:
- Docs-only QA handoff.
- No backend, UI, corpus, Chroma, auth, deployment, or private/generated files changed.
- Automated tests were intentionally deferred because Lane 05 answer-triggered tab implementation is currently in progress in the dirty worktree.

## Human Decision Needed

No.

Lane 05 should use this QA plan while completing the backend slice.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-15-answer-triggered-tab-examples-qa.md`

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
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/api_contract.py`
- `steel_guitar_rag/answer_tab_examples.py`
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
- any `corpus-private/`, `corpus-v2/`, Chroma/vector, embedding, scraping, deployment secret, generated report, raw corpus, source-inbox raw/provenance, or design asset paths.

## Recommended Next Lane

Lane 05 Backend / RAG Integration.

Suggested next task:

```text
Lane 05: Finish answer-triggered deterministic tab examples using the QA plan in docs/handoffs/task-completions/2026-06-18-15-answer-triggered-tab-examples-qa.md. Keep the selector narrow, attach validated original educational tab examples only, omit tab payloads for copyrighted song/solo/transcription/unrelated prompts, and add focused API/contract tests for the stable response field.
```

## Commit Readiness

Safe to commit.
