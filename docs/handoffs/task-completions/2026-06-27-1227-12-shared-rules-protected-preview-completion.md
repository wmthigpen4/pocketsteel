# Lane 12 Shared Rules Protected Preview Completion

## Task Summary

Requested end-to-end protected-preview verification for the latest E9 Fretboard Explorer build after:

- Lane 06 mobile/control-density work.
- Lane 05 shared deterministic Explorer music-rules boundary work.
- Implementation commit `b55a12e feat: add shared explorer music rules boundary`.
- Integration refresh commit `36cec1a docs: refresh explorer music rules status`.

Completed:

- Inspected repo guidance, runtime/deployment guidance, integration status, the Lane 05 shared-rules handoff, and relevant Lane 06 mobile/control-density handoffs.
- Confirmed current branch and HEAD.
- Confirmed current HEAD contains `b55a12e`.
- Attempted the documented protected-preview LaunchDaemon restart path.
- Verified local `/api/version`.
- Ran authenticated protected-preview browser smoke at the exact cache-busted Explorer URL.
- Refreshed `integration-status.md`.

Intentionally not changed:

- No app runtime/UI/backend code was edited.
- No DNS, Cloudflare Access policy, secrets, auth policy, scraping, embeddings, Chroma/vector stores, raw corpus, private transcript files, or deployment path config were changed.
- No API fallback was used as browser smoke.

Overall result: **WARN / browser behavior passed but runtime-version proof is blocked**.

The protected static/browser behavior passed the requested Explorer checks, but `/api/version` still reports runtime SHA `4040a47`, which does not contain `b55a12e`. The documented LaunchDaemon restart command requires interactive `sudo` and failed in the non-interactive Codex tool context.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=shared-rules-boundary-b55a12e`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=shared-rules-boundary-b55a12e`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=shared-rules-boundary-b55a12e`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; the Explorer page loaded, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `36cec1a`, containing implementation commit `b55a12e`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"4040a47","git_branch":"feature/answer-api","server_started_at":"2026-06-26T01:51:23.747502+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes after Cloudflare Access; `https://app.steelguitarrag.com/?v=shared-rules-boundary-b55a12e` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes, as a protected redirect to the app shell; it drops query strings
- Whether `/ui/steel-guitar-rag-mock.html` works: root redirect reached it and loaded the app shell
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user for focused visual/UI review; Lane 12 after interactive restart for strict runtime proof
- Do not test these URLs: do not treat local `127.0.0.1` or API fallback as protected-preview browser proof
- Known caveats: runtime `/api/version` is stale; strict end-to-end runtime certification is blocked until the LaunchDaemon is restarted interactively

## Branch And Version

- Branch: `feature/answer-api`
- Starting HEAD: `36cec1a`
- Final HEAD before docs commit: `36cec1a`
- Expected implementation commit: `b55a12e`
- Current HEAD contains `b55a12e`: yes
- Local runtime `/api/version`: `4040a47`
- Runtime contains `b55a12e`: no
- Protected page script evidence:
  - `e9-music-rules.js?v=shared-music-rules-20260627`
  - `e9-fretboard-explorer.js?v=shared-music-rules-20260627`

## Restart Attempt

Documented restart path inspected:

```bash
deploy/macos/install-private-preview-launchdaemon.sh restart
```

Attempted command:

```bash
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh restart
curl -sS http://127.0.0.1:8770/api/version
lsof -nP -iTCP:8770 -sTCP:LISTEN
```

Result:

- `status` and `restart` both failed because `sudo` requires an interactive terminal/password prompt in this tool context.
- `/api/version` remained `4040a47`.
- Python remained listening on `127.0.0.1:8770`.

No non-documented restart path was used.

## Protected Browser Smoke Results

### Page Load And Auth

