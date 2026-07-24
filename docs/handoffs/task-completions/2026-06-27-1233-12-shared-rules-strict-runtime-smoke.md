# Lane 12 Shared Rules Strict Runtime Smoke

## Task Summary

Requested a strict protected-preview rerun after the user restarted the Mac mini LaunchDaemon interactively. The goal was to prove the protected-preview runtime contains `b55a12e feat: add shared explorer music rules boundary`, not just that the browser can fetch updated static Explorer assets.

Completed:

- Inspected repo guidance, runtime/deployment guidance, integration status, and the previous Lane 12 shared-rules protected-preview handoff.
- Confirmed current branch and HEAD.
- Confirmed current HEAD contains `b55a12e`.
- Verified local `/api/version` now reports `a6abc61`, which contains `b55a12e`.
- Ran authenticated protected-preview browser smoke at the exact cache-busted Explorer URL.
- Verified root behavior separately.
- Refreshed `integration-status.md`.

Intentionally not changed:

- No app runtime, backend, UI, auth, DNS, Cloudflare Access, tunnel, scraper, corpus, Chroma/vector, embedding, private-source, or deployment config files were changed.
- No API fallback was used as browser smoke.

Overall result: **PASS**.

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
- Expected git HEAD: `a6abc61`, containing implementation commit `b55a12e`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"a6abc61","git_branch":"feature/answer-api","server_started_at":"2026-06-27T17:30:30.410070+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes after Cloudflare Access; `https://app.steelguitarrag.com/?v=shared-rules-boundary-b55a12e` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes, as a protected redirect to the app shell; it drops query strings
- Whether `/ui/steel-guitar-rag-mock.html` works: root redirect reached it and loaded the app shell
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: do not treat local `127.0.0.1` or API fallback as protected-preview browser proof
- Known caveats: direct `/ui/...?...` URLs remain required when exact cache-busting matters because root drops query strings

## Branch And Version

- Branch: `feature/answer-api`
- Starting HEAD: `a6abc61`
- Final HEAD before docs commit: `a6abc61`
- Expected implementation commit: `b55a12e`
- Current HEAD contains `b55a12e`: yes
- Local runtime `/api/version`: `a6abc61`
- Runtime contains `b55a12e`: yes
- `server_started_at`: `2026-06-27T17:30:30.410070+00:00`
- Protected page script evidence:
  - `pedal-steel-fretboard.js?v=explorer-harmonized-path-mode-20260626`
  - `e9-fretboard-explorer-data.js?v=explorer-harmonized-path-mode-20260626`
  - `e9-music-rules.js?v=shared-music-rules-20260627`
  - `e9-fretboard-explorer.js?v=shared-music-rules-20260627`

## Protected Browser Smoke Results

### Page Load And Auth

- Exact protected URL loaded after Cloudflare Access authentication.
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`.
- Page identified as E9 Fretboard Explorer.
- No Cloudflare Access login or verification-code text remained on the page.
- No `[object Object]`.
- Browser console warning/error log was empty during the smoke.
- Page-level horizontal overflow at `1280x720`: no.

### Copedent / Control Labels

- `Emmons E9`, `Day E9`, `Custom E9 (with LKV)`, and disabled `My Copedent (E9) - Coming soon in Backstage` options were present.
- Standard `Emmons E9` impact section showed learner-facing controls including `A pedal`, `B pedal`, `C pedal`, `E-raise lever`, `E-lower lever`, `D-lower lever`, and `G-lower lever`.
- Standard `Emmons E9` did not expose learner-facing `B-to-Bb` / LKV controls in the impact section.
- `Custom E9 (with LKV)` was selectable and exposed `B-to-Bb vertical` plus custom LKV-related semantics.
- Labels were readable display labels rather than raw internal object strings.

### Voicing Identifier

- `Voicing identifier` mode loaded.
- The UI showed fret, string, pedal/lever controls, and an identified `G` result for the tested default state.
- A selected SVG candidate rendered.
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
- Complete high-confidence `4-5-6-9` candidates appeared.
- Omitted-tone labeling remained present on partials.

`Cmin9` and `Cm9`, Core grip:

- Both parsed as `Cm9 (minor 9)`.
- Both showed `0 candidates` and a clear no-practical-voicing state under the current filters.
- No fallback, parser dump, debug, or internal error text appeared.

`V7 in G`, Core grip:

- Parsed target: `D7 (dominant 7)`.
- Text included `V7 in G resolves to D7`.
- Result count: `6 candidates`.
- D7 candidates showed omitted `3rd (F#)` where partial.

Selection and controls:

- Chord Finder result buttons rendered.
- Selecting a result produced selected result state and highlighted one SVG candidate.
- Notation controls remained usable near the fretboard: `Notes`, `NNS`, `Roman`, `Numbers`.

## Root Behavior

- Tested root URL: `https://app.steelguitarrag.com/?v=shared-rules-boundary-b55a12e`.
- Final URL after redirect: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Query string preservation: not preserved.
- Cloudflare Access result: authenticated session loaded the app shell.
- Q&A input was present on the app shell.
- This root behavior is acceptable for app-shell access, but the direct Explorer URL remains the correct strict cache-busted smoke URL.

## API Fallback Status

Not used. This was a protected-preview browser smoke with an authenticated Cloudflare Access session.

## Files Changed

- Created `docs/handoffs/task-completions/2026-06-27-1233-12-shared-rules-strict-runtime-smoke.md`.
- Updated `docs/handoffs/task-completions/integration-status.md`.

No implementation files were changed.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -5 --oneline
git merge-base --is-ancestor b55a12e HEAD
curl -sS http://127.0.0.1:8770/api/version
git diff --check
git diff --cached --name-only
```

Results:

- Branch: `feature/answer-api`.
- HEAD before docs commit: `a6abc61`.
- HEAD contains `b55a12e`: yes.
- Runtime `/api/version`: `a6abc61`.
- Runtime contains `b55a12e`: yes, by ancestry through current HEAD.
- `git diff --check`: passed before docs edits.
- `git diff --cached --name-only`: no staged files at task start.
- Browser smoke at the exact protected URL: passed.

No focused code tests were run because no implementation fix was made.

## Risks / Blockers

Risk: low.

Reasons:

- Runtime version proof now passes.
- Protected browser/static behavior passed the requested Explorer checks.
- No implementation or deployment configuration was changed in this task.

Known caveat:

- Root redirects to `/ui/steel-guitar-rag-mock.html` and drops query strings. Use the direct `/ui/e9-fretboard-explorer.html?...` URL for exact cache-busted Explorer smoke.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-27-1233-12-shared-rules-strict-runtime-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files.
- Corpus/source data, private source data, scraper output, Chroma/vector stores, embeddings, credentials, secrets, Cloudflare/tunnel configuration, raw design assets, and parked docs outside this scoped handoff/status update.

## Recommended Next Lane

Lane 01 Repo Steward only if a separate coordination cleanup is needed. Otherwise the exact protected Explorer URL is ready for user smoke.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Use the protected Explorer URL for user smoke:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=shared-rules-boundary-b55a12e
```
