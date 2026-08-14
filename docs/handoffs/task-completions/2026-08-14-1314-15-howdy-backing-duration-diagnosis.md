# Howdy backing-track duration diagnosis

## Task summary

Diagnosed why the local Howdy player displays `0:24` even though the supplied
backing track is nearly four minutes. No runtime, musical artifact, private
asset, package, or deployment was changed.

The current companion intentionally packages a separate owner-review file
named `howdy-backing-solo-preview.mp3`. That file is 24.063991 seconds long,
and the private canonical companion sets `media.durationMs` plus its final
event/chord boundaries to 24,064 ms. This is one eight-bar form at 79.8 BPM:
`8 bars × 4 beats × 60 / 79.8 ≈ 24.06 seconds`.

The supplied source file `source/howdy-backing-track.mp3` is 237.187052
seconds, or about 3:57.2. It was not the file packaged into the local bundle.
The player is therefore accurately representing the short review artifact,
but the product decision to substitute one solo pass for the real track was
incorrect for a full backing-track experience.

## Lane classification

- Primary: `15 QA / Answer Eval`
- Follow-up: `06 UX/UI Design` plus private companion authoring
- Task type: read-only diagnosis

## Files changed

- This diagnosis handoff only.

No implementation files, private companion data, audio files, generated
bundles, or deployment state were changed.

## Tests and checks

- `ffprobe` on the packaged owner-review audio: 24.063991 seconds.
- `ffprobe` on the supplied backing track: 237.187052 seconds.
- Private companion metadata inspection: `durationMs=24064`, 54 events, first
  event starts at 0, final event/chord ends at 24,064 ms.
- Repo documentation inspection: the local packaging command explicitly names
  `howdy-backing-solo-preview.mp3`.
- Git status inspected; unrelated parked files remain untouched.

## Integration notes

Correcting this is not a safe filename swap. The browser seek limit and end
behavior come from canonical `media.durationMs`, and the authored solo,
phrases, chord ranges, looping, and highlighting currently end at 24,064 ms.

A correct full-track implementation should:

1. Package the 237.187-second source track after rights approval.
2. Author the full track/form and chord timeline through the exact audio end.
3. Identify the solo-section start/end offsets within that track.
4. Keep Phrase Practice looping the authored solo ranges while letting Chords
   play through the complete backing track.
5. Rebase solo event times to their actual full-track positions or add an
   explicit deterministic section-offset contract.
6. Regenerate and re-review chords, UI timing, print references, hashes, and
   the private companion revision.

Using only the full MP3 with the current 24-second metadata would cause the UI
to stop early and desynchronize from the audio.

## Risk assessment

Medium for the eventual fix because it changes private musical timing,
artifact hashes, chord structure, loop behavior, and approval scope. The
diagnosis itself is read-only and low risk.

## Human decision needed

Yes. Confirm that the intended Play Along experience uses the complete 3:57
backing track, while Phrase Practice continues to target and loop the specific
eight-bar solo form. That is the recommended split.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-14-1314-15-howdy-backing-duration-diagnosis.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- the three pre-existing unrelated untracked handoffs
- `output/`, `tmp/`, `.wrangler/`, private companion JSON, backing audio,
  videos, transcripts, rendered PDFs, identities, credentials, and all
  unrelated dirty files

## Recommended next lane

Lane 06/private companion authoring after the user confirms the full-track plus
solo-loop split. Lane 15 should then verify full-duration timing and section
loops independently.

## Commit readiness

Safe to commit

## Suggested next step

Authorize a scoped correction that rebuilds the canonical companion against
the complete backing track, preserves an eight-bar solo practice section, and
keeps the revised private audio/content outside Git.
