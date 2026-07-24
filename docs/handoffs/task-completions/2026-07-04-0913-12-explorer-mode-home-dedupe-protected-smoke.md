# 2026-07-04 09:13 - Lane 12 - Explorer Mode Home Dedupe Protected Smoke

## Task summary

Requested: run authenticated protected-preview browser smoke for Explorer Mode Home dedupe at:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-dedupe-0f401a4`

Completed: verified repo state, confirmed current HEAD contains implementation commit `0f401a4`, refreshed the LaunchDaemon-supervised protected-preview runtime from stale `2c8c7e2` to current `7dcd8cb`, verified local `/api/version`, and attempted protected-preview browser smoke in the in-app browser.

Intentionally not changed: no app implementation files, no UI/backend behavior, no Cloudflare Access policy, no DNS, no secrets, no deployment architecture, no corpus, no scraping, no embeddings, no Chroma/vector stores, no private transcripts, and no unrelated dirty/untracked work.

Result: **WARN / blocked by Cloudflare Access browser login**. The protected URL redirected to the Cloudflare Access login page, so the Explorer DOM checks could not be completed and browser smoke is not a pass.

## Smoke Target

- Target type: protected-preview browser smoke
- Result type: blocked browser smoke; API fallback not used
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-dedupe-0f401a4`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-dedupe-0f401a4`
- Exact URL the user should use after login: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-dedupe-0f401a4`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: failed/not completed in the in-app browser; page redirected to Cloudflare Access login
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected implementation commit: `0f401a4`
- Expected repo HEAD: `7dcd8cb`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"7dcd8cb","git_branch":"feature/answer-api","server_started_at":"2026-07-04T14:12:16.159967+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not verified through authenticated browser in this run
- Whether app root `/` is expected to work: expected to redirect to the app shell based on prior Lane 12 smoke, but not reverified here
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in this Explorer-only run
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, based on standing protected-preview app behavior
- Whether `/ui/e9-fretboard-explorer.html` works: blocked by Cloudflare Access login in browser
- API fallback status: not used; API fallback would not prove browser smoke
- Who should test this URL: Codex after Cloudflare Access login is completed in the in-app browser, then the user if smoke passes
- Do not test these URLs: root-only URLs as proof of cache-busted Explorer behavior
- Known caveats: runtime is current, but browser auth was not complete

## Runtime verification

- Branch: `feature/answer-api`
- Starting HEAD: `7dcd8cb`
- Final repo HEAD at handoff write: `7dcd8cb`
- `git merge-base --is-ancestor 0f401a4 HEAD`: passed
- Dirty runtime-affecting file check for `steel_guitar_rag/*.py`, `ui/*.js`, `scripts/*.py`, and `tests`: clean
- Initial `/api/version`: stale at `2c8c7e2`
- Restart path attempted first: `deploy/macos/install-private-preview-launchdaemon.sh restart`
  - Result: blocked because `sudo` required an interactive password
- Fallback restart used: killed the current `127.0.0.1:8770` listener PID and allowed the LaunchDaemon to restart it
- New listener PID: `37230`
- Listener start time: `Sat Jul 4 09:12:15 2026`
- LaunchDaemon state after restart: running
- LaunchDaemon label: `com.steelguitarrag.private-preview`
- LaunchDaemon runs count after restart: `5`
- Runtime `/api/version` after restart: `7dcd8cb`

## Protected browser result

