# 2026-06-18 Lane 12 Tab Engine Deploy Smoke Plan

## Task Summary

Lane 12 was asked to prepare a deployment and smoke-test readiness handoff for the committed deterministic tab engine and the answer-page tab UI work, without modifying app code.

Completed:

- Inspected repo state on branch `feature/answer-api`.
- Confirmed backend tab engine commit `686fd3c feat: add deterministic tab engine slice` is in history.
- Confirmed current HEAD is later: `07f9b9d feat: render tab examples on answer page`.
- Inspected `/api/tab/render` route shape in `steel_guitar_rag/api.py`.
- Inspected `tests/test_tab_engine.py` payload examples and answer-page tab UI wiring tests.
- Created this deployment/smoke checklist only.

Intentionally not changed:

- No backend code was modified.
- No frontend code was modified.
- No unrelated deployment/static issues were fixed.
- No DNS, Cloudflare Tunnel, Cloudflare Access, Chroma, embeddings, corpus, source data, scraping, or visual assets were touched.
- Nothing was staged or committed.

Task classification:

- Lane: `12 Self-Hosted Deployment`
- Type: docs-only deployment readiness handoff
- Mode: GREEN for this handoff; actual restart/deployment is RED and requires an explicit protected-preview smoke/deploy task.

## 1. Current Deployment Assumptions

- Branch: `feature/answer-api`
- Current HEAD at inspection: `07f9b9d`
- Relevant commits in history:
  - `686fd3c feat: add deterministic tab engine slice`
  - `0bd0780 test: add tab engine ui QA coverage`
  - `07f9b9d feat: render tab examples on answer page`
- The backend tab engine files from `686fd3c` are committed:
  - `steel_guitar_rag/tab_engine.py`
  - `/api/tab/render` route in `steel_guitar_rag/api.py`
  - `tests/test_tab_engine.py`
- The answer-page tab UI is also now present in current HEAD, but the worktree still has dirty runtime-affecting UI/test files. Do not use the current dirty worktree for protected-preview restart until Lane 06 either commits the intended UI changes or parks them.
- Expected private preview route remains:
  - public URL: `https://app.steelguitarrag.com/`
  - final app shell URL after root redirect: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
  - local backend: `http://127.0.0.1:8770`
  - auth provider: Cloudflare Access
- The tab render endpoint is served by the same Mac mini app process. It does not use Chroma or Ollama directly.
- `/api/tab/render` currently does not perform per-route app auth in `steel_guitar_rag/api.py`; protected-preview safety depends on:
  - Cloudflare Access protecting `app.steelguitarrag.com`
  - the local app binding only to `127.0.0.1`
  - no router port forwarding to the app

## 2. Local Smoke Commands

Use a clean committed runtime state before starting local or protected-preview smoke. First gate the worktree:

```bash
git status --short
git rev-parse --short HEAD
git log --oneline -5
git diff --check
git status --short -- 'steel_guitar_rag/*.py' 'ui/*.js' 'scripts/*.py' tests
```

Stop if dirty runtime-affecting files are present in `steel_guitar_rag/*.py`, `ui/*.js`, `scripts/*.py`, or `tests`, unless the current task explicitly says to verify that dirty Lane 06 state.

Focused checks for the committed tab engine and answer-page tab UI:

```bash
.venv/bin/python -m pytest tests/test_tab_engine.py -q
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
git diff --check
```

Optional broader focused API checks before restart:

```bash
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py -q
```

Known full-suite caveat: full `pytest` may still show two unrelated failures listed below; those should not block tab-engine protected-preview smoke unless they affect this route or answer-page rendering.

## 3. API Smoke Commands For `/api/tab/render`

Route confirmed from repo inspection:

```text
POST /api/tab/render
Content-Type: application/json
```

Expected response shape:

```json
{
  "ok": true,
  "tab": "...fixed-width tab text...",
  "issues": [],
  "metadata": {
    "profile": "default_e9",
    "event_count": 1
  }
}
```

Successful local curl example:

```bash
curl -sS \
  -X POST http://127.0.0.1:8770/api/tab/render \
  -H "Content-Type: application/json" \
  --data '{
    "profile": "default_e9",
    "events": [
      {
        "chord": "G",
        "lyric": "pick",
        "notes": [
          {"string": 4, "fret": 3},
          {"string": 5, "fret": 3},
          {"string": 6, "fret": 3}
        ]
      }
    ]
  }'
```

