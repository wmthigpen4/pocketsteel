# 2026-07-04 10:01 - Lane 12 Progression Guide Protected Smoke

## Task Summary

Lane 12 was asked to restart or verify the protected-preview runtime for Progression Guide v0 and run authenticated protected-preview browser smoke.

Completed:

- Verified repo branch and HEAD.
- Verified current repo HEAD is `a33e855`, not the requested `8c2536c`; `a33e855` contains both required commits:
  - `8c2536c docs: refresh integration status for progression guide`
  - `75fc370 feat: add deterministic progression guide`
- Verified the LaunchDaemon-supervised local runtime is serving `8c2536c`.
- Confirmed Cloudflare Access browser session succeeded.
- Ran authenticated protected-preview browser smoke at the exact cache-busted URL.
- Captured screenshots for representative pass and fail states.

Intentionally not changed:

- No app runtime/UI/backend implementation files were modified.
- No DNS, Cloudflare Access policy, secrets, auth configuration, corpus, scraping, embeddings, Chroma/vector stores, private transcripts, licensing metadata, or unrelated assets were changed.
- No API fallback was used as proof of browser behavior.

## Smoke Target

- Target type: protected-preview browser smoke
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=progression-guide-v0-75fc370`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=progression-guide-v0-75fc370`
- Exact URL the user should use: not ready for user smoke due blocker below
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `8c2536c`
- Required app-code commit: `75fc370`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"8c2536c","git_branch":"feature/answer-api","server_started_at":"2026-07-04T14:44:35.629467+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes as redirect; root drops query string
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, canonical cache-busted smoke URL
- Who should test this URL: Codex only until blocker is fixed
- Do not test these URLs: root URL for cache-busted validation, because it drops the query string
- Known caveats: current repo HEAD is `a33e855`, a newer docs-only state containing `8c2536c`; runtime remained at expected `8c2536c`

## Runtime Verification

- Branch: `feature/answer-api`
- Current repo HEAD at closeout: `a33e855`
- Requested expected runtime/app HEAD: `8c2536c`
- Required app-code commit present in repo: yes, `git merge-base --is-ancestor 75fc370 HEAD` returned success
- Requested docs commit present in repo: yes, `git merge-base --is-ancestor 8c2536c HEAD` returned success
- Runtime `/api/version`: `8c2536c`
- Listener: Python on `127.0.0.1:8770`, PID `4446`
- Listener start time: `Sat Jul 4 09:44:35 2026`
- Restart notes: runtime had already been refreshed from stale `7dcd8cb` to `8c2536c` during this Lane 12 run. The documented direct `launchctl kickstart` was permission-blocked, so the user-owned listener process was terminated and the LaunchDaemon `KeepAlive` respawned it. No additional restart was performed after `/api/version` matched the requested runtime.

## Protected Browser Results

Loaded frontend assets:

- `https://app.steelguitarrag.com/ui/answer-client.js?v=progression-guide-v0-20260704`
- `https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=explorer-compare-fix-20260702b`

Root behavior:

- `https://app.steelguitarrag.com/?v=progression-guide-v0-75fc370` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- The root redirect drops the query string, so root is not suitable for cache-busted validation.

Console/page errors:

- No relevant browser console errors were recorded during the final checks.
- No `[object Object]` was observed in tested responses.

## Prompt Results

| Prompt | Result | Notes |
| --- | --- | --- |
| `Show me a C F G C progression on E9.` | PASS | Rendered progression guide/card, fretboard visible, no tab, no source cards, no empty source shell. |
| `How do I play I IV V I in C on pedal steel?` | PASS | Rendered progression guide/card, fretboard visible, no tab, no source cards, no empty source shell. |
| `Give me a beginner route through G C D G.` | PASS | Rendered progression guide/card, fretboard visible, no tab, no source cards, no empty source shell. |
| `Show me C Am Em F Dm G7 C as a pedal steel progression.` | PASS | Rendered progression guide/card, fretboard visible, no tab, no source cards, no empty source shell. |
| `Show me a 1 4 5 1 progression in G.` | PASS | Rendered progression guide/card, fretboard visible, no tab, no source cards, no empty source shell. |
| `Show me a G C D G progression route.` | PASS | Rendered progression guide/card, fretboard visible, no tab, no source cards, no empty source shell. |
| `How do I move through a simple song progression in G?` | FAIL | Returned generic specificity fallback: `I need a more specific steel-guitar question...`; no progression card, no fretboard, and visible `No sources returned` shell. |
| `Show me a G to C move.` | PASS | Movement Lesson Card rendered with deterministic tab and matching fretboard; no source cards. |
| `Show me a G major grip.` | PASS | Static fretboard-first response; full 4-5-6 G major grip; no visible tab; no source cards. |
| `Where is G on E9?` | PASS | Full G major starter positions available; answer did not default to 5-7-8 open as a full chord; no visible tab. |
| `Show me a 5-7-8 G grip.` | PASS with caveat | Correctly labels 5-7-8 as partial/color/no-3rd; no tab; no source cards. Generic glossary below the card mentions A+B, but the selected 5-7-8 grip itself is open/no-pedals and not assigned inert A+B. |
| `What are good Fender Steel King settings?` | PASS | Concrete Buddy Emmons Steel King starting block shown; source cards visible and secondary; no stale fretboard/tab/progression UI. |

