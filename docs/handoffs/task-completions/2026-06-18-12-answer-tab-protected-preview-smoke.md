# 2026-06-18 Lane 12 Answer Tab Protected-Preview Smoke

## Task Summary

Lane 12 was asked to verify answer-triggered deterministic tab example payloads from commit `beec57a` or later, without implementing new product behavior.

Completed:

- Inspected the required prior smoke handoff, integration status, tab/API code, answer UI bridge, and local/protected-preview startup scripts.
- Confirmed current branch `feature/answer-api`.
- Confirmed current HEAD `af645c9`, which includes `beec57a fix: render answer tab example payloads`.
- Ran the requested focused regression checks.
- Started the documented loopback-only v2 preview stack in local-dev mode for local API and browser smoke.
- Ran local API smoke against `/api/answer`.
- Ran local browser smoke against the same-origin answer UI.
- Ran narrow/mobile viewport smoke for the tab card.
- Restarted the documented protected-preview process on `127.0.0.1:8770` in Cloudflare Access production auth mode.
- Verified the protected-preview process, cwd, and `/api/version` identity locally.
- Attempted protected-preview browser smoke through `https://app.steelguitarrag.com/`; Cloudflare Access login was required and the in-app browser session was not authenticated, so protected browser smoke is blocked.
- Verified `/api/tab/render` locally against the protected-preview process.
- Reran the protected-preview browser attempt after the follow-up request for an authenticated session; no authenticated Access session was available in the in-app browser, and the browser again landed on the Cloudflare Access login page.

Intentionally not changed:

- No backend feature behavior was changed.
- No frontend feature behavior was changed.
- No landing-sign/cache-bust work was touched.
- No DNS, Cloudflare Access policy, tunnel config, Chroma/vector stores, embeddings, corpus/source data, scraping, or visual assets were modified.
- No unrelated dirty files were staged.
- No implementation commit was made. This handoff is safe to exact-path commit as a blocked protected-preview smoke record.

Task classification:

- Lane: `12 Self-Hosted Deployment`
- Type: verification / protected-preview smoke
- Mode: RED for protected-preview restart, explicitly authorized by the task.

## Smoke Target

- Target type: local and protected-preview
- Result type: local browser smoke completed; protected-preview browser smoke blocked by Cloudflare Access login
- Exact local browser URL tested: `http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=answer-tab-smoke-af645c9`
- Cache-busted local URL tested: `http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=answer-tab-smoke-af645c9`
- Exact protected-preview browser URL attempted: `https://app.steelguitarrag.com/?v=answer-tab-smoke-af645c9`
- Exact protected-preview URL for authenticated retest: `https://app.steelguitarrag.com/?v=answer-tab-smoke-af645c9`
- Auth required: yes for protected preview
- Auth provider: Cloudflare Access
- Cloudflare Access login result: blocked; browser landed on the Cloudflare Access email/code login page on both protected-preview attempts
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `af645c9`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"af645c9","git_branch":"feature/answer-api","server_started_at":"2026-06-18T21:32:04.420792+00:00","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- Whether app root `/` works: protected-preview root redirects through Cloudflare Access before app shell can load
- Whether app root `/` is expected to work: yes after Cloudflare Access login
- Whether `/ui/steel-guitar-rag-mock.html` works: yes locally; protected-preview browser route needs authenticated Access session
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user or Lane 12 with an authenticated Cloudflare Access browser session
- Do not test these URLs: local `127.0.0.1` as proof of protected-preview behavior; public landing Pages routes; unauthenticated protected-preview `/api/answer`
- Known caveats: broad parked dirty files remain; `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py` contain unrelated landing-sign cache-bust work and were not touched.

## Current Repo State

- Branch: `feature/answer-api`
- Commit tested: `af645c9 docs: define tab engine next feature ladder`
- Required implementation commit included: yes, `beec57a fix: render answer tab example payloads` is in history.
- Relevant commits in recent history:
  - `af645c9 docs: define tab engine next feature ladder`
  - `beec57a fix: render answer tab example payloads`
  - `3b1f393 docs: add future tab engine red-team matrix`
  - `dc1f4b8 feat: attach deterministic tab examples to answers`
  - `812b46a test: define answer-triggered tab example QA`
  - `2bf2767 docs: define answer-triggered tab UX behavior`
  - `7834c67 docs: plan tab engine follow-on slices`
  - `54a28c7 fix: clear tab examples on stage return`

Dirty runtime-adjacent files present before smoke:

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`

The diff in those files is unrelated landing-sign asset cache-busting. It was not changed or staged by this Lane 12 task.

## Local Server Command Used

Local-dev same-origin v2 preview smoke:

```bash
PYTHONPATH=. .venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --answer-auth-mode local_dev \
  --auth-provider scaffold
```

The initial sandboxed bind failed with `PermissionError: [Errno 1] Operation not permitted`, so the same command was rerun outside the sandbox to allow loopback binding.

Protected-preview restart command used:

```bash
set -a
source ~/.steel-rag/env/private-preview.env
set +a