Expected checks:

- HTTP status is `200`.
- JSON has `"ok": true`.
- `issues` is `[]`.
- `metadata.profile` is `default_e9`.
- `metadata.event_count` is `1`.
- `tab` includes 10 string rows, including ` 4 |`, ` 5 |`, ` 6 |`, and `10 |`.
- The `3` markers on strings 4, 5, and 6 align in one event column.

String-aware A/B pedal curl example:

```bash
curl -sS \
  -X POST http://127.0.0.1:8770/api/tab/render \
  -H "Content-Type: application/json" \
  --data '{
    "events": [
      {
        "chord": "C",
        "notes": [
          {"string": 4, "fret": 3},
          {"string": 5, "fret": 3, "changes": ["A"]},
          {"string": 6, "fret": 3, "changes": ["B"]}
        ]
      }
    ]
  }'
```

Expected checks:

- JSON has `"ok": true`.
- String 5 row includes `3A`.
- String 6 row includes `3B`.
- String 4 row does not show an impossible `3A` or `3B`.

Validation failure curl example:

```bash
curl -sS \
  -X POST http://127.0.0.1:8770/api/tab/render \
  -H "Content-Type: application/json" \
  --data '{
    "events": [
      {
        "notes": [
          {"string": 4, "fret": 3, "changes": ["A"]}
        ]
      }
    ]
  }'
```

Expected checks:

- HTTP status is `200`.
- JSON has `"ok": false`.
- `tab` is an empty string.
- `issues[0].code` is `unaffected_string_change`.
- `issues[0].message` says `Change A does not affect string 4.`
- `metadata.profile` is `default_e9`.

Unsupported profile curl example:

```bash
curl -sS \
  -X POST http://127.0.0.1:8770/api/tab/render \
  -H "Content-Type: application/json" \
  --data '{"profile":"c6","events":[]}'
```

Expected checks:

- JSON has `"ok": false`.
- `issues[0].code` is `unsupported_profile`.
- No tab text is rendered.

Protected-preview API smoke after Cloudflare Access login:

```bash
curl -sS \
  -X POST https://app.steelguitarrag.com/api/tab/render \
  -H "Content-Type: application/json" \
  --data '{"events":[{"notes":[{"string":4,"fret":3},{"string":5,"fret":3},{"string":6,"fret":3}]}]}'
```

For unauthenticated shell curl, expected behavior is Cloudflare Access interception, not raw tab JSON. A direct unauthenticated public POST returning tab JSON would be a security blocker for protected preview.

## 4. Browser Smoke Checklist For Answer-Page Tab Card

Run this only after Lane 06 answer-page tab rendering is committed or the task explicitly asks to verify the dirty Lane 06 state.

Smoke target block:

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/?v=tab-engine-<HEAD>
- Cache-busted URL tested: https://app.steelguitarrag.com/?v=tab-engine-<HEAD>
- Exact URL the user should use: https://app.steelguitarrag.com/?v=tab-engine-<HEAD>
- Auth required: yes
- Auth provider: Cloudflare Access
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: <HEAD>
- Version endpoint: /api/version
- Version endpoint result: must match <HEAD>
- Whether app root / works: yes, expected to redirect to /ui/steel-guitar-rag-mock.html
- Whether /ui/steel-guitar-rag-mock.html works: yes
- API fallback status: not a replacement for browser tab-card rendering
```

Browser UI checks:

- Open the app through Cloudflare Access.
- Confirm `/api/version` reports the expected clean committed HEAD.
- Confirm Q&A input is unlocked.
- Submit at least one answer prompt expected to include tab examples once Lane 06 wires answer payloads into the answer page, for example:
  - `Show me a simple E9 lick in G.`
  - `Show me a country lick in G.`
  - `Teach me some B+C pedal skills.`
- Verify the answer page displays a tab section between the answer card and fretboard section.
- Verify the tab card title is visible, for example `Tab example`.
- Verify the tab block uses fixed-width/monospace formatting and horizontal scrolling if needed.
- Verify row labels/string rows are readable and aligned.
- Verify pedal/lever markings render only on affected strings.
- Verify validation label appears as `Validated` for valid payloads.
- Verify validation/issue notes appear for invalid payloads if exposed by the UI.
- Verify metadata renders as readable key/value text, not `[object Object]`.
- Verify `intervals`, `chordTones`, `why`, and `sourceNote` render only when present.
- Verify the tab section hides cleanly when an answer has no `tabs` or `tab` payload.
- Verify the fretboard card still renders below the tab section when a fretboard payload is also present.
- Verify source cards remain below tab/fretboard content and are not promoted into the answer body.
- Verify mobile/narrow layout preserves tab readability through horizontal scrolling.
- Check console logs for JavaScript errors.

## 5. Protected Preview Smoke Checklist

Use the documented private-preview command from the repo root after runtime dirty gate is clean:

```bash
cd ~/Documents/Pocket\ Steel
source .venv/bin/activate

