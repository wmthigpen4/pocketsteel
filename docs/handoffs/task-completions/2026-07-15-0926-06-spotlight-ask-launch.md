# Spotlight Ask Launch and Full-Screen Ask Workspace

## Task summary

Implemented the approved three-state Ask flow:

- Kept the landing-page structure unchanged outside the existing Ask card.
- Replaced the landing Ask form with a launch-only card containing one example-prefill button, one primary CTA, the active-E9 context line, and the supplied spotlight artwork.
- Restored the full-screen Ask workspace as the sole primary-search surface.
- Preserved the existing answer workspace, follow-up composer, immediate follow-up chips, answer API, access checks, and copedent context.
- Added `is-asking` shell state and centralized entry through `openAskWorkspace({ prefill })`.
- Kept `ui/assets/landing/mockup_search_card.png` as an untracked design reference with no runtime reference.

Intentionally not changed: backend/API behavior, authentication, retrieval, answer content, URL routing, product-wide branding, the current answer workspace, or Backstage implementation.

## Files changed

- `ui/steel-guitar-rag-mock.html` — exact Ask-card, Ask-workspace, state-transition, and cache-key hunks only.
- `ui/workspace-shell.css` — launch-card visuals, spotlight crop, full-screen Ask layout, and `is-asking` responsive shell state.
- `ui/assets/landing/spotlight.png` — supplied 1254×1254 PNG, unchanged.
- `tests/test_landing_home_ui.py` — launch-only/card/artwork assertions.
- `tests/test_frontend_answer_ui.py` — sole-primary-input and three-state navigation assertions.
- `tests/test_same_origin_smoke_server.py` — spotlight static-serving and cache-key assertions.
- This handoff.

No files were deleted. `ui/assets/landing/mockup_search_card.png` remains untracked and must not be staged.

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- Inline page script parsed with `new vm.Script(...)` — passed.
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py -k 'not test_backstage_plan_and_activity_uses_all_approved_assets'` — 67 passed, 1 deselected.
- `.venv/bin/python -m pytest -q` — 1134 passed, 2 unrelated failures from parked Backstage/copedent work:
  - `tests/test_copedent_profile_store.py::test_backstage_exposes_common_profiles_and_mechanical_editor_fields` expects `saveControlFields()` in the independently dirty `ui/backstage-copedent-manager.js`.
  - `tests/test_frontend_answer_ui.py::test_backstage_plan_and_activity_uses_all_approved_assets` expects currently parked Backstage artwork references.
- `git diff --check` — passed.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/steel-guitar-rag-mock.html?v=spotlight-ask-local-20260715`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/steel-guitar-rag-mock.html?v=spotlight-ask-local-20260715`
- Exact URL the user should use: protected-preview URL to be recorded after commit/restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: static local server; explicit submission intentionally exercised the existing error state
- Expected backend port: 8765
- Expected git HEAD: pre-commit working tree based on `7f99e6113509d72f6e69042c28d241f111813df5`
- Version endpoint: not available on static server
- Version endpoint result: not available
- If version endpoint missing, how version is inferred: cache-busted working-tree URL
- Whether app root `/` works: yes as directory listing; not used as app target
- Whether app root `/` is expected to work: no, canonical local target is the exact UI path
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: production root as proof of this uncommitted build
- Known caveats: local static server returns the expected answer error after submission because no answer API is mounted

Verified:

- Landing Ask card has zero editable inputs, exactly two buttons, and the spotlight background loaded with `right top` positioning and `cover` sizing.
- CTA opened `page is-asking` with an empty focused field, four suggestions, and the answer workspace hidden.
- Example opened `page is-asking` with exact prefill `Show me a classic country move.` and no answer workspace.
- Enter explicitly transitioned to `page is-answering` with the submitted question.
- Answer-header Ask returned to a blank, focused full-screen Ask workspace.
- Desktop and narrow viewport checks had no horizontal page overflow; all four full-screen suggestions remained visible.

## Integration notes

The HTML file contains substantial unrelated parked Backstage/copedent changes. Commit only the Ask-specific hunks. The landing mockup is reference-only. The spotlight asset must be staged by exact path.

## Risk assessment

Low-to-medium UI risk. The state transition is frontend-only and covered by focused tests/browser smoke. Rollback is the scoped implementation commit. Primary remaining risk is accidental staging of unrelated dirty HTML hunks, mitigated by cached-diff review.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/workspace-shell.css`
- `ui/assets/landing/spotlight.png`
- `tests/test_landing_home_ui.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-15-0926-06-spotlight-ask-launch.md`
- Ask-specific hunks only from `ui/steel-guitar-rag-mock.html`

## Files that must not be staged

- `ui/assets/landing/mockup_search_card.png`
- Unrelated Backstage/copedent hunks in `ui/steel-guitar-rag-mock.html`
- `ui/backstage-copedent-manager.js`
- `docs/handoffs/task-completions/integration-status.md` in the implementation commit
- All other dirty/untracked files not listed above

## Recommended next lane

Lane 01 Repo Steward for exact-hunk staging and commit, then Lane 12 for protected-preview update and authenticated smoke.

## Commit readiness

Safe to commit.

## Suggested next step

Proceed under Repo Steward auto-approval: stage exact files plus Ask-specific HTML hunks, review the cached diff, commit, update the protected preview, and run authenticated browser smoke at an exact cache-busted URL.