## Screenshots

- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/progression-c-f-g-c-retry.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/progression-diatonic-c.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/progression-g-1451.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/progression-simple-song-g-retry.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/movement-g-to-c.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/static-g-major-grip.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/where-g-e9.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/explicit-578-g-grip.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/steel-king-settings.png`

## Tests And Checks

Run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log --oneline -8`
- `git merge-base --is-ancestor 75fc370 HEAD`
- `git merge-base --is-ancestor 8c2536c HEAD`
- `curl -sS http://127.0.0.1:8770/api/version`
- `lsof -nP -iTCP:8770 -sTCP:LISTEN`
- `ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command`
- authenticated protected-preview browser smoke at the exact cache-busted URL
- root redirect check for `https://app.steelguitarrag.com/?v=progression-guide-v0-75fc370`
- browser console error checks
- `git diff --check`

Results:

- Runtime version check passed for expected `8c2536c`.
- Browser auth passed.
- Core progression guide prompts passed.
- Regression prompt `How do I move through a simple song progression in G?` failed protected browser smoke.
- `git diff --check` passed before docs changes and after this handoff/status update.

Skipped:

- Full pytest was not rerun in Lane 12; Lane 05 already recorded full local test pass with `888 passed`.

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-07-04-1001-12-progression-guide-protected-smoke.md`

Updated:

- `docs/handoffs/task-completions/integration-status.md`

Generated artifacts:

- Screenshots under `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/`

Deleted:

- None.

## Risk Assessment

Risk: medium.

Why:

- Protected preview runtime is confirmed at the expected progression-guide version.
- Most progression-guide and regression behavior passed in the authenticated browser.
- One required natural-language progression prompt still routes to generic fallback and exposes an empty source-card shell, so user smoke should not be cleared for Progression Guide v0.

Rollback notes:

- No app code was changed in this Lane 12 run.
- If needed, restart the LaunchDaemon-supervised runtime back to a previous commit using the documented private-preview process after checking out the intended repo state.

## Blockers

User smoke is blocked by:

- `How do I move through a simple song progression in G?` returning generic specificity fallback instead of progression guide behavior.
- The same failed response shows a visible `No sources returned` source shell.

Likely owning lanes:

- Lane 05 for progression-intent routing/classification so the prompt maps to the deterministic progression guide.
- Lane 06 if the empty `No sources returned` shell should remain hidden for source-free fallback responses.

## Human Decision Needed

No immediate human decision is needed for Lane 12.

The next technical decision is whether Lane 05 should broaden the Progression Guide v0 intent matcher to include natural-language "simple song progression" phrasing. The current smoke result is enough to route that work.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-07-04-1001-12-progression-guide-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/progression-c-f-g-c-retry.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/progression-diatonic-c.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/progression-g-1451.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/progression-simple-song-g-retry.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/movement-g-to-c.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/static-g-major-grip.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/where-g-e9.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/explicit-578-g-grip.png`
- `docs/handoffs/task-completions/assets/2026-07-04-progression-guide-protected-smoke/steel-king-settings.png`

## Files That Must Not Be Staged

- Existing unrelated dirty and untracked corpus/provenance/RAG/brand/design/docs files.
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/` raw/provenance files
- `.wrangler/`
- secrets, env files, Cloudflare credentials, auth/DNS/deployment policy files

## Recommended Next Lane

Lane 05 Backend / RAG Integration.

Suggested next prompt:

```text
Lane 05 Backend / RAG Integration

Fix the protected-preview Progression Guide v0 blocker from Lane 12: the prompt "How do I move through a simple song progression in G?" routes to the generic specificity fallback and shows a visible "No sources returned" shell instead of deterministic progression-guide behavior. Keep the scope narrow: broaden the progression intent/routing only as needed, preserve source-free deterministic progression-guide responses, and add focused tests for this prompt. Do not touch corpus, scraping, Chroma, embeddings, DNS, auth, or deployment.
```

## Commit Readiness

Safe to commit with exact-path staging only after `git diff --cached --check` passes.
