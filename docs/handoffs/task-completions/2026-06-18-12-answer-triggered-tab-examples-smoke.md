# 2026-06-18 Lane 12 Answer-Triggered Tab Examples Smoke Plan

## Task Summary

Lane 12 was asked to prepare local and protected-preview smoke coverage for answer-triggered deterministic tab examples after Lane 05 lands, without touching app implementation code.

Completed:

- Inspected repo state first.
- Confirmed branch `feature/answer-api`.
- Confirmed relevant commits in history:
  - `686fd3c feat: add deterministic tab engine slice`
  - `54a28c7 fix: clear tab examples on stage return`
  - `7834c67 docs: plan tab engine follow-on slices`
- Inspected local/protected-preview startup docs.
- Inspected `/api/answer` and `/api/tab/render` route shape from repo code.
- Inspected current in-progress answer-triggered tab example contract read-only.
- Created this deployment/smoke handoff only.

Intentionally not changed:

- No backend code was modified.
- No frontend code was modified.
- No unrelated deployment/static issues were fixed.
- No DNS, Cloudflare Tunnel, Cloudflare Access, Chroma, embeddings, corpus, source data, scraping, or visual assets were touched.

Task classification:

- Lane: `12 Self-Hosted Deployment`
- Type: docs-only deployment smoke planning
- Mode: GREEN for this handoff; actual protected-preview restart/deployment remains RED and requires an explicit Lane 12 smoke task.

## 1. Current Deployment Assumptions

- Branch at inspection: `feature/answer-api`
- Current HEAD at inspection: `7834c67`
- Backend deterministic tab engine exists in committed history at `686fd3c`.
- Answer-page tab rendering exists in committed history before this handoff.
- Lane 05 answer-triggered deterministic tab examples are still in progress in the working tree at inspection.
- Current in-progress answer-triggered code adds `pocketsteel/answer_tab_examples.py` and wires helper calls into `/api/answer`, but that code is not committed and must not be staged by Lane 12.
- The in-progress answer payload key is currently `tab_example` with `rendered_tab`; the committed frontend normalizer inspected in `ui/answer-client.js` reads `tabs[]` or top-level `tab`. Post-Lane-05 smoke must verify the final backend/frontend contract is aligned.
- Protected-preview app should remain Mac-hosted through Cloudflare Access and Cloudflare Tunnel:

```text
Internet -> Cloudflare Access -> Cloudflare Tunnel -> Mac mini app on 127.0.0.1:8770
```

- Ollama and Chroma must remain local-only.
- `/api/tab/render` is a deterministic helper route and does not directly use Chroma or Ollama.
- `/api/tab/render` does not currently enforce per-route app auth in `pocketsteel/api.py`; public hostname protection depends on Cloudflare Access covering `app.steelguitarrag.com` and the app binding only to `127.0.0.1`.

Do not run protected-preview smoke from a dirty runtime worktree unless the task explicitly asks to smoke that dirty state. At inspection, dirty runtime-affecting paths included:

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `pocketsteel/answer_tab_examples.py` as untracked in-progress Lane 05 work

## 2. Local Server Startup Commands From Repo Inspection

Preflight before starting any server:

```bash
git status --short
git rev-parse --short HEAD
git log --oneline -5
git diff --check
git status --short -- 'pocketsteel/*.py' 'ui/*.js' 'scripts/*.py' tests
```

Stop if dirty runtime-affecting files are present unless the task explicitly says to test that dirty state.

Local same-origin answer UI smoke server:

```bash
cd ~/Documents/Pocket\ Steel
source .venv/bin/activate

PYTHONPATH=. \
STEEL_RAG_CHROMA_PATH="~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma" \
STEEL_RAG_CHROMA_COLLECTION="steel_guitar_unified" \
.venv/bin/python scripts/serve_answer_smoke.py --controlled-states --port 8770
```

Open:

```text
http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user
```

Local v2 rerank smoke server for protected-preview-like retrieval:

