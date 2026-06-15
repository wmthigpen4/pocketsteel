# Curated Guidance Routing Design

## Task Summary

- What was requested: design how `curated_guidance` should eventually participate in Steel Guitar RAG answers while staying private-review, auth-gated, clearly labeled, and separate from public SGF/forum retrieval.
- What was completed: created this Lane 18 product/architecture design handoff with an executive recommendation, routing matrix, answer-mode design, auth/private-review policy, source-card labeling policy, feature-flag plan, Lane 05 implementation slices, Lane 15 QA plan, risks, non-goals, and recommended next lane.
- What was intentionally not changed: no code, prompts, `/api/answer`, UI, SGF retrieval, Chroma/vector stores, embeddings, `corpus-private/`, source-inbox data, scraping, deployment, DNS, staging, or commits were changed.

## Executive Recommendation

Use `curated_guidance` as a private-review teaching aid, not as public source material.

Recommended first integration:

- Protected-preview only.
- Auth-gated to admin/backstage users first.
- Disabled by default through feature flags.
- Routed only for teaching-style steel-guitar questions where curated guidance is likely to improve the lesson.
- Returned as capped excerpts with private labels, never as full guidance bodies.
- Used to synthesize teacher-first answers, not to quote large private material.
- Kept separate from SGF/forum source cards in both routing and labeling.

Do not blend curated guidance into anonymous/public answers. Do not promote it as public evidence. Do not make it part of SGF retrieval or Chroma. Do not expose private filenames, local paths, `private_review` internals, or full private guidance text to ordinary users.

## Current State

Committed slice:

- Commit: `f959769 curated guidance private retriever`
- Retriever: `pocketsteel/curated_guidance_retriever.py`
- Feature flag: `ENABLE_CURATED_GUIDANCE_RETRIEVAL`
- Default state: disabled.
- Input path: `corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl`
- Output: metadata and capped excerpts only.
- Not wired into:
  - `/api/answer`
  - SGF retrieval
  - Chroma
  - source cards
  - UI
  - auth
  - production

Known QA findings:

- Offline top-3 retrieval was useful for all 10 test teaching queries.
- Strongest topics:
  - split tuning
  - B+C pedals
  - B-to-Bb / vertical lever
  - right-hand blocking
- Warnings were mostly metadata/quality gates.
- No `possible_transcript_residue` flag appeared.
- Quality issues before app integration:
  - duplicate hashes
  - under-100-word rows
  - no-steel-term rows
  - missing topic tags
  - overlong rows
  - broad combined-card rows

## When Curated Guidance Should Be Used

Curated guidance should be eligible only when all of these are true:

- User is authorized for private-review guidance in the current environment.
- Feature flags permit curated guidance for answers.
- The question is in steel-guitar teaching scope.
- The answer intent benefits from lesson-style/private-review guidance rather than public forum consensus.
- The retriever returns clean enough, capped, relevant results.

Good-fit query classes:

- Teaching requests:
  - "Show me how to use B+C."
  - "How do I tune a split on string 6?"
  - "How should I practice right-hand blocking?"
- "Show me how" requests involving E9 mechanics, grips, pedals/levers, bar movement, or practice.
- Tab, lick, and interval explanation requests when the user needs mechanics, not copyrighted full tab.
- Practice-plan requests where curated notes can provide a drill shape or teaching sequence.
- Mechanical setup questions about E9 pulls, split tuning, vertical lever alternatives, or pedal/lever technique.
- Hybrid teaching questions where SGF wisdom can add player consensus but curated guidance can supply a clearer lesson.

Best first topics:

- split tuning
- B+C pedals
- B-to-Bb / vertical lever alternatives
- right-hand blocking

## When Curated Guidance Should Not Be Used

Curated guidance should not be used for:

