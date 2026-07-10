# Melody Studio Protected-Preview Smoke

## Task summary

Completed the authorized protected-preview restart and authenticated browser smoke for the Melody Studio UX rescue. Runtime `4a00fc2` exposes the new feature-gated header action and dedicated guided workspace. All required protected checks passed.

No auth policy, DNS, Tunnel, secrets, private environment, corpus, Chroma, source-inbox, private transcript, or visual-asset content was changed.

## Files changed

- `docs/handoffs/task-completions/integration-status.md` — refreshed to the Melody Studio protected pass and user-smoke state.
- `docs/handoffs/task-completions/2026-07-10-1354-12-melody-studio-protected-smoke.md` — this report.
- Deleted: none.
- Generated artifacts: none.

## Tests and checks

- Confirmed repo and loopback runtime SHA `4a00fc2`.
- Confirmed `/api/version` reports `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, and `features.melodyExercise=true`.
- Confirmed the installed wrapper matches the repo-managed wrapper.
- Loopback root: 302 to `/ui/steel-guitar-rag-mock.html`.
- Loopback home: 200.
- Loopback Melody Studio: 200.
- Anonymous loopback `POST /api/answer`: 401 with Cloudflare Access identity required.
- Authenticated protected browser smoke: passed.
- Implementation verification remains green: full pytest `913 passed`, JavaScript syntax passed, `git diff --check` passed, and local browser smoke passed.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-studio-4a00fc2-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-studio-4a00fc2-20260710`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: runtime `4a00fc2`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `4a00fc2`, correct branch/retrieval/auth/feature values
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: redirects to `/ui/steel-guitar-rag-mock.html`; a separate root tab showed signed-out/backstage state and dropped the query string
- Whether app root `/` is expected to work: redirect is expected; it is not the canonical smoke target
- Whether `/ui/steel-guitar-rag-mock.html` works: yes; the authenticated page exposes Melody Studio in the header
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex completed automated smoke; the user should now run the checklist below
- Do not test these URLs: do not use bare root for cache-sensitive smoke; do not use local `127.0.0.1` as proof of protected behavior
- Known caveats: API fallback is not browser smoke; automatic audio/link transcription remains out of scope

## Protected browser results

- Home header rendered Explore Fretboard, Melody Studio, and Go Backstage in the approved order.
- Melody Studio opened through the header and showed the four plain-language learner jobs.
- Switching Artist Solo to Original Exercise cleared artist/song/source values and hid recording fields.
- Original preset `1 2 3 5` rendered an exact/high-confidence, source-free, fretboard-first lesson with four steps and fixed-width tab.
- Next Note changed the visible fretboard selection from event 1 to `melody-g-section-1-event-2`, selected `2. A · S4 F5`, and updated the active tab-step and explanation.
- A ten-note phrase rendered Section 1 of 2 with eight events; Continue to Section 2 rendered two events and hid continuation.
- Recording-only artist flow preserved attribution, explained that the link is not analyzed, directed the learner to paste/build the passage, kept tab/fretboard hidden, and used no copyright-refusal language.
- No `[object Object]` and no relevant console warnings/errors appeared.

## User-smoke checklist

1. From home, confirm **Melody Studio** appears between Explore Fretboard and Backstage and opens the dedicated workspace.
2. Choose **Make a practice phrase**, select preset `1 2 3 5`, and build the lesson.
3. Click **Next note**; confirm the selected position and text change to A, string 4, fret 5.
4. Click **Edit phrase**, enter `1 2 3 4 5 6 7 1 3 2`, build, and continue to Section 2.
5. Start over, choose **Learn an artist’s solo**, enter recording identity without notes, and confirm the Studio clearly asks you to paste/build the passage without pretending it listened to the link.
6. On mobile, confirm header labels remain readable and tab scrolls horizontally without breaking spacing.

## Integration notes

- Protected automated smoke is complete. User smoke may begin.
- Any reported defect is approved for the existing end-to-end autopilot repair loop.
- Preserve the smoke freeze until the user closes this adjustment.

## Risk assessment

- Risk: low-to-medium during user smoke because this adds a new route and shared header/fretboard behavior.
- Mitigations: unchanged backend contract, feature gating, 913-test full suite, local browser smoke, and authenticated protected browser smoke.
- Rollback: revert `4a00fc2`; the prior API remains compatible.

## Human decision needed

Yes: complete the six-item user-smoke checklist and report pass/fail observations.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-10-1354-12-melody-studio-protected-smoke.md`

## Files that must not be staged

All other dirty and untracked paths.

## Recommended next lane

User smoke; Lane 01/06/15 autopilot repair only if a defect is reported.

## Commit readiness

Safe to commit

## Suggested next step

The user opens the exact cache-busted Melody Studio URL and runs the six-item checklist above.
