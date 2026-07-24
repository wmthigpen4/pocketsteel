# Lane 12 - Explorer SVG Selected-Group Protected Smoke

## Task Summary

Requested Lane 12 protected-preview verification for `17f2b55 fix: render selected explorer groups on fretboard`.

Completed:
- Confirmed current branch and HEAD.
- Found the launchd-supervised protected-preview runtime was initially stale at `65ac86a`.
- Refreshed the launchd-supervised runtime by terminating the stale `127.0.0.1:8770` listener and allowing the LaunchDaemon to restart it.
- Verified local `/api/version` reports `17f2b55`.
- Verified authenticated protected-preview browser smoke for the E9 Fretboard Explorer selected-group SVG rendering.
- Verified root and canonical app URL behavior.
- Ran prompt spot-checks for static grip, movement, copyright refusal, and gear answers.
- Left unrelated dirty and untracked work untouched.

Intentionally not changed:
- No backend/UI product logic.
- No corpus, embeddings, Chroma/vector stores, scraping output, auth policy, DNS, Cloudflare Access policy, or private source data.
- No unrelated parked files.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=17f2b55`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=17f2b55`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=17f2b55`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; authenticated browser session loaded the Explorer, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `17f2b55`
- Version endpoint: `/api/version`
- Version endpoint result:

```json
{
  "git_sha": "17f2b55",
  "git_branch": "feature/answer-api",
  "server_started_at": "2026-06-24T00:38:23.859793+00:00",
  "python_module": "steel_guitar_rag.api",
  "retrieval_mode": "hybrid_private_first",
  "auth_provider": "cloudflare_access"
}
```

- Whether app root `/` works: yes, root redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes, as a redirect to the canonical app shell
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: bare localhost as proof of protected-preview behavior; API fallback as proof of browser behavior
- Known caveats: root `/?v=17f2b55` redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string.

## Runtime And LaunchDaemon Evidence

- Branch: `feature/answer-api`
- Starting HEAD: `17f2b55`
- Runtime before refresh: stale at `65ac86a`
- Runtime after refresh: `17f2b55`
- Listener: Python on `127.0.0.1:8770`
- Listener PID after refresh: `52698`
- PID start time: `Tue Jun 23 19:38:23 2026`
- LaunchDaemon: `system/com.steelguitarrag.private-preview`
- LaunchDaemon state: running
- LaunchDaemon program: `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`
- LaunchDaemon runs: `34`
- Logs:
  - stdout: `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
  - stderr: `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`
- Cloudflare Tunnel status: `cloudflared` process present (`pgrep -x cloudflared` returned PID `677`; tunnel token/arguments were not printed)
- `deploy/macos/install-private-preview-launchdaemon.sh status`: could not run non-interactively because sudo required a terminal/password
- `deploy/macos/install-private-preview-launchdaemon.sh version`: succeeded and reported `17f2b55`

## Protected Preview Browser Results

### Explorer Route

- URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=17f2b55`
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`
- H1: `E9 Fretboard Explorer`
- Cloudflare Access: authenticated session succeeded
- Script cache-busts observed:
  - `/ui/pedal-steel-fretboard.js?v=selected-svg-render-20260623`
  - `/ui/e9-fretboard-explorer-data.js?v=selected-svg-render-20260623`
  - `/ui/e9-fretboard-explorer.js?v=selected-svg-render-20260623`
- Console/page errors: none reported by the in-app browser dev log
- `[object Object]`: not present
- Raw `five_eight_branch`: not present in visible body text

### Selected String-Row And SVG Marker Checks

The Explorer SVG exposes one `.pedal-steel-fretboard__highlight` group per visible card and one `data-highlight-dot` rect per selected string. Counts below came from the authenticated protected-preview DOM.

