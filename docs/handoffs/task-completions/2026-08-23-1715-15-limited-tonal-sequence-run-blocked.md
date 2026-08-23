# Limited tonal-sequence run — blocked at route gate

## Task summary

The user approved one limited, no-training run of a deterministic tonal-transition sequence decoder over the same three private songs and explicitly prohibited continuous experimentation.

The decoder was frozen before execution with one 25-state N/major/minor state space and one fixed transition matrix: base change `-1.2`, same-root mode change `-0.45`, perfect fourth/fifth `-0.55`, relative major/minor `-0.65`, existing boundary scale `1.3`, and existing boundary bias `-2.0`. Fit count and parameter-search count were both zero. Chordify labels were reserved for post-decode scoring and did not enter decoding.

The sole invocation exited nonzero at a fail-closed route assertion. The stored local bundle routes are:

- `cowboy-take-me-away-no-steel`: `expanded-mixture`, gate probability `0.8883239119553314`;
- `string-by`: `expanded-mixture`, gate probability `0.8901415756503026`;
- `togetheragainbackingtrack-191201-185354`: `conservative-sparse`, gate probability `0.9105899461315915`.

The harness required every song to use the expanded route. It constructed model inference state for all three songs and decoded/scored the first two in memory, then stopped before decoding Together Again. Because the report was designed to publish only after all three closed, no candidate measurement was retained and no result file was created. The process was not retried and no parameter or route rule was changed.

The useful architectural finding is that a sequence layer must run after routing or implement both expanded and conservative evidence paths. Attaching the tonal decoder only to the expanded branch cannot evaluate the exact Together Again failure that motivated this run.

## Files changed

- Added this factual handoff only.

Private temporary, untracked experiment source:

- `~/Documents/Pocket Steel/tmp/chordify-upload/run_limited_tonal_sequence_check.py`
- SHA-256 `18ce2fb39cc3dc0085fc17159ec046bc5b87a16dbdf3d5ab4426f1a5fc442f0f`

No result JSON was created. No production code, model, UI, local proof bundle, audio, MIDI, threshold, or tracked test was changed.

## Tests and checks

- Frozen harness compilation under the v4 Python 3.12 environment — passed.
- Pre-run assertion that the result path did not exist — passed.
- Sole three-song invocation — failed closed with `RuntimeError: togetheragainbackingtrack-191201-185354 no longer uses the preregistered expanded route.`
- Post-run route inspection of the existing ignored local proof — confirmed the two expanded routes and one conservative route above.
- Post-run result-path check — absent, as designed on incomplete closure.
- `git status --short` before this receipt — clean.
- No browser smoke was run because no UI or retained result changed.

## Integration notes

This is not evidence that the tonal prior helps or hurts accuracy. It is also not a scientific negative result; the candidate never completed the three-song scope. Any future bounded run must choose and freeze a router-aware contract before inference, use the selected expanded or conservative logits and matching boundary stream for each song, and still score only after decoding.

## Risk assessment

**Low.** No production or generated application artifact changed, no training occurred, and the failure was fail-closed. Repeating the run without a newly frozen router-aware contract would violate the user's bounded-run instruction.

## Human decision needed

**Yes.** A second run requires explicit approval of one corrected, router-aware invocation. No parameter search or exploratory retries should be authorized.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-23-1715-15-limited-tonal-sequence-run-blocked.md`

## Files that must not be staged

- `~/Documents/Pocket Steel/tmp/chordify-upload/`
- `ui/chord-reader-proof/local-tests/`
- all private audio, MIDI, generated proof data, and experiment code

## Recommended next lane

Stop at the user checkpoint. If a second run is later approved, Lane 18 should freeze the exact post-router decoder seam, followed by one Lane 15 invocation and no retry.

## Commit readiness

Safe to commit

## Suggested next step

Report the fail-closed result in plain English and do not run another model or decoder in this task.