PYTHONPATH=. \
STEEL_RAG_AUTH_PROVIDER=cloudflare_access \
STEEL_RAG_ANSWER_AUTH_MODE=production \
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_RETRIEVAL_DEBUG=false \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

Restart evidence:

- Process listening: `Python` PID `20100` on `127.0.0.1:8770`.
- Process cwd: `~/Documents/Steel Guitar RAG`.
- `/api/version` reported `git_sha: af645c9`, `git_branch: feature/answer-api`, `server_started_at: 2026-06-18T21:32:04.420792+00:00`, `retrieval_mode: hybrid_private_first`, `auth_provider: cloudflare_access`.

## Local API Smoke Results

Endpoint: `POST http://127.0.0.1:8770/api/answer`

Header: `X-Steel-Rag-Dev-Access-Role: beta_user`

| Question | Expected | Actual | Result |
| --- | --- | --- | --- |
| Show me a G major grip | Returns safe deterministic tab payload | HTTP 200, `tab_example.id=g-major-456-open`, `rendered_tab` present, `sources=[]` | Pass for payload |
| Show me a G to C move | Returns safe deterministic tab payload | HTTP 200, `tab_example.id=g-to-c-456-beginner`, `rendered_tab` present, `sources=[]` | Pass for payload |
| How do I use A+B pedals? | Returns safe deterministic tab payload | HTTP 200, `tab_example.id=a-b-pedal-major-position`, `rendered_tab` present, `sources=[]` | Pass for payload |
| Why does my amp buzz at idle? | Normal non-tab answer, no generated tab | HTTP 200, no `tab_example`, gear/tone answer returned with sources | Pass |
| Give me the tab for Together Again note-for-note | No generated tab for named copyrighted song request | HTTP 200, no `tab_example`; mapped to safe song-approach guidance | Pass |
| Transcribe the full solo from a recording into tab | No generated tab for full-solo transcription request | HTTP 200, no `tab_example`; mapped to safe song-approach guidance | Pass |

Caveat: the three safe tab prompts included `tab_example` correctly, but the primary answer text still said, "I need a more specific steel-guitar question..." This is not a tab payload/rendering blocker, but it is a Lane 05 answer-quality follow-up if those prompts are expected to have direct teaching copy in the answer body.

## `/api/tab/render` Smoke

Endpoint: `POST http://127.0.0.1:8770/api/tab/render`

Payload: one G grip event on strings 4, 5, and 6 at fret 3.

Result:

- HTTP 200.
- `ok: true`.
- `issues: []`.
- `metadata.profile: default_e9`.
- `metadata.event_count: 1`.
- Fixed-width tab preview began with:

```text
Ch |G
 1 |
 2 |
 3 |
```

## Local Browser Smoke Results

URL: `http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=answer-tab-smoke-af645c9`

Desktop/browser results:

| Question | Tab visible | Code block | Spacing / monospace | Stage return clears tab | Console errors | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Show me a G major grip | Yes | Yes | `ui-monospace...`, `white-space: pre`, `overflow-x: auto` | Yes | None | Pass for rendering |
| Show me a G to C move | Yes | Yes | `ui-monospace...`, `white-space: pre`, `overflow-x: auto` | Yes | None | Pass for rendering |
| How do I use A+B pedals? | Yes | Yes | `ui-monospace...`, `white-space: pre`, `overflow-x: auto` | Yes | None | Pass for rendering |
| Why does my amp buzz at idle? | No | No | Not applicable | Yes | None | Pass |
| Give me the tab for Together Again note-for-note | No | No | Not applicable | Yes | None | Pass |
| Transcribe the full solo from a recording into tab | No | No | Not applicable | Yes | None | Pass |

Narrow viewport smoke:

- Viewport: `390x844`.
- Prompt: `Show me a G to C move`.
- Tab card visible: yes.
- Code block present: yes.
- `white-space: pre`: yes.
- Tab container `overflow-x: auto`: yes.
- Console errors: none.

Screenshots: none captured. Evidence was collected through DOM, computed style, console log, and API response inspection.

## Protected Preview Smoke Result

Protected-preview process was restarted and verified locally, but authenticated browser smoke could not proceed because the in-app browser was not logged into Cloudflare Access.

The follow-up protected browser attempt used the requested URL:

```text
https://app.steelguitarrag.com/?v=answer-tab-smoke-af645c9
```

Observed result:

- Final browser URL: Cloudflare Access login URL on `late-waterfall-73da.cloudflareaccess.com`.
- Page title: `Sign in ・ Cloudflare Access`.
- Visible page text included: `Log in to Steel Guitar RAG Private Preview`, `Email`, `Send login code`.
- App shell loaded: no.
- `#question` present: no.
- `#answer-workspace` present: no.
- Q&A unlocked: not reached.
- Protected-preview browser smoke result: blocked, not failed.

Attempted URL:

```text
https://app.steelguitarrag.com/?v=answer-tab-smoke-af645c9
```

Observed final page:

