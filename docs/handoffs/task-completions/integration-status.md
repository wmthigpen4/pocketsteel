# Integration Status — Current Snapshot

Updated: 2026-07-10 12:41 America/Chicago

## Repository state

- Branch: `feature/answer-api`
- Current HEAD: use `git rev-parse HEAD` after this status-refresh commit; the required implementation ancestor is `f37201a955dfed5f0d2bc3dc46fbea6ef9bb7133`.
- Latest implementation: `f37201a feat: add Melody Exercise teaching workflow`
- User-facing app name: **The Turnaround**. Existing Steel Guitar RAG names remain in technical paths and historical material; no broad rename is approved.

## Melody Exercise v0

Status: **local development complete; protected-preview update blocked by host sudo**.

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

## Protected preview blocker

- Expected runtime HEAD: the current checkout HEAD after the status refresh, containing implementation commit `f37201a`.
- Live loopback `/api/version`: `da1a763`, branch `feature/answer-api`, started 2026-07-09; Melody feature absent.
- Installed LaunchDaemon wrapper differs from the committed wrapper and must be reinstalled.
- `sudo -n true` failed because a host password is required. Codex did not request, read, or handle a password.
- Public root, canonical UI URL, and `/api/version` correctly redirect unauthenticated requests to Cloudflare Access.
- In-app protected navigation reached the Cloudflare Access email login page; login was not attempted, so protected browser behavior is **not tested**.
- No protected-preview user-smoke URL is approved yet.

Required privileged host step:

```bash
cd ~/Documents/Pocket\ Steel
deploy/macos/install-private-preview-launchdaemon.sh install
deploy/macos/install-private-preview-launchdaemon.sh restart
```

After the privileged step, Lane 12 must verify local `/api/version` equals the then-current `git rev-parse HEAD`, authenticate through Cloudflare Access, and smoke the exact cache-busted direct UI URL before user smoke begins.

## Dirty worktree

After the implementation commit, unrelated work remains parked:

- 16 tracked modified paths.
- 1,784 untracked porcelain entries.
- Tracked parked work includes README/source-policy/source-registry/current-command/source-inbox/pipeline changes and two landing brand assets.
- Protected/generated groups, corpus/vector data, source-inbox raw/provenance, private material, and unrelated assets were not staged, deleted, reset, or cleaned.

## Next action

1. The user performs the two documented sudo commands above in a trusted local terminal.
2. Codex resumes Lane 12, verifies `HEAD` and `/api/version`, runs authenticated protected browser smoke, records root/UI/API behavior, and produces one exact user-smoke URL only if green.
3. User-reported issues then enter the approved end-to-end autopilot repair loop without renewed feature approval.
