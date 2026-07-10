# Integration Status — Current Snapshot

Updated: 2026-07-10 12:56 America/Chicago

## Repository state

- Branch: `feature/answer-api`
- Current HEAD: use `git rev-parse HEAD` after this status-refresh commit; the required implementation ancestor is `f37201a955dfed5f0d2bc3dc46fbea6ef9bb7133`.
- Latest implementation: `f37201a feat: add Melody Exercise teaching workflow`
- User-facing app name: **The Turnaround**. Existing Steel Guitar RAG names remain in technical paths and historical material; no broad rename is approved.

## Melody Exercise v0

Status: **PASS — implementation, local verification, protected-preview update, and authenticated protected browser smoke complete; ready for user smoke**.

- Artist solos, commercial recordings, and complete arrangements route to teaching/transcription behavior, never copyright refusal.
- Missing source material asks for a link, upload, passage, recording/version, or section.
- Output labels transcription, E9 adaptation, or teaching simplification and exact, approximate, or interpretive accuracy.
- Long material is divided into sections of at most eight events.
- Deterministic v0 placement is E9 in G/C major.
- A shared validated event sequence drives the stepper, fixed-width tab, and fretboard.
- Original exercises suppress source identity/cards; recording lessons preserve attribution when supplied.
- Feature flag: `STEEL_RAG_ENABLE_MELODY_EXERCISE`; app default off, approved private-preview wrapper default on.

Canonical contract: `docs/melody-exercise-v0.md`.
Implementation handoff: `docs/handoffs/task-completions/2026-07-10-1238-01-melody-exercise-v0-autopilot.md`.

## Verification

- Full pytest: `911 passed`.
- Core JavaScript syntax: passed.
- Private-preview wrapper/install shell syntax: passed.
- `git diff --check`: passed.
- Authenticated local answer evaluation: 295/295 requests reached `/api/answer` with the explicit local `beta_user` role. The previous 401-only report was replaced. Current automatic buckets: 29 pass, 76 directness, 1 formatting, 1 retrieval mismatch, 188 weak/no-source.
- Local structured API smoke: ready artist lesson with four events, approximate label, tab, fretboard, and one recording source.
- Local browser smoke: pass at `http://127.0.0.1:8898/ui/steel-guitar-rag-mock.html?access=beta_user&v=melody-v0-local-20260710`.
- Browser verified synchronized event/position IDs, source attribution, original-source suppression, fixed tab whitespace/overflow, and no `[object Object]`.
- Protected browser smoke: pass at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=melody-v0-c9e3650-20260710`.
- Protected smoke verified artist attribution, transcription/adaptation and accuracy labels, shared event/tab/fretboard state, eight-event sectioning, Section 1 of 2 continuation, source-needed guidance without refusal, source suppression for original exercises, existing progression behavior, hidden empty source areas, and no `[object Object]`.

## Protected preview

- Runtime smoke HEAD: `c9e3650` (contains implementation `f37201a`).
- Loopback `/api/version`: `c9e3650`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`.
- Installed wrapper matches the committed wrapper.
- Cloudflare Access login succeeded in the in-app browser.
- Exact protected UI URL passed authenticated browser smoke.
- Browser navigation directly to `/api/version` was blocked by the browser client; the loopback version endpoint provided exact runtime proof. API fallback is not browser smoke.
- Protected root `/` redirects to `/ui/steel-guitar-rag-mock.html`, drops the cache-bust, and the separate root tab showed the signed-out/backstage state. Use the exact direct `/ui/...?...` URL for user smoke.
- Protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1256-12-melody-protected-preview-pass.md`.

## Dirty worktree

After the implementation commit, unrelated work remains parked:

- 16 tracked modified paths.
- 1,784 untracked porcelain entries.
- Tracked parked work includes README/source-policy/source-registry/current-command/source-inbox/pipeline changes and two landing brand assets.
- Protected/generated groups, corpus/vector data, source-inbox raw/provenance, private material, and unrelated assets were not staged, deleted, reset, or cleaned.

## Next action

1. The user runs the short Melody Exercise v0 checklist at `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=melody-v0-c9e3650-20260710`.
2. User-reported issues enter the approved end-to-end autopilot repair loop without renewed feature approval.
3. After user smoke passes, choose the next approved development slice; do not begin unrelated broad feature work during the smoke freeze.
