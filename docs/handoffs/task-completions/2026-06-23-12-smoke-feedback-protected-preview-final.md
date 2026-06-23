# Lane 12 smoke-feedback protected-preview final

## Pass / warn / fail

**Pass with warnings.**

Authenticated Cloudflare Access protected-preview browser smoke completed after the app LaunchDaemon was refreshed to the intended implementation commit `1c0bbd6`.

Warnings:

- Root `https://app.steelguitarrag.com/?v=1c0bbd6` redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string. The redirected root surface displayed older prompt-chip copy. Use the direct cache-busted `/ui/...?...` URL for smoke.
- `Show me a G major grip.` is fretboard-first and does not show a rendered tab/code block, but the fretboard detail exposes technical `tab_example_event` / `Tab event` wording. Route this learner-facing metadata leak to Lane 06 or Lane 05 depending on ownership of the payload/detail contract.
- Ab/A-flat prose normalizes correctly, but the fretboard card labels canonicalize the enharmonic chord as `G# major`. This is technically equivalent but may be a UX copy decision for Lane 06 / Lane 18.

API fallback was not used as browser-smoke proof.

## Task summary

Requested:

- Confirm Lane 15 QA approval for the smoke-feedback implementation state.
- Refresh the protected-preview runtime to the intended committed HEAD.
- Run authenticated Cloudflare Access browser smoke for the main app, Explorer, root behavior, and prompt matrix.

Completed:

- Confirmed Lane 15 QA passed with warning at `1c0bbd6`.
- Confirmed starting HEAD before runtime refresh was `1c0bbd6`.
- Confirmed the running runtime was stale at `ddd7953`.
- Restarted the launchd-supervised app process by terminating stale PID `72903`; launchd restarted it as PID `94266`.
- Confirmed `/api/version` reports `1c0bbd6` locally and through protected preview.
- Confirmed listener is Python on `127.0.0.1:8770`.
- Confirmed LaunchDaemon owns the app runtime.
- Confirmed manual `screen` runtime is absent.
- Confirmed Cloudflare Tunnel process is running.
- Ran authenticated protected-preview browser smoke at the exact cache-busted main app URL.
- Ran root behavior check.
- Ran Explorer direct-route and main-page click-through checks.
- Ran the full protected-preview answer prompt matrix.

Intentionally not changed:

- No backend/UI implementation files.
- No DNS, Cloudflare Access policy, tunnel config, auth settings, secrets, corpus, Chroma, embeddings, scraper output, private-source data, or source-inbox data.
- No API fallback was reported as protected-preview browser smoke.

## Lane 15 approval

Latest relevant QA handoff inspected:

- `docs/handoffs/task-completions/2026-06-23-15-main01-focused-smoke-feedback-qa.md`

Lane 15 result:

- Pass with warning.
- Current commit under QA: `1c0bbd6 fix: separate backstage and fretboard header actions`.
- Lane 15 explicitly recorded no remaining QA blocker for Lane 12, with protected-preview restart/smoke still required.
- Lane 15 warning: prior loopback runtime was stale at `ddd7953`, so Lane 12 had to restart/verify protected preview.

## Branch and commits

- Branch: `feature/answer-api`
- Starting implementation HEAD: `1c0bbd6`
- Current repo HEAD after blocked-smoke handoff commit: `cc884b2`
- Runtime commit expected: `1c0bbd6`
- Runtime commit reported after restart: `1c0bbd6`

Recent commits inspected:

```text
cc884b2 docs: record final smoke feedback protected preview
1c0bbd6 fix: separate backstage and fretboard header actions
2d3d662 fix: expose all explorer keys and backstage link
5031f43 fix: normalize accidentals and route flat-key string groupings
0c050ee fix: polish smoke feedback UI and explorer controls
```

## Runtime refresh evidence

Before refresh:

- `/api/version`: `git_sha=ddd7953`
- Listener PID: `72903`
- PID start time: `Tue Jun 23 13:18:17 2026`
- Runtime was stale relative to implementation HEAD `1c0bbd6`.

Restart path:

