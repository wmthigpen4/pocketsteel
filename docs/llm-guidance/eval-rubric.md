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

## Visual UI Smoke Evidence

Pass when:

- UI-facing QA includes screenshot evidence for the actual state tested.
- Protected-preview, local, or production browser smoke records exact URLs and cache-busted URLs before screenshots are interpreted.
- The report verifies visible behavior, not just DOM counts, marker counts, API responses, or console checks.
- Main app smoke shows Q&A/search still visually primary and header buttons visible, separated, readable, and not overlapping.
- Explorer smoke shows key, scale, harmony/view, and string-group controls visible with selected states.
- Explorer smoke shows selected string groups affecting the visible fretboard markers/clusters and the row/card/detail list.
- Fretboard visuals avoid full-string lanes unless full-lane rendering was explicitly requested.
- The report compares against the user-provided screenshot or visual reference when one exists.
- Console status is recorded.

Fail when:

- A handoff says `visual pass` without screenshot paths or attached cropped images.
- The evidence proves only that elements exist in the DOM.
- The report omits exact protected-preview/cache-busted URLs for a cache-sensitive UI check.
- Header buttons, Explorer controls, selected string groups, visible fretboard markers/clusters, or detail panels are not visually checked.
- Raw internal labels, `[object Object]`, stale cache hints, or overlapping full-string lanes are visible.
- A user-provided visual reference is not compared.

## Browser Smoke Target Clarity

Pass when browser-smoke reports identify the real target before the test begins:

- `Smoke Target` block is present with target type, result type, exact browser URL tested, cache-busted URL tested when needed, exact URL the user should use, auth requirements, auth provider, Cloudflare Access login result, local backend URL, expected port, expected git HEAD, version endpoint result or version inference, root-path actual and expected behavior, `/ui/steel-guitar-rag-mock.html` actual and expected behavior, tester owner, URLs not to test, and caveats.
- `URL tested` and `URL user should test` are both recorded in QA handoffs.
- Protected-preview reports say whether Cloudflare Access login succeeded before protected-preview behavior was tested.
- Local `127.0.0.1` results are labeled local and are not treated as proof of protected-preview behavior.
- API-only checks are labeled `API fallback, not browser smoke`.

Fail when:

- Browser smoke pass/fail is reported without the exact URL tested.
- API fallback smoke is reported as browser smoke.
- A handoff says only "test app.steelguitarrag.com" when the intended target is `/ui/steel-guitar-rag-mock.html`.
- Root `/` is assumed to work without saying whether it is wired for that smoke.
- Cache-sensitive UI checks omit the complete `?v=...` URL.
- Protected-preview smoke omits whether Cloudflare Access login succeeded.
- Protected-preview, production-root, local, and API fallback evidence are mixed together without labels.
- The user cannot tell which URL the user should open.

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