- Public unauthenticated answers.
- Anonymous users.
- Ordinary public production routes.
- Historical/player-context questions such as "Who is Buddy Emmons?"
- Opinion/consensus questions where public SGF wisdom is the correct evidence layer.
- Pure SGF source-backed answers that ask what forum players say.
- Vendor/current/product availability questions that need curated official/current source registry, not private teaching notes.
- Gear diagnosis unless the question is really a teaching/mechanics issue and the guidance is directly relevant.
- Off-domain, unsafe, impossible-output, or copyright-guardrail prompts.
- Questions outside E9/steel teaching scope.
- Any request where the private corpus is missing, disabled, or returns only low-quality results.

## Routing Matrix

| Intent / question class | Primary route | Curated guidance role | SGF role | Fretboard role | Source card behavior |
| --- | --- | --- | --- | --- | --- |
| Off-domain / unsafe / impossible | No retrieval / guardrail | Forbidden | Forbidden | Forbidden | No source cards |
| Missing-context `this/that/here` prompt | Clarification | Forbidden | Forbidden | Usually forbidden | No source cards |
| Deterministic major chord positions | Deterministic fretboard/position engine | Forbidden by default | Forbidden | Required | No SGF cards; no curated cards |
| Deterministic supported E9 mechanics | Deterministic rules first | Optional support only for admin/private-review teaching mode | Forbidden unless user asks forum wisdom | Optional | No curated cards unless enabled and authorized |
| Teaching-style E9 mechanics | Curated guidance only or deterministic + curated | Primary private teaching aid | Optional only if user asks player consensus | Optional if concrete positions | Private teaching guidance cards, capped |
| Practice plan / drill | Curated guidance only when authorized | Primary support for lesson structure | Usually none | Optional | Private guidance cards optional/secondary |
| Tab / lick / interval explanation | Deterministic + curated guidance | Support mechanics and teaching explanation | Usually none | Optional | Private guidance cards optional/secondary |
| Hybrid teaching + player wisdom | Hybrid SGF + curated guidance | Teaching structure | Consensus/disagreements | Optional | Separate public SGF and private guidance card groups |
| Gear diagnosis | SGF or direct diagnostic route | Usually forbidden | Supporting evidence when relevant | Forbidden | SGF source cards only unless explicitly a teaching/setup mechanics question |
| Historical/player-context | SGF/curated registry | Forbidden | Primary if source-backed | Forbidden | Public/curated public source cards |
| Vendor/buying/current facts | Curated source registry / official current links | Forbidden | Secondary, stale by default | Forbidden | Official/current source cards |
| General forum wisdom | SGF only | Forbidden | Primary | Usually forbidden | SGF cards only |

## Answer-Mode Design

### SGF Only

Use when the user asks what players say, what forum wisdom exists, historical/player context, opinion/consensus, product anecdotes, or gear experience.

Curated guidance must not silently enter this path.

### Curated Guidance Only

Use for protected-preview/admin teaching prompts where the user asks for a lesson, drill, lick explanation, split-tuning help, B+C use, vertical lever alternatives, or blocking practice.

The answer should be teacher-first synthesis. Curated guidance excerpts should be evidence below the answer, not the answer body.

### Hybrid SGF + Curated Guidance

Use only when both are explicitly valuable:

- SGF supplies player consensus, caveats, or disagreement.
- Curated guidance supplies lesson structure or mechanical explanation.

Hybrid results must keep labels separate:

- SGF evidence
- Private teaching guidance

Do not merge private guidance into a public-looking SGF source card.

### Deterministic Fretboard / Position Engine

Use before retrieval for concrete visualizable chord/position questions.

Curated guidance can be future optional support only for advanced teaching mode after deterministic output is already correct. It must not replace pitch/copedent math.

### No Retrieval / Clarification Needed

Use when the prompt is off-domain, unsafe, impossible, missing key/fret/string/pedal context, or asks for unspecified "this/that/here" material.

Curated guidance must not be used to guess missing context.

## Auth And Private-Review Policy

### Public Users

