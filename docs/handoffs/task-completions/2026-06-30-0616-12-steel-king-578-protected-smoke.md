# Steel King Settings And 5-7-8 Protected Preview Smoke

## Task Summary

Lane 12 restarted and verified the protected-preview runtime at `e37f00e`, then ran authenticated protected-preview browser smoke for:

- `c635dd5 fix: correct e9 5-7-8 grip classification`
- `e37f00e fix: add source-backed steel king settings answer`

Completed:

- Confirmed branch `feature/answer-api`.
- Confirmed repo `HEAD` is `e37f00e`.
- Confirmed starting protected runtime was stale at `0406b1c`.
- Restarted the normal LaunchDaemon-supervised private-preview app by terminating the stale app listener PID and letting launchd `KeepAlive` restart the configured wrapper.
- Confirmed `/api/version` now reports `e37f00e`.
- Ran authenticated Cloudflare Access browser smoke at the exact cache-busted protected URL.
- Captured representative screenshots.
- Refreshed integration status.

Intentionally not changed:

- No app runtime/UI/backend implementation files.
- No Cloudflare Access policy, DNS, secrets, auth configuration, deployment architecture, corpus, scraping, embeddings, Chroma/vector stores, private transcripts, licensing metadata, or unrelated assets.
- No API fallback was used as proof of browser behavior.

## Smoke Target