```bash
cd ~/Documents/Pocket\ Steel
source .venv/bin/activate

.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8781 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --candidate-k 20 \
  --min-excerpt-chars 80 \
  --question-only-penalty 0.12 \
  --mention-only-penalty 0.20 \
  --answer-advice-boost 0.04 \
  --quality-boost 0.04 \
  --quality-threshold 0.70 \
  --noise-penalty 0.06 \
  --noise-threshold 0.60
```

Open:

```text
http://127.0.0.1:8781/ui/steel-guitar-rag-mock.html?access=beta_user
```

Private-preview auth-config local server:

```bash
cd ~/Documents/Pocket\ Steel
source .venv/bin/activate

set -a
source ~/.steel-rag/env/private-preview.env
set +a

PYTHONPATH=. \
.venv/bin/python scripts/serve_answer_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

For protected-preview restart, prefer the existing `scripts/serve_v2_rerank_smoke.py` command documented in previous Lane 12 handoffs, with `--host 127.0.0.1`, `--port 8770`, production answer auth mode, Cloudflare Access auth provider, and the v2/private Chroma environment values.

Stop an existing local server:

```bash
lsof -tiTCP:8770 -sTCP:LISTEN | xargs kill 2>/dev/null || true
```

## 3. API Smoke Commands For Answer Endpoint

Use these after Lane 05 lands. The exact final answer-tab payload key must be verified from the final committed implementation. At inspection, in-progress Lane 05 uses `tab_example.rendered_tab`; committed frontend tab rendering reads `tabs[].tabText` or top-level `tab`.

Local-dev curl shape for `/api/answer`:

```bash
curl -sS \
  -X POST http://127.0.0.1:8770/api/answer \
  -H "Content-Type: application/json" \
  -H "X-Steel-Rag-Dev-Access-Role: beta_user" \
  --data '{"question":"Show me a G major grip"}'
```

Expected post-Lane-05 checks:

- HTTP status is `200`.
- Answer body remains a normal teacher-first answer.
- Response includes deterministic tab example data under the final agreed contract key.
- If final key is still `tab_example`, it should include:
  - `id`
  - `title`
  - `context`
  - `rendered_tab`
  - `validation.ok`
  - `validation.profile`
  - `validation.eventCount`
  - `explanation`
  - `intervals`
  - `events`
- If final key is `tabs`, at least one tab object should include a renderable text field such as `tabText`, `tab`, or `text`, plus readable metadata/validation.
- No `[object Object]` should appear in serialized UI-normalized data or browser rendering.

Scenario curl examples:

```bash
# Should return/render a G major grip tab example.
curl -sS \
  -X POST http://127.0.0.1:8770/api/answer \
  -H "Content-Type: application/json" \
  -H "X-Steel-Rag-Dev-Access-Role: beta_user" \
  --data '{"question":"Show me a G major grip"}'
```

```bash
# Should return/render a G-to-C move tab example.
curl -sS \
  -X POST http://127.0.0.1:8770/api/answer \
  -H "Content-Type: application/json" \
  -H "X-Steel-Rag-Dev-Access-Role: beta_user" \
  --data '{"question":"Show me a G to C move"}'
```

```bash
# Should return/render an A+B pedal tab example.
curl -sS \
  -X POST http://127.0.0.1:8770/api/answer \
  -H "Content-Type: application/json" \
  -H "X-Steel-Rag-Dev-Access-Role: beta_user" \
  --data '{"question":"How do I use A+B pedals?"}'
```

```bash
# Should answer normally and should not include a tab example.
curl -sS \
  -X POST http://127.0.0.1:8770/api/answer \
  -H "Content-Type: application/json" \
  -H "X-Steel-Rag-Dev-Access-Role: beta_user" \
  --data '{"question":"Why does my amp buzz at idle?"}'
```

```bash
# Copyright-sensitive named song tab request should not include generated tab.
curl -sS \
  -X POST http://127.0.0.1:8770/api/answer \
  -H "Content-Type: application/json" \
  -H "X-Steel-Rag-Dev-Access-Role: beta_user" \
  --data '{"question":"Give me the tab for Together Again note-for-note"}'