- Curated guidance forbidden.
- No private-review source cards.
- No private excerpts.
- No private filenames, source paths, `visibility`, or `private_review` labels.
- Public answer behavior must be identical when curated guidance flags are off or unavailable.

### Anonymous Users

Same as public users. Curated guidance is forbidden.

### Private Beta Users

Default recommendation: curated guidance remains off unless a product decision explicitly grants beta access.

If later enabled for beta users:

- Use globally private-reviewed guidance only, not user-specific private material.
- Show clear labels such as "Private teaching guidance".
- Keep excerpts capped and secondary.
- Do not expose filenames or internal review metadata.

### Admin / Backstage Users

Recommended first audience.

Admin/backstage users may see capped curated-guidance source cards in protected preview if all relevant feature flags are on.

Admin UI may expose a slightly more explicit label such as "Private teaching guidance (review)" but should still avoid local source paths and full bodies.

### Protected Preview

Protected preview is the first safe integration target.

Requirements:

- Authenticated only.
- Feature-flagged.
- Clear labels.
- Capped excerpts.
- No full private bodies.
- No public promotion.
- Safe fallback if corpus is missing.

### User-Specific vs Globally Private

`curated_guidance` should initially be globally private-review guidance, not user-specific memory.

Do not mix it with the user's personal copedent/profile data. Personal/profile-backed answers require a separate authorization model and separate labels.

## Source-Card Labeling Policy

Recommended user-facing label:

- `Private teaching guidance`

Recommended secondary label:

- `Curated guidance note`

Acceptable admin/backstage-only label:

- `Private teaching guidance (review)`

Avoid:

- `Internal practice note` for ordinary users, because "internal" can make the app feel leaky.
- `private_review` in UI.
- raw `content_layer` values.
- raw `source_path`.
- local filenames by default.
- full guidance titles if they contain internal naming, local draft language, or source provenance that has not been reviewed.

Recommended source-card shape:

```json
{
  "title": "Private teaching guidance",
  "label": "Curated guidance note",
  "visibility": "private_teaching_guidance",
  "excerpt": "Capped paraphrase or capped excerpt...",
  "sourceKind": "curated_guidance",
  "reviewStatus": "private_review"
}
```

For non-admin users, omit `reviewStatus`, raw `visibility`, filenames, and source paths from visible UI. Backend may keep machine metadata internally for QA.

## What Should Be Shown In Answers

### Answer Body

The answer body should be synthesized and teacher-first:

- direct answer
- why it works
- steel-guitar application
- practice step
- caveats when needed

Curated guidance should inform the answer, but the answer should not copy large private bodies.

### Excerpt Length

Current retriever cap is 500 characters. Recommended app caps:

- Backend result cap: keep 500 characters maximum.
- User-facing card excerpt: 240-320 characters by default.
- Admin/backstage expanded excerpt: up to 500 characters.
- Never show full guidance bodies through `/api/answer`.

### Paraphrasing vs Quoting

Default: paraphrase.

Short excerpts may be shown as evidence in source cards only when:

- user is authorized,
- flags are enabled,
- excerpt is capped,
- text passed quality filters,
- source-card label clearly marks private teaching guidance.

Do not quote long private guidance passages in the answer body.

### Filenames And Paths

Default: do not show filenames or source paths.

Admin/debug tooling may expose source identifiers only in protected admin contexts after explicit approval. Public, anonymous, and ordinary beta UI should not expose local filenames or paths.

### `private_review` Visibility

Do not show the raw term `private_review` in user-facing UI.

Use:

- "Private teaching guidance"
- "Curated guidance note"
- "Review-only teaching note" for admin/backstage if needed

### Full Guidance Bodies

Never show full guidance bodies in `/api/answer`.

Full bodies may be reviewed only in a separate admin/provenance review tool after explicit product/security approval, not in the answer UI.

## Feature Flag Plan

Current flag:

- `ENABLE_CURATED_GUIDANCE_RETRIEVAL`
  - Enables the private local retriever.
  - Should remain default off.

