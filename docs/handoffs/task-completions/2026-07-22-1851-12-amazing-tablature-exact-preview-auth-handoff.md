# Amazing Tablature exact preview activation and authentication handoff

## Task summary

Recovered and activated the exact Amazing Tablature frontend release after the user authorized activation.

- Confirmed the originally installed LaunchDaemon still targeted stale release `3cb63c3`.
- Diagnosed fresh-daemon startup failures caused by a release `.venv` symlink back into macOS-protected `Documents` and launch-blocking provenance metadata on recopied daemon files.
- Created a self-contained external runtime environment and exact detached release at `~/.steel-rag/releases/4b443c7-standalone` without changing repository or source data.
- Cleared only launch-blocking extended attributes from the installed plist/wrapper and bootstrapped the canonical system LaunchDaemon.
- Verified the system-supervised listener now runs exact implementation commit `4b443c79a01f9a615b2cef36763e9d94c4dd3ab1` on `127.0.0.1:8770`.
- Reached the protected Melody Studio URL through Cloudflare Access in both available browser sessions. Neither session is currently authenticated, so functional protected browser smoke is waiting only for user sign-in.

No source images, training records, challenger artifacts, validation data, sealed-test data, embeddings, vector stores, auth policy, DNS, Tunnel configuration, Access policy, or secrets were changed.

## Files changed

- `docs/handoffs/task-completions/2026-07-22-1851-12-amazing-tablature-exact-preview-auth-handoff.md`

Operational artifacts outside the repository:

- `~/.steel-rag/venvs/pocket-steel-py312-20260722` — clone-on-write copy of the existing tested repository virtual environment, outside the macOS-protected workspace path.
- `~/.steel-rag/releases/4b443c7-standalone` — clean detached checkout of exact commit `4b443c79a01f9a615b2cef36763e9d94c4dd3ab1` linked to the external runtime environment.
- `/Library/LaunchDaemons/com.steelguitarrag.private-preview.plist` — installed exact standalone release definition.
- `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh` — content-identical wrapper for commit `4b443c7`; launch-blocking extended attributes removed.

## Tests and checks

- Standalone virtual environment import check: passed.
- Exact detached release preflight and plist lint: passed.
- Installed wrapper SHA-256 matched the exact release wrapper.
- LaunchDaemon state: running and system-supervised.
- Listener owner: LaunchDaemon Python process on `127.0.0.1:8770`.
- `/health/live`: passed.
- `/health/ready`: passed.
- `/api/version`: `git_sha=4b443c7`.
- Loopback root: HTTP 302 to `/ui/steel-guitar-rag-mock.html`.
- Loopback home UI: HTTP 200.
- Loopback Melody Studio: HTTP 200.
- Protected URL: reached Cloudflare Access login in the in-app browser and Chrome; authentication not yet completed.
- Previously completed full repository suite: `1375 passed`.
- Previously completed local browser functional smoke: passed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke pending authentication; API/loopback verification is not browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=arrangement-engine-4b443c7-20260722`
- Cache-busted URL tested: same as above
- Exact URL the user should use: same as above
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: sign-in required; login page reached successfully
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: runtime implementation `4b443c79a01f9a615b2cef36763e9d94c4dd3ab1`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: matched `4b443c7`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; HTTP 302 to home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes; HTTP 200 loopback
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user signs in; Codex then completes browser smoke
- Do not test these URLs: validation, sealed-test, or stale discovery review URLs
- Known caveats: browser session authentication is the only remaining release-goal item

## Integration notes

The existing deployment runbook assumes a release `.venv` symlink into the primary workspace. On this host, a freshly launched background daemon can be denied access to that protected `Documents` target. Future release tooling should support a shared external runtime environment and should strip launch-blocking provenance metadata from installed daemon files before bootstrap. This handoff records the issue; it does not change deployment source code in the completed product release.

`docs/handoffs/task-completions/integration-status.md` remains pre-existing dirty coordination work and was not edited or staged.

## Risk assessment

Low runtime risk. Exact SHA, health, readiness, static routes, listener ownership, and LaunchDaemon supervision are verified. Remaining risk is limited to unverified authenticated browser behavior.

## Human decision needed

Yes, operational only: complete Cloudflare Access sign-in in the visible in-app browser tab and reply `Signed in`. No password, OTP, or email address should be sent to Codex.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-22-1851-12-amazing-tablature-exact-preview-auth-handoff.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated historical untracked handoffs
- Everything under `corpus-private/`
- Raw source images, validation data, sealed-test data, embeddings, vector stores, credentials, environment files, logs, and generated reports

## Recommended next lane

Lane 12 Self-Hosted Deployment immediately after Cloudflare Access sign-in.

## Commit readiness

Safe to commit

## Suggested next step

After the user signs in, verify `/api/session`, arrange `1 2 3 5` in G, confirm four score events plus synchronized fretboard/tab output and the visible deterministic engine status, inspect console errors, then write the final protected-preview pass handoff and close the release goal.
