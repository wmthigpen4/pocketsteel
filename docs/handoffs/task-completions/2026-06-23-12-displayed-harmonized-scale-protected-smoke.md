# Lane 12 Displayed Harmonized Scale Protected Smoke

## Task summary

Lane 12 verified the launchd-supervised protected preview for `0ad025f fix: prevent harmonized scale fallback display`.

Result: **FAIL / BLOCKED**.

The protected preview `/api/version` reports `0ad025f`, Cloudflare Access succeeded, Q&A unlocked, and the protected browser UI was tested at the exact cache-busted URL. However, prompts 1-8 still displayed the generic specificity fallback in the browser UI. The app process could not be kickstarted from this non-interactive session, and process evidence shows PID `5054` started before the Lane 05 files were modified. That means the version endpoint is current to repo HEAD, but the loaded Python process is likely still using pre-fix imported modules.

No app code, deployment configuration, auth policy, DNS, corpus, embeddings, Chroma/vector data, scraper output, private source data, or implementation files were changed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=0ad025f`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=0ad025f`
- Exact URL the user should use: blocked until the app LaunchDaemon is restarted with sudo and this smoke passes
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; app and Explorer were not on the Access login screen
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `0ad025f`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"0ad025f","git_branch":"feature/answer-api","server_started_at":"2026-06-23T18:08:23.651468+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not missing locally
- Whether app root `/` works: yes, but it redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string
- Whether app root `/` is expected to work: yes as a redirect entrypoint, not as the cache-busted canonical smoke target
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes; it is the canonical cache-busted smoke URL
- Who should test this URL: Lane 12 after sudo restart; user smoke should wait
- Do not test these URLs: bare root as the cache-busted target because root drops the query string
- Known caveats: `deploy/macos/install-private-preview-launchdaemon.sh status` and `restart` require sudo; direct `launchctl kickstart` was denied with `Operation not permitted`.

## Runtime and deployment status

- Branch: `feature/answer-api`
- Starting HEAD: `0ad025f`
- Runtime commit expected: `0ad025f`
- Runtime commit reported by `/api/version`: `0ad025f`
- Launchd supervision status: `system/com.steelguitarrag.private-preview` is running as a LaunchDaemon.
- LaunchDaemon program: `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`
- LaunchDaemon repo env: `STEEL_RAG_REPO_DIR=/Users/cory/Documents/Steel Guitar RAG`
- Durable app logs:
  - stdout: `/Users/cory/Library/Logs/steel-guitar-rag/app.out.log`
  - stderr: `/Users/cory/Library/Logs/steel-guitar-rag/app.err.log`
- Manual screen status: absent; `screen -ls` reported no sockets.
- Listener status: `Python` PID `5054` is listening on `127.0.0.1:8770`.
- Process start: PID `5054` started `Tue Jun 23 11:06:15 2026`.
- Lane 05 file modification times:
  - `steel_guitar_rag/answer_intent_classifier.py`: `Jun 23 13:00:25 2026`
  - `steel_guitar_rag/curated_answers.py`: `Jun 23 13:00:31 2026`
  - `tests/test_api_search.py`: `Jun 23 13:01:07 2026`
- Cloudflare Tunnel status: `system/com.cloudflare.cloudflared` is running as a LaunchDaemon. Token details were intentionally redacted and not recorded.

Restart attempt:

- `launchctl kickstart -k system/com.steelguitarrag.private-preview` returned `Operation not permitted`.
- The helper restart command requires sudo and could not be used non-interactively.
- The app LaunchDaemon was therefore not successfully restarted in this task.

## URLs tested

- Main app: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=0ad025f`
- Explorer: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=0ad025f`
- Root behavior check: `https://app.steelguitarrag.com/?v=0ad025f`

Root behavior:

- Start URL: `https://app.steelguitarrag.com/?v=0ad025f`
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
- The visible answer text mentions older 11th-fret E-lower wording as a typo, but the row/card route remains corrected.

## Explorer browser smoke results

