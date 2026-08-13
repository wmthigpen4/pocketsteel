# Follow-up context and provenance repair

## Task summary

- Reproduced the failed protected-preview user smoke exactly: after the deterministic position-strategy answer, `What is your source of information for this?` was submitted as a follow-up but reached the backend without its parent exchange and routed as `off_domain:unknown`.
- Persisted the bounded parent exchange in same-tab session storage and made follow-up submission reload and send that context explicitly. Starting a new Q&A or returning home still clears the conversation.
- Added a contextual provenance answer for deterministic position-strategy teaching. It explains that the original answer came from the deterministic E9 rules layer, verifies the 3rd-fret/A+B/8th-fret pitches, separates calculated mechanics from curated arranging guidance, and states honestly that no SGF quotation produced the original answer.
- Added an honest recovery response when a source follow-up is marked as a follow-up but arrives without its parent context.
- Reused the existing Source notes card presentation to display `Deterministic E9 rules` provenance instead of the misleading `No sources returned` state.
- Replaced the answer client's shared asset path with a SHA-256 content-addressed filename. Protected smoke proved this Cloudflare route can reuse the cached path independently of a query-string cache-buster; a new digest filename is therefore required to make the asset identity verifiable and collision-free.
- No new page, visual redesign, corpus/vector mutation, scraping, embeddings, auth, DNS, Tunnel, Access, secret, Cloudflare configuration, or `chatgpt.site` work was performed.

## Files changed

- `steel_guitar_rag/api.py`
- `steel_guitar_rag/api_contract.py`
- `steel_guitar_rag/curated_answers.py`
- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_api_search.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-13-1231-27-followup-context-provenance-repair.md`

## Tests and checks run

- Protected-preview reproduction on release `585e74b1`
  - FAIL reproduced: the clean two-turn browser flow returned the generic specificity refusal.
  - Runtime trace: `off_domain:unknown`; fallback `sgf_quarantine_specificity_fallback`; zero source cards.
- Local same-origin browser regression on the repaired tree
  - PASS: exact original question followed by exact source question rendered the contextual provenance answer.
  - PASS: the existing Source notes area rendered `Answer provenance` / `Deterministic E9 rules` and the E9 calculation summary.
  - PASS: no browser errors or warnings.
  - Runtime trace: `steel_guitar:source_provenance_followup` -> `deterministic`; evidence `deterministic_e9_pitch_calculation`; verification `answer_contract`; fallback `none`.
- Protected cold-client check after the first activation
  - CAUGHT before release handoff: a browser with a pre-activation cached copy of the semantic `v1035` asset loaded stale frontend code and could not initialize the Q&A workspace.
  - A digest query-string retry was deliberately rejected after the protected route still returned the stale shared-path asset.
  - FIXED: the HTML now references a new answer-client filename containing the exact SHA-256 digest. Regression tests recompute the name, verify the content-addressed file matches the canonical client byte-for-byte, and verify the static server serves it with immutable caching.
- `.venv/bin/pytest -q tests/test_api_search.py tests/test_frontend_answer_ui.py tests/test_canonical_frontier_client.py tests/test_same_origin_smoke_server.py`
  - PASS: 442 passed.
- Focused follow-up regression selection
  - PASS: 8 passed.
- `.venv/bin/ruff check ...`
  - PASS.
- `git diff --check`
  - PASS.
- Initial full suite on the intentionally dirty implementation checkout
  - 1,661 passed; one deployment preflight assertion stopped at `release has unstaged tracked changes` before reaching its expected branch-check assertion.
- Clean-commit full suite on branch checkout
  - PASS: 1,662 passed in 86.60 seconds.
- Final detached release suite
  - PASS: 1,660 passed, 2 branch-check tests deliberately deselected because the release checkout is detached, in 86.17 seconds.
- Final protected-preview browser smoke on the content-addressed release
  - PASS: the exact position-strategy question returned the deterministic teaching answer.
  - PASS: the exact follow-up `What is your source of information for this?` returned the contextual provenance explanation instead of the generic specificity refusal.
  - PASS: Source notes rendered `Answer provenance` / `Deterministic E9 rules` with the pitch-calculation summary.
  - PASS: no browser console errors or warnings.
  - Runtime trace: `steel_guitar:source_provenance_followup` -> `deterministic`; evidence `deterministic_e9_pitch_calculation`; synthesis `contextual_provenance_explanation`; verification `answer_contract`; fallback `none`.
- Existing user LaunchAgent activation
  - PASS: live, ready, exact version, LaunchAgent supervision, and listener ownership checks.
  - The existing canonical frontier on port 8771 remained ready and unchanged.

## Risks

- Same-tab session storage temporarily holds at most eight normalized conversation strings, each capped at 8,000 characters. It is cleared on a new Q&A or return home and is never sent outside the existing same-origin answer request.
- The direct provenance explanation currently covers deterministic position-strategy answers. Other contextual follow-ups continue through the existing contextual classifier/frontier path.
- The backend recovery clarifier remains necessary when an old cached client or malformed request marks a provenance question as a follow-up without including context.
- Previously poisoned shared-path asset URLs can remain in browser or edge caches without affecting this release because the page references a distinct content-addressed filename.

## Human decision needed

- None. This is the direct bug-fix continuation of the failed user smoke and stays within the approved protected-release scope.

## Safe-to-stage exact file list

- `steel_guitar_rag/api.py`
- `steel_guitar_rag/api_contract.py`
- `steel_guitar_rag/curated_answers.py`
- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_api_search.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-13-1231-27-followup-context-provenance-repair.md`

## Files that must not be staged

- `.venv` (runtime-only symlink).
- Any corpus, source, vector-index, embedding, private-data, environment, secret, log, generated, brand, public-page, DNS, auth, Tunnel, Access, or Cloudflare configuration file.
- The pre-existing unrelated dirty files in `/Users/cory/Documents/Pocket Steel/play-along-route-fix`:
  - `docs/handoffs/task-completions/integration-status.md`
  - `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
  - `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`

## Recommended next lane

- Owner review in the already-open protected Q&A workspace. No additional deployment lane is required for this repair.

## Commit readiness

Released from a clean detached checkout after exact preflight, full-suite verification, supervised health verification, and authenticated protected-browser smoke.
