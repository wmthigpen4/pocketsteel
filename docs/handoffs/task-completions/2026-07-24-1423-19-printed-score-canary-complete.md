# Lane 05/06 — Printed-Score Canary Complete

## Outcome

The founder-provided printed-score screenshot is now a passing private
melody-import canary on the exact local release.

The source is recognized as G major in 2/2 cut time. The printed symbol is cut
time, not 4/4, so the earlier 4/4 acceptance condition was corrected instead
of coercing the score to an inaccurate meter.

The normalized treble candidate contains 48 notated timeline events:

- 47 sounding note segments
- 1 eighth rest
- 38 attacks after tied continuations are collapsed
- 8 complete measures

The 38 attacks exactly match the founder-provided scientific-pitch sequence.
The bass staff is isolated as a separate 8-event candidate and cannot enter
the arrangement accidentally.

## Product behavior

- PDF, PNG, JPG, and WebP intake remains provider-neutral.
- Ambiguous multi-staff output requires explicit staff or voice selection.
- The treble score may be shown provisionally for review, but confirmation and
  arrangement stay disabled until the user selects it.
- Provider output without note-level confidence is shown as structurally
  reviewable, never as fabricated 100% confidence.
- Missing key or meter, unsupported meter, and incomplete or overfull measures
  hard-stop arrangement.
- Recognition failures identify the reader failure. Rescan guidance appears
  only when a provider supplies image-quality evidence.
- Tied continuations remain visible in the editable notation but collapse into
  sustained performance events for playback and arrangement.
- The deterministic arranger produced 38 mechanically valid E9 attack events
  across two phrases, with score, tab, fretboard, movement guidance, and
  playback rendered from the approved event set.

## Exact implementation

- Commit: `0b22455d2109c6df65f10da9e912a5fb903a45eb`
- Exact release:
  `/Users/cory/.steel-rag/releases/0b22455d-printed-score-canary`
- Loopback test URL:
  `http://127.0.0.1:8791/ui/melody-workbench.html?access=beta_user&build=0b22455d`
- Runtime version endpoint reported `git_sha: 0b22455d`.
- No protected-preview or public deployment was performed.

## Private acceptance artifacts

The source image and founder-authoritative ground truth live only under:

`corpus-private/melody-import-acceptance/much-too-young/`

That directory is ignored by Git. Neither source pixels nor ground truth were
staged or committed.

The generic canary runner validates source SHA-256, exact key and meter,
timeline events, attack sequence, staff isolation, confidence honesty,
measure structure, arranger pitch parity, route pitch parity, mechanical tab
validity, and fretboard event parity.

## Verification

- Full suite after the final UI warning fix: `1507 passed`
- Focused OMR/import/UI/same-origin suite: `37 passed`
- Private acceptance canary: passed twice consecutively
- Ruff: passed
- `git diff --check`: passed
- Live in-app browser smoke on the exact release:
  - uploaded the private source through the real file chooser
  - recognized G major and 2/2 cut time
  - exposed treble 48-event and bass 8-event choices
  - kept confirmation disabled before explicit staff selection
  - cleared the selection warning after choosing treble
  - generated 17 + 21 playable attacks across the two phrases
  - rendered synchronized score, E9 tab, fretboard, and playback controls
  - produced no browser console warnings or errors

## Production gates still open

- Homr is an optional local recognition adapter selected explicitly with
  `STEEL_RAG_SCORE_OMR_PROVIDER=homr`; the default provider was not silently
  changed.
- Homr licensing must be reviewed before any production or commercial use.
- Provider privacy, retention, subprocessors, and contract terms remain launch
  gates.
- Music-copyright counsel and the upload/right-to-process policy remain launch
  gates.
- This passing canary does not authorize public deployment.
- Handwriting, handwritten chord charts, and existing tablature images remain
  unsupported.

## Safe-to-stage exact file

- `docs/handoffs/task-completions/2026-07-24-1423-19-printed-score-canary-complete.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- the existing modified canonical-validation handoff
- unrelated untracked historical handoffs
- `corpus-private/**`
- `corpus-v2/**`
- `source-inbox/**`
- `.wrangler/**`
- uploaded score images, temporary recognition files, and logs

## Commit readiness

The implementation is committed and the exact loopback release is ready for
founder testing. It is intentionally not ready for public deployment.
