# 2026-06-30 21:16 Lane 12 - Parameterized Movement Cards Protected Smoke

## Task Summary

Requested Lane 12 protected-preview restart and browser smoke for Parameterized Movement Cards v1.

Completed:

- Verified repo branch and HEAD.
- Confirmed current repo HEAD `e449180` contains app-code commit `254752a`.
- Verified the LaunchDaemon-supervised protected-preview runtime was stale at `e37f00e`.
- Restarted the normal protected-preview runtime by terminating the stale `127.0.0.1:8770` listener and allowing `com.steelguitarrag.private-preview` to restart it.
- Verified local `/api/version` now reports `e449180`.
- Ran authenticated protected-preview browser smoke through Cloudflare Access at the exact cache-busted URL.
- Captured representative screenshots for movement, static fretboard-first, and Steel King settings cases.
- Refreshed `docs/handoffs/task-completions/integration-status.md`.

Intentionally not changed:

- No backend or UI implementation files.
- No DNS, Cloudflare Access policy, auth configuration, tunnel configuration, secrets, deployment architecture, corpus, scraping, embeddings, Chroma/vector stores, private transcripts, licensing metadata, or unrelated assets.
- No API fallback was used as proof of browser behavior.

## Smoke Target

- Target type: protected-preview browser smoke
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=parameterized-movement-cards-254752a`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=parameterized-movement-cards-254752a`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=parameterized-movement-cards-254752a`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; app shell loaded in the authenticated browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected repo HEAD: `e449180`
- Required app-code commit: `254752a`
- Version endpoint: `/api/version`
- Version endpoint result: local origin returned `{"git_sha":"e449180","git_branch":"feature/answer-api","server_started_at":"2026-07-01T04:13:03.378070+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- Protected browser `/api/version` caveat: direct browser navigation to `https://app.steelguitarrag.com/api/version` was blocked by the browser environment with `net::ERR_BLOCKED_BY_CLIENT`; local origin version proof plus authenticated protected browser smoke were recorded
- Whether app root `/` works: yes, but it redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as a redirect, not as the exact cache-busted target
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes; this remains the canonical cache-busted smoke URL
- API fallback status: not used
- Who should test this URL: the user may user-smoke the exact URL above
- Do not test these URLs: root-only URL when exact cache-busting matters, because root drops the query string during redirect
- Known caveats: root `https://app.steelguitarrag.com/?v=parameterized-movement-cards-254752a` redirects to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html` and drops the query string

## Runtime Restart Evidence

Before restart:

- `/api/version`: `e37f00e`
- Listener PID: `10945`
- Listener command: `scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 ... --answer-auth-mode production --auth-provider cloudflare-access`
- LaunchDaemon: `system/com.steelguitarrag.private-preview`, state `running`

Restart action:

- Terminated stale listener PID `10945`.
- LaunchDaemon restarted the process automatically.

After restart:

- `/api/version`: `e449180`
- Listener PID: `47454`
- Start time: `Tue Jun 30 21:13:02 2026`
- `server_started_at`: `2026-07-01T04:13:03.378070+00:00`
- Branch: `feature/answer-api`
- Auth provider: `cloudflare_access`
- Retrieval mode: `hybrid_private_first`

## Prompt Results

| Prompt | Result | Browser observations |
| --- | --- | --- |
| `Show me a G to C move.` | PASS | Direct original G I-IV prose, compact deterministic tab, matching fretboard payload, fixed-width tab spacing, no source cards. |
| `Show me a G to D move.` | PASS | Direct original G I-V prose, deterministic tab with G to D events, matching fretboard payload, no source cards. |
| `Show me a 1 to 4 move in G.` | PASS | Routed to G I-IV movement; direct prose, tab, and matching fretboard. |
| `Show me a 1 to 5 move in G.` | PASS | Routed to G I-V movement; direct prose, tab, and matching fretboard. |
| `Show me a 1 4 5 1 move in G.` | PASS | Routed to G I-IV-V-I movement; four-event deterministic tab and matching fretboard cards. |
| `How do I connect no-pedals to A+B positions?` | PASS | Defaults to G, explains that default, shows G I-IV movement, deterministic tab, and matching fretboard. |
| `Show me a G major grip.` | PASS | Static fretboard-first answer with G major 4-5-6 grip; no visible tab block by default. |
| `Where is G on E9?` | PASS | Defaults to full G major starter positions; first selected card is a full G major grip, not 5-7-8 open; no visible tab block. |
| `Show me a 5-7-8 G grip.` | PASS | Explicit 5-7-8 request remains partial/color/no-3rd; no inert A+B; no visible tab block. |
| `What are good Fender Steel King settings?` | PASS | Concrete Buddy Emmons Steel King settings block with source notes; no safety/electrical boilerplate; stale tab/fretboard shells remained hidden. |

Additional checks:

- No generic `I need a more specific steel-guitar question` fallback appeared for movement prompts.
- Movement tab blocks used monospace font family and `white-space: pre`.
- Deterministic movement examples displayed `No sources returned`; no source cards were shown as supporting deterministic examples.
- Static prompts stayed fretboard-first and did not show a visible tab block.
- The Steel King settings prompt showed source-backed answer notes and did not display stale tab/fretboard content.
- No visible `[object Object]`.
- Browser console warnings/errors: none recorded.

## Screenshots

- `docs/handoffs/task-completions/assets/2026-06-30-parameterized-movement-cards-protected-smoke/protected-1451-movement-tab-fretboard.png`
- `docs/handoffs/task-completions/assets/2026-06-30-parameterized-movement-cards-protected-smoke/protected-static-g-major-fretboard-first.png`
- `docs/handoffs/task-completions/assets/2026-06-30-parameterized-movement-cards-protected-smoke/protected-steel-king-settings.png`

## Files Changed

- `docs/handoffs/task-completions/2026-06-30-2116-12-parameterized-movement-cards-protected-smoke.md`
- `docs/handoffs/task-completions/assets/2026-06-30-parameterized-movement-cards-protected-smoke/protected-1451-movement-tab-fretboard.png`
- `docs/handoffs/task-completions/assets/2026-06-30-parameterized-movement-cards-protected-smoke/protected-static-g-major-fretboard-first.png`
- `docs/handoffs/task-completions/assets/2026-06-30-parameterized-movement-cards-protected-smoke/protected-steel-king-settings.png`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files:

- None.

Generated artifacts:

- Three protected-preview smoke screenshots listed above.

## Tests And Checks

- `git status --short` - run before and after; broad unrelated dirty/untracked work remains parked.
- `git branch --show-current` - `feature/answer-api`.
- `git rev-parse --short HEAD` - `e449180`.
- `git log --oneline -5` - confirmed `e449180` after `254752a`.
- `git merge-base --is-ancestor 254752a HEAD` - PASS, runtime HEAD contains required app-code commit.
- `git status --short -- 'steel_guitar_rag/*.py' 'ui/*.js' 'scripts/*.py' tests` - no dirty runtime-affecting files.
- `curl -sS http://127.0.0.1:8770/api/version` before restart - stale `e37f00e`.
- `lsof -nP -iTCP:8770 -sTCP:LISTEN` before restart - PID `10945`.
- `launchctl print system/com.steelguitarrag.private-preview` - state `running`.
- Terminated stale listener PID `10945`; launchd restarted the app.
- `curl -sS http://127.0.0.1:8770/api/version` after restart - PASS, `e449180`.
- `lsof -nP -iTCP:8770 -sTCP:LISTEN` after restart - PID `47454`.
- Protected-preview browser smoke through Cloudflare Access - PASS.
- Browser root check at `https://app.steelguitarrag.com/?v=parameterized-movement-cards-254752a` - redirected to `/ui/steel-guitar-rag-mock.html` and dropped query string.
- Direct UI check at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=parameterized-movement-cards-254752a` - PASS.
- Browser console warning/error read - none recorded.
- `git diff --check` - PASS.

Skipped:

- No implementation tests were rerun in Lane 12 because this task changed no app code. Lane 05 recorded focused and full local test pass for the implementation.
- API fallback was not used.

## Integration Notes

- Protected preview is now serving repo/runtime HEAD `e449180`, which contains `254752a`.
- Parameterized Movement Cards v1 is ready for user smoke at the direct cache-busted `/ui` URL.
- Root remains a redirect and drops query strings; do not use root when exact cache-busting matters.
- The UI still includes hidden tab/fretboard shell elements for non-matching responses, but browser-visible content correctly hides stale tab/fretboard state for the Steel King prompt.

## Risk Assessment

Risk: low.

Why:

- Lane 12 only restarted the existing LaunchDaemon-supervised app and wrote docs/screenshots.
- Browser smoke passed through Cloudflare Access.
- No app implementation, auth, DNS, tunnel, corpus, Chroma/vector, scraping, private transcript, licensing, or secret files were changed.

Rollback:

- If needed, revert the docs-only smoke commit.
- Runtime rollback would require restarting the LaunchDaemon from a prior checked-out commit; no rollback was needed during this task.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-30-2116-12-parameterized-movement-cards-protected-smoke.md`
- `docs/handoffs/task-completions/assets/2026-06-30-parameterized-movement-cards-protected-smoke/protected-1451-movement-tab-fretboard.png`
- `docs/handoffs/task-completions/assets/2026-06-30-parameterized-movement-cards-protected-smoke/protected-static-g-major-fretboard-first.png`
- `docs/handoffs/task-completions/assets/2026-06-30-parameterized-movement-cards-protected-smoke/protected-steel-king-settings.png`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Existing unrelated parked dirty/untracked files in `README.md`, `corpus_metadata/`, `docs/`, `rag_*.py`, `source-inbox/`, `ui/brand/`, `public/brand/`, `Neon Sign/`, corpus/private/vector/scraper/auth/deploy/source-data paths, and generated/private artifacts.
- Existing untracked enhanced-learning-card handoff/screenshots from prior work unless a separate task explicitly scopes them.

## Recommended Next Lane

Lane 01 only if further integration-status or release coordination is needed after user smoke. Otherwise user smoke can proceed.

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke:

```text
Open https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=parameterized-movement-cards-254752a

Smoke:
- Show me a G to C move.
- Show me a G to D move.
- Show me a 1 to 4 move in G.
- Show me a 1 to 5 move in G.
- Show me a 1 4 5 1 move in G.
- How do I connect no-pedals to A+B positions?
- Show me a G major grip.
- Where is G on E9?
- Show me a 5-7-8 G grip.
- What are good Fender Steel King settings?
```
