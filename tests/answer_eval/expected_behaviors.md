# Answer Eval Expected Behaviors

This document explains how to interpret `tests/answer_eval/question_bank.jsonl` during manual smoke, browser smoke, or future evaluator wiring. The bank is intentionally broader than the current automated fixtures so product reviewers can sample the answer stack by expected answer class, not just by past failures.

## Common Pass Rules

Every answer should:

- answer the user directly before adding context
- use steel-guitar-specific language when the question is in-domain
- avoid raw Steel Guitar Forum fragments as the answer body
- avoid `[object Object]`, raw JSON, weak-source warning text, and internal implementation language
- use source cards only when the row expects source-backed evidence
- suppress source cards for deterministic fretboard, off-domain, impossible-output, invalid-symbol, and missing-context answers
- show a fretboard payload only when the row allows or requires a concrete visual answer

## Bucket Behaviors

### Valid Forum-Wisdom Steel Questions

Expected shape: source-backed synthesis. These answers may use retrieval and should include useful source cards. The answer body should summarize consensus, disagreement, and practical takeaways rather than copying forum snippets.

Fail if source cards are missing, excerpts are unrelated, or the main answer starts with forum chatter such as `Top`, `Does anyone know`, or first-person source fragments.

### Copedent-Aware Position Questions

Expected shape: structured E9/copedent answer. Personal setup questions should use authorized profile facts only. Standard E9 answers should say when they are assuming standard E9.

Fail if SGF copedent chatter is treated as the user profile, if 12-string strings leak into 10-string E9 answers, or if private facts appear in a generic/public answer.

### Fretboard-Rendering Questions

Expected shape: deterministic, source-free answer with `response.fretboard.positions` when the prompt asks for concrete positions.

Known facts to preserve:

- G open/no-pedals: fret 3
- G A+F: fret 6
- G A+B: fret 10
- A+F and A+B must not be swapped

Fail if source cards appear, the fretboard payload is missing, the answer borrows another key, or backend emits raw UI geometry.

### Gear Diagnosis Questions

Expected shape: practical diagnosis first. The answer should include likely causes, isolation steps, what to check or carry, and safety cautions for electrical/amp work when appropriate.

Source cards are allowed as support, but the answer must not be just anecdotes, jokes, gore stories, or generic product definitions.

### Practice-Plan Questions

Expected shape: immediately playable routine. Prefer time boxes, strings, frets, pedals/levers, grips, listening goals, and one measurable result.

Fail if the answer is a vague essay, player ranking, raw forum story, or generic encouragement without a drill.

### Tab/Interval Explainer Questions

Expected shape: copyright-safe mechanics explanation. Name strings, frets, pedals/levers, changed notes, chord tones, intervals, omitted tones, and whether context is missing.

For prompts containing `this`, `that`, `here`, or unspecified voicings, a clarifying question is acceptable and often required.

### Source-Required Questions

Expected shape: cited synthesis. Player/history/current-ish/vendor/forum-wisdom claims need source cards or curated links when evidence matters.

Fail if no source cards appear, if links are missing when known, or if source cards replace the answer.

### Off-Domain Guardrail Questions

Expected shape: short guardrail and redirect to steel-guitar topics. Retrieval is not allowed.

Fail if the answer retrieves SGF material, shows source cards, shows a fretboard, or tries to answer non-steel trivia/weather/recipes/current events directly.

### Impossible Or Abusive Large-Output Questions

Expected shape: scope/size/safety refusal with a steel-guitar redirect. Retrieval is not allowed.

Fail if the answer attempts the bulk output, reveals private/corpus/vector data, or displays source cards.

### Regression Cases From Known Failures

Expected shape: each row follows the route described in `docs/llm-guidance/known-failures.md`.

Use these as quick probes after answer-routing changes. They cover invalid chord prompts, source-card leakage, missing fretboards, weak-source leakage, raw fragments, off-domain leakage, and stale protected-preview behavior.

