# Lane 12 Browser Harmonized Scale Protected Smoke

## Task summary

Lane 12 verified the launchd-supervised protected preview for `db6ae81 fix: route browser harmonized scale prompts deterministically`.

Result: **FAIL**.

The protected preview is running `db6ae81`, Cloudflare Access/browser authentication succeeded, Q&A unlocked, and the app responded through the browser UI. However, the broader G harmonized-scale, G natural-minor harmonized-scale, and diminished-position prompts still returned the generic specificity fallback through the protected browser UI. The specific `strings 5 and 8` branch prompt passed, and the Explorer 5&8 route/UI passed.

No app code, deployment configuration, auth policy, DNS, corpus, embeddings, Chroma/vector data, scraper output, private source data, or implementation files were changed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=db6ae81`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=db6ae81`
- Exact URL the user should use: **blocked for user smoke until Lane 05 fixes the broader browser-route fallback**
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; app page was not on the Access login screen
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `db6ae81`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"db6ae81","git_branch":"feature/answer-api","server_started_at":"2026-06-23T17:49:17.912185+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not missing locally; browser navigation to `https://app.steelguitarrag.com/api/version` was blocked by the browser client, so the runtime version is proven by local `/api/version`, the launchd wrapper `version` command, and listener/process evidence.
- Whether app root `/` works: yes, but it redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string
- Whether app root `/` is expected to work: yes as a redirect entrypoint, not as the cache-busted canonical smoke target
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes; it is the canonical cache-busted smoke URL
- Who should test this URL: Codex after a Lane 05 fix; user smoke should wait
- Do not test these URLs: bare root as the cache-busted target because root drops the query string
- Known caveats: the local `deploy/macos/install-private-preview-launchdaemon.sh status` command invokes sudo and could not run in this non-interactive session; `launchctl print` and `lsof` were used instead.

## Runtime and deployment status

- Branch: `feature/answer-api`
- Starting HEAD: `db6ae81`
- Runtime commit expected: `db6ae81`
- Runtime commit reported by `/api/version`: `db6ae81`
- Launchd supervision status: `system/com.steelguitarrag.private-preview` is running as a LaunchDaemon.
- LaunchDaemon program: `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`
- LaunchDaemon repo env: `STEEL_RAG_REPO_DIR=/Users/cory/Documents/Steel Guitar RAG`
- Durable app logs:
  - stdout: `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
  - stderr: `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`
- Manual screen status: absent; `screen -ls` reported no sockets.
- Listener status: `Python` PID `5054` is listening on `127.0.0.1:8770`.
- Cloudflare Tunnel status: `system/com.cloudflare.cloudflared` is running as a LaunchDaemon. Token details were intentionally not recorded.

The app LaunchDaemon was not restarted during this task because the loaded app process already reported the target runtime `db6ae81`.

## URLs tested

- Main app: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=db6ae81`
- Explorer: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=db6ae81`
- Root behavior check: `https://app.steelguitarrag.com/?v=db6ae81`

Root behavior:

- Start URL: `https://app.steelguitarrag.com/?v=db6ae81`
- Final URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- Query string preservation: not preserved
- App shell loaded after redirect: yes

## Main app browser smoke results

| # | Prompt | Result | Actual behavior |
|---|---|---|---|
| 1 | Show me a G harmonized scale. | FAIL | Returned generic fallback: "I need a more specific steel-guitar question..." No fretboard. No tab. |
| 2 | Show me G major harmonized scale on E9. | FAIL | Returned generic fallback. No fretboard. No tab. |
| 3 | Show me a G major harmonized scale. | FAIL | Returned generic fallback. No fretboard. No tab. |
| 4 | Show me a G harmonized scale on E9. | FAIL | Returned generic fallback. No fretboard. No tab. |
| 5 | Show me a G natural minor harmonized scale. | FAIL | Returned generic fallback. No fretboard. No tab. |
| 6 | Show me G natural minor harmonized scale on E9. | FAIL | Returned generic fallback. No fretboard. No tab. |
| 7 | Show me the F# diminished position in G. | FAIL | Returned generic fallback. No fretboard. No tab. |
| 8 | Show me the A diminished position in G minor. | FAIL | Returned generic fallback. No fretboard. No tab. |
| 9 | Show me a G harmonized scale on strings 5 and 8. | PASS | Returned deterministic 5&8 branch guidance and rendered a fretboard SVG. No tab. Friendly `5&8`/`strings 5 and 8` wording appeared. |
| 10 | Show me a G major grip. | PASS | Returned direct prose and fretboard-first static grip answer. No visible tab card. |
| 11 | Show me a 4-5-6 grip. | PASS | Returned direct prose and fretboard-first static grip answer. No visible tab card. |
| 12 | Show me a G to C move. | PASS | Returned direct prose, fretboard, and deterministic tab. |
| 13 | Give me a beginner lick in G. | PASS | Returned direct prose, fretboard, and deterministic tab. |
| 14 | Give me the full tab for a modern copyrighted song. | PASS | Refused/redirected safely. No fretboard. No generated tab. |
| 15 | What are good Fender Steel King settings? | PASS | Returned gear answer without stale tab/fretboard payload. |

Expected vs actual:

- Broader G major harmonized-scale prompts passed: **no**
- G natural minor harmonized-scale prompts passed: **no**
- Diminished-position prompts passed: **no**
- 5&8 branch correction passed: **yes**
- Static grip regressions passed: **yes**
- Movement/tab regressions passed: **yes**
- Copyright guardrail passed: **yes**
- Gear/no-stale-payload regression passed: **yes**
- Console errors on main app smoke: none observed
- API fallback status: not used as a browser-smoke substitute

5&8 branch details:

- The answer showed both valid branch families.
- The rendered rows/cards showed the C/E branch at fret 13 with E-lower.
- The rendered rows/cards did not use fret 11 E-lower as the C/E branch.
- The answer text mentions the older 11th-fret E-lower wording as a typo, but the visible row/card route remains corrected.

## Explorer browser smoke results

- Explorer URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=db6ae81`
- Page loaded through protected preview: yes
- Page identified as E9 Fretboard Explorer: yes
- Expanded key selector displayed: `G`, `C`, `D`, `F`, `Bb`, `Eb`
- `Showing validated positions` appeared: yes
- Raw `N validated rows` primary copy appeared: no
- Raw `five_eight_branch` label leak: no
- Broken 5-8 label rendering: no
- `5&8 branch positions` option appeared: yes
- 5&8 branch mode rendered usable rows/cards: yes
- `13 E-lower` branch present: yes
- `11 E-lower` branch absent: yes
- `E-lower+E-lower` appeared: no
- `[object Object]` appeared: no
- Console errors on Explorer page: none observed

## Tests and checks run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -1 --oneline`
- `git log -10 --oneline`
- `git diff --name-only`
- `git diff --cached --name-only`
- `git diff --check` - passed
- `launchctl print system/com.steelguitarrag.private-preview`
- `launchctl print system/com.cloudflare.cloudflared`
- `deploy/macos/install-private-preview-launchdaemon.sh status 2>&1 || true` - could not run because sudo requires an interactive password
- `deploy/macos/install-private-preview-launchdaemon.sh version 2>&1 || true` - reported `db6ae81`
- `curl -sS http://127.0.0.1:8770/api/version || true` - reported `db6ae81`
- `lsof -nP -iTCP:8770 -sTCP:LISTEN || true` - Python PID `5054` listening on `127.0.0.1:8770`
- `screen -ls || true` - no sockets found
- Authenticated protected-preview browser smoke for the 15 requested main-app prompts
- Authenticated protected-preview browser smoke for Explorer route and 5&8 branch UI

Skipped:

- No broad pytest suite was run; this was a protected-preview browser/runtime smoke task.
- No app restart was run because the loaded LaunchDaemon runtime already reported `db6ae81`.

## Files changed

Created:

- `docs/handoffs/task-completions/2026-06-23-12-browser-harmonized-scale-protected-smoke.md`

Modified implementation files:

- None

Deleted files:

- None

Generated artifacts:

- None

## Integration notes

Lane 05 should treat this as a backend/browser-answer-route regression, not a deployment/version mismatch:

- The runtime is current at `db6ae81`.
- Browser auth succeeded and Q&A was unlocked.
- The specific `strings 5 and 8` browser prompt hits deterministic routing correctly.
- Broader G major, G natural minor, and diminished-position prompts still fall through to the generic specificity fallback in the protected browser UI.

Lane 12 does not need to change launchd, Cloudflare Tunnel, DNS, Access policy, or runtime startup for this failure.

## Risk assessment

Risk: **medium**.

Reason:

- Runtime/deployment health is good, but the core user-facing harmonized-scale prompts still fail in authenticated browser smoke.
- User smoke should not proceed for the broader harmonized-scale slice until Lane 05 fixes the browser route behavior.

Rollback notes:

- No code or deployment config changed.
- No rollback needed for Lane 12.

## Human decision needed

No.

The owning lane is clear: route back to Lane 05 for the broader harmonized-scale browser-answer fallback.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-06-23-12-browser-harmonized-scale-protected-smoke.md`

## Files that must not be staged

Do not stage unrelated parked work, including:

- `README.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/`
- `corpus_metadata/`
- `ui/brand/`
- `public/brand/` generated/raw media assets
- unrelated untracked handoffs under `docs/handoffs/task-completions/`
- corpus, Chroma/vector stores, embeddings, scraper output, credentials, env files, logs, or private source data

## Recommended next lane

Lane 05 Backend / RAG Integration.

Suggested next prompt:

```text
Lane 05 — Backend / RAG Integration

Investigate why protected-preview browser UI requests at runtime db6ae81 still return the generic specificity fallback for:
- Show me a G harmonized scale.
- Show me G major harmonized scale on E9.
- Show me a G major harmonized scale.
- Show me a G harmonized scale on E9.
- Show me a G natural minor harmonized scale.
- Show me G natural minor harmonized scale on E9.
- Show me the F# diminished position in G.
- Show me the A diminished position in G minor.

Lane 12 verified that /api/version reports db6ae81, Cloudflare Access succeeds, Q&A unlocks, and the specific "Show me a G harmonized scale on strings 5 and 8." browser prompt passes. Fix the broader browser-answer route without touching deployment, DNS, auth, corpus, Chroma, embeddings, scraping, or private data. Add same-origin/browser-path regression coverage for the failing prompts and hand back to Lane 12 for protected-preview smoke.
```

## Commit readiness

Safe to commit.
