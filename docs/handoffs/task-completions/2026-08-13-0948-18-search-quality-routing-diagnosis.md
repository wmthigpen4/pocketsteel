# Search quality routing diagnosis

## Task summary

- Compared the user-provided Google result and Steel Guitar RAG answer for: “How does a steel guitar player decide when to move frets? Why not just stay on one fret?”
- Diagnosed the live protected application's route, current runtime wiring, deterministic coverage, SGF frontier health, and relevant evaluation coverage.
- Made no application, prompt, classifier, retrieval, corpus, index, deployment, auth, or service changes.

## Lane and task mode

- Lane: `18 Product / Architecture`, with read-only Lane 05 and Lane 15 evidence.
- Task type: diagnosis and architecture recommendation.
- Mode: GREEN for the diagnosis. Any answer-routing or retrieval change is YELLOW and requires an approved implementation scope.

## Finding

This is primarily a control-plane failure, not a missing-corpus failure.

The live route trace for the 88-character question reported:

- classification: `steel_guitar:copedent_position`
- route: `deterministic`
- corpus probe: `not_needed`
- retrieval: `legacy_local_retrieval`
- evidence: `0_source_cards`
- synthesis: `deterministic_or_curated_legacy`
- displayed answer: `answer_with_optional_sources`
- fallback: `none`

The user-visible answer was nevertheless the generic specificity fallback. This means fallback observability is also inaccurate.

## Root cause

1. The deterministic classifier treats the generic tokens `fret` and `frets` as copedent-position vocabulary. The copedent branch runs before the general in-domain source-backed branch, so this clear beginner concept question becomes `copedent_position` with `needs_sources=false` and `retrieval_allowed=false`.
2. No deterministic selector recognizes this phrasing. The visual answer, unsupported-position answer, fretboard payload, intent-mode curated answer, foundation concept answer, and SGF quarantine teacher answer all return `None` for the exact question.
3. The high-quality canonical SGF frontier only runs for `source_backed_rag` and `hybrid`; this question is therefore not sent to it. The old local Chroma retrieval path still runs, but the completed response contains zero displayable source cards.
4. After the deterministic miss, the system does not escalate to the canonical frontier. It falls through the legacy path and ultimately replaces the unusable answer with “I need a more specific steel-guitar question.”
5. The answer contract accepts that refusal as valid general forum wisdom, so the quality gate does not reject a non-answer to a clear in-domain question.
6. The route trace leaves `fallback=none` when the SGF quarantine fallback is displayed. Monitoring therefore undercounts exactly this quality failure.

## Runtime evidence

- Protected application listener: `127.0.0.1:8770`, git SHA `4a77e849`, started 2026-08-06.
- Site process configuration:
  - `STEEL_RAG_CANONICAL_FRONTIER_ENABLED=true`
  - frontier URL `http://127.0.0.1:8771/v1/answer`
  - timeout 90 seconds
  - Chroma collection `steel_guitar_unified`
  - retrieval mode `hybrid_private_first`
- Canonical frontier listener: `127.0.0.1:8771`, ready.
- Frontier architecture: `canonical-frontier-v1034-balanced-terra-normalized-attribution-independent-guard-exact-entity-fallback`.
- Verified frontier bundle reports 1,948,039 indexed canonical passages.
- The running classifier file is byte-identical to the current worktree classifier, so the defect remains present at current `HEAD`.

## Comparison with Google

Google wins this example because it directly answers the user's actual beginner concept question. Its overview is not fully pedal-steel precise: it understates how much chord and melodic movement pedals and knee levers can provide while the bar stays on one fret. Its organic result set also contains substantial ordinary-guitar and fretwire noise. The decisive product failure is therefore not Google's result count; it is that Steel Guitar RAG refuses an answerable question despite having more specialized knowledge.

## Evaluation blind spot

- The current suite includes nearby prompts such as “Teach me a lesson on bar movement,” “Why does my bar movement sound rough?”, and a highly specific G-to-C up-neck move.
- Those tested phrasings pass and exercise existing deterministic content.
- The suite does not include the broader conceptual distinction between staying at one fret and moving the bar, nor paraphrases such as “when should I change positions?”
- The current classifier test suite passes 104 tests and the foundation-concept API test passes, even though this exact live question fails.
- The v1034 release audit's fresh integrated expert-quality gate used only five cases. It proves the frontier can work when reached; it does not prove broad beginner-query routing coverage.

## Recommended repair slice

1. Add a first-class `beginner_concept` or `position_strategy` intent for “why/when move frets/bar/positions” questions. Do not treat bare `fret(s)` as sufficient evidence of a concrete copedent-position request.
2. Add a deterministic teacher answer explaining harmony, melody, inversions/register, voice leading, tone, mechanical availability, and setup for the next phrase. Include the important counterpoint that pedal steel can often change harmony at one fret with pedals and levers.
3. Add deterministic-miss escalation: if a deterministic route produces no answer artifact, retry route selection as source-backed or hybrid instead of entering the legacy fallback.
4. Send source-backed/hybrid requests to the canonical frontier; retire the legacy answer path as a silent quality fallback for eligible in-domain questions.
5. Make a clear in-domain non-answer fail the answer contract. A specificity request should be allowed only when a material fact is genuinely missing.
6. Mark quarantine/specificity fallbacks explicitly in route telemetry and add counters/alerts.
7. Add paraphrase families and adversarial keyword collisions to the must-pass user smoke bank, including this exact question.

## Files changed

- Added this diagnosis handoff only.
- No product files changed.

## Tests and checks

- Rendered and visually inspected all five pages of the Google PDF and the complete one-page Steel Guitar RAG PDF.
- Reproduced the exact classifier decision locally.
- Confirmed all deterministic answer selectors return no match for the exact question.
- Confirmed nearby movement wording selects an existing deterministic lesson.
- Inspected the live signed-in answer page and the privacy-safe live route trace.
- Verified the protected application version, runtime flags, both listeners, and canonical frontier readiness.
- `.venv/bin/pytest tests/test_answer_intent_classifier.py -q` — PASS, 104 tests.
- `.venv/bin/pytest tests/test_api_search.py::test_steel_guitar_101_foundation_concepts_are_teacher_first_and_source_free -q` — PASS, 1 test.

## Risks

- A narrow regex patch alone would fix this sentence but preserve the systemic paraphrase brittleness.
- Routing every beginner concept through SGF would add latency and can let anecdotal forum text dominate basic instruction. Deterministic teacher content should lead; SGF should enrich or support it when useful.
- Any production routing change requires focused regression tests and protected-preview smoke.

## Human decision needed

Approve a YELLOW implementation scope for the seven-point repair slice above. No corpus rebuild, embedding rebuild, scraping, auth, DNS, or raw-data change is needed.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-13-0948-18-search-quality-routing-diagnosis.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing unrelated modification).
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md` (pre-existing unrelated untracked file).
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md` (pre-existing unrelated untracked file).
- Corpus, Chroma, vector indexes, evaluation state, private data, credentials, environment files, logs, generated PDF renders, or deployment artifacts.

## Recommended next lane

- Lane 18: approve the answer/routing contract.
- Lane 05: implement the smallest complete deterministic-plus-frontier escalation fix.
- Lane 15: add the paraphrase family and run focused API and protected browser smoke.

## Commit readiness

The handoff is ready for exact-path staging if desired. No product implementation is present or ready to commit.
