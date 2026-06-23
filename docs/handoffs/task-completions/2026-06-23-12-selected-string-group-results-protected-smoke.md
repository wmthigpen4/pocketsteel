# Lane 12 - Selected String Group Results Protected Smoke

## Task Summary

Requested Lane 12 protected-preview verification for `65ac86a fix: show selected explorer string group results`.

Completed:
- Confirmed repo HEAD is `65ac86a`.
- Found the launchd-supervised protected-preview runtime was stale at `283468b`.
- Refreshed the existing LaunchDaemon-owned app process and verified `/api/version` now reports `65ac86a`.
- Verified the Explorer through Cloudflare Access with the cache-busted protected URL.
- Verified the selected-results strip, selected string-group row list, SVG highlights, filter switching, main app header actions, root redirect behavior, and optional prompt spot checks.

Intentionally not changed:
- No backend/UI/product code.
- No DNS, Cloudflare Access policy, tunnel config, secrets, corpus, Chroma/vector stores, embeddings, scraping, source-inbox, private-source, or transcript data.
- No API fallback was used as protected-preview browser-smoke proof.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=65ac86a`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=65ac86a`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=65ac86a`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; browser was already authenticated and did not land on the Access login page.
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `65ac86a`
- Version endpoint: `/api/version`
- Version endpoint result: `git_sha=65ac86a`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`, `server_started_at=2026-06-23T23:22:53.017617+00:00`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, it redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes, as a redirect to the canonical app page
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both Codex and the user
- Do not test these URLs: stale cache-bust URLs from previous Explorer slices
- Known caveats: root redirects to `/ui/steel-guitar-rag-mock.html` and drops query strings; use direct `/ui/...?...` URLs when exact cache-busting matters.

## Runtime And Deployment Evidence

- Branch: `feature/answer-api`
- Starting HEAD: `65ac86a`
- Runtime expected: `65ac86a`
- Runtime before refresh: `283468b`
- Runtime after refresh: `65ac86a`
- Listener: Python process on `127.0.0.1:8770`
- Listener PID after refresh: `21021`
- Listener start time: `Tue Jun 23 18:22:52 2026`
- LaunchDaemon: `com.steelguitarrag.private-preview` running
- LaunchDaemon runs count after refresh: `33`
- App command: `scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 ... --answer-auth-mode production --auth-provider cloudflare-access`
- Manual `screen` runtime: absent (`screen -ls` reported no sockets)
- Cloudflare Tunnel: `cloudflared` process present (`pid 677`); token contents intentionally not recorded

Restart notes:
- `launchctl kill TERM system/com.steelguitarrag.private-preview` was not permitted from this session.
- Killing the existing user-owned listener PID allowed launchd to restart the service, after which `/api/version` reported `65ac86a`.
- `deploy/macos/install-private-preview-launchdaemon.sh status` could not complete non-interactively because `sudo` required a password.

## Explorer Browser Smoke

URL tested:
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=65ac86a`

Result: Pass.

Observed:
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`
- Cloudflare Access login: succeeded/already authenticated
- Fresh script cache-busts:
  - `pedal-steel-fretboard.js?v=selected-group-results-20260623`
  - `e9-fretboard-explorer-data.js?v=selected-group-results-20260623`
  - `e9-fretboard-explorer.js?v=selected-group-results-20260623`
- Stale Explorer cache-busts from earlier slices were not present.
- No `[object Object]`.
- No visible raw `five_eight_branch` label.
- No browser console errors recorded.

## Selected String-Group Results

Primary target:
- Key: `A`
- Scale: `major`
- Harmony/view: `3-string diatonic harmony`
- String group: `6-8-10`

Result: Pass.

Observed:
- Selected-results strip appeared above the SVG.
- Strip header: `6-8-10: 5 visible positions`
- Visible row-list entries: `5`
- SVG highlights: `5`
- Row list included explicit string group labels.
- Every visible row-list entry included `6-8-10`.
- Selected detail panel included `String group 6-8-10`.

Sample row labels:
- `5 I - 6-8-10 - Core grip - 10: E; 6: C#; 8: A`
- `10 IV - 6-8-10 - Core grip - 10: A; 6: F#; 8: D`
- `12 V - 6-8-10 - Core grip - 10: B; 6: G#; 8: E`
- `15 vii° / partial viiø - E-raise - 6-8-10 - Core grip - 10: D; 6: B; 8: G#`
- `17 I - 6-8-10 - Core grip - 10: E; 6: C#; 8: A`

## Filter Switching Checks

Result: Pass.

| State | Visible rows | SVG highlights | Header/result |
| --- | ---: | ---: | --- |
| A major / 3-string / `6-8-10` | 5 | 5 | `6-8-10: 5 visible positions` |
| A major / 3-string / `5-6-8` | 5 | 5 | `5-6-8: 5 visible positions` |
| A major / 3-string / `6-8-10` again | 5 | 5 | `6-8-10: 5 visible positions` |
| A major / 2-string / all | 40 | 40 | `all 2-string groups: 40 visible positions` |
| A major / 3-string after switch back | 34 | 34 | `all 3-string groups: 34 visible positions` |
| G major / 2-string / all | 44 | 44 | `all 2-string groups: 44 visible positions` |
| G major / 2-string / `5-8` | 4 | 4 | `5-8: 4 visible positions` |