- `launchctl kickstart -k system/com.steelguitarrag.private-preview` failed with `Operation not permitted`.
- `deploy/macos/install-private-preview-launchdaemon.sh restart` failed because non-interactive `sudo` could not read a password.
- Because the process was stale and launchd supervision was active, stale user-owned PID `72903` was terminated with `SIGTERM`.
- LaunchDaemon restarted the app automatically as PID `94266`.

After refresh:

```json
{
  "git_sha": "1c0bbd6",
  "git_branch": "feature/answer-api",
  "server_started_at": "2026-06-23T19:54:06.883215+00:00",
  "python_module": "pocketsteel.api",
  "retrieval_mode": "hybrid_private_first",
  "auth_provider": "cloudflare_access"
}
```

Listener:

- PID: `94266`
- Start time: `Tue Jun 23 14:54:06 2026`
- Command: `scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 ... --answer-auth-mode production --auth-provider cloudflare-access`

LaunchDaemon:

- Label: `system/com.steelguitarrag.private-preview`
- State: running
- PID: `94266`
- Runs: `26`
- Program: `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`
- Repo env: `STEEL_RAG_REPO_DIR=/Users/cory/Documents/Pocket Steel`
- Host/port env: `STEEL_RAG_HOST=127.0.0.1`, `STEEL_RAG_PORT=8770`
- Logs:
  - `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
  - `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`

Manual screen runtime:

- `screen -ls`: no sockets found.

Cloudflare Tunnel:

- `com.cloudflare.cloudflared` LaunchDaemon is running.
- `cloudflared` process is present.
- Tunnel token contents were not copied into this handoff.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded after user completed login in the in-app browser.
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `1c0bbd6`
- Version endpoint: `/api/version`
- Version endpoint result: protected preview and local loopback both report `git_sha=1c0bbd6`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, but with cache-bust caveat.
- Whether app root `/` is expected to work: yes as a convenience redirect, but not as the only cache-busted smoke target.
- Whether `/ui/steel-guitar-rag-mock.html` works: yes.
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes.
- Who should test this URL: the user and Lane 12.
- Do not test these URLs: do not treat local `127.0.0.1` or unauthenticated API fallback as protected-preview browser smoke.
- Known caveats: root drops the query string; use direct `/ui/...?...` URLs for exact asset/version smoke.

## Exact URLs tested

- Main app: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`
- Explorer: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=1c0bbd6`
- Root: `https://app.steelguitarrag.com/?v=1c0bbd6`
- Protected version: `https://app.steelguitarrag.com/api/version`

## Main UI smoke

| Check | Status | Evidence |
|---|---|---|
| Cloudflare Access login | Pass | App shell loaded after user completed login. |
| Q&A/search visible and primary | Pass | Main app showed prompt textbox and Ask control. |
| `Go Backstage` exists | Pass | Button text `Go Backstage`; `aria-controls="backstage"`. |
| `Explore Fretboard` exists as separate upper-right control | Pass | Header link text `Explore Fretboard`. |
| Explorer link points to Explorer route | Pass | Link href `/ui/e9-fretboard-explorer.html`. |
| Explorer link opens Explorer route | Pass | Click-through loaded `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html`. |
| Old large Explorer callout styling gone | Pass | `Open Fretboard Explorer` / large callout copy absent on direct cache-busted main URL. |
| Removed prompt chip `Explain this lick like a steel player would` absent | Pass | Not present. |
| Removed prompt chip `Show me a smoother turnaround` absent | Pass | Not present. |
| Visible prompt chips are self-contained | Pass | Direct cache-busted main URL showed current self-contained prompt chips. |
| Console/page errors | Pass | No relevant browser console errors captured. |

Root behavior:

- `https://app.steelguitarrag.com/?v=1c0bbd6` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Query string was dropped.
- The redirected root surface displayed older prompt-chip copy.
- Use `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6` for exact cache-busted user smoke.

## Prompt matrix results

