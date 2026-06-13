# QA User Smoke Blocker Repair

- Branch: `feature/answer-api`
- HEAD verified by local version endpoint: `97071e6`
- Lane: `15 QA / Answer Eval`
- Date: 2026-06-13
- Commit readiness: `Safe to commit`

## Task Summary

Requested: QA the user-smoke blockers before any deployment/root-route work, covering backend chord-position routing and answer-page fretboard/filter UI behavior.

Completed:

- Read the requested repo protocol, integration status, blocker/fix handoffs, answer-eval guidance, teacher-first policy, current backend answer surfaces, current UI/fretboard surfaces, and current tests.
- Ran focused backend/API/eval tests, focused UI/fretboard tests, JS syntax checks, and full pytest.
- Started a loopback-only current-worktree answer UI/API on `127.0.0.1:8784`.
- Ran direct `/api/answer` checks for backend-only prompt variants.
- Ran local browser smoke for the requested 10 prompts with the required `Smoke Target` block.
- Verified fretboard filter behavior in the browser, including default Recommended, grip filters, voicing filters, combined filters, no-match empty state, and All positions.

Intentionally not changed:

- No implementation files were modified by this QA task.
- No files were staged or committed.
- No deployment, DNS, Cloudflare Tunnel, auth/security config, Chroma/vector stores, embeddings, scraping, corpus-private, corpus-v2, source-inbox, provenance/legal files, public assets, brand assets, `Neon Sign/`, or design assets were changed.

## Pass / Fail Decision

Decision: `PASS / Safe to commit`.

The backend user-smoke blockers and the UI feedback blockers are cleared in local current-worktree QA. Deployment/root-route verification may proceed in Lane 12 after Repo Steward commits the approved slices. External/user protected-preview smoke remains blocked until Lane 12 verifies the committed code on the protected preview with Cloudflare Access.

## Smoke Target

```text
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8784/ui/steel-guitar-rag-mock.html?access=beta_user&v=qa-user-smoke-blocker-repair-97071e6
- Cache-busted URL tested: http://127.0.0.1:8784/ui/steel-guitar-rag-mock.html?access=beta_user&v=qa-user-smoke-blocker-repair-97071e6
- Exact URL the user should use: for this local QA target, rerun the startup command and open http://127.0.0.1:8784/ui/steel-guitar-rag-mock.html?access=beta_user&v=qa-user-smoke-blocker-repair-97071e6; protected-preview user smoke still needs a Lane 12 URL after deployment/root-route verification
- Auth required: no for this local smoke
- Auth provider: scaffold
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8784
- Expected backend port: 8784
- Expected git HEAD: 97071e6
- Version endpoint: http://127.0.0.1:8784/api/version
- Version endpoint result: {"git_sha":"97071e6","git_branch":"feature/answer-api","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"scaffold"}
- If version endpoint missing, how version is inferred: not needed; endpoint was available
- Whether app root `/` works: yes, returned HTTP 200 and the UI HTML
- Whether app root `/` is expected to work: yes for this local smoke server
- Whether `/ui/steel-guitar-rag-mock.html` works: yes, returned HTTP 200
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex for this local smoke; the user after Lane 12 provides a protected-preview URL
- Do not test these URLs: bare protected-preview root as proof of this local result; local 127.0.0.1 as proof of Cloudflare Access/protected-preview behavior
- Known caveats: local browser smoke does not prove protected-preview cache, auth, tunnel, root-route, or deployment freshness
```

Startup command used:

```bash
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_ANSWER_AUTH_MODE=local_dev \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8784 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --answer-auth-mode local_dev \
  --auth-provider scaffold
```

Reachability:

- `GET http://127.0.0.1:8784/`: `HTTP/1.0 200 OK`
- `GET http://127.0.0.1:8784/ui/steel-guitar-rag-mock.html?access=beta_user&v=qa-user-smoke-blocker-repair-97071e6`: `HTTP/1.0 200 OK`
- `GET http://127.0.0.1:8784/api/answer`: `HTTP/1.0 405 Method Not Allowed` as expected for GET
- `GET http://127.0.0.1:8784/api/version`: `HTTP/1.0 200 OK`, reported `97071e6`