- Exact protected URL loaded after Cloudflare Access authentication.
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`.
- Page identified as E9 Fretboard Explorer.
- No Cloudflare Access login text remained on the page.
- No `[object Object]`.
- Browser console warning/error log was empty during the smoke.

### Mobile / Control Density Baseline

- Desktop viewport used: `1280x720`.
- Page-level horizontal overflow: no (`scrollWidth` matched `clientWidth`).
- Notation controls remained visible near the fretboard: `Notes`, `NNS`, `Roman`, `Numbers`.
- Desktop layout remained usable for the tested Explorer states.

### Copedent / Control Labels

- `Emmons E9`, `Day E9`, `Custom E9 (with LKV)`, and disabled `My Copedent (E9) - Coming soon in Backstage` options were present.
- Standard `Emmons E9` impact section showed learner-facing controls such as `A pedal`, `B pedal`, `C pedal`, `E-raise lever`, `E-lower lever`, `D-lower lever`, and `G-lower lever`; no learner-facing `B-to-Bb` / LKV control appeared in the Emmons impact controls.
- `Custom E9 (with LKV)` was selectable and exposed `B-to-Bb vertical` plus custom LKV-related controls.
- Labels were readable display labels rather than raw internal object strings.

### Voicing Identifier

- `Voicing identifier` mode loaded.
- The UI showed fret, string, pedal/lever controls, and an identified `G` result for the default state.
- Result text remained readable and did not expose `[object Object]`.

### Chord / Voicing Finder

`Fmaj7`, Core grip:

- Target: `Fmaj7 (major 7)`.
- Result count: `14 candidates`.
- Omitted tones appeared where appropriate.
- No dominant/V7 mislabel near the target result.

`Fmaj7`, All practical grip:

- Target: `Fmaj7 (major 7)`.
- Result count: `24 candidates`.
- Grip vocabulary changed candidate breadth from 14 to 24.
- Omitted-tone labeling remained present.

`Cmin9` and `Cm9`, Core grip:

- Both parsed as `Cm9 (minor 9)`.
- Both showed `0 candidates` and a clear no-practical-voicing state under the current filters.
- No fallback/internal error text appeared.

`V7 in G`, Core grip:

- Parsed target: `D7 (dominant 7)`.
- Text included `V7 in G resolves to D7`.
- Result count: `6 candidates`.
- D7 candidates showed omitted `3rd (F#)` where partial.

Selection:

- Chord Finder result buttons rendered with `explorer-active-result`.
- Selecting a result produced selected result state and highlighted SVG candidates.

## API Fallback Status

Not used. This was a protected-preview browser smoke with an authenticated Cloudflare Access session.

## Files Changed

- Created `docs/handoffs/task-completions/2026-06-27-1227-12-shared-rules-protected-preview-completion.md`.
- Updated `docs/handoffs/task-completions/integration-status.md`.

No implementation files were changed.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -8 --oneline
git merge-base --is-ancestor b55a12e HEAD
curl -sS http://127.0.0.1:8770/api/version
git merge-base --is-ancestor b55a12e 4040a47
git diff --check
git diff --cached --name-only
deploy/macos/install-private-preview-launchdaemon.sh status
deploy/macos/install-private-preview-launchdaemon.sh restart
lsof -nP -iTCP:8770 -sTCP:LISTEN
```

Results:

- Branch: `feature/answer-api`.
- HEAD: `36cec1a`.
- HEAD contains `b55a12e`: yes.
- Runtime `4040a47` contains `b55a12e`: no.
- `git diff --check`: passed before docs edits.
- `git diff --cached --name-only`: no staged files at task start.
- LaunchDaemon `status` / `restart`: blocked by non-interactive `sudo`.
- Browser smoke at the exact protected URL: behavior passed with runtime-version caveat.

No focused code tests were run because no fix was made.

## Risks / Blockers

Risk: medium.

Reasons:

- Protected browser/static behavior passed the requested Explorer checks.
- The required runtime version proof failed because `/api/version` remains stale.
- The documented restart path could not run in Codex because `sudo` needs an interactive terminal.

Blocker for clean end-to-end pass:

- Run the documented restart in a local Terminal:

```bash
cd ~/Documents/Pocket\ Steel
deploy/macos/install-private-preview-launchdaemon.sh restart
curl -sS http://127.0.0.1:8770/api/version
```

Then rerun Lane 12 against the same exact protected URL and confirm `/api/version` reports `b55a12e`, `36cec1a`, or a later commit containing `b55a12e`.

## Human Decision Needed

No for focused UI/user review at the exact protected URL.

Yes for strict completion: the operator must run the interactive LaunchDaemon restart or provide an environment where `sudo` can run the documented restart path.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-27-1227-12-shared-rules-protected-preview-completion.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files.
- Any implementation files.
- Any corpus, Chroma/vector store, embedding, scraper output, private source, auth, DNS, secret, or raw asset files.

## Recommended Next Lane

- Lane 12 rerun after an interactive LaunchDaemon restart if strict runtime provenance is required.
- Otherwise, user smoke can perform focused visual/UI review at the exact direct Explorer URL with the documented runtime-version caveat.

## Commit Readiness

Safe to commit.

## Suggested Next Step

For strict end-to-end completion, run this locally and then rerun Lane 12:

```bash
cd ~/Documents/Pocket\ Steel
deploy/macos/install-private-preview-launchdaemon.sh restart
curl -sS http://127.0.0.1:8770/api/version
```

Then smoke:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=shared-rules-boundary-b55a12e
```
