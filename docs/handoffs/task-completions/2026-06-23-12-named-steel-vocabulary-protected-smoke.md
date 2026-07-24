# Lane 12 Named Steel Vocabulary Protected Smoke

## Task Summary

Lane 12 refreshed the Mac mini protected-preview runtime to the named steel vocabulary routing fix and browser-smoked the protected app through Cloudflare Access.

Completed:

- Verified current branch and HEAD.
- Found the protected-preview LaunchDaemon runtime was stale before refresh.
- Refreshed the LaunchDaemon-supervised app by terminating the stale `127.0.0.1:8770` listener and allowing launchd to restart it.
- Verified `/api/version` reports `c8703e2`.
- Ran authenticated protected-preview browser smoke at the exact cache-busted app URL.
- Verified root URL behavior separately.
- Preserved unrelated dirty work.

Intentionally not changed:

- No backend, frontend, auth, DNS, Cloudflare Access, tunnel config, corpus, Chroma, embeddings, scraping, or private-source files were modified.
- No API fallback was used as a substitute for protected-preview browser smoke.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=c8703e2`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=c8703e2`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=c8703e2`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; authenticated browser session loaded the app, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `c8703e2`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"c8703e2","git_branch":"feature/answer-api","server_started_at":"2026-06-24T03:29:15.737952+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: root redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes, as a redirect to the app shell
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: bare root if cache-bust preservation matters, because root currently drops the query string on redirect
- Known caveats: root `https://app.steelguitarrag.com/?v=c8703e2` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html` and dropped the query string

## Runtime Evidence

- Branch: `feature/answer-api`
- HEAD before smoke: `c8703e2`
- Initial local `/api/version` before refresh: stale at `1d3728a`
- Runtime refresh method: terminated the stale port `8770` listener; launchd restarted the configured private-preview app
- Local `/api/version` after refresh: `c8703e2`
- Listener: Python on `127.0.0.1:8770`
- Listener PID after refresh: `49595`
- Listener start time: `Tue Jun 23 22:29:15 2026`
- LaunchDaemon: `system/com.steelguitarrag.private-preview`
- LaunchDaemon state: running
- LaunchDaemon runs count after refresh: `36`
- Durable logs:
  - stdout: `~/Library/Logs/steel-guitar-rag/app.out.log`
  - stderr: `~/Library/Logs/steel-guitar-rag/app.err.log`
- Cloudflare Tunnel: cloudflared process running, PID `677`; token-bearing process arguments were not copied into this handoff

## Root Behavior

Checked: `https://app.steelguitarrag.com/?v=c8703e2`

Observed:

- Final browser URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- Query string was dropped during redirect.
- App shell loaded.
- Root was not an Access login page in the authenticated browser session.
- The root-loaded app showed the stage with the Q&A input visible but gated until Backstage Pass.
- No browser console errors or warnings were recorded on the root check.

Implication:

- Use the direct `/ui/steel-guitar-rag-mock.html?v=c8703e2` URL when exact cache-bust preservation matters.

## Prompt Results

| Prompt | Result | Notes |
| --- | --- | --- |
| `What does a Franklin pedal do?` | Pass | Direct on-domain answer. No generic fallback. Answer explains common Franklin pedal/change: lowers 5 and 10 B to A and 6 G# to F#. No fretboard or tab. |
| `What is a Franklin change?` | Pass | Direct on-domain answer. No generic fallback. Explains common Franklin change and musical use. No fretboard or tab. |
| `What is a zero pedal?` | Pass | Direct on-domain answer. No generic fallback. Explains P0 as an extra pedal left of A with setup-specific function. No fretboard or tab. |
| `What is a half stop?` | Pass | Direct on-domain answer. No generic fallback. Explains tactile intermediate stop and common 2nd-string example. No fretboard or tab. |
| `What is split tuning?` | Pass | Direct on-domain answer. No generic fallback. Explains combined raise/lower tuning point. No fretboard or tab. |
| `What is a compensator?` | Pass | Direct on-domain answer. No generic fallback. Explains extra pull/adjustment for pitch correction. No fretboard or tab. |
| `What is the Emmons setup?` | Pass | Direct on-domain answer. No generic fallback. Explains A-B-C pedal order versus Day setup. No fretboard or tab. |
| `What is a copedent?` | Pass | Direct on-domain answer. No generic fallback. Defines tuning and mechanical-change chart. No fretboard or tab. |
| `Show me a G major grip.` | Pass | Static grip regression passed. Direct answer with visible fretboard/SVG. No generated tab block. |
| `Give me the full tab for a modern copyrighted song.` | Pass | Copyright guardrail passed. Refused full copyrighted song tab/modern arrangement/solo/transcription. No generated tab block and no fretboard. |

Additional browser checks:

- Q&A input was unlocked in the authenticated protected-preview session.
- Submitted prompt values were verified before each send.
- No `[object Object]` appeared.
- No generic `I need a more specific steel-guitar question` fallback appeared.
- Browser console/page errors: none recorded during the prompt matrix.

## Tests And Checks Run

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -5 --oneline
git diff --cached --name-only
git diff --check
curl -sS http://127.0.0.1:8770/api/version
lsof -nP -iTCP:8770 -sTCP:LISTEN
ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command
launchctl print system/com.steelguitarrag.private-preview
deploy/macos/install-private-preview-launchdaemon.sh version
```

Browser smoke was run through the authenticated in-app browser at the exact protected-preview URL above.

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-23-12-named-steel-vocabulary-protected-smoke.md`

No implementation files changed.

## Integration Notes

- The protected-preview runtime now serves `c8703e2`, which contains the named steel vocabulary routing fix.
- The failed Franklin pedal prompt is verified fixed in protected-preview browser smoke.
- Named steel vocabulary questions route on-domain and no longer trigger the generic steel-question fallback.
- Static G major grip and copyright guardrail regressions passed.
- Root redirects to `/ui/steel-guitar-rag-mock.html` but drops the cache-bust query string; use the direct `/ui/...?...` URL for cache-busted smoke.

## Risk Assessment

Risk: low.

Reason:

- This was a protected-preview smoke and docs-only handoff.
- Runtime refresh used the existing LaunchDaemon-supervised service behavior.
- No product code, deployment config, DNS, auth policy, corpus, Chroma, embeddings, scraping, secrets, or private-source files were modified.

Rollback note:

- If runtime issues appear, use the existing LaunchDaemon restart/rollback process and verify `/api/version` before browser smoke.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-named-steel-vocabulary-protected-smoke.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files already present in the worktree.
- Corpus files, Chroma/vector stores, embeddings, `source-inbox/`, private-source material, secrets, credentials, env files, Cloudflare tokens, generated media/assets, and scraper output.

## Recommended Next Lane

Lane 01 Repo Steward.

Recommended task:

```text
Lane 01: Refresh integration-status.md for c8703e2 named steel vocabulary routing and Lane 12 protected-preview smoke. Preserve unrelated dirty work and stage exact paths only.
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit this scoped Lane 12 handoff with:

```bash
git add docs/handoffs/task-completions/2026-06-23-12-named-steel-vocabulary-protected-smoke.md
git diff --cached --name-only
git diff --cached --check
git commit -m "docs: record named steel vocabulary protected smoke"
```