Recommended additional flags:

- `ENABLE_CURATED_GUIDANCE_IN_ANSWER`
  - Allows `/api/answer` orchestration to consider curated guidance.
  - Default off.
- `ENABLE_CURATED_GUIDANCE_SOURCE_CARDS`
  - Allows curated guidance evidence cards to appear for authorized users.
  - Default off.
- `ENABLE_CURATED_GUIDANCE_HYBRID_MODE`
  - Allows SGF + curated guidance hybrid answers.
  - Default off.
- `ENABLE_PRIVATE_REVIEW_SOURCES`
  - Umbrella gate for any private-review source layer in answer flows.
  - Default off.

Recommended gating rule:

All of the following must be true before curated guidance participates in an answer:

- `ENABLE_PRIVATE_REVIEW_SOURCES=true`
- `ENABLE_CURATED_GUIDANCE_RETRIEVAL=true`
- `ENABLE_CURATED_GUIDANCE_IN_ANSWER=true`
- authorized role is admin/backstage for the first slice
- route intent is curated-guidance eligible
- private JSONL exists
- retriever returns clean, capped results

Source cards additionally require:

- `ENABLE_CURATED_GUIDANCE_SOURCE_CARDS=true`

Hybrid additionally requires:

- `ENABLE_CURATED_GUIDANCE_HYBRID_MODE=true`

## Existing Answer Engine Interaction

### Intent Classifier Changes

Future classifier should distinguish:

- teaching_mechanics
- practice_drill
- tab_or_lick_explainer
- setup_mechanics
- public_forum_wisdom
- deterministic_fretboard
- gear_diagnostic
- history_or_player_context
- off_domain_or_guardrail
- missing_context

Curated guidance eligibility should be a routing attribute, not a public response field:

```json
{
  "curated_guidance_allowed": true,
  "curated_guidance_mode": "private_review_teaching"
}
```

Do not expose this classifier metadata in public `/api/answer` responses.

### Retrieval Orchestration

Recommended order:

1. Guardrail/off-domain/missing-context checks.
2. Deterministic fretboard/rules engine when applicable.
3. Curated guidance eligibility check.
4. SGF eligibility check.
5. Retrieve from only the allowed sources for that route.
6. Compose teacher-first answer.
7. Attach source cards according to auth and flags.

Do not call curated guidance as a generic fallback after SGF is weak. It should be intent-routed, not desperation-routed.

### Answer Prompt / Composer Changes

Future answer composition should treat curated guidance as private teaching context.

Composer rules:

- Synthesize.
- Paraphrase by default.
- Use snippets only as source-card excerpts.
- Do not quote large bodies.
- Do not mention local private corpus internals.
- Keep source-backed, deterministic, and private-review evidence separate.

### Source-Card Rendering

Curated guidance cards should render in a separate group or with a distinct label.

Recommended grouping:

1. Answer
2. Fretboard, if present
3. Sources
   - Public SGF evidence
   - Private teaching guidance

Do not visually merge public SGF cards and private guidance cards.

### Failure Behavior When Private Corpus Is Missing

If curated guidance is enabled but the private JSONL is missing:

- Do not error the answer.
- Do not show a source card.
- Do not mention missing private files to the user.
- Log or expose admin-only diagnostic metadata if a debug channel exists.
- Fall back to deterministic route, SGF route, or no-retrieval teacher answer depending on the intent.

For admin/backstage protected preview, a non-blocking warning may be acceptable outside the answer body, but never expose local paths or private corpus details to normal users.

## Lane 05 Implementation Slices

### Slice 1: Routing Classifier Only

Goal: classify curated-guidance eligibility without retrieving or changing answers.

Allowed changes:

- Add internal route fields or helper functions.
- Tests for eligible/ineligible intents.

Do not:

- Retrieve curated guidance.
- Change public response shape.
- Add source cards.