```

Protected-preview answer endpoint smoke:

- Use authenticated browser/network tools where possible.
- If using shell curl against `https://app.steelguitarrag.com/api/answer` without an Access session, expected result is Cloudflare Access interception or denial, not a raw answer.
- API fallback must not be reported as browser smoke.

## 4. API Smoke Commands For `/api/tab/render` If Still Relevant

`/api/tab/render` remains useful as a deterministic lower-level smoke even after answer-triggered examples land. It proves the renderer itself is healthy before diagnosing answer-route or UI contract issues.

Valid G grip example:

```bash
curl -sS \
  -X POST http://127.0.0.1:8770/api/tab/render \
  -H "Content-Type: application/json" \
  --data '{
    "profile": "default_e9",
    "events": [
      {
        "chord": "G",
        "notes": [
          {"string": 4, "fret": 3},
          {"string": 5, "fret": 3},
          {"string": 6, "fret": 3}
        ]
      }
    ]
  }'
```

Expected:

- `ok: true`
- `issues: []`
- `metadata.profile: default_e9`
- `metadata.event_count: 1`
- `tab` includes aligned rows for strings 4, 5, and 6

Valid A+B string-aware example:

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

Expected:

- `ok: true`
- string 5 row includes `3A`
- string 6 row includes `3B`
- string 4 row does not show `3A` or `3B`

Validation failure example:

```bash
curl -sS \
  -X POST http://127.0.0.1:8770/api/tab/render \
  -H "Content-Type: application/json" \
  --data '{"events":[{"notes":[{"string":4,"fret":3,"changes":["A"]}]}]}'
```

Expected:

- `ok: false`
- `tab: ""`
- issue code `unaffected_string_change`

Security check for protected preview:

```bash
curl -sS -i \
  -X POST https://app.steelguitarrag.com/api/tab/render \
  -H "Content-Type: application/json" \
  --data '{"events":[{"notes":[{"string":4,"fret":3}]}]}'
```

Unauthenticated shell curl should be intercepted by Cloudflare Access. Returning raw tab JSON publicly would be a protected-preview blocker.

## 5. Browser Smoke Checklist

Run browser smoke only after Lane 05 lands and the runtime dirty gate is clean, unless explicitly instructed to test dirty work.

Smoke target block for the handoff that runs this smoke:

```text
Smoke Target:
- Target type: local or protected-preview
- Result type: browser smoke
- Exact browser URL tested: <exact URL>
- Cache-busted URL tested: <exact URL with ?v=answer-tabs-<HEAD>>
- Exact URL the user should use: <exact URL>
- Auth required: yes for protected preview
- Auth provider: Cloudflare Access for protected preview
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: <HEAD after Lane 05>
- Version endpoint: /api/version
- Version endpoint result: <must match HEAD>
- Whether app root / works: expected yes by redirect
- Whether /ui/steel-guitar-rag-mock.html works: expected yes
- API fallback status: not a replacement for browser tab rendering
```

Browser smoke scenarios:

1. `Show me a G major grip`
   - Expected: normal answer plus visible deterministic tab example.
   - Verify the tab title or context indicates G major/4-5-6/default E9.
   - Verify tab rows are fixed-width and aligned.

2. `Show me a G to C move`
   - Expected: normal answer plus visible deterministic G-to-C tab example.
   - Verify the tab shows multiple events/movement, not just a single static grip.

3. `How do I use A+B pedals?`
   - Expected: normal answer plus visible A+B pedal tab example.
   - Verify A/B markings appear only on affected strings.

4. Unrelated gear question: `Why does my amp buzz at idle?`
   - Expected: normal answer rendering unchanged.
   - Expected: no tab example/card.

5. Copyright-sensitive named-song tab request: `Give me the tab for Together Again note-for-note`
   - Expected: no generated tab.
   - Expected: copyright-safe refusal or safe guidance.
   - Expected: no deterministic tab block attached just because the prompt contains the word `tab`.

6. Normal answer rendering regression:
   - Ask a known non-tab steel question such as `What are common Fender Steel King settings?`
   - Verify answer card, sections, source notes/source cards, and follow-ups still render normally.

