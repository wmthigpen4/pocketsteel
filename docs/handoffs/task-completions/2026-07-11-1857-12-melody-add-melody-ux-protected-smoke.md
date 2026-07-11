# Melody Add-a-Melody UX Protected Smoke

## Task summary

Restarted the protected preview at `2c445e9` and verified the simplified Melody Studio workflow in the authenticated in-app browser. The runtime serves the three-path Add a melody design, hides import/catalog choices when the session flag is unavailable, preserves drafts behind an inline replacement decision, arranges typed phrases, returns populated drafts through Edit melody, and keeps advanced staff controls collapsed.

The initial protected controller cache key briefly produced a mixed HTML/controller build. A scoped cache-bust commit (`2c445e9`) changed the controller asset key, the listener was restarted again, and the final browser smoke passed on the fresh asset. No auth, DNS, Tunnel, environment, or deployment configuration changed.

## Files changed

- This protected-smoke handoff
- `docs/handoffs/task-completions/integration-status.md` (coordination refresh)

## Tests and checks

- Implementation commit: `7657554 Simplify Melody Studio phrase workflow`
- Cache-bust commit and final runtime HEAD: `2c445e9 Bust Melody Studio workflow cache`
- Focused final cache checks: 16 passed
- Underlying implementation focused slice: 41 passed, 300 deselected
- Full pytest: 935 passed
- Loopback `/api/version`: `2c445e9`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`
- Loopback `/`: 302 to `/ui/steel-guitar-rag-mock.html`
- Loopback home UI, Melody Studio, controller, and `/api/version`: 200
- Loopback anonymous `/api/answer`: 401 with Cloudflare Access identity required
- Authenticated protected root: redirected successfully to the canonical home UI
- Protected browser console warnings/errors: none

### Protected feature smoke

1. Loaded the exact cache-busted Studio URL and confirmed the fresh `melody-add-melody-ux-20260711-2` controller asset.
2. Entered `1 2 3 5`; sequence chips resolved to G4, A4, B4, and D5.
3. Alternate entry controls changed to Replace melody.
4. Choosing audio exposed the inline replacement panel. Keep editing closed it and preserved the typed phrase.
5. Arrange for E9 produced `Your melody exercise in G`.
6. Edit melody returned to the populated editor with phase `Review melody` and the original `1 2 3 5` draft intact.
7. Replacing the phrase with the staff editor required explicit confirmation.
8. Score setup and Score tools were closed initially. After adding G4, the phase changed to Review melody; pitch remained visible while chord/lyric/tie/articulation stayed collapsed under Selected note details.
9. The final Studio tab was reloaded to the clean Add a melody starting state and left open for user smoke.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-add-melody-ux-2c445e9-20260711`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-add-melody-ux-2c445e9-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; the existing signed-in browser loaded the Studio and completed an answer request
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `2c445e9`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `2c445e9`
- If version endpoint missing, how version is inferred: not missing locally; direct protected JSON navigation is browser-client blocked, so loopback version plus authenticated committed-asset behavior establishes runtime identity
- Whether app root `/` works: yes; protected browser redirected to the canonical home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: unversioned or earlier `melody-add-melody-ux-7657554` and `melody-lead-sheet-repair` URLs
- Known caveats: protected import/catalog choices follow the session feature flag; real microphone and host-file selection remain user-smoke boundaries; API fallback is not browser smoke

## Integration notes

- User smoke may continue at the exact URL above.
- The in-app browser is left open at the clean initial Add a melody state.
- All unrelated dirty files remain parked and unstaged.

## Risk assessment

Medium-low. This is a UI hierarchy/state change with unchanged server contracts. The mixed-cache warning was closed by the second cache key and final authenticated browser pass.

## Human decision needed

No.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-1857-12-melody-add-melody-ux-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All unrelated dirty corpus, source-inbox, private-data, deployment, public/brand, Neon Sign, RAG pipeline, README, environment, and pre-existing documentation files.

## Recommended next lane

User smoke. Any reported issue remains an end-to-end user-smoke Autopilot repair.

## Commit readiness

Safe to commit

## Suggested next step

Use the exact protected URL and try the quick phrase, audio, optional recording details, and staff-review paths without opening advanced controls unless needed.