- Target type: protected-preview browser smoke
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=steel-king-578-e37f00e`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=steel-king-578-e37f00e`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=steel-king-578-e37f00e`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; existing authenticated in-app browser session loaded the app shell
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `e37f00e`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"e37f00e","git_branch":"feature/answer-api","server_started_at":"2026-06-30T13:09:15.224521+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- Whether app root `/` works: yes, it redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes, as a redirect to the app shell
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: do not use unauthenticated local or API-fallback results as protected browser proof
- Known caveats: root drops the query string during redirect, so exact cache-busted smoke should use the direct `/ui/steel-guitar-rag-mock.html?...` URL.

## Runtime Restart Evidence

Starting runtime:

```json
{"git_sha":"0406b1c","git_branch":"feature/answer-api","server_started_at":"2026-06-30T12:09:35.855631+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}
```

Service state before restart:

- LaunchDaemon label: `com.steelguitarrag.private-preview`
- State: running
- Program: `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`
- Old listener PID: `42935`
- Old PID start time: `Tue Jun 30 05:09:35 2026`

Restart method:

- Terminated stale listener PID `42935`.
- launchd restarted the configured wrapper via the installed LaunchDaemon `KeepAlive` behavior.
- No DNS, Cloudflare Access, auth, secrets, tunnel, Chroma/vector store, corpus, embedding, scraping, private transcript, or deployment architecture changes were made.

Runtime after restart:

```json
{"git_sha":"e37f00e","git_branch":"feature/answer-api","server_started_at":"2026-06-30T13:09:15.224521+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}
```

New listener:

- PID: `10945`
- Start time: `Tue Jun 30 06:09:14 2026`
- Port: `127.0.0.1:8770`
- LaunchDaemon state: running
- LaunchDaemon runs count: `5`

## Prompt Results

| Prompt | Result | Fretboard | Tab | Source behavior | Notes |
| --- | --- | --- | --- | --- | --- |
| `Where is G on E9?` | PASS | Visible | Not visible | No source cards returned | Default selected visible card was fret 3 open grip `4-5-6`, not `5-7-8`. The answer explains plain no-pedals `5-7-8` is usually partial/color when it omits the 3rd. No inert A+B label appeared for 5-7-8. |
| `Show me a G major grip.` | PASS | Visible | Not visible | No source cards returned | Full G major starter card used grip `4-5-6`, fret 3 open, with notes G-D-B. |
| `Show me a 5-7-8 G grip.` | PASS | Visible | Not visible | No source cards returned | Answer says this is not a full plain G major grip; card labels `G5/add9 (no 3rd)`, grip `5-7-8`, fret 3 open, notes D-A-G, intervals 5-2/9-1. No A+B on the static 5-7-8 card. |
| `Show me a G chord on strings 5-7-8.` | PASS | Visible | Not visible | No source cards returned | Same partial/color behavior as the explicit 5-7-8 prompt. No A+B on the static 5-7-8 card. |
| `What are good Fender Steel King settings?` | PASS | Hidden/cleared | Hidden/cleared | Two source cards visible | Answer starts with Buddy Emmons' E9 Steel King starting point: EQ Tilt 10-11, Treble 11, Mid Level 10-11, Mid Frequency 11, Bass 1, Reverb 10. It explains why these are starting points and does not show safety/electrical boilerplate. |
| `What Steel King settings did Buddy Emmons use?` | PASS | Hidden/cleared | Hidden/cleared | Two source cards visible | Same source-backed Buddy Emmons settings block rendered. |
| `How do I set the mid controls on a Fender Steel King?` | PASS | Hidden/cleared | Hidden/cleared | Two source cards visible | Same source-backed settings answer with Mid Level/Mid Frequency interaction. |
| `Why does my amp buzz at idle?` | PASS | Hidden/cleared | Hidden/cleared | Diagnostic source cards visible | Diagnostic/safety structure remains for a buzz/amp-noise question. It did not route to the Steel King settings answer. |
| `Show me a G to C move.` | PASS | Visible | Visible | No source cards returned | Movement answer showed deterministic tab plus matching fretboard. Visible `pre.tab-block` used monospace font and `white-space: pre`. |
| `How do I use A+B pedals?` | PASS | Visible | Visible | No source cards returned | A+B movement/pedal answer showed deterministic tab plus matching fretboard. Visible `pre.tab-block` used monospace font and `white-space: pre`. |

## Browser Evidence

Screenshots captured:

- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-578-g-grip-partial-no-third.png`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-steel-king-buddy-settings.png`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-amp-buzz-diagnostic.png`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-g-to-c-movement-tab-fretboard.png`

Additional browser checks:

- Q&A unlocked after Cloudflare Access login.
- `/ui/steel-guitar-rag-mock.html?...` loaded the app shell.
- Root `https://app.steelguitarrag.com/?v=steel-king-578-e37f00e` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html` and dropped the query string.
- No `[object Object]` appeared.
- Browser console check after the screenshot pass returned no relevant warnings or errors.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
curl -sS http://127.0.0.1:8770/api/version
lsof -nP -iTCP:8770 -sTCP:LISTEN
ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command
launchctl print system/com.steelguitarrag.private-preview
kill 42935
git diff --check
```

Results:

- `git diff --check`: passed before and after the docs update.
- `/api/version`: stale at `0406b1c` before restart, current at `e37f00e` after restart.
- Protected browser smoke: passed through Cloudflare Access.

Skipped:

- No broad pytest run in Lane 12; Lane 05 recorded local tests and local browser smoke for the implementation commits. This task verified protected runtime deployment/browser behavior.

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-30-0616-12-steel-king-578-protected-smoke.md`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-578-g-grip-partial-no-third.png`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-steel-king-buddy-settings.png`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-amp-buzz-diagnostic.png`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-g-to-c-movement-tab-fretboard.png`

Modified:

- `docs/handoffs/task-completions/integration-status.md`

Deleted:

- None.

Generated artifacts:

- Protected-preview smoke screenshots listed above.

## Integration Notes

- Protected-preview runtime is now on `e37f00e`.
- Exact user-smoke URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=steel-king-578-e37f00e`
- Root is usable as an app redirect, but not suitable for cache-busted validation because it drops the query string.
- Static 5-7-8 requests now clearly communicate partial/color/no-3rd behavior and avoid inert A+B labeling.
- Steel King settings answer is now concrete and source-backed, while amp buzz remains diagnostic.

## Risk Assessment

Risk: low.

Why:

- Runtime was brought to the expected committed HEAD.
- Protected browser smoke covered the exact requested E9, Steel King, diagnostic, and movement regressions.
- No implementation files, deployment config, auth policy, DNS, secrets, corpus, Chroma/vector stores, embeddings, scraping, private transcripts, or unrelated assets were modified.

Rollback:

- If this runtime needs rollback, restart the LaunchDaemon from the desired previous repo commit using the documented Mac mini operator workflow.
- The docs-only handoff/status update can be reverted independently.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-30-0616-12-steel-king-578-protected-smoke.md`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-578-g-grip-partial-no-third.png`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-steel-king-buddy-settings.png`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-amp-buzz-diagnostic.png`
- `docs/handoffs/task-completions/assets/2026-06-30-steel-king-578-protected-smoke/protected-g-to-c-movement-tab-fretboard.png`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

Do not stage unrelated parked work, including the pre-existing dirty docs, corpus metadata, RAG scripts, source-inbox files, landing/sign assets, `public/`, `ui/brand/`, `Neon Sign/`, private/generated data, Chroma/vector stores, embeddings, scraping outputs, auth/DNS/deployment files, or secrets.

## Recommended Next Lane

Lane 01 Repo Steward if further commit splitting is needed; otherwise user smoke may proceed at the exact direct app URL.

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=steel-king-578-e37f00e
```