| # | Prompt | Status | Evidence |
|---|---|---|---|
| 1 | `Show me an A-flat major string grouping.` | Pass with caveat | No generic fallback. Direct Ab prose. Fretboard rendered. No warnings. No code/tab block. Caveat: fretboard labels canonicalize enharmonically as `G# major`. |
| 2 | `Show me an A♭ major string grouping.` | Pass with caveat | Same as A-flat. No generic fallback. Fretboard rendered. No source cards. No warnings. Caveat: `G# major` fretboard labels. |
| 3 | `Show me an Ab major string grouping.` | Pass with caveat | Same as A-flat. No generic fallback. Fretboard rendered. No source cards. No warnings. Caveat: `G# major` fretboard labels. |
| 4 | `Show me C♯ major on E9.` | Pass | No generic fallback. C# major deterministic answer. Fretboard rendered. No source cards, warning, or tab block. |
| 5 | `Show me C# major on E9.` | Pass | Same as C-sharp symbol prompt. No generic fallback. Fretboard rendered. |
| 6 | `Show me a G harmonized scale.` | Pass | No generic fallback. Static fretboard-first answer. No source cards, warning, or tab block. Includes F# diminished m7b5 guard text. |
| 7 | `Show me a G natural minor harmonized scale.` | Pass | No generic fallback. Static fretboard-first answer. No source cards, warning, or tab block. Includes A diminished m7b5 guard text. |
| 8 | `Show me the F# diminished position in G.` | Pass | No generic fallback. Fretboard rendered. No source cards, warning, or tab block. Explicitly says diminished triad, not full F#m7b5. |
| 9 | `Show me the A diminished position in G minor.` | Pass | No generic fallback. Fretboard rendered. No source cards, warning, or tab block. Explicitly says diminished triad, not full Am7b5. |
| 10 | `Show me a G harmonized scale on strings 5 and 8.` | Pass | No generic fallback. Static 5&8 branch answer. No source cards, warning, or tab block. Includes corrected 13th-fret E-lower branch. |
| 11 | `Show me a G major grip.` | Warn | Fretboard-first and no rendered tab/code block. However visible fretboard details expose `tab_example_event` / `Tab event` wording, which violates the no-internal-metadata expectation. |
| 12 | `Show me a G to C move.` | Pass | Movement prompt rendered deterministic tab plus matching fretboard. No source cards or warning. |
| 13 | `Give me a beginner lick in G.` | Pass | Beginner lick rendered direct prose, deterministic tab, and matching fretboard. A+B action uses strings 5 and 6, not string 8. |
| 14 | `Give me the full tab for a modern copyrighted song.` | Pass | Refused/redirected safely. No source cards, warnings, or rendered tab block. No answer-body routing to a source answer. |
| 15 | `What are good Fender Steel King settings?` | Pass | Gear answer rendered normally with source cards. No stale tab block and no stale fretboard answer payload. |

Shared prompt checks:

- No `[object Object]` appeared.
- No generic fallback appeared.
- No relevant console/page errors appeared.
- Deterministic grip/exercise answers were source-free where expected.
- Gear answer remained source-backed where expected.
- Copyright/full-tab request refused safely.

## Explorer smoke

Exact URL:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=1c0bbd6`

| Check | Status | Evidence |
|---|---|---|
| Explorer loads through Cloudflare Access | Pass | Page title `E9 Fretboard Explorer - Steel Guitar RAG`. |
| Multiple string groups can be selected | Pass | Selected `3-4-5` and `4-5-6` together; rows filtered to those groups. |
| 5&8 branch positions grouped with 2-string harmonized scale | Pass | Harmony option text `5&8 branch positions (2-string)`. |
| 5&8 branch mode rows | Pass | Fret 6 A+E-raise, fret 8 E-lower, fret 11 A+E-raise, and fret 13 E-lower rows visible. |
| Advanced swaps explanation | Pass | Learner-facing advanced swaps / E-lower pocket copy visible. |
| Internal validation/RAG copy | Pass | No `RAG-generated`, `corpus retrieval`, or raw internal branch id leak. |
| m7b5 / vii / partial / degree symbol help text | Pass | Glossary/help text visible for diminished and half-diminished concepts. |
| Starter/common/advanced filters | Pass | No standalone confusing filter controls exposed; core and advanced groups are separated. |
| All pitch classes in key selector | Pass | Key selector includes `C`, `C#`, `Db`, `D`, `D#`, `Eb`, `E`, `F`, `F#`, `Gb`, `G`, `G#`, `Ab`, `A`, `A#`, `Bb`, `B`. |
| No raw `five_eight_branch` label leak | Pass | Not visible. |
| No `E-lower+E-lower` | Pass | Not visible. |
| No `[object Object]` | Pass | Not visible. |
| Console/page errors | Pass | No relevant browser console errors captured. |