Additional filter notes:
- `5-8` appeared under `2-string groups` for G major.
- No separate `5&8` branch optgroup/family appeared.
- No visible raw `five_eight_branch` label appeared.
- Switching `5-6-8` ↔ `6-8-10` stayed non-empty.
- Switching `2-string` ↔ `3-string` stayed non-empty.

## Main App And Root Smoke

Canonical app URL tested:
- `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=65ac86a`

Root URL tested:
- `https://app.steelguitarrag.com/?v=65ac86a`

Result: Pass.

Observed:
- Canonical app page loaded through Cloudflare Access.
- `Explore Fretboard` and `Get a Backstage Pass`/`Go Backstage` remained separate header actions.
- `Explore Fretboard` link target: `/ui/e9-fretboard-explorer.html`
- Clicking `Explore Fretboard` opened the Explorer route.
- Header button style remained at the accepted restored behavior:
  - Font family: `"Gill Sans", "Gill Sans MT", "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif`
  - Font size: `16px`
  - Font weight: `400`
  - Text transform: `none`
- Root redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html` and dropped the query string.
- No `[object Object]`.
- No browser console errors recorded.

## Prompt Spot Checks

These were optional browser checks through the protected-preview app UI, not API fallback.

| Prompt | Result | Notes |
| --- | --- | --- |
| `Show me a G major grip.` | Pass | Direct prose appeared. Fretboard/SVG rendered. One visible position card. No visible tab block. No generic fallback. |
| `Show me a G to C move.` | Pass | Direct prose appeared. Deterministic tab block rendered. Fretboard/SVG rendered with two visible position cards. No generic fallback. |
| `Give me the full tab for a modern copyrighted song.` | Pass | Refused full copyrighted song tab. No tab block. No fretboard. No generic fallback. |

Source-note caveat:
- Source-free responses still render the UI's `Source notes / No sources returned` section. This was not treated as a populated source-card leak.

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-23-12-selected-string-group-results-protected-smoke.md`

Modified implementation files:
- None

Deleted files:
- None

Generated artifacts:
- None

## Tests And Checks Run

- `git status --short` - reviewed; unrelated dirty and untracked files remain parked.
- `git branch --show-current` - `feature/answer-api`
- `git rev-parse --short HEAD` - `65ac86a`
- `git log -10 --oneline` - reviewed; intended HEAD `65ac86a`.
- `git diff --name-only` - reviewed parked dirty files.
- `git diff --cached --name-only` - empty before handoff staging.
- `launchctl print system/com.steelguitarrag.private-preview` - confirmed service running.
- `deploy/macos/install-private-preview-launchdaemon.sh status` - could not complete because non-interactive sudo required a password.
- `deploy/macos/install-private-preview-launchdaemon.sh version` - before refresh showed stale `283468b`.
- `curl -sS http://127.0.0.1:8770/api/version` - after refresh reported `65ac86a`.
- `lsof -nP -iTCP:8770 -sTCP:LISTEN` - confirmed Python listener on `127.0.0.1:8770`.
- `ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command` - confirmed PID `21021` and start time.
- `screen -ls` - no sockets.
- Cloudflare Tunnel process check - `cloudflared` process present; token not recorded.
- Browser smoke at protected Explorer URL - pass.
- Browser smoke at protected app URL - pass.
- Browser smoke at protected root URL - pass, redirects to canonical app page.
- Optional protected-preview prompt spot checks - pass.
- `git diff --check` - pass.

Skipped:
- Full pytest was not run because this task was protected-preview runtime/browser verification and no implementation files were changed.

## Integration Notes

- Protected preview is now serving runtime commit `65ac86a`.
- The selected string-group result strip and selected row rendering fix is verified through Cloudflare Access.
- The direct cache-busted Explorer URL should be used for user smoke: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=65ac86a`
- Root remains usable as an entry point but not as a reliable cache-bust URL because it redirects and drops query strings.

## Risk Assessment

Risk: Low.

Reason:
- Only a docs handoff was created.
- Runtime action was limited to refreshing a stale launchd-supervised protected-preview process so it served the already-committed HEAD.
- No product logic, data, auth policy, DNS, tunnel configuration, Chroma/vector stores, corpus, embeddings, or scraping state was modified.

Rollback:
- If protected preview must be returned to a prior runtime, restart the launchd service from the desired committed checkout. No code rollback was performed by this task.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-selected-string-group-results-protected-smoke.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files, including:
- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/*`
- `public/brand/*`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- scraper output
- credentials or env files
- any untracked parked handoffs/assets not named in the safe-to-stage list

## Recommended Next Lane

Lane 01 Repo Steward if integration status should be refreshed after this protected-preview pass.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 01: refresh `docs/handoffs/task-completions/integration-status.md` with the `65ac86a` selected string-group results protected-preview pass, preserving unrelated parked work.