The temporary local smoke server was stopped after QA with `Ctrl-C`.

## Backend Prompt Results

Direct loopback `/api/answer` checks:

| Prompt | Result | Sources | Warnings | Fretboard | Notes |
| --- | --- | ---: | --- | --- | --- |
| `How do I play an E chord on the E9 neck?` | Pass | 0 | `[]` | yes, 44 positions | Teacher-first E major positions: 0/open, 3 A+F, 7 A+B. |
| `How do I play a B-flat chord on the E9 pedal steel?` | Pass | 0 | `[]` | yes, 44 positions | Normalized to Bb display; positions 6/open, 9 A+F, 13 A+B. |
| `How do I play a Bb chord on E9?` | Pass | 0 | `[]` | yes, 44 positions | Same Bb deterministic route. |
| `What is the location for a G chord with A+B?` | Pass | 0 | `[]` | yes, 44 positions | Directly says G with A+B is at the 10th fret. |
| `How do I play a G chord on the E9?` | Pass | 0 | `[]` | yes, 44 positions | Positions 3/open, 6 A+F, 10 A+B. |
| `Where do I play a G chord on the E9?` | Pass | 0 | `[]` | yes, 44 positions | Same deterministic route. |
| `How do I play an A chord?` | Pass | 0 | `[]` | yes, 49 positions | Positions 5/open, 8 A+F, 12 A+B. |
| `How do I play a D chord?` | Pass | 0 | `[]` | yes, 40 positions | Positions 10/open, 13 A+F, 17 A+B. |
| `What is the capital of France?` | Pass | 0 | `[]` | no | Off-domain retrieval gating preserved. |
| `Write me a Python script to scrape Instagram.` | Pass | 0 | `[]` | no | Unsafe/off-domain retrieval gating preserved. |

Across direct backend checks:

- No raw SGF/forum/source fragments as primary answers.
- No `[object Object]`.
- No weak-source warning as primary answer.
- Deterministic chord-position answers returned `sources: []`.
- Off-domain/unsafe prompts returned no sources and no fretboard payload.

## Browser Smoke Results

| Prompt | Result | Sources | Fretboard | Default visible cards | Notes |
| --- | --- | ---: | --- | ---: | --- |
| `How do I play an E chord on the E9 neck?` | Pass | 0 | yes | `3 / 44` | Teacher-first E positions. |
| `How do I play a B-flat chord on the E9 pedal steel?` | Pass | 0 | yes | `3 / 44` | Teacher-first Bb positions. |
| `What is the location for a G chord with A+B?` | Pass | 0 | yes | `3 / 44` | Direct A+B at 10th fret. |
| `How do I play a G chord on the E9?` | Pass | 0 | yes | `3 / 44` | Teacher-first G positions. |
| `Where do I play a G chord on the E9?` | Pass | 0 | yes | `3 / 44` | Teacher-first G positions. |
| `How do I play an A chord?` | Pass | 0 | yes | `3 / 49` | Teacher-first A positions. |
| `How do I play a D chord?` | Pass | 0 | yes | `3 / 40` | Teacher-first D positions. |
| `Show me the fretboard` | Pass | 0 | yes | `3 / 44` | Shows a starter standard E9/G reference rather than random forum text. |
| `What’s it mean for a song to be a swing or a waltz?` | Pass | 3 | no | n/a | Teacher-first explanation; source cards below answer as evidence. |
| `What is the capital of France?` | Pass | 0 | no | n/a | Guardrail; no sources or fretboard. |

Across browser smoke:

- No `[object Object]`.
- No weak-source warning as primary answer.
- No raw SGF/forum/source fragment as primary answer.
- Deterministic visual answers had fretboard payload and no source cards.
- Non-fretboard prompts did not show fretboard.
- Off-domain prompt did not retrieve.