- Browser URL attempted: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-dedupe-0f401a4`
- Final browser URL: Cloudflare Access login URL under `late-waterfall-73da.cloudflareaccess.com`
- Page title: `Sign in ・ Cloudflare Access`
- Page heading: `Log in to Steel Guitar RAG Private Preview`
- Cloudflare Access login: not completed in this run
- Explorer page loaded: no
- Six task cards verified: no, blocked by Access
- Duplicate legacy five-card row verified absent: no, blocked by Access
- Task-card click behavior verified: no, blocked by Access
- Static handoff URL verified: no, blocked by Access
- Movement handoff URL verified: no, blocked by Access
- Mobile/narrow viewport verified: no, blocked by Access
- Console errors: not meaningful because the Explorer app did not load
- Screenshot captured: `docs/handoffs/task-completions/assets/2026-07-04-explorer-mode-home-dedupe-protected-smoke/explorer-home-dedupe-desktop.png` showing the Cloudflare Access login blocker

## Expected checks still pending after auth

After the in-app browser is authenticated, rerun the protected URL and verify:

- Six "Choose what you want to learn" task cards render.
- The duplicate legacy five-card mode row does not render as a second competing row.
- Each task card selects the expected existing Explorer mode/state:
  - Find a chord
  - Find a note
  - Explore a grip
  - Walk a harmonized scale
  - Study a movement path
  - Identify a voicing
- Existing lower controls remain available.
- Static handoff URL initializes:
  `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?mode=single&source=answer&key=G&fret=3&strings=4-5-6&grip=4-5-6&v=explorer-mode-home-dedupe-0f401a4-static`
- Movement handoff URL initializes:
  `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?mode=path&source=movement-card&key=G&progression=I-IV&v=explorer-mode-home-dedupe-0f401a4-movement`
- Mobile/narrow viewport has no page-level horizontal overflow.
- No relevant console errors.
- No `[object Object]`.

## Files changed

- Created `docs/handoffs/task-completions/2026-07-04-0913-12-explorer-mode-home-dedupe-protected-smoke.md`
- Created screenshot asset folder `docs/handoffs/task-completions/assets/2026-07-04-explorer-mode-home-dedupe-protected-smoke/`
- Created screenshot `docs/handoffs/task-completions/assets/2026-07-04-explorer-mode-home-dedupe-protected-smoke/explorer-home-dedupe-desktop.png`
- Updated `docs/handoffs/task-completions/integration-status.md`

## Tests and checks

- `git status --short` - completed; broad unrelated dirty/untracked work remains parked
- `git branch --show-current` - `feature/answer-api`
- `git rev-parse --short HEAD` - `7dcd8cb`
- `git log --oneline -8` - completed
- `git merge-base --is-ancestor 0f401a4 HEAD` - passed
- `git status --short -- 'steel_guitar_rag/*.py' 'ui/*.js' 'scripts/*.py' tests` - clean
- `curl -sS http://127.0.0.1:8770/api/version` - passed after restart, returned `7dcd8cb`
- `lsof -nP -iTCP:8770 -sTCP:LISTEN` - passed, Python listening on `127.0.0.1:8770`
- `launchctl print system/com.steelguitarrag.private-preview` - passed, service running
- `deploy/macos/install-private-preview-launchdaemon.sh restart` - attempted, blocked by non-interactive sudo password requirement
- Listener PID kill/restart via LaunchDaemon supervision - completed
- Protected browser navigation to exact URL - blocked by Cloudflare Access login
- `git diff --check` - passed before docs write; must be rerun after this handoff/status update

## Integration notes

- Runtime freshness is no longer the blocker: `/api/version` reports `7dcd8cb`, which contains `0f401a4`.
- The remaining blocker is only Cloudflare Access authentication in the in-app browser.
- API fallback was intentionally not used because it would not prove protected-preview browser behavior.
- Once the browser is authenticated, no runtime restart should be necessary unless `/api/version` changes or the process becomes stale.

## Risk assessment

Risk: low. This run changed only docs/status/screenshot artifacts and restarted the existing LaunchDaemon-supervised app process to the current committed HEAD. No app code or protected configuration was modified.

Rollback/restart note: the service is LaunchDaemon-supervised. If needed, use the documented LaunchDaemon restart path when an interactive sudo session is available, or stop the listener PID and allow launchd to restart it.

## Human decision needed

Yes. Complete Cloudflare Access login in the in-app browser, then rerun Lane 12 protected-preview browser smoke for the exact Explorer URL.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-04-0913-12-explorer-mode-home-dedupe-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/assets/2026-07-04-explorer-mode-home-dedupe-protected-smoke/explorer-home-dedupe-desktop.png`

## Files that must not be staged

- Any unrelated dirty or untracked files currently parked in the worktree
- `README.md`
- `corpus_metadata/*`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_*.py`
- `source-inbox/*`
- `ui/brand/*`
- `public/brand/*`
- `Neon Sign/`
- Corpus/private/source/provenance/vector/deployment/auth/secrets files

## Recommended next lane

Lane 12: rerun protected-preview browser smoke after Cloudflare Access login is complete in the in-app browser.

## Commit readiness

Safe to commit as a WARN/blocker docs-only handoff/status update if exact-path staged.

## Suggested next step

After Cloudflare Access login, run:

```text
Lane 12: Rerun authenticated protected-preview smoke for Explorer Mode Home dedupe at https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mode-home-dedupe-0f401a4. Runtime /api/version should already report 7dcd8cb containing 0f401a4. Verify the six task cards are the single primary entry and the duplicate legacy five-card row is gone.
```
