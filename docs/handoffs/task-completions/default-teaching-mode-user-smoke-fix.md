# Default Teaching Mode User Smoke Fix

## Task Summary

User smoke found predictable steel-guitar teaching prompts falling through to retrieved forum/source fragments instead of deterministic teaching answers. This scoped backend fix adds a pre-retrieval default teaching mode for broad steel-learning prompts, movement questions, pocket/lick requests, everyday steel-playing questions, and frustrated feedback prompts.

Completed:
- Added deterministic curated answer modes for the reported teaching prompts.
- Added classifier gating so the prompts disable retrieval and do not request sources or fretboard payloads.
- Added answer-contract aliases so the new curated intents pass answer-shape validation.
- Added API and classifier regression coverage for the reported prompts.

Intentionally not changed:
- No UI, deployment, auth, corpus, Chroma/vector, scraping, source-data, or `/api/answer` schema changes.
- No protected-preview restart; this needs a later Lane 12 verification after commit.

## Files Changed

- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/answer_contracts.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/default-teaching-mode-user-smoke-fix.md`

## Root Cause

Several broad learner prompts were in-domain for pedal steel but too open-ended for the existing deterministic position/theory gates. They were allowed to retrieve from Steel Guitar Forum evidence, which could place raw or semi-raw forum fragments into the primary answer body. The app needed a source-free teaching default before retrieval for these predictable prompts.

## Exact Fix

- Added intent modes for:
  - `teach_me_something`
  - `movement_request`
  - `progression_intro_request`
  - `pocket_request`
  - `lick_request`
  - `vague_learning_request`
  - `frustrated_learning_request`
  - `everyday_context`
- Routed the reported prompts before retrieval.
- Marked those curated answers as source-free in the API layer.
- Kept pure deterministic teaching answers fretboard-free unless the prompt explicitly asks for positions/fretboard.
- Preserved older deterministic movement, song/copyright, and 1-4-5-1 regression behavior.

## Smoke Target

- Target type: API-fallback
- Exact browser URL: `https://app.steelguitarrag.com/`
- Cache-busted URL: protected-preview URL deferred until Lane 12 deploys/verifies this commit
- Auth required: local no; protected preview yes
- Auth provider: local none/scaffold; protected preview Cloudflare Access
- Local backend URL: direct API helper, no browser server
- Expected backend port: not used
- Expected git HEAD: current local HEAD plus scoped patch
- Version endpoint result: not used
- Root URL status: not used as proof
- API fallback status: required for this backend-only local verification; API fallback, not browser smoke
- Exact URL the user should test: `https://app.steelguitarrag.com/?v=default-teaching-mode-<commit>` after Cloudflare Access login and Lane 12 verification

## Smoke Result

Local API fallback passed `10 pass / 0 fail` for:
- `Tell me something about pedal steel I might not already know`
- `I am playing a G chord on 3rd fret and need to move up the neck to a 4 chord (not staying still and going to A+B). Where should I go?`
- `Show me an example of a 1-4-5-1 intro`
- `Show me a specific pocket so I can learn something new`
- `Give me an example of just one steel guitar lick`
- `Can you tell me how to play anything? Just one thing!`
- `Can I play rock and roll on the steel guitar? How?`
- `Can I play steel guitar in my kitchen?`
- `Can you chew gum and play pedal steel?`
- frustrated feedback prompt from user smoke

Assertions checked:
- clean primary answer body
- no sources
- no warnings
- no fretboard payload

## Tests And Checks

- `git diff --check` - passed
- `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_search.py -q` - `276 passed`
- `.venv/bin/python -m pytest tests/test_answer_eval.py -q` - `9 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_full_answer_quality_eval.py -q` - `45 passed`
- `.venv/bin/python -m pytest -q` - `641 passed, 2 failed`

Full-suite failures are the known unrelated Lane 06/static blockers:
- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

## Integration Notes

No schema/API response shape change. The change only affects pre-retrieval classification and curated deterministic answer selection for broad teaching-mode prompts.

Protected preview still needs Lane 12 verification after this commit is available in the protected runtime.

## Risk Assessment

Risk: medium. The fix touches shared routing, but it is guarded by focused prompt predicates and regression tests. The predicates were narrowed to avoid stealing older A+B movement and copyright-aware song prompts.

Rollback: revert the scoped commit if the new teaching gates over-capture unrelated prompts.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 should verify protected preview from the new commit or later.

Exact prompt:

```text
LANE: 12 Self-Hosted Deployment
REASONING: MEDIUM
Branch: feature/answer-api

Restart or verify protected-preview runtime from the default teaching-mode commit or later.

Smoke Target:
- Target type: protected-preview
- Exact browser URL: https://app.steelguitarrag.com/
- Cache-busted URL: https://app.steelguitarrag.com/?v=default-teaching-mode-<commit>
- Auth required: yes
- Auth provider: Cloudflare Access
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: the default teaching-mode commit or later
- Version endpoint result: record if available
- Root URL status: record observed behavior
- API fallback status: not sufficient for protected-preview browser smoke
- Exact URL the user should test: https://app.steelguitarrag.com/?v=default-teaching-mode-<commit> after Cloudflare Access login

Verify the reported default teaching prompts return deterministic teacher-first answers with no raw forum fragments, no source cards, no warnings, and no fretboard payload unless explicitly requested.
```
