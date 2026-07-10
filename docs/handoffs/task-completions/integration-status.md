# Integration Status — Current Snapshot

Updated: 2026-07-10 13:54 America/Chicago

## Repository state

- Branch: `feature/answer-api`
- Current implementation: `4a00fc2 feat: add guided Melody Studio workspace`
- Melody API baseline: `f37201a feat: add Melody Exercise teaching workflow`
- User-facing app name: **The Turnaround**. Existing Steel Guitar RAG technical paths remain; no broad rename is approved.

## Melody Studio

Status: **PASS — local and authenticated protected-preview smoke complete; ready for user smoke**.

- The home header now exposes feature-gated actions in this order: Explore Fretboard, Melody Studio, Backstage.
- The technical inline Melody form was removed from home.
- `/ui/melody-workbench.html` provides four learner jobs: artist solo, song arrangement, own melody, and original practice phrase.
- Recording fields appear only for source-based jobs and are cleared when switching to source-free work.
- Phrase entry supports notes, scale degrees, simple one-string E9 tab, note/degree palette buttons, deterministic presets, sequence editing, and section counts.
- Source links are labeled as attribution only; Melody Studio does not claim to listen to or transcribe the link.
- Results are fretboard-first. Previous/Next and event buttons visibly synchronize the selected fretboard position, active step, tab-step label, and explanation.
- Long phrases continue through the existing `sectionNumber` contract.
- Original exercises suppress recording identity and source UI.
- Deterministic scope remains E9 in G/C major.

Canonical contract: `docs/melody-exercise-v0.md`.
Implementation handoff: `docs/handoffs/task-completions/2026-07-10-1341-06-melody-studio-ux-rescue.md`.
Protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1354-12-melody-studio-protected-smoke.md`.

## Verification

- Full pytest: `913 passed`.
- Core JavaScript syntax: passed for answer client, Melody Studio, and fretboard component.
- `git diff --check`: passed.
- Local browser smoke: pass at `http://127.0.0.1:8898/ui/melody-workbench.html?access=beta_user&v=melody-studio-local-20260710`.
- Protected browser smoke: pass at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-studio-4a00fc2-20260710`.
- Browser verified header ordering/gating, all task cards, stale-state cleanup, presets/sequence UI, original-source suppression, visible event/fretboard/tab synchronization, Section 2 continuation, honest source-needed guidance, fixed-width tab overflow, and no `[object Object]` or console errors.

## Protected preview

- Runtime smoke HEAD: `4a00fc2`.
- Loopback `/api/version`: `4a00fc2`, `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`.
- Installed wrapper matches the committed wrapper.
- Cloudflare Access login succeeded in the in-app browser.
- Loopback root redirects to `/ui/steel-guitar-rag-mock.html`; home and Melody Studio routes return 200; anonymous answer calls remain 401.
- A separate protected root tab drops the cache-bust and showed the signed-out/backstage state. Use the exact direct Melody Studio URL for user smoke.
- API fallback is not browser smoke; authenticated browser behavior was verified at the direct Studio URL.

## Dirty worktree

- Unrelated tracked and untracked corpus/source/pipeline/landing-asset work remains parked.
- Protected/generated groups, corpus/vector stores, source-inbox raw/provenance, private material, and unrelated assets were not staged, deleted, reset, or cleaned.

## Next action

1. The user runs the Melody Studio checklist at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-studio-4a00fc2-20260710`.
2. User-reported defects enter the approved end-to-end autopilot repair loop without renewed feature approval.
3. Keep the user-smoke freeze; do not begin unrelated broad feature work until this smoke closes.