### Slice 2: Protected-Preview Answer Orchestration Only

Goal: when admin/backstage protected preview and flags are enabled, retrieve curated guidance for eligible teaching questions and pass it to the answer composer.

Required:

- Default off.
- Admin/backstage only.
- Missing corpus fallback.
- No public route behavior change.

### Slice 3: Source Card Labeling Only

Goal: add labeled private teaching guidance cards for authorized protected-preview users.

Required:

- Distinct label.
- Capped excerpt.
- No filenames/paths.
- No full bodies.
- No public UI exposure.

### Slice 4: Protected-Preview Smoke Only

Goal: verify protected-preview behavior before any broader promotion.

Smoke:

- feature flags off
- feature flags on for admin/backstage
- public route blocked
- missing private corpus fallback
- curated teaching query
- SGF wisdom query
- hybrid query if hybrid flag enabled

### Slice 5: Admin / Backstage Controls

Goal: add explicit operational controls for private-review sources if product wants ongoing review.

Examples:

- admin-only display of review status
- source audit metadata
- private-review source toggle

This is not required for first integration.

### Slice 6: Public Production Promotion, If Ever

Recommendation: do not promote curated guidance to public production until:

- provenance/legal review approves it,
- quality flags are cleaned or filtered,
- full body exposure is impossible by contract,
- auth behavior is audited,
- Lane 15 signs off,
- product explicitly approves public/beta scope.

## Lane 15 QA Plan

Required test cases:

- Feature flag off:
  - curated guidance retriever not called;
  - answer behavior unchanged.
- Private corpus missing:
  - no crash;
  - no user-facing private-path warning;
  - fallback answer still works.
- Protected preview on:
  - admin/backstage user can receive curated guidance only when all flags allow it.
- Public route off:
  - anonymous/public answer never includes curated guidance, source labels, private excerpts, filenames, or `private_review`.
- Teaching query uses curated guidance:
  - split tuning;
  - B+C pedals;
  - B-to-Bb / vertical lever;
  - right-hand blocking.
- SGF wisdom query does not use curated guidance:
  - "What do players say about wound 6th strings?"
  - "What do forum players say about lowering string 6?"
- Hybrid query uses both only when hybrid flag is enabled:
  - SGF cards and curated guidance cards remain separately labeled.
- Excerpts stay capped:
  - backend never emits over 500 chars;
  - UI default excerpt target is 240-320 chars if implemented.
- No private full bodies leak:
  - answer body;
  - source cards;
  - JSON response;
  - logs/smoke reports.
- Source labels are clear:
  - user-facing label says "Private teaching guidance" or equivalent;
  - raw `private_review`, source paths, and filenames do not appear for normal users.

Suggested regression buckets:

- curated_guidance_public_leak
- curated_guidance_full_body_leak
- curated_guidance_path_or_filename_leak
- curated_guidance_wrong_intent
- curated_guidance_missing_corpus_fallback
- curated_guidance_source_label_confusing
- curated_guidance_hybrid_blending
- curated_guidance_excerpt_over_cap

## Risks

Risk level: medium.

Why:

- The retriever is isolated and disabled today, but answer integration could accidentally expose private-review material.
- The source layer has known quality issues that should be filtered before broader use.
- Hybrid routing can confuse users if public SGF evidence and private guidance are visually blended.
- Full guidance bodies, local filenames, and private metadata must stay out of normal answer responses.

Risk mitigations:

- Protected-preview/admin first.
- Multiple feature flags.
- Auth checks before retrieval.
- Intent allowlist, not fallback retrieval.
- Capped excerpts.
- No filenames/paths in UI.
- No full bodies.
- Separate source-card group/label.
- Lane 15 smoke before any user-facing promotion.

## Explicit Non-Goals