7. Browser layout:
   - Verify tab block spacing survives browser rendering.
   - Verify monospace/fixed-width row alignment.
   - Verify long tab lines do not force page-wide layout overflow.
   - Verify mobile/narrow width scrolls tab horizontally.
   - Verify no `[object Object]` appears anywhere in the tab card.
   - Verify no console errors.

Contract-diagnosis checks if the card does not render:

- Inspect raw `/api/answer` JSON.
- If JSON contains `tab_example.rendered_tab` but no visible card, likely frontend contract/rendering mismatch.
- If JSON contains `tabs[]` with no visible card, likely frontend render gate or CSS hidden-state issue.
- If JSON has no tab payload for expected prompts, likely Lane 05 answer-trigger selection/routing issue.
- If `/api/tab/render` works but `/api/answer` tab payload does not, likely answer attachment/routing issue.

## 6. Protected Preview Smoke Checklist

Do not restart protected preview until:

- Lane 05 implementation is committed or intentionally scoped for dirty-state testing.
- Runtime dirty gate is clean, or the task explicitly says to test dirty runtime files.
- Focused tests have passed.

Recommended focused checks before restart:

```bash
.venv/bin/python -m pytest tests/test_tab_engine.py -q
.venv/bin/python -m pytest tests/test_api_contract.py -q
.venv/bin/python -m pytest tests/test_api_search.py -q
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Restart protected preview with documented private-preview command:

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

Verify process:

```bash
lsof -nP -iTCP:8770 -sTCP:LISTEN
curl -sS http://127.0.0.1:8770/api/version
curl -sS -I http://127.0.0.1:8770/
curl -sS -I http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html
```

Expected:

- process listens only on `127.0.0.1:8770`
- process cwd is repo root
- `/api/version` reports expected HEAD
- root redirects to `/ui/steel-guitar-rag-mock.html`
- fallback UI route returns 200

Protected public checks:

- unauthenticated `https://app.steelguitarrag.com/` redirects to Cloudflare Access
- unauthenticated public `/api/answer` does not return an answer
- unauthenticated public `/api/tab/render` is intercepted by Cloudflare Access
- authenticated browser loads root/fallback UI
- authenticated browser `/api/version` reports expected HEAD
- authenticated browser smoke scenarios pass

## 7. Expected Pass/Fail Behavior

Pass:

- `Show me a G major grip` returns a normal answer and deterministic tab payload/card.
- `Show me a G to C move` returns a normal answer and deterministic tab payload/card.
- `How do I use A+B pedals?` returns a normal answer and deterministic tab payload/card.
- Gear prompt does not include tab payload/card.
- Named copyrighted song tab request does not include generated tab.
- Normal answer rendering is unchanged for non-tab prompts.
- Tab card renders with readable title, context/metadata, validation status, and fixed-width tab text.
- Tab text row alignment survives browser rendering.
- Mobile/narrow view scrolls tab horizontally instead of breaking layout.
- No `[object Object]` appears.
- `/api/version` matches expected HEAD.
- Cloudflare Access still protects public app routes.
- `/api/answer` auth behavior remains unchanged.

Fail/block:

- Expected tab prompts produce no answer tab payload after Lane 05 lands.
- Raw answer JSON includes tab payload but browser card stays hidden.
- Raw answer JSON uses `tab_example.rendered_tab` while frontend still only reads `tabs[]` or top-level `tab`, unless Lane 06 has bridged that contract.
- Gear/off-topic prompt shows a tab example.
- Named copyrighted song request generates tab.
- Tab rows are misaligned, wrapped into unreadability, or overflow the entire page.
- `[object Object]` appears.
- Public unauthenticated `/api/tab/render` returns raw JSON through `app.steelguitarrag.com`.
- Public unauthenticated `/api/answer` returns an answer.
- Runtime dirty gate is not clean and the smoke task did not explicitly authorize dirty-state verification.

## 8. Known Unrelated Caveats

Known unrelated full-suite failures from the task context:

1. Landing source vs deployed static HTML mismatch.
2. Missing public fretboard background route.

Current worktree caveats at inspection:

- Dirty runtime-affecting files are present.
- `pocketsteel/answer_tab_examples.py` is untracked in-progress Lane 05 work.
- `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py` are dirty.
- `ui/brand/` contains dirty/untracked visual assets and is a protected visual-design path.
- Many unrelated docs, corpus metadata, source-inbox, generated, and design files remain dirty/untracked.

Do not treat the two known full-suite failures as tab smoke blockers unless they affect the answer-page tab card, app shell loading, or protected-preview routing.

## 9. Rollback Considerations

If answer-triggered tabs regress protected preview:

1. Stop the `8770` app process.
2. Restart protected preview from the last known good committed HEAD.
3. Verify `/api/version` reports the rollback HEAD.
4. Verify root and fallback app URLs still load through Cloudflare Access.
5. Verify unauthenticated `/api/answer` remains blocked.
6. Verify unauthenticated public `/api/tab/render` remains intercepted by Cloudflare Access.
7. Do not change DNS.
8. Do not change Cloudflare Access policy.
9. Do not expose Ollama.
10. Do not expose Chroma.
11. Do not run scraping.
12. Do not modify corpus, Chroma, embeddings, source-inbox, or private source data.

If only tab rendering fails but answer quality remains safe, a possible product/UI rollback is to hide the answer-page tab card or suppress answer-triggered tab payloads. That decision belongs to Lane 05/06/18 and should not be made by Lane 12 during smoke.

## 10. Recommended Post-Lane-05 Deploy Prompt

Use this after Lane 05 commits answer-triggered deterministic tab examples and Repo Steward confirms the runtime dirty gate is clean:

```text
Lane: 12 Self-Hosted Deployment
Reasoning level: MEDIUM-HIGH

Task: Restart protected preview from the clean committed answer-triggered tab examples HEAD and run browser smoke.

Read:
- AGENTS.md
- docs/handoffs/task-completions/2026-06-18-12-answer-triggered-tab-examples-smoke.md
- latest Lane 05 answer-triggered tab examples handoff
- latest Lane 06 answer-page tab rendering handoff if present
- latest Repo Steward commit handoff for the answer-triggered tab examples commit
- docs/current-commands.md
- docs/private-preview-operations.md
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
- git status --short -- 'pocketsteel/*.py' 'ui/*.js' 'scripts/*.py' tests

Stop before restart if dirty runtime-affecting files are present.

Run focused checks:
- .venv/bin/python -m pytest tests/test_tab_engine.py -q
- .venv/bin/python -m pytest tests/test_api_contract.py -q
- .venv/bin/python -m pytest tests/test_api_search.py -q
- node --check ui/answer-client.js
- .venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
- .venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
- git diff --check

Restart protected preview using the documented private-preview command.

Verify:
- process listens on 127.0.0.1:8770
- process cwd is repo root
- /api/version reports current HEAD
- root URL loads through Cloudflare Access
- Q&A unlocks after Access login
- unauthenticated public /api/answer remains blocked
- unauthenticated public /api/tab/render is intercepted by Cloudflare Access

Browser smoke:
- Open https://app.steelguitarrag.com/?v=answer-tabs-<HEAD>
- Ask: Show me a G major grip
- Ask: Show me a G to C move
- Ask: How do I use A+B pedals?
- Ask: Why does my amp buzz at idle?
- Ask: Give me the tab for Together Again note-for-note
- Ask one normal non-tab steel question to confirm answer rendering is unchanged.

Verify:
- expected first three prompts show visible deterministic tab examples
- gear question shows no tab
- named copyrighted song tab request shows no generated tab
- tab rows are aligned and horizontally scroll on narrow/mobile width
- no [object Object]
- no console errors
- source/fretboard/normal answer rendering remains healthy

Create a handoff under docs/handoffs/task-completions/ with the smoke target block, version evidence, prompt results, tab-card rendering result, auth/security checks, caveats, and readiness decision.
```

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-18-12-answer-triggered-tab-examples-smoke.md`

Modified: none.

Deleted: none.

Generated artifacts: none.

## Tests And Checks

Commands run:

```text
git status --short
git branch --show-current
git rev-parse --short HEAD
git log --oneline -10
test -e docs/handoffs/task-completions/2026-06-18-12-answer-triggered-tab-examples-smoke.md && echo EXISTS || echo MISSING
rg -n "tab_examples|answer_tab|tabs|/api/tab/render|serve_v2_rerank|serve_answer_smoke|api/answer" pocketsteel ui tests docs/current-commands.md docs/private-preview-operations.md docs/handoffs/task-completions/2026-06-18-12-tab-engine-deploy-smoke-plan.md
sed -n '230,270p' pocketsteel/api.py
sed -n '260,335p' tests/test_tab_engine.py
sed -n '1,260p' docs/current-commands.md
sed -n '1,260p' docs/private-preview-operations.md
sed -n '1,260p' docs/handoffs/task-completions/2026-06-18-12-tab-engine-deploy-smoke-plan.md
sed -n '1,260p' pocketsteel/answer_tab_examples.py
git diff -- pocketsteel/api.py ui/answer-client.js ui/steel-guitar-rag-mock.html tests/test_frontend_answer_ui.py
git show --stat --oneline 54a28c7
git show --stat --oneline 7834c67
git diff -- pocketsteel/api.py
rg -n "tab_example|tabs|rendered_tab|tabText|tab_text|tab_example_payload" pocketsteel tests ui/answer-client.js ui/steel-guitar-rag-mock.html
sed -n '120,172p' pocketsteel/api_contract.py
rg -n "devAccessHeaders|X-|Steel|access" ui/answer-client.js pocketsteel/access_control.py tests/test_api_search.py
sed -n '1,120p' ui/answer-client.js
sed -n '200,250p' pocketsteel/access_control.py
```

Finish checks:

```text
git diff --check
git diff --cached --check
git diff --cached --name-only
git status --short
```

## Integration Notes

- The final Lane 05 answer payload contract is the highest-risk integration point.
- Current in-progress Lane 05 code appears to attach `payload["tab_example"]`; current committed frontend normalizes `payload.tabs` or top-level `payload.tab`.
- Post-Lane-05 smoke should explicitly capture raw answer JSON for one tab prompt before diagnosing browser rendering.
- `/api/tab/render` can isolate renderer health from `/api/answer` attachment and browser UI issues.
- Cloudflare Access coverage for `/api/tab/render` must be verified because route-level app auth is not currently present.

## Risk Assessment

Risk: medium for the future smoke target.

Why:

- Answer-triggered tabs add a new answer payload contract and UI rendering path.
- The in-progress payload key may not yet match the committed frontend normalizer.
- The public helper route `/api/tab/render` relies on hostname-level Cloudflare Access for protected-preview public exposure.
- The current worktree is dirty in runtime-affecting paths.

Rollback note:

- Restart from the previous known-good committed HEAD if protected preview regresses.
- Do not touch DNS, Cloudflare Access policy, Chroma, embeddings, corpus, source-inbox, private source data, scraping, Ollama, or visual assets during rollback.

## Human Decision Needed

No for this handoff.

Yes before actual protected-preview smoke if runtime files remain dirty: decide whether Lane 05/06 should commit/park first or whether Lane 12 is explicitly testing dirty runtime work.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-12-answer-triggered-tab-examples-smoke.md`

## Files That Must Not Be Staged

- `pocketsteel/*.py`
- `pocketsteel/answer_tab_examples.py`
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

Recommended next lane: `05 Backend / RAG Integration`, then `01 Repo Steward`, then `12 Self-Hosted Deployment`.

- Lane 05 should finish and test the answer-triggered deterministic tab example contract.
- Lane 01 should commit the exact approved implementation slice when ready.
- Lane 12 should run the recommended protected-preview smoke prompt only after a clean committed runtime state exists.

## Commit Readiness

Safe to commit only as an exact-path docs-only handoff if the staged diff contains only this file and `git diff --cached --check` passes.