## Checks run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -10 --oneline`
- `git diff --name-only`
- `git diff --cached --name-only`
- `launchctl print system/com.steelguitarrag.private-preview`
- `deploy/macos/install-private-preview-launchdaemon.sh status`
  - blocked by non-interactive `sudo`
- `deploy/macos/install-private-preview-launchdaemon.sh version`
- `curl -sS http://127.0.0.1:8770/api/version || true`
- `lsof -nP -iTCP:8770 -sTCP:LISTEN || true`
- `ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command || true`
- `screen -ls || true`
- `launchctl print system/com.cloudflare.cloudflared`
- `pgrep -fl cloudflared || true`
- `git diff --check`
- Browser navigation to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=1c0bbd6`
- Browser navigation to `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=1c0bbd6`
- Browser navigation to `https://app.steelguitarrag.com/?v=1c0bbd6`
- Browser navigation to `https://app.steelguitarrag.com/api/version`

## Files changed

- Updated `docs/handoffs/task-completions/2026-06-23-12-smoke-feedback-protected-preview-final.md`.

No implementation files were changed.

## Risks

Risk: low to medium.

Reasons:

- Runtime is current at `1c0bbd6`.
- Protected-preview browser smoke completed through Cloudflare Access.
- Most functional checks passed.
- Remaining warnings are smoke UX/copy concerns, not runtime blockers.

Remaining risks:

- Root redirect drops cache-bust and can show stale prompt-chip copy.
- Static G major grip answer exposes `tab_example_event` / `Tab event` technical detail.
- Ab/A-flat fretboard labels use enharmonic `G# major` labels while prose uses Ab.

## Blockers

No runtime/deployment blocker remains.

Potential product/UX follow-ups:

- Lane 06 / Lane 05: hide or avoid `tab_example_event` / `Tab event` technical wording for static grip fretboard details.
- Lane 06 / Lane 18: decide whether Ab/A-flat fretboard cards should display requested flat spelling instead of enharmonic `G# major`.
- Lane 12 / Lane 06: decide whether root redirect should preserve query strings to avoid stale root smoke.

## Human decision needed

No for Lane 12 runtime readiness.

Optional decisions:

- Whether the warning items above should block user smoke or be routed as follow-up UX bugs.

## Safe-to-stage files

- `docs/handoffs/task-completions/2026-06-23-12-smoke-feedback-protected-preview-final.md`

## Files that must remain unstaged

- All unrelated modified and untracked worktree files.
- Backend/UI implementation files.
- Deployment/launchd scripts and plists.
- Cloudflare Access, DNS, tunnel, auth, and secret files.
- Corpus, Chroma/vector stores, embeddings, scraper output, source-inbox, private-source files, and generated data.
- Brand/design assets and unrelated handoffs.

## Recommended next lane

Lane 01 Repo Steward.

Recommended next prompt:

```text
Lane 01: Refresh integration-status.md after Lane 12 completed protected-preview smoke at runtime 1c0bbd6. Record pass-with-warnings, preserve unrelated dirty work, and stage only the integration-status refresh.
```

If the warning items should be fixed before user smoke, route them first:

- Lane 06 for root/query-string UX, stale prompt-chip presentation, and visible internal `tab_example_event` wording.
- Lane 18 if the Ab/G# enharmonic display needs a product policy decision.

## Commit readiness

Safe to commit as a docs-only protected-preview smoke handoff update.
