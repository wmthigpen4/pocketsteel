# No-Op Answer Intent Classifier Source-Backed Fix

Date: 2026-06-13
Branch: feature/answer-api
HEAD: 4124b88

## QA Blocker Addressed

Lane 15 found that the previous no-op classifier drift fix cleared the guardrail and fretboard-overrouting blockers, but introduced a remaining source-backed retrieval blocker:

- 24 steel-guitar rows that expected retrieval were classified as retrieval-disabled or off-domain.
- The affected rows included player bios, steel-guitar brands, vendor/accessory questions, and practical gear prompts.

This pass restores source-backed steel routing without enabling retrieval gating and without changing public `/api/answer` behavior.

## Files Changed

- `pocketsteel/answer_intent_classifier.py`
- `tests/test_answer_intent_classifier.py`
- `docs/handoffs/task-completions/no-op-answer-intent-classifier-source-backed-fix.md`

Related existing no-op hook:

- `pocketsteel/api.py` already imports and calls `classify_answer_request(...)`; the returned decision remains unused.

## Classifier Rule Changes

- Added steel-domain source-backed allow rules for:
  - known steel players/history context: Buddy Emmons, Lloyd Green, Paul Franklin, Jeff Newman, Jimmy Day, Ralph Mooney, Sarah Jory, Curly Chalker, Doug Jernigan, John Hughey, notable pedal-steel records;
  - brands/manufacturers/products: Mullen, MSA, Emmons, Emmons push-pull, Carter, Sho-Bud, Benado Steel Dream, Telonics, Fender Steel King;
  - vendor/accessory topics: accessories, pedal-steel strings, volume pedals, tone/slide bars, pac-a-seats/steel seats, picks/finger picks;
  - practical gear/maintenance prompts: string breakage at gigs, tuners/batteries, oil/parts/pedal rods, thin tone, pedals not returning, delay/effects-loop questions, hum touching the changer.
- Added `steel players` / `steelers` and finger-pick language as steel-domain terms.
- Kept source-backed allow rules ahead of the copedent branch so gear/vendor/player prompts are not swallowed by mechanical `pedal/string` matching.
- Kept specific mechanical prompts such as `How do I use my string 6 lower in A?` routed as `copedent_position` rather than source-backed retrieval.

## Source-Backed Retrieval Restored

Focused tests now cover:

- `Who was Buddy Emmons?`
- `Who was Lloyd Green?`
- `Tell me about Paul Franklin.`
- `What did players say about Buddy Emmons tone?`
- `What are notable records with pedal steel?`
- `Is Mullen or MSA a better guitar?`
- `What do players say about Emmons push-pull guitars?`
- `What do players say about Carter steels?`
- `What brands of pedal steel are commonly recommended?`
- `Are Sho-Bud guitars good for beginners?`
- `What vendors sell pedal steel accessories?`
- `Where can I buy pedal steel strings?`
- `What volume pedals do steel players recommend?`
- `What seats/pac-a-seats do players use?`
- `What bars do pedal steel players like?`
- `What are common Fender Steel King settings?`
- `What delay settings do steel players use?`
- `How do players diagnose hum that changes when touching the changer?`
- `What do players say about Telonics volume pedals?`
- `Should delay go in the effects loop?`
- `My 3rd string keeps breaking at gigs. What should I carry?`
- `Do steel players use battery-powered tuners live?`

These classify as `steel_guitar`, `retrieval_allowed=true`, `needs_sources=true`, `needs_fretboard=false`, with `allowed_answer_shape` of either `source_backed` or `gear_diagnosis`.

## Prior Blockers Stayed Fixed

The explicit 264-row question-bank validation now reports:

```text
rows 264
contract_key_mismatches: 0
invalid_domain_enum: 0
invalid_intent_enum: 0
invalid_shape_enum: 0
offdomain_or_unsafe_domain_mismatches: 0
offdomain_or_unsafe_retrieval_mismatches: 0
impossible_or_large_output_misclassified_as_steel: 0
impossible_or_large_output_retrieval_allowed: 0
non_fretboard_expected_but_classifier_needs_fretboard: 0
steel_source_backed_expected_retrieval_but_classifier_disallows: 0
```

This confirms:

- off-domain prompts still disable retrieval;
- unsafe/impossible prompts still disable retrieval;
- impossible/large-output prompts are not misclassified as ordinary steel;
- non-position prompts do not over-classify as `needs_fretboard=true`;
- source-backed steel prompts now allow retrieval.

## Tests Run

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Results:

- `tests/test_answer_intent_classifier.py`: 62 passed
- `tests/test_answer_eval.py`: 9 passed
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: 228 passed
- explicit 264-row question-bank classifier validation: all tracked mismatch counts 0
- `git diff --check`: passed

Full pytest was not run because this is a narrow no-op classifier slice and the requested focused suites plus explicit question-bank validation passed.

## Behavior Confirmations

- Retrieval gating is still disabled.
- `/api/answer` still only calls the classifier as a no-op hook.
- The classifier result is not used for runtime routing.
- Public `/api/answer` response shape is unchanged.
- No answer text, source rendering, fretboard rendering, UI files, Chroma, embeddings, corpus data, scraping, auth, deployment, or DNS behavior changed.

## Risk Assessment

Risk: low to medium.

- Low user-facing risk because runtime behavior remains unchanged.
- Medium coordination risk because the classifier is regex-based and may need additional phrase tuning before future retrieval gating.
- Rollback is straightforward: remove or revert the classifier/test/handoff slice, including the existing `pocketsteel/api.py` no-op hook if the whole no-op classifier scaffold is abandoned.

## Safe-To-Stage List

For this source-backed classifier fix:

- `pocketsteel/answer_intent_classifier.py`
- `tests/test_answer_intent_classifier.py`
- `docs/handoffs/task-completions/no-op-answer-intent-classifier-source-backed-fix.md`

Include `pocketsteel/api.py` only if Repo Steward is staging the existing approved no-op classifier hook in the same classifier scaffold commit.

## Must Remain Unstaged

- UI files, `ui/brand/`, `public/`, `Neon Sign/`, raw design assets
- Chroma/vector stores, embeddings, corpus-private, corpus-v2
- source-inbox raw data and provenance/legal/source-policy data
- generated reports not explicitly approved
- deployment secrets, `.wrangler`, DNS config
- unrelated dirty worktree files from other lanes

## Exact Next Prompt For 15 QA / Answer Eval

Re-review the no-op answer intent classifier source-backed fix. Verify the 264-row question-bank classifier validation has zero mismatches for off-domain/unsafe retrieval, impossible/large-output classification, non-position `needs_fretboard`, and source-backed steel retrieval. Confirm focused classifier/API/eval tests pass, `/api/answer` still exposes no classifier metadata, and retrieval gating remains disabled.

## Ready For QA Re-Review

Yes. This source-backed classifier drift fix is ready for Lane 15 QA re-review.

## Commit Readiness

Needs human review first.
