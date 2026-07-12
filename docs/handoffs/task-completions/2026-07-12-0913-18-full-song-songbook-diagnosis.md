# Melody Studio full-song songbook diagnosis

## Task summary

Diagnosed why songbook lessons show only eight notes. Two independent limitations are involved:

1. The arranger deliberately slices every melody into eight-event practice sections through `MAX_EVENTS_PER_SECTION = 8` and the existing `sectionNumber` continuation contract.
2. The catalog itself currently stores only an eight-note Amazing Grace excerpt and 15–16-note teaching phrases for the other songs. The missing remainder of each melody is not present in the score draft, so UI changes alone cannot display a complete song.

The second limitation conflicts with the approved songbook plan, which called for a complete verse/chorus melody where it fits the reviewed score limits. No runtime changes were made during this diagnosis.

## Recommended product contract

- Store one complete reviewed melody cycle for every song: the full verse melody and chorus/refrain where the song has a distinct refrain. Do not duplicate additional lyrical verses when they reuse the same melody.
- Encode written repeats once in the stored playback/lesson sequence so the learner can move linearly through the complete form.
- Replace fixed eight-event sections with musically meaningful sections aligned to phrase and measure boundaries. Default to four- or eight-measure phrases, with a practical ceiling based on rendered density rather than raw note count.
- Show the complete lead sheet before arranging and a persistent section chooser/whole-song progress indicator in the E9 lesson.
- Let Previous/Next Section move in both directions without rebuilding or losing the reviewed draft.
- Make Print offer the complete song tablature; optionally retain Current section as a secondary print choice.
- Change songbook cards from phrase labels to explicit complete-form metadata: total notes, measures, and lesson sections.
- Do not fabricate missing notes. Each complete melody/version must be checked against its named public-domain source before its catalog record is marked confirmed.

## Files changed

- `docs/handoffs/task-completions/2026-07-12-0913-18-full-song-songbook-diagnosis.md`

No implementation, catalog data, tests, feature flags, auth, deployment, corpus, source-inbox, private-data, or brand files changed.

## Tests and checks

- Inspected the approved songbook plan and implementation handoff.
- Confirmed frontend and backend both use eight-event lesson sections.
- Confirmed current catalog records contain only 8–16 melody events.
- Confirmed the repository contains no additional reviewed full-score resources for these songs.
- `git diff --check` required before closeout.

## Integration notes

- Existing `sectionNumber` behavior can remain compatible.
- `score_draft_v1` already supports up to 64 events, but some complete forms may require raising that reviewed-song-only ceiling or encoding repeat/form metadata rather than duplicating events.
- Full-song print requires assembling validated tab across every section; printing the current route's eight-event response is insufficient.
- This work is catalog/source review plus backend/UI behavior, not a cosmetic toggle.

## Risk assessment

Medium. The implementation path is straightforward, but musical/version accuracy is the product risk. Expanding phrases from memory or by repetition would be unacceptable.

## Human decision needed

No further product decision is needed if the recommended direction is approved: one complete melody cycle, including a distinct chorus/refrain once, divided at musical phrase/measure boundaries rather than every eight notes. Lyrics for additional verses remain out of scope when they reuse the same melody.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-12-0913-18-full-song-songbook-diagnosis.md`

## Files that must not be staged

Every other modified or untracked path, including corpus/source-inbox/private-data work, deployment files, `public/`, `ui/brand/`, `Neon Sign/`, generated reports, and unrelated runtime/docs files.

## Recommended next lane

After product confirmation: `18 Product / Architecture` for the full-form/source manifest, then `05 Backend / RAG Integration`, `06 UX/UI Design`, `15 QA`, `01 Repo Steward`, and `12 Self-Hosted Deployment` through the normal Autopilot loop.

## Commit readiness

Needs human review first

## Suggested next step

Approve the complete-melody-cycle and phrase-based-section direction, then replace the excerpt records with reviewed full forms and add whole-song navigation/printing while removing the fixed eight-note lesson boundary.