- Do not implement code in this lane.
- Do not modify prompts.
- Do not modify `/api/answer`.
- Do not modify UI.
- Do not modify SGF retrieval.
- Do not modify Chroma or embeddings.
- Do not stage or commit.
- Do not touch `corpus-private/`.
- Do not expose private-review guidance as public source material.
- Do not copy large private guidance bodies into answers.
- Do not blend private guidance into public answers without auth/private-review controls.
- Do not treat curated guidance as a replacement for deterministic pitch/fretboard logic.

## Files Changed

- Created:
  - `docs/handoffs/task-completions/curated-guidance-routing-design.md`
- Changed:
  - None
- Deleted:
  - None
- Generated artifacts:
  - None

## Tests And Checks

Commands run:

- `git status --short`
  - Status before editing captured a broad pre-existing dirty worktree. The target design handoff did not exist at that point.
- `sed -n '1,220p' AGENTS.md`
  - Passed for repo protocol and lane/safety context.
- `sed -n '1,240p' docs/handoffs/task-completions/integration-status.md`
  - Passed for current integration context.
- `test -f docs/handoffs/task-completions/curated-guidance-routing-design.md; printf '%s\n' $?`
  - Passed. Returned `1`, confirming this handoff did not exist before the task.
- `git show --stat --oneline f959769 --`
  - Passed. Confirmed the committed curated-guidance private retriever slice and related files.
- `sed -n '1,280p' pocketsteel/curated_guidance_retriever.py`
  - Passed for read-only retriever inspection.
- `sed -n '280,430p' pocketsteel/curated_guidance_retriever.py`
  - Passed for read-only retriever inspection.
- `sed -n '1,260p' docs/llm-guidance/answer-contract.md`
  - Passed for answer contract context.
- `sed -n '1,260p' docs/llm-guidance/teacher-first-answer-policy.md`
  - Passed for teacher-first answer policy context.
- `sed -n '1,260p' docs/handoffs/task-completions/curated-guidance-private-retriever-plan.md`
  - Passed for prior curated-guidance implementation context.
- `sed -n '1,260p' docs/handoffs/task-completions/curated-guidance-private-retriever-qa.md`
  - Passed for prior curated-guidance QA context.
- `sed -n '1,260p' docs/handoffs/task-completions/curated-guidance-qa-retrieval-eval.md`
  - Passed for prior offline retrieval eval context.
- `sed -n '1,240p' tests/test_curated_guidance_retriever.py`
  - Passed for current retriever test-context inspection.
- `git status --short`
  - Passed. Broad pre-existing dirty worktree remains; this task added only `docs/handoffs/task-completions/curated-guidance-routing-design.md`.
- `git diff --check`
  - Passed.
- `git status --short -- docs/handoffs/task-completions/curated-guidance-routing-design.md`
  - Passed. Shows `?? docs/handoffs/task-completions/curated-guidance-routing-design.md`.
- `git diff --check -- docs/handoffs/task-completions/curated-guidance-routing-design.md`
  - Passed.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/curated-guidance-routing-design.md`
  - Passed. Used because the handoff is new and untracked, so normal `git diff --check` does not inspect its contents.
- Tests skipped and why:
  - Unit, browser, and eval tests were skipped because this was a docs-only design task and no executable code, API behavior, UI behavior, retrieval behavior, corpus data, Chroma/vector store, embeddings, or prompts changed.

## Integration Notes

- This design deliberately keeps curated guidance separate from SGF/forum retrieval.
- First runtime integration should be admin/backstage protected-preview only.
- Public/anonymous answers must not include curated guidance.
- Curated guidance should not become a generic weak-source fallback.
- Curated guidance should support teacher-first synthesis for eligible teaching prompts.
- Full private guidance bodies must never be returned through `/api/answer`.
- `corpus-private/` was not read or modified for this task.

## Commit Readiness

Needs human review first

## Recommended Next Lane

Recommended lane: 05 Backend / RAG Integration, after Lane 15 reviews this design.

Recommended next step: Lane 05 should implement only the first protected-preview routing slice behind feature flags, after Lane 15 reviews this design.