lsof -tiTCP:8770 -sTCP:LISTEN | xargs kill 2>/dev/null || true

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
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

Verify process and version:

```bash
lsof -nP -iTCP:8770 -sTCP:LISTEN
curl -sS http://127.0.0.1:8770/api/version
curl -sS -I http://127.0.0.1:8770/
curl -sS -I http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html
```

Expected:

- Process listens only on `127.0.0.1:8770`.
- Process cwd is the repo path.
- `/api/version` reports the expected clean committed HEAD.
- Root redirects to `/ui/steel-guitar-rag-mock.html`.
- `/ui/steel-guitar-rag-mock.html` returns 200.

Public protected checks:

- Unauthenticated `https://app.steelguitarrag.com/` redirects to Cloudflare Access.
- Unauthenticated `POST https://app.steelguitarrag.com/api/answer` does not return an answer.
- Unauthenticated `POST https://app.steelguitarrag.com/api/tab/render` should not return raw tab JSON if Cloudflare Access is protecting the hostname.
- Authenticated browser can load the app, unlock Q&A, and render tab examples.
- Authenticated browser `/api/version` reports expected HEAD.

## 6. Known Unrelated Blockers/Caveats

Known unrelated full-suite failures from the task context:

1. Landing source vs deployed static HTML mismatch.
2. Missing public fretboard background route.

Current worktree caveats at inspection:

- Current HEAD is `07f9b9d`, not `686fd3c`; the answer-page tab UI has landed in history.
- There are many unrelated dirty/parked files.
- Runtime-affecting dirty files are currently present in:
  - `tests/test_frontend_answer_ui.py`
  - `ui/steel-guitar-rag-mock.html`
- Do not restart protected preview for user smoke from this dirty runtime state unless the task explicitly asks to verify those dirty Lane 06 changes. Prefer a clean commit or parked dirty state first.
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png` is dirty and `ui/brand/` is a protected visual-design path. Do not stage it from Lane 12.

## 7. Rollback Considerations

If tab output regresses in protected preview:

1. Stop the `8770` app process.
2. Restart protected preview from the last known good committed HEAD.
3. Verify `/api/version` reports the rollback HEAD.
4. Verify `https://app.steelguitarrag.com/` still passes Cloudflare Access.
5. Keep `/api/answer` protected.
6. Do not expose Ollama or Chroma for debugging.
7. Do not reset Chroma, regenerate embeddings, run scraping, or modify corpus data as part of tab rollback.
8. Preserve logs locally for Lane 05/Lane 06 diagnosis, but do not commit private logs.

If tab rendering is unsafe but answer behavior is otherwise healthy, the lowest-risk UI rollback is to hide/suppress the answer-page tab section while leaving `/api/tab/render` available only for local/protected API smoke. That product/UI decision belongs to Lane 06/18 and should not be made by Lane 12 during deployment smoke.

## 8. What Logs/Errors To Inspect

Local terminal running `scripts/serve_v2_rerank_smoke.py`:

- Python tracebacks.
- `POST /api/tab/render` 500s.
- malformed JSON errors.
- `POST /api/answer` 500s when answers include tab payloads.

Browser DevTools:

- Console errors from `ui/answer-client.js`.
- Console errors from `ui/steel-guitar-rag-mock.html`.
- Network status for `/api/answer`.
- Network status for `/api/tab/render` if manually invoked from the browser.
- Whether answer JSON includes `tabs` or top-level `tab`.
- Whether `#answer-tab` is hidden or visible.
- DOM state under `#answer-tab-list`.
- Whether `[object Object]` appears anywhere in tab card text.

Cloudflare:

- Access logs: confirm authenticated session for protected preview.
- Tunnel status: confirm connected tunnel to local app.
- No new hostname routing for Ollama or Chroma.