## UI Feedback Results

Browser-verified on `How do I play a G chord on the E9?`:

- `Why these families matter` is rendered as `.answer-section.is-wide`.
- The wide section measured `1006px`, equal to the answer detail grid width, inside an answer card measuring `1060px`.
- Default `Recommended` view is limited and nonempty: `3 / 44` visible cards, one visible detail card, selected `g-open-3`.
- Voicing filters are present: `Recommended`, `Starter`, `Full chord`, `Root position`, `Inversions`, `Partial/rootless`, `Dominant pockets`, `All positions`.
- Grip filters are present: `All grips`, `1-4-5`, `3-4-5`, `4-5-6`, `4-5-7`, `5-6-8`, `5-7-8`, `6-8-10`, `7-8-10`.
- Grip `4-5-6` filters selector cards/details/highlights to matching visible cards: `3 / 44`.
- `Full chord + 4-5-6` works: `6 / 44`, one visible detail card, selected `g-open-3`.
- `All positions + all grips` is opt-in and reveals the full set: `44 / 44`.
- `Recommended + 3-4-5` is a true no-match combination and shows: `No positions match these filters. Try All positions or a different grip.`
- Technical/internal metadata is collapsed by default: `0 / 44` technical panels open.
- Learner fields remain visible before technical details are expanded.

## Screenshots

Transient screenshots were captured under `/tmp/pocketsteel-qa-user-smoke-blocker-repair/`:

- `/tmp/pocketsteel-qa-user-smoke-blocker-repair/how-do-i-play-a-g-chord-on-the-e9-final.png`
- `/tmp/pocketsteel-qa-user-smoke-blocker-repair/show-me-the-fretboard-final.png`
- `/tmp/pocketsteel-qa-user-smoke-blocker-repair/what-s-it-mean-for-a-song-to-be-a-swing-or-a-waltz-final.png`
- `/tmp/pocketsteel-qa-user-smoke-blocker-repair/what-is-the-capital-of-france-final.png`
- `/tmp/pocketsteel-qa-user-smoke-blocker-repair/g-chord-filter-no-match.png`

Transient machine-readable smoke output:

- `/tmp/pocketsteel-qa-user-smoke-blocker-repair/browser-smoke-results-final.json`
- `/tmp/pocketsteel-qa-user-smoke-blocker-repair/browser-smoke-results.json`

## Tests And Checks

Passed:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_search.py::test_smoke_ready_chord_fretboard_prompts_route_deterministically tests/test_api_search.py::test_show_me_the_fretboard_returns_default_visual_without_retrieval_fragments
.venv/bin/python -m pytest
```

Results:

- `tests/test_answer_intent_classifier.py`: `65 passed`
- `tests/test_answer_eval.py`: `9 passed`
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: `238 passed`
- JS syntax checks: passed
- `tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py -q`: `49 passed`
- Focused fretboard/API selectors: `48 passed`
- Full pytest: `671 passed`
- `git diff --check`: passed

Invalid focused-selector attempts, corrected immediately:

```bash
.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_search.py::test_smoke_ready_chord_fretboard_prompts_route_deterministically tests/test_api_search.py::test_show_me_the_fretboard_returns_default_e9_reference
.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_search.py::test_smoke_ready_chord_fretboard_prompts_route_deterministically tests/test_api_search.py::test_show_me_the_fretboard_returns_safe_default_reference
```

Both failed because the guessed test node ids do not exist. The correct node id was then run and passed:

`tests/test_api_search.py::test_show_me_the_fretboard_returns_default_visual_without_retrieval_fragments`

## Files Changed

Created by this QA task:

- `docs/handoffs/task-completions/qa-user-smoke-blocker-repair.md`

No implementation files were modified by this QA task.

## Exact Files Approved For Commit

Approved for Repo Steward exact-path or hunk-level staging, assuming the diffs match the corresponding Lane 05/Lane 06 handoffs:

- `pocketsteel/answer_intent_classifier.py`
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/general-chord-position-routing-user-smoke-fix.md`
- `ui/pedal-steel-fretboard.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/user-feedback-fretboard-ui-enforcement-fix.md`
- `docs/handoffs/task-completions/qa-user-smoke-blocker-repair.md`

