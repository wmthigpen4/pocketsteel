# String By Play-Along Key Diagnosis

## Task Summary

- Diagnosed why Play Along presented `String By.mp3` as E-flat when the song is
  in A-flat.
- Re-ran the exact current on-device analysis worker against the supplied MP3.
- Inspected the global key estimate, section-key regions, retained raw chord
  candidates, context-adjusted chord output, relevant implementation, and
  focused key-region tests.
- No detector, UI, test, deployment, project data, or audio file was changed.

## Lane Classification

- Lane 15 QA / Answer Eval diagnosis with Lane 05 implementation implications.
- GREEN read-only analysis. Any calibration or routing change remains a
  separate implementation task.

## Finding

The failure is a deterministic feedback error in section-key classification,
not an inability to identify any A-flat evidence.

The current worker's opening/global estimate was:

- A-flat major: `1.379`
- E-flat major: `1.335`
- Reported starting key: A-flat major
- Reported key confidence: `0.503`

The section classifier then produced:

- bars 1-12: A-flat major, confidence `0.503`
- bars 13-131: E-flat major, confidence `0.542`
- bars 132-154: A-flat major, confidence `0.601`

The middle region is false. E-flat is the dominant of A-flat, so the two
interpretations share prominent E-flat and A-flat harmony. The decisive failure
is that key-region scoring is allowed to choose the best context-favored chord
candidate instead of remaining anchored to the audio-leading candidate. Once
E-flat is provisionally favored, the decoder applies E-flat key priors to the
same evidence and rewrites audible A-flat-key harmony to fit E-flat.

For the false E-flat region, the raw audio-leading counts included:

- E-flat: 32
- A-flat: 23
- B-flat minor: 23
- F minor: 12

B-flat minor and F minor support A-flat major. After the false E-flat context
was applied, the final map contained 25 B-flat-major events and only one
B-flat-minor event across the entire song. Seventeen events were directly
changed from raw `Bbm` to final `Bb`; other `Bbm` events were changed to E-flat,
E-flat 7, or B-flat 7. This creates a self-reinforcing E-flat reading and also
inflates confidence on context-adjusted chords as high as `0.98`.

## Implementation Cause

- `estimateKey` combines chroma profile, chord-context, primary-harmony, and
  cadence scores. The correct A-flat result wins globally, but only narrowly.
- `keyEvidenceScore` takes the maximum among 18 chord candidates after adding a
  key prior. This lets a weaker, context-compatible chord quality outrank the
  audio-leading quality while evaluating a possible key.
- `detectKeyRegions` allows a new key after six bars with a fixed `0.72`
  transition penalty. That penalty is too weak for this long dominant-heavy
  A-flat recording.
- `decodeSequence` then applies the selected key prior again. The false E-flat
  region therefore changes B-flat minor to B-flat major and reinforces the
  incorrect interpretation.
- The focused regression suite covers synthetic G-C-A modulations, a silent
  intro, borrowed flat-seven harmony, and seventh calibration, but not an
  unmodulated flat-key song with a prominent dominant and sustained ii-minor
  evidence.

## Tests And Checks

- `ffprobe` on the supplied MP3: passed; 195.116 seconds, 44.1 kHz stereo MP3.
- Exact worker reproduction: FFmpeg decoded the supplied file to mono 11.025
  kHz float PCM, then `ui/practice-analysis-worker.js::analyzePcm` analyzed it
  with default user-song options. Completed successfully and reproduced the
  false A-flat -> E-flat -> A-flat key journey.
- Diagnostic rerun with raw-to-final transition counts: completed successfully.
- Source inspection and `git blame` on the key estimator, region scorer, and
  sequence decoder: completed.
- `git diff --check` for this handoff: passed.
- No test suite was run because no implementation or test file changed.

## Files Changed

- Created this diagnosis handoff only.
- No generated PCM, analysis JSON, or copy of the audio was retained.

## Integration Notes

- The user's report is valid. The current code reproduces the bad E-flat
  behavior for most of the song even though the initial global estimate is
  A-flat.
- If the Review page literally displayed E-flat as the starting key from bar
  1, the stored browser project may contain an earlier analysis result. That is
  separate from, and does not negate, the reproduced false E-flat main region.
- A safe fix should make modulation evidence audio-led, prevent a proposed key
  from changing chord quality while scoring itself, use stronger/hysteretic
  modulation thresholds, and add a non-audio numeric regression derived from
  this failure without committing the private MP3.

## Risk Assessment

- Diagnosis risk: low; no runtime or user data changed.
- Prospective fix risk: medium. Key-region calibration can affect genuine
  modulations and should be evaluated against both this A-flat failure and the
  existing G-C-A modulation cases.

## Human Decision Needed

- Yes. The user asked why, not for an implementation change. A separate bug-fix
  request is needed before changing key-region scoring and chord decoding.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-08-14-1422-15-string-by-key-diagnosis.md`

## Files That Must Not Be Staged

- The supplied MP3 or any derived audio/PCM.
- `docs/handoffs/task-completions/integration-status.md` (pre-existing change).
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
  (pre-existing untracked file).
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
  (pre-existing untracked file).
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
  (pre-existing untracked file).
- `output/` (pre-existing untracked directory).

## Recommended Next Lane

- Lane 05 Backend / RAG Integration for the smallest key-region scoring fix,
  followed by Lane 15 regression evaluation on existing genuine-modulation
  fixtures and a new A-flat/E-flat ambiguity fixture.

## Commit Readiness

- Safe to commit (handoff only). No commit was requested.

## Suggested Next Step

- Explicitly request an end-to-end fix for the false A-flat-to-E-flat key-region
  promotion in Play Along, preserving genuine modulation detection.
