# Integration Status — Current Snapshot

Updated: 2026-07-10 16:32 America/Chicago

## Repository state

- Branch: `feature/answer-api`
- Current implementation: `1249201 fix melody lesson labels`
- Melody API baseline: `f37201a feat: add Melody Exercise teaching workflow`
- Melody Studio now uses Steel Guitar RAG branding. No broad repository rename is approved.

## Melody Studio

Status: **PASS — octave-aware arranger and current lesson-clarity repairs are committed, deployed to protected preview, and ready for user smoke**.

- The home header now exposes feature-gated actions in this order: Explore Fretboard, Melody Studio, Backstage.
- The technical inline Melody form was removed from home.
- `/ui/melody-workbench.html` provides four learner jobs: artist solo, song arrangement, own melody, and original practice phrase.
- Recording fields appear only for source-based jobs and are cleared when switching to source-free work.
- Phrase entry supports notes, scale degrees, literal one-string E9 tab, note/degree palette buttons, deterministic presets, sequence editing, and section counts.
- After task selection, the task-card grid collapses so the active editor/result is the page focus.
- Phrase notes are clean selectable token/pitch chips. One Selected note toolbar provides plainly labeled octave, ordering, automatic, and removal actions.
- Unmarked degrees use closest-playable octave contour by default; ascending, descending, preserve-input, and per-note octave controls are available.
- Per-note octave controls modify only the selected event; they do not re-anchor later automatic notes.
- Literal tab preserves string, fret, control state, and pitch register.
- Source links are labeled as attribution only; Melody Studio does not claim to listen to or transcribe the link.
- Results are fretboard-first. Single-note, Recommended Harmony, thirds, sixths, and chord-melody routes appear when mechanically available.
- Only Single Note and Recommended Harmony are shown initially; specialist routes live under More arrangements.
- Route, Previous/Next, and event controls visibly synchronize the selected fretboard position, active step, fixed-width tab, pedal/lever instructions, and explanation.
- Melody Studio hides the Explorer-oriented position-card strip, filters, legend, and full technical inspector. A compact Current note readout now states the active note, string(s), fret, controls, and movement cue.
- Melody tab omits artificial `Ly | step N` rows. Event selectors spell out string, fret, and pedal/lever positions, and the primary harmony route is labeled `Recommended harmony` without duplication.
- Long phrases continue through the existing `sectionNumber` contract.
- Original exercises suppress recording identity and source UI.
- Deterministic scope remains E9 in G/C major.
- Melody Studio contains no `The Turnaround` copy and now uses the same image-free amber/dark gradient background as E9 Fretboard Explorer.

Canonical contract: `docs/melody-exercise-v0.md`.
Implementation handoff: `docs/handoffs/task-completions/2026-07-10-1341-06-melody-studio-ux-rescue.md`.
Protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1354-12-melody-studio-protected-smoke.md`.
Adjustment handoff: `docs/handoffs/task-completions/2026-07-10-1404-12-melody-studio-background-protected-smoke.md`.
Arranger implementation handoff: `docs/handoffs/task-completions/2026-07-10-1432-05-06-melody-studio-arranger-upgrade.md`.
Arranger protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1435-12-melody-arranger-protected-smoke.md`.
Calm-controls protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1552-12-melody-studio-calm-controls-protected-smoke.md`.
Independent-octave protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1559-12-independent-octave-protected-smoke.md`.
Fretboard-clarity implementation handoff: `docs/handoffs/task-completions/2026-07-10-1609-06-melody-fretboard-card-cleanup.md`.
Fretboard-clarity protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1611-12-melody-fretboard-cleanup-protected-smoke.md`.
Lesson-label implementation handoff: `docs/handoffs/task-completions/2026-07-10-1631-06-melody-lesson-label-cleanup.md`.
Lesson-label protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1632-12-melody-lesson-labels-protected-smoke.md`.

## Verification

- Full pytest: `921 passed`.
- Core JavaScript syntax: passed for answer client, Melody Studio, and fretboard component.
- `git diff --check`: passed.
- Local browser smoke: pass at `http://127.0.0.1:8898/ui/melody-workbench.html?access=beta_user&v=arranger-local-20260710`.
- Protected browser smoke: pass at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lesson-labels-1249201-20260710`.
- Browser verified header ordering/gating, all task cards, stale-state cleanup, presets/sequence UI, original-source suppression, visible event/fretboard/tab synchronization, Section 2 continuation, honest source-needed guidance, fixed-width tab overflow, and no `[object Object]` or console errors.

## Protected preview

- Runtime smoke HEAD: `1249201`.
- Loopback `/api/version`: `1249201`, `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`.
- Preview refresh succeeded without `sudo` by terminating only the user-owned port-8770 listener and allowing the installed LaunchDaemon to restart it.
- Installed wrapper matches the committed wrapper.
- Cloudflare Access login succeeded in the in-app browser.
- Loopback root redirects to `/ui/steel-guitar-rag-mock.html`; home and Melody Studio routes return 200; anonymous answer calls remain 401.
- A separate protected root tab drops the cache-bust and showed the signed-out/backstage state. Use the exact direct Melody Studio URL for user smoke.
- API fallback is not browser smoke; authenticated browser behavior was verified at the direct Studio URL.

## Dirty worktree

- Unrelated tracked and untracked corpus/source/pipeline/landing-asset work remains parked.
- Protected/generated groups, corpus/vector stores, source-inbox raw/provenance, private material, and unrelated assets were not staged, deleted, reset, or cleaned.

## Next action

1. The user verifies the simplified tab and event labels at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lesson-labels-1249201-20260710`.
2. User-reported defects enter the approved end-to-end autopilot repair loop without renewed feature approval.
3. Keep the user-smoke freeze; do not begin unrelated broad feature work until this smoke closes.
