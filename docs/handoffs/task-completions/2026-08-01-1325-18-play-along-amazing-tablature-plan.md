# Play Along Amazing Tablature integration plan

## Task summary

Revise the Amazing Grace Play Along lesson so grip changes teach a musical
purpose instead of presenting one three-string accompaniment grip throughout
the song. Reuse the existing reviewed 35-note NEW BRITAIN melody and Amazing
Tablature arrangement intelligence rather than creating a separate
one-anchor-per-bar melody model.

The recommended lesson will be **Follow the Melody**. It will preserve the
exact melody pitch and register as the highest sounding voice while Amazing
Tablature chooses an honest single note, dyad, or three-string grip for each
reviewed melody event. The current move-the-bar and same-fret routes remain
available as explicitly labeled chord-accompaniment lessons. A complete
three-string **Full Chord Melody** route is available as the advanced path.

## Product decision

The Play Along lesson selector, in default order, will contain:

1. **Follow the Melody** — recommended; the existing Amazing Tablature
   Recommended arrangement with all 35 reviewed melody events and mixed
   single-note, dyad, and triad textures.
2. **Chord Foundation · Move the Bar** — the current accompaniment route
   through common chord pockets.
3. **Chord Foundation · Stay Near Fret 3** — the current accompaniment route
   emphasizing pedals and levers with minimal bar travel.
4. **Full Chord Melody · Advanced** — the existing Amazing Tablature
   chord-melody route, using validated three-note grips while keeping the
   melody on top.

Different grips are not introduced for variety. A grip changes only when it
serves the melody, chord support, voice leading, control posture, register, or
another stated teaching purpose. The two Chord Foundation lessons must state
that their highest note is an accompaniment voice and is not necessarily the
song melody.

## Reviewed source and synchronization

- Use `amazing-grace-new-britain` as the reviewed melody source: 35 events in
  G, 3/4, with a one-beat pickup and exact pitch/register values.
- Keep the Kevin MacLeod lesson edit's authored audio, beat grid, chord
  timeline, lyrics, recording credit, and rights documentation authoritative
  for Play Along.
- Join the reviewed melody to the recording by measure and beat, including
  interpolated half-beats. Store confirmed audio-clock timestamps for the
  joined melody events; do not run an independent tempo timer.
- Review every joined onset against the audible melody lead. The public-domain
  score supplies pitch and rhythm, but it does not override the recording's
  confirmed chord at a given time.
- Preserve all 35 melody events. Do not replace them with one event per bar or
  silently omit passing notes.
- Lock the opening teaching example at fret 3:
  - pickup D4 on strings 5-6-8;
  - G4 on strings 4-5-6;
  - B4 on strings 3-4-5.

This opening demonstrates the lesson's central idea: the bar can remain at
fret 3 while the grip changes so D, G, and B become the highest voice in turn.

## Amazing Tablature integration

- Feed the synchronized melody events and the recording's active chord context
  through the existing melody arranger. Reuse its exact-pitch validation,
  arrangement roles, grip vocabulary, canonical grips, performance controls,
  path summaries, transitions, alternate positions, movement instructions,
  and selection reasons.
- Adapt the existing Recommended arrangement to **Follow the Melody** without
  changing its event count or rhythmic durations.
- Use the existing chord-melody arrangement for **Full Chord Melody**. Do not
  manufacture a triad when the exact melody pitch cannot remain the highest
  voice.
- Reuse the existing active-copedent boundary. For custom copedents, rerun the
  same melody and harmony targets against that profile. Hard pitch, register,
  chord-support, and mechanical validation remain non-negotiable.
- If a custom copedent cannot support the preferred texture, reduce triad to
  dyad to single note while preserving the exact melody pitch. If the pitch is
  mechanically unavailable, mark the event unavailable and keep both Chord
  Foundation lessons accessible.
- Prefer simple beginner control postures for the recommended route when two
  positions are otherwise equivalent. Do not substitute a different melody
  note merely to avoid a control.

## Player behavior

- Rename the current **Route** control to **Lesson** and make **Follow the
  Melody** the default.
- Add the compact objective **Keep the melody as the highest note.** when a
  melody lesson is selected. Use accompaniment-specific objectives for the two
  Chord Foundation lessons.
- Keep the current chord as the primary visual. Current instructions identify
  the actual texture: `Pick string 5`, `Play strings 5 · 6`, or `Play strings
  4 · 5 · 6`.
- Do not reintroduce duplicate current-grip bubbles in the Now card. Keep the
  compact fret reference and one instruction line.
- On the fretboard, preserve the established first-line label format of string
  number followed by its applicable pedal or lever, such as `5 A`.
- Add a second, non-color-only label to the melody-bearing string:
  `★ MELODY B4`. The current label is prominent; the upcoming label uses the
  readable muted treatment already used for the next grip.
- Current and upcoming visuals remain synchronized to `audio.currentTime`.
  Chord Foundation routes continue to advance on chord events; melody routes
  advance on the joined 35-event melody timeline.
- Keep lyrics visible as phrase context. Melody labels must use scientific
  pitch names and must not imply that the instrumental recording contains a
  sung lyric syllable.
- Preserve play/pause, restart, seeking, speed, backing volume, bar-quantized
  loops, two-bar and four-bar practice, Full Song, and Less Help.
- In Less Help, retain the playable fretboard marker but hide the melody note
  name, selection explanation, and upcoming-detail text.

## Paused teaching explanation

When a melody lesson is paused, expose a compact **Why this position?** panel
without competing with the moving player during playback.

The panel contains:

- exact melody pitch and the string carrying it;
- melody scale degree and its role against the active chord;
- supporting pitches beneath the melody;
- the canonical grip, fret, and per-string controls;
- the existing Amazing Tablature selection reason rewritten as concise learner
  copy when necessary;
- the reason for changing from the previous position;
- up to two mechanically valid alternatives that preserve the same exact
  melody pitch and register.

Alternatives are comparison-only in this slice. They show grip, fret,
controls, top note, and tradeoff such as added bar travel or a more complex
control posture. They do not mutate, persist, or locally repair the reviewed
route.

For the opening B4 example, the explanation should communicate: strings 3-4-5
put B4 above G and D; remaining on 4-5-6 at fret 3 would leave G4 on top.

## Interfaces and compatibility

- Extend the curated `PracticeProject` with an optional confirmed melody
  timeline containing stable event id, start/end timestamp, duration, source
  measure/beat, exact pitch value and label, active chord, arrangement role,
  and optional phrase context.
- Add lesson definitions that identify the existing Amazing Tablature route
  type and the current Chord Foundation route data. Do not copy the melody
  arranger's ranking logic into the browser or the curated track manifest.
- Adapt Amazing Tablature events into the existing Play Along position shape,
  including notes by string, controls by string, canonical grip, melody
  string, supporting pitches, movement, selection reason, and exact-melody
  alternatives.
- Keep the existing chord-karaoke arrange request and response compatible for
  Chord Foundation and local projects.
- If the arrange endpoint needs a new request level for melody playback, make
  it additive and versioned. The request may contain timing, chords, exact
  target pitches, and copedent context; it must not contain audio bytes.
- Device-only imports remain chord-only until they have confirmed melody data.
  Automatic melody inference from local audio is out of scope.
- Do not change Cloudflare Access, accounts, saved copedents, Melody Studio
  routes, Fretboard Explorer, Lessons, Steel Guitar Q&A, or the Songs catalog
  hierarchy.

## Test and acceptance plan

- Assert the joined lesson contains all 35 reviewed melody events with
  unchanged pitch, register, order, and rhythmic duration.
- Assert every current melody marker identifies the highest mechanical pitch
  in its displayed position.
- Assert supporting notes fit the recording's active chord or are explicitly
  labeled as melodic tension by the existing arrangement role.
- Lock the opening D4/G4/B4 fret-3 grip sequence as a golden fixture.
- Confirm Recommended arrangement events preserve their single, dyad, and
  triad textures; Full Chord Melody must never silently reduce to a false
  three-note label.
- Test open, pedal, lever, combined-control, same-fret, bar-slide, sustained,
  passing-tone, tension, resolution, phrase-ending, and unavailable events.
- Confirm all displayed control labels remain attached to the strings they
  affect.
- Confirm current and upcoming melody cues follow their authored timestamps
  within 80 ms during normal playback, slow playback, seeking, looping,
  restart, and pause/resume.
- Confirm paused alternatives preserve the exact melody pitch/register and
  cannot change the active route.
- Add landscape visual and accessibility tests at common phone sizes. Melody
  role, current/upcoming state, and control state must remain understandable
  without color.
- Regression-test both Chord Foundation routes, the 24-fret neck, lyrics,
  audio playback, the curated catalog, local-device privacy, custom copedents,
  all four existing home features, and Melody Studio's existing Amazing
  Tablature routes.
- Run focused backend/UI tests, JavaScript syntax checks, full pytest, local
  browser smoke, exact-path commit, and protected-preview smoke before user
  smoke.

## Rollout order

1. Author and review the 35-event melody-to-recording timestamp fixture.
2. Add the backend adapter from the existing Amazing Tablature routes to Play
   Along events, preserving current chord-only compatibility.
3. Add the Lesson selector, melody-string labels, and paused explanation UI in
   the current Steel Guitar RAG styles.
4. Complete focused and full regression testing plus local browser smoke.
5. Commit exact intended paths through Lane 01.
6. Update the protected preview and run authenticated smoke through Lane 12.
7. Hand the exact cache-busted Amazing Grace URL to the user for smoke testing.

## Files changed

- `docs/handoffs/task-completions/2026-08-01-1325-18-play-along-amazing-tablature-plan.md`

No runtime, catalog, melody, audio, rights, test, authentication, deployment,
corpus, private-training, or generated files changed in this planning task.

## Tests and checks

- Inspected the current Play Along project/route contract and player behavior.
- Inspected the reviewed Amazing Grace public-domain melody fixture.
- Inspected the existing Amazing Tablature mixed, pocket-first, and
  chord-melody route behavior and tests.
- `git diff --check` is required before closeout.
- Runtime tests are not required for this docs-only plan.

## Risk assessment

Medium. The required musical intelligence already exists, but the Kevin
MacLeod audio alignment must be reviewed event by event and the recording's
authored harmony must remain authoritative. A mechanically valid grip is not
sufficient unless its exact highest pitch matches the reviewed melody event.

## Human decision needed

Yes. Approve this replacement plan and its four-lesson ordering before the
YELLOW UI-flow and additive interface implementation begins.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-01-1325-18-play-along-amazing-tablature-plan.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- all unrelated modified or untracked historical handoffs
- corpus, source-inbox, private-training, generated, audio, rights, auth,
  deployment, brand, and secret-bearing files

## Recommended next lane

After approval, Lane 05 should adapt Amazing Tablature's reviewed route output
to the Play Along contract, Lane 06 should implement the teaching UI, Lane 15
should verify synchronization and regression behavior, Lane 01 should commit
exact paths, and Lane 12 should complete protected-preview smoke.

## Commit readiness

Needs human review first.

## Suggested next step

Approve this Markdown plan, then run the implementation as one bounded Play
Along/Amazing Tablature Autopilot feature scope.