- Explorer URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=0ad025f`
- Page loaded through protected preview: yes
- Page identified as E9 Fretboard Explorer: yes
- `5&8 branch positions` option appeared: yes
- 5&8 branch mode rendered usable rows/cards: yes
- Raw `five_eight_branch` label leak: no
- Broken 5-8 label rendering: no
- `13 E-lower` branch present: yes
- `11 E-lower` branch absent: yes
- `[object Object]` appeared: no
- Console errors on Explorer page: none observed

## Tests and checks run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -12 --oneline`
- `git diff --name-only`
- `git diff --cached --name-only`
- `git diff --check` - passed
- `launchctl print system/com.steelguitarrag.private-preview`
- `launchctl print system/com.cloudflare.cloudflared` with token redacted from local output capture
- `deploy/macos/install-private-preview-launchdaemon.sh status 2>&1 || true` - could not run because sudo requires an interactive password
- `deploy/macos/install-private-preview-launchdaemon.sh version 2>&1 || true` - reported `0ad025f`
- `curl -sS http://127.0.0.1:8770/api/version || true` - reported `0ad025f`
- `lsof -nP -iTCP:8770 -sTCP:LISTEN || true` - Python PID `5054` listening on `127.0.0.1:8770`
- `screen -ls || true` - no sockets found
- `ps -p 5054 -o pid,lstart,command`
- `stat -f '%Sm %N' steel_guitar_rag/answer_intent_classifier.py steel_guitar_rag/curated_answers.py tests/test_api_search.py`
- `launchctl kickstart -k system/com.steelguitarrag.private-preview 2>&1 || true` - denied with `Operation not permitted`
- Authenticated protected-preview browser smoke for the 15 requested main-app prompts
- Authenticated protected-preview browser smoke for Explorer route and 5&8 branch UI

Skipped:

- No broad pytest suite was run; this was a protected-preview browser/runtime smoke task.
- No successful app restart was run because system LaunchDaemon kickstart requires elevated permission.

## Files changed

Created:

- `docs/handoffs/task-completions/2026-06-23-12-displayed-harmonized-scale-protected-smoke.md`

Modified implementation files:

- None

Deleted files:

- None

Generated artifacts:

- None

## Integration notes

This should be treated first as a Lane 12 runtime-refresh blocker, not yet as a confirmed Lane 05 code regression:

- `/api/version` reports `0ad025f`.
- The Python process listening on `127.0.0.1:8770` started before the Lane 05 code files were modified.
- Browser behavior matches the pre-fix failure mode from `db6ae81`.
- The non-interactive Lane 12 session could not kickstart the system LaunchDaemon.

After a privileged restart, rerun the same protected browser smoke. If prompts 1-8 still fail after PID/start time confirms a post-`0ad025f` process, route back to Lane 05.

## Risk assessment

Risk: **medium**.

Reason:

- Runtime/deployment health is partially good: launchd, tunnel, auth, Q&A, specific 5&8 branch, Explorer, and regressions are working.
- The intended Lane 05 fix is not proven live in the loaded Python process.
- User smoke should not proceed for the broader harmonized-scale slice until a privileged LaunchDaemon restart and rerun pass.

Rollback notes:

- No code or deployment config changed.
- No rollback needed for this Lane 12 task.

## Human decision needed

Yes.

Run the privileged restart from a Terminal session with sudo access:

```bash
cd /Users/cory/Documents/Pocket\ Steel
deploy/macos/install-private-preview-launchdaemon.sh restart
curl -sS http://127.0.0.1:8770/api/version
ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command
```

Then rerun Lane 12 protected-preview smoke at:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=0ad025f
```

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-06-23-12-displayed-harmonized-scale-protected-smoke.md`

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

Lane 12 Self-Hosted Deployment after privileged restart.

Suggested next prompt:

```text
Lane 12: After I ran deploy/macos/install-private-preview-launchdaemon.sh restart with sudo, rerun protected-preview smoke using docs/handoffs/task-completions/2026-06-23-12-displayed-harmonized-scale-protected-smoke.md. Confirm the listening Python process started after commit 0ad025f and verify the broader G harmonized-scale/diminished prompts in the authenticated browser.
```

## Commit readiness

Safe to commit.