## Exact Hunks Needing Careful Staging

Backend hunks:

- Generalized chord-position parsing for E9 neck/pedal-steel phrasing, spelled accidentals, `Bb`/`B-flat`, and `with A+B` location prompts.
- Classifier coverage that marks those chord-position questions as deterministic/fretboard-needed/source-free.
- Curated answer/fretboard payload paths that preserve teacher-first chord-position answers and suppress SGF source cards.
- Test hunks for the exact user-smoke blocker prompts.

UI hunks:

- Fretboard filter label/visibility behavior that preserves visible cards in default Recommended and exposes learner-friendly `All positions`.
- Tests asserting voicing and grip filters remain present and usable.

## Files That Should Remain Parked

Keep parked unless separately approved:

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- unrelated backend/RAG/test/docs hunks in shared files
- `docs/handoffs/task-completions/integration-status.md`
- deployment/DNS/Cloudflare/auth/security files
- `public/`, `ui/brand/`, `Neon Sign/`, and raw design assets
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, DBs, logs, generated reports, and scraping outputs
- `source-inbox` raw/generated/provenance files and legal/provenance/source-policy files
- root RAG/build scripts unless separately approved

## Deployment / Root Route / User Smoke Status

- Deployment/root-route verification work is allowed to proceed after Repo Steward commits the approved backend/UI slices.
- Protected-preview user smoke is still blocked until Lane 12 verifies a protected-preview URL from the committed code, including Cloudflare Access login and cache-busted UI freshness.
- External tester use remains blocked until protected-preview browser smoke passes and the root-route question is resolved or clearly documented.

## Risk Assessment

Risk: medium.

Why:

- Local current-worktree browser smoke and full pytest are green.
- The remaining risk is commit hygiene in a broadly dirty worktree and the separate protected-preview deployment/cache/auth surface.

Rollback:

- Revert the exact backend routing hunks and UI filter/label hunks if protected-preview behavior diverges after commit/deployment.

## Suggested Repo Steward Prompt

```text
LANE: 01 Repo Steward
REASONING: HIGH
Branch: feature/answer-api

Commit the QA-approved user-smoke blocker repair slices only.

Approved files:
- pocketsteel/answer_intent_classifier.py
- pocketsteel/fretboard_examples.py
- pocketsteel/curated_answers.py
- tests/test_answer_intent_classifier.py
- tests/test_fretboard_examples.py
- tests/test_api_search.py
- docs/handoffs/task-completions/general-chord-position-routing-user-smoke-fix.md
- ui/pedal-steel-fretboard.js
- tests/test_pedal_steel_fretboard_ui.py
- docs/handoffs/task-completions/user-feedback-fretboard-ui-enforcement-fix.md
- docs/handoffs/task-completions/qa-user-smoke-blocker-repair.md

Use exact-path and hunk-level staging. Do not use git add . Do not stage unrelated dirty files, generated/private/corpus/vector/source-inbox/deploy/design assets, or integration-status.md unless separately approved.

Before commit, inspect diffs for overlap and run:
git diff --check
.venv/bin/python -m pytest

After commit, write a Repo Steward handoff with commit hash and exact staged files.
```

## Lane 05 Revision Prompt If Blocked

Not needed. No backend answer-quality blocker remains from this QA pass.

## Suggested Next Step

- Lane: `01 Repo Steward`
- Task: hunk-stage and commit the approved backend/UI user-smoke blocker repair slices.
- After that: Lane `12 Self-Hosted Deployment` should run protected-preview/root-route browser smoke from the committed hash with Cloudflare Access login evidence.