Security-specific checks:

- Confirm public unauthenticated `/api/tab/render` does not bypass Cloudflare Access.
- Confirm app process remains bound to `127.0.0.1`.
- Confirm no local env secrets, tunnel tokens, or Cloudflare credentials appear in logs/screenshots/handoffs.

## 9. Pass/Fail Criteria

Local API pass:

- `/api/tab/render` returns 200 JSON for valid and invalid payloads.
- Valid payload returns `ok: true`, non-empty `tab`, empty `issues`, and expected metadata.
- Invalid mechanical payload returns `ok: false`, empty `tab`, and readable issue codes/messages.
- Unsupported profile returns `ok: false` and `unsupported_profile`.
- No Python traceback appears.

Answer-page UI pass:

- Answer response with `tabs` or `tab` renders a visible tab card.
- Tab card appears between the answer card and fretboard/source sections.
- Fixed-width tab rows are readable and aligned.
- Tab text is not collapsed, wrapped into unreadability, or clipped without scroll.
- No `[object Object]` appears.
- Missing optional fields do not render broken labels.
- No tab payload means the tab section remains hidden.
- Existing answer, fretboard, and source rendering still works.
- Mobile/narrow layout is usable.
- Browser console has no relevant errors.

Protected preview pass:

- Runtime `/api/version` matches expected clean committed HEAD.
- Root app URL loads through Cloudflare Access.
- Q&A unlocks only after Access login.
- Public unauthenticated root redirects to Access.
- Public unauthenticated `/api/answer` remains blocked.
- Public unauthenticated `/api/tab/render` is intercepted by Access.
- Authenticated browser smoke passes.

Fail/block:

- Runtime dirty gate has uncommitted runtime changes not explicitly in scope.
- `/api/version` does not match expected HEAD.
- Public unauthenticated `/api/tab/render` returns raw tab JSON through `app.steelguitarrag.com`.
- Tab card does not render when answer JSON includes `tabs`.
- Tab card renders `[object Object]`.
- Tab rows are visibly misaligned.
- Invalid tab payload renders as valid.
- `/api/answer` auth behavior changes.
- Cloudflare Access, Tunnel, DNS, Chroma, embeddings, corpus, or scraping changes are required to make the smoke pass.

## 10. Recommended Post-Lane-06 Deployment Prompt

Use this prompt after Lane 06 commits or parks the answer-page tab UI changes and the runtime dirty gate is clean:

```text
Lane: 12 Self-Hosted Deployment
Reasoning level: MEDIUM-HIGH

Task: Restart protected preview from the clean committed tab UI HEAD and run browser smoke for deterministic tab examples.

Read:
- AGENTS.md
- docs/handoffs/task-completions/2026-06-18-12-tab-engine-deploy-smoke-plan.md
- latest Lane 06 answer-page tab UI handoff
- latest Repo Steward commit handoff for the tab UI commit
- docs/private-preview-operations.md
- docs/current-commands.md
- scripts/serve_v2_rerank_smoke.py
- current git status and HEAD

Do not:
- change DNS
- change Cloudflare Access policy
- touch corpus, Chroma, embeddings, source-inbox, private corpus, scraping, or source data
- modify implementation files
- stage or commit anything
- use API fallback as browser smoke

First verify:
- git status --short
- git rev-parse --short HEAD
- git log --oneline -5
- git diff --check
- git status --short -- 'steel_guitar_rag/*.py' 'ui/*.js' 'scripts/*.py' tests

Stop before restart if dirty runtime-affecting files are present in steel_guitar_rag/*.py, ui/*.js, scripts/*.py, or tests.

Run:
- .venv/bin/python -m pytest tests/test_tab_engine.py -q
- node --check ui/answer-client.js
- .venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
- git diff --check

Restart protected preview using the documented private-preview command.

Verify:
- process listens on 127.0.0.1:8770
- process cwd is the repo path
- /api/version reports current HEAD
- root URL loads through Cloudflare Access
- Q&A unlocks after Access login
- unauthenticated /api/answer remains blocked
- unauthenticated public /api/tab/render is intercepted by Cloudflare Access
- authenticated /api/tab/render returns validated tab JSON for a known payload

Browser smoke:
- Open https://app.steelguitarrag.com/?v=tab-engine-<HEAD>
- Ask a prompt expected to produce tab examples, such as "Show me a simple E9 lick in G."
- Verify visible tab card between answer and fretboard/source sections.
- Verify fixed-width tab rows align.
- Verify metadata/interval/chord-tone/issue text is readable.
- Verify no [object Object].
- Verify no console errors.
- Verify mobile/narrow layout remains usable.

Create a handoff under docs/handoffs/task-completions/ with the smoke target block, version evidence, prompt results, tab-card rendering result, security checks, caveats, and user-smoke readiness decision.
```

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-18-12-tab-engine-deploy-smoke-plan.md`

Modified: none.

Deleted: none.

Generated artifacts: none.

## Tests And Checks

Commands run:

```text
git status --short
git rev-parse --short HEAD
git log --oneline -8
git branch --show-current
rg -n "tab/render|tab_engine|render_tab|Tab" steel_guitar_rag tests scripts docs/current-commands.md docs/private-preview-operations.md docs/self-hosted-deployment-plan.md docs/cloudflare-tunnel-private-preview.md
sed -n '1,260p' tests/test_tab_engine.py
sed -n '1,260p' steel_guitar_rag/tab_engine.py
sed -n '230,270p' steel_guitar_rag/api.py
sed -n '260,360p' tests/test_tab_engine.py
sed -n '1,260p' docs/current-commands.md
sed -n '1,520p' docs/private-preview-operations.md
sed -n '1,220p' scripts/serve_v2_rerank_smoke.py
sed -n '400,520p' ui/answer-client.js
sed -n '3460,3518p' ui/steel-guitar-rag-mock.html
sed -n '1380,1485p' tests/test_frontend_answer_ui.py
```

Required finish check:

```text
git diff --check
```

Result recorded by Lane 12 after writing this handoff.

Skipped:

- No unit tests were run because this was a docs-only deployment-readiness handoff and the user provided known test status.
- No browser smoke was run because this task was a smoke plan only.
- No protected-preview restart was run.

## Integration Notes

- `/api/tab/render` is available as a deterministic API route independent of Chroma/Ollama retrieval.
- The answer-page UI normalization accepts both top-level `tab` and `tabs` payloads.
- The UI currently caps displayed tabs to the first three examples.
- Deployment smoke must verify Cloudflare Access protects `/api/tab/render` on the public hostname because the app route itself does not contain an auth check.
- Do not deploy or restart protected preview from the currently dirty runtime worktree unless a later task explicitly asks to verify dirty Lane 06 work.

## Risk Assessment

Risk: medium for next deployment smoke.

Why:

- Backend tab engine is deterministic and focused, but it introduces a new API surface.
- Public hostname safety depends on Cloudflare Access protecting all app paths.
- Answer-page tab rendering is a new UI surface and should be browser-smoked on desktop and narrow view.
- Current worktree has dirty runtime-affecting UI/test files, so runtime verification should wait for a clean committed state unless explicitly scoped otherwise.

Rollback note:

- Roll back by restarting protected preview from the last known good committed HEAD and verifying `/api/version`.
- Do not alter DNS, Tunnel, Access policy, Chroma, embeddings, corpus, scraping, or Ollama as part of rollback.

## Human Decision Needed

No for this handoff.

Yes before actual protected-preview restart/deployment smoke if runtime dirty files remain: decide whether to commit/park Lane 06 changes first or explicitly smoke the dirty Lane 06 state.

## Safe-To-Stage Exact File List

If the user later asks for an exact-path docs commit:

- `docs/handoffs/task-completions/2026-06-18-12-tab-engine-deploy-smoke-plan.md`

## Files That Must Not Be Staged

- `steel_guitar_rag/*.py`
- `ui/*.js`
- `ui/steel-guitar-rag-mock.html`
- `tests`
- `ui/brand/`
- `Neon Sign/`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/`
- scraping outputs
- `.wrangler/`
- credentials, private env files, tunnel tokens, or logs
- unrelated parked docs/corpus/source/design files

## Recommended Next Lane

Recommended next lane: `06 UX/UI Design` or `01 Repo Steward`.

- If Lane 06 changes in `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py` are intentional and ready, Lane 06/01 should finish or commit that slice first.
- After a clean committed runtime state exists, Lane 12 should run the recommended protected-preview smoke prompt above.

## Commit Readiness

Not ready to commit.

Reason: the user did not explicitly instruct a commit, and the worktree is not clean. This handoff is safe as an exact-path docs artifact, but Lane 01 should decide whether to commit it later.
