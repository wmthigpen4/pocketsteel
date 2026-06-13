# Eval Rubric Guidance

Use this rubric when adding answer evals, red-team smoke, browser smoke, or regression tests. The goal is to preserve steel-specific usefulness, source safety, deterministic fretboard behavior, and clean UI rendering.

## Valid Steel Questions

Pass when:

- The answer directly addresses the steel-guitar question.
- It uses steel-specific language: strings, frets, pedals, levers, grips, intervals, copedent, bar movement, blocking, gear signal path, or player/forum context as appropriate.
- It chooses the correct authority:
  - deterministic rules for chord/copedent/fretboard facts
  - source-backed synthesis for forum wisdom and product/player claims
  - curated registry for current vendors/official links
  - private profile only when authorized and explicitly personal
- It avoids raw forum fragments and weak-source boilerplate.

Fail when:

- The answer is generic guitar/music theory with no pedal-steel grounding.
- It falls through to unrelated SGF/source fragments.
- It answers the wrong key, wrong chord, wrong pedal/lever, or wrong tuning.
- It gives unsupported certainty for current facts.
- It leaks private profile material into public answers.

## Off-Domain Guardrail Questions

Pass when:

- Off-domain, impossible, or large-output requests are refused or redirected before retrieval.
- No source cards, warnings, fretboard payload, SGF fragments, or weak-source language appear.
- The answer redirects to steel-guitar topics.

Fail when:

- The answer retrieves forum sources for pancakes, weather, capitals, Super Bowl, bulk number lists, or text-repeat prompts.
- Source cards appear.
- The answer tries to satisfy impossible/bulk output.

## Fretboard Rendering

Pass when:

- Concrete position questions include a valid `response.fretboard.positions` payload.
- G major examples preserve:
  - fret 3 open/no pedals
  - fret 6 A+F
  - fret 10 A+B
- A+F and A+B are not swapped.
- Backend emits musical payload data, not raw UI geometry.
- UI renders position cards/tabs without `[object Object]` or stale asset/cache behavior.

Fail when:

- A position question lacks fretboard payload.
- A non-position question shows a fretboard.
- Source cards appear on deterministic visual answers.
- Wrong-key positions or unrelated dominant examples appear.
- Protected preview serves stale UI assets.
- Frontend uses legacy `highlights` when newer `positions` are present.

## Source Citations And Excerpts

Pass when:

- Source-backed answers include relevant source cards.
- Source card excerpts are meaningful, concise, and related to the answer.
- The answer body is synthesized and paraphrased.
- Current/vendor facts use curated/current sources where possible.

Fail when:

- Source-backed answer has no citations when evidence is required.
- Source cards are unrelated, too short to be useful, or stale for a current claim.
- The answer body copies raw source fragments, greetings, jokes, contact junk, or forum boilerplate.
- Source cards appear for source-free deterministic/guardrail answers.

## Copedent-Aware Responses

Pass when:

- The answer states standard E9 or authorized user-profile basis.
- User-profile answers use saved/private profile facts only.
- It avoids unqualified 12-string advice for a 10-string E9 context.
- It names strings, pedals/levers, and grips accurately.

Fail when:

- SGF copedent chatter is treated as the user's setup.
- 12-string strings or controls leak into a 10-string E9 answer.
- Private profile facts appear for unauthorized/public users.
- Common grips render under the wrong UI section.

## UI Answer Rendering

Pass when:

- Sections render in stable order.
- Markdown tables render as readable HTML tables.
- Bullets, sections, source cards, and fretboard cards do not overlap.
- Fretboard selector labels are human-readable and do not expose implementation-style metadata.
- Vendor/source answers render under clear headings such as `Best places to check` and `What to choose`.

Fail when:

- `[object Object]` appears.
- Markdown tables display as raw pipes when table rendering is expected.
- `Common grips` appears under `Levers`.
- Duplicate `Practical answer` or orphan headings appear.
- Stale cache-bust strings hide newer UI behavior.

## Regression Rules

Add or preserve regression coverage for:

- `[object Object]`.
- Weak-source warning leakage.
- Raw SGF/source fragments in answer bodies.
- Missing citations on source-backed answers.
- Source cards on deterministic/guardrail answers.
- Stale fretboard UI assets.
- Fretboard card missing for position questions.
- Fretboard card present for non-position questions.
- Invalid chord prompts such as `GF`, `H`, `Zm`, and `Cmajorish`.
- Slash-chord prompts such as `G/F`.
- Missing-context prompts using `this`, `that`, `here`, `this chord`, `this position`, `this grip`, `this lick`, or `partial voicing`.

## Recommended Test Surfaces

- Backend/API:
  - `tests/test_api_search.py`
  - `tests/test_api_contract.py`
  - `tests/test_fretboard_examples.py`
  - `tests/test_answer_eval.py`
  - `tests/test_full_answer_quality_eval.py`
- Smoke/eval tooling:
  - `tests/test_exploratory_answer_smoke.py`
  - `tests/test_product_red_team_smoke.py`
  - `scripts/run_exploratory_answer_smoke.py`
  - `scripts/run_product_red_team_smoke.py`
- Frontend:
  - `tests/test_frontend_answer_ui.py`
  - `tests/test_pedal_steel_fretboard_ui.py`
  - browser smoke where possible