| State | Card count | SVG highlight count | Dot count | Dot strings | Result groups | Highlight groups | Result |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| G major, 3-string, `5-6-8` | 5 | 5 | 15 | `5,6,8` | `5-6-8` | `5-6-8` | Pass |
| G major, 3-string, `6-8-10` | 5 | 5 | 15 | `6,8,10` | `6-8-10` | `6-8-10` | Pass |
| A major, 3-string, `6-8-10` | 5 | 5 | 15 | `6,8,10` | `6-8-10` | `6-8-10` | Pass |
| G major, 2-string, `5-8` | 4 | 4 | 8 | `5,8` | `5-8` | `5-8` | Pass |

Result: selected string-row lanes passed. Cards, selected row list, SVG highlight groups, and per-string marker dots stayed in sync when switching groups and switching 2-string/3-string modes.

## App And Root Checks

### Canonical App URL

- URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=17f2b55`
- Result: app shell loaded
- Q&A input: unlocked
- Header entry: `Explore Fretboard`
- Explorer link target: `/ui/e9-fretboard-explorer.html`
- Console/page errors: none reported
- `[object Object]`: not present

### Root URL

- URL tested: `https://app.steelguitarrag.com/?v=17f2b55`
- Final URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- Result: root redirects to the canonical app shell and drops the query string
- Q&A input: unlocked after redirect
- Console/page errors: none reported

## Prompt Spot-Checks

| Prompt | Result |
| --- | --- |
| `Show me a G major grip.` | Pass. Direct prose appeared, fretboard visible, one fretboard highlight, no tab card, no fallback, no `[object Object]`. |
| `Show me a G to C move.` | Pass. Direct prose appeared, tab card visible, fretboard visible with two highlights, no fallback, no `[object Object]`. |
| `Give me the full tab for a modern copyrighted song.` | Pass. Clear copyright/refusal answer, no tab card, no fretboard, no fallback, no `[object Object]`. |
| `What are good Fender Steel King settings?` | Pass. Gear answer rendered normally with source cards, no tab card, no fretboard, no stale payload. |

## Tests And Checks Run

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -10 --oneline
git diff --name-only
git diff --cached --name-only
curl -sS http://127.0.0.1:8770/api/version
lsof -nP -iTCP:8770 -sTCP:LISTEN
ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command
launchctl print system/com.steelguitarrag.private-preview
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh version
pgrep -x cloudflared | sed 's/^/cloudflared pid: /'
git diff --check
```

Results:
- `git diff --check`: passed.
- Local `/api/version`: passed and reports `17f2b55`.
- LaunchDaemon print: running.
- LaunchDaemon status helper: blocked by non-interactive sudo.
- LaunchDaemon version helper: passed and reports `17f2b55`.
- Protected-preview browser smoke: pass.

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-23-12-explorer-svg-selected-group-protected-smoke.md`

No implementation files changed.

## Risks

Risk level: low.

Rationale:
- Verification-only Lane 12 handoff.
- Runtime refresh used launchd supervision by terminating the stale listener and allowing the existing LaunchDaemon to restart it.
- No product logic, auth, DNS, tunnel config, corpus, Chroma, embeddings, or private data changed.

Remaining operational caveat:
- The install/status helper requires interactive sudo for `status` in this environment. Runtime health was verified with `launchctl print`, `lsof`, `ps`, and `/api/version`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-explorer-svg-selected-group-protected-smoke.md`

## Files That Must Not Be Staged

- Unrelated modified files already present before this task, including `README.md`, corpus metadata docs/JSON, RAG helper scripts, source-inbox inventory files, UI brand assets, generated reports, and all untracked parked handoffs/assets/data.
- Any corpus, Chroma/vector store, embeddings, scraper output, private-source, credential, token, env, DNS, Cloudflare Access, or tunnel files.

## Recommended Next Lane

Lane 01 Repo Steward or integration-status refresh if the team wants this protected-preview pass recorded in the coordination file.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 01: refresh `docs/handoffs/task-completions/integration-status.md` with `17f2b55` and this Lane 12 protected-preview pass, or proceed to user smoke using `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=17f2b55`.