- URL host: `late-waterfall-73da.cloudflareaccess.com`.
- Title: `Sign in ・ Cloudflare Access`.
- Visible page text: `Log in to Steel Guitar RAG Private Preview`, `Email`, `Send login code`.
- App shell loaded: no.
- Q&A unlocked: not reached.
- Protected-preview tab rendering: blocked by auth, not failed.

Authenticated retest checklist:

1. Open `https://app.steelguitarrag.com/?v=answer-tab-smoke-af645c9`.
2. Complete Cloudflare Access login.
3. Confirm app redirects to `/ui/steel-guitar-rag-mock.html`.
4. Confirm Q&A unlocks.
5. Confirm `/api/version` reports `af645c9` or a later approved commit containing `beec57a`.
6. Ask:
   - `Show me a G major grip`
   - `Show me a G to C move`
   - `How do I use A+B pedals?`
   - `Why does my amp buzz at idle?`
   - `Give me the tab for Together Again note-for-note`
   - `Transcribe the full solo from a recording into tab`
7. Expected:
   - the three safe tab prompts render a visible tab card;
   - tab text is fixed-width and preserves alignment;
   - non-tab/copyright/full-solo prompts do not show generated tab;
   - no stale tab remains after returning to the stage;
   - no console errors.

## Tests And Checks Run

Passed:

```bash
git diff --check
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_tab_engine.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
.venv/bin/python -m pytest tests/test_api_search.py -q
```

Results:

- `git diff --check`: passed.
- `node --check ui/answer-client.js`: passed.
- `node --check ui/pedal-steel-fretboard.js`: passed.
- `tests/test_frontend_answer_ui.py`: `20 passed`.
- `tests/test_tab_engine.py`: `20 passed`.
- `tests/test_api_contract.py`: `5 passed`.
- `tests/test_api_search.py`: `255 passed`.

The same focused check set was rerun during the follow-up protected-preview attempt and passed:

- `git diff --check`: passed.
- `node --check ui/answer-client.js`: passed.
- `node --check ui/pedal-steel-fretboard.js`: passed.
- `tests/test_frontend_answer_ui.py`: `20 passed`.
- `tests/test_tab_engine.py`: `20 passed`.
- `tests/test_api_contract.py`: `5 passed`.
- `tests/test_api_search.py`: `255 passed`.

Known unrelated full-suite caveats from Repo Steward were not rerun:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`.
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`.

## Defects Or Caveats Found

- Protected-preview browser smoke is blocked until a Cloudflare Access-authenticated browser session is available. Per the user's approval behavior, this was not retried repeatedly after Access blocked the app shell.
- Safe tab prompts render tab cards, but their primary answer body remains the generic specificity fallback. If product expectation is that these exact prompts answer directly in prose and tab, send this to Lane 05 as an answer-quality follow-up.
- Local browser smoke was run from the current worktree, which includes unrelated landing-sign cache-bust changes in `ui/steel-guitar-rag-mock.html`; those changes were not touched or staged.

## Risk Assessment

Risk: medium.

Reason:

- The answer tab payload and local browser rendering paths passed.
- The protected-preview process is running the expected code and reports `af645c9`.
- The actual protected-preview browser smoke is not complete because Cloudflare Access login blocked app access in this session.

Rollback/restart note:

- To return to the previous protected-preview runtime, restart the prior committed HEAD/process using the same private-preview command from that checkout or stop the current process on `127.0.0.1:8770`.
- No DNS, tunnel, Access policy, Chroma, embeddings, corpus, or scraping changes were made.

## Human Decision Needed

Yes.

Decision needed: either complete Cloudflare Access login in the in-app browser and rerun the protected-preview checklist above, or route the generic answer-body caveat to Lane 05 if the tab prompts must produce direct prose rather than only a tab card.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-12-answer-tab-protected-preview-smoke.md`

## Files That Must Not Be Staged

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `deploy/landing/index.html`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `tests/test_frontend_answer_ui.py`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `ui/steel-guitar-rag-mock.html`
- all untracked corpus/source/design/private/generated files and handoff assets outside this task.

## Recommended Next Lane

- Lane 12 if Cloudflare Access login can be completed for the authenticated protected-preview browser smoke.
- Lane 05 if the generic fallback answer body on safe tab prompts should be treated as a product defect.

## Commit Readiness

Safe to commit.

Reason: local/API/browser smoke passed for the tab rendering path, the protected-preview process reports `af645c9`, and the follow-up protected-preview browser attempt is clearly documented as blocked by Cloudflare Access login rather than reported as a pass.

## Suggested Next Step

Lane 12 prompt:

```text
Complete Cloudflare Access login in the in-app browser, then rerun protected-preview browser smoke for answer tab examples at https://app.steelguitarrag.com/?v=answer-tab-smoke-af645c9. Verify /api/version reports af645c9 or later, safe tab prompts render visible fixed-width tab cards, non-tab/copyright/full-solo prompts do not render generated tab, and no stale tab remains after returning to stage. Do not modify files or commit.
```