### Home-Screen TRY ASKING Prompt Questions

Expected shape: every clickable prompt should either produce a useful answer or ask for missing context. Home prompts should not fall through to raw retrieval fragments.

Fail if the answer is mostly source snippets, jokes, unrelated anecdotes, or 12-string guidance for a 10-string E9 context.

### Ambiguous Steel Terms That Need Clarification Or Careful Routing

Expected shape: ask for the missing key, chord, fret, strings/grip, pedals/levers, or target sound before retrieval.

Fail if the app guesses randomly, retrieves unrelated forum fragments, or shows source cards for underspecified `this/that/here` prompts.

## Manual Smoke Procedure

1. Choose a bucket or sample every bucket.
2. Run each `question` against the local or protected-preview answer UI/API.
3. Compare the answer against:
   - `expected_domain`
   - `expected_intent`
   - `retrieval_allowed`
   - `sources_required`
   - `fretboard_allowed`
   - `copedent_required`
   - `expected_answer_shape`
   - `must_include`
   - `must_not_include`
4. Record failures by symptom, not just by prompt:
   - raw forum fragment
   - missing source card
   - unexpected source card
   - missing fretboard
   - unexpected fretboard
   - wrong key/chord/pedal/lever
   - off-domain retrieval leak
   - weak-source warning leak
   - `[object Object]`
5. Promote confirmed failures into automated tests or the product red-team matrix.

## Browser Smoke Notes

Every browser smoke report, protected-preview smoke report, production smoke report, or API fallback used because browser tooling could not run must include this block before pass/fail results:

```text
Smoke Target:
- Target type: local | protected-preview | production-root | API-fallback
- Result type: browser smoke | API fallback, not browser smoke
- Exact browser URL tested:
- Cache-busted URL tested:
- Exact URL the user should use:
- Auth required: yes/no
- Auth provider: Cloudflare Access / none / other
- Cloudflare Access login result: succeeded / failed / not required / not attempted
- Local backend URL:
- Expected backend port:
- Expected git HEAD:
- Version endpoint:
- Version endpoint result:
- If version endpoint missing, how version is inferred:
- Whether app root `/` works:
- Whether app root `/` is expected to work:
- Whether `/ui/steel-guitar-rag-mock.html` works:
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work:
- Who should test this URL: Codex / the user / both
- Do not test these URLs:
- Known caveats:
```

Browser smoke pass/fail is invalid unless the exact URL tested is recorded. API fallback must be labeled `API fallback, not browser smoke`, protected-preview smoke must say whether Cloudflare Access login succeeded, and any root URL that is not expected to work must be called out explicitly.

For UI smoke, also verify:

- source cards have useful titles, labels, URLs, and readable excerpts
- fretboard cards render from `response.fretboard.positions`
- selector labels are human-readable
- markdown tables render as tables
- no stale protected-preview asset behavior is visible
- no text overlaps on mobile/narrow layouts

For UI-facing changes, visual smoke must include screenshot-backed evidence. A report may say `visual pass` only when it records screenshot paths or attached cropped images for the relevant visible state. If browser tooling can only prove DOM presence or console status, report `technical pass; visual not verified`.

Required visual checks for main app changes:

- Q&A/search remains visually primary
- header buttons are visible, separated, readable, and not overlapping
- answer, source-card, fretboard, tab, and prompt-chip areas do not visually crowd each other
- no raw internal labels or `[object Object]` text appears

Required visual checks for E9 Fretboard Explorer changes:

- key, scale, harmony/view, and string-group controls are visible and show selected state
- selected string groups visibly update the row/card/detail list
- selected string groups visibly update fretboard markers/clusters
- full-string lanes are absent unless the feature explicitly asks for them
- core and advanced groups remain distinguishable when relevant
- raw internal branch labels do not appear
- console status is recorded

When a user provides a screenshot or asks to match a visual reference, compare the smoke screenshot against that reference and record the visible match or mismatch. DOM counts do not override a visible mismatch.
