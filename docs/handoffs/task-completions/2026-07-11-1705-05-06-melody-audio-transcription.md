# Melody Studio short-phrase audio transcription

## Task summary

Implemented the approved first slice of real short-phrase audio transcription for Melody Studio.

The existing Play or hum placeholder is now a unified **Record or upload audio** workflow. It accepts up to 15 seconds from the microphone or a local WAV/MP3/M4A/AAC/OGG file, performs monophonic pitch and rhythm estimation in the browser, opens a session-only editable `score_draft_v1`, and routes the reviewed notes through the existing mechanically validated E9 arranger.

The transcription engine now provides:

- fractional-MIDI pitch detection and median smoothing;
- stable-note segmentation with brief-jitter merging;
- silence/rest detection;
- tempo-based duration quantization against supported score values;
- per-note and overall confidence;
- low-confidence review warnings;
- a visible confidence explanation for the selected score event;
- explicit user-edit confirmation without converting the overall audio origin to exact transcription.

Audio is decoded on device, is never sent to `/api/answer`, and is released after transcription. The answer request contains only structured score events and compact transcription metadata with `audioRetained=false`. Audio-derived E9 lessons remain labeled `approximate` with the supplied confidence and an on-device-estimation note.

This slice is intentionally monophonic and does not claim chord separation, band separation, source-link listening, or full-recording transcription. Auth, DNS, Cloudflare policy, corpus, Chroma, scraping, source-inbox, private data, and dependency configuration were not changed.

## Files changed

- `docs/melody-exercise-v0.md`
- `steel_guitar_rag/melody_assistant.py`
- `ui/melody-score.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1705-05-06-melody-audio-transcription.md`

Deleted files: none. Generated repository artifacts: none. A temporary local WAV used during smoke preparation was written outside the repository and is not staged.

## Tests and checks

- Focused Melody/backend/same-origin suite: `38 passed`.
- Full pytest after final changes: `935 passed in 37.78s`.
- `node --check ui/melody-workbench.js` — pass.
- `node --check ui/melody-score.js` — pass.
- `node --check ui/pedal-steel-fretboard.js` — pass.
- Exact-path `git diff --check` — pass.
- Local browser workspace smoke — pass.

Pure deterministic tests prove:

- 440 Hz maps to MIDI 69;
- a two-note C4/D4 sample phrase with a gap becomes C4, rest, D4;
- durations quantize to the selected tempo grid;
- synthesized 440 Hz PCM is detected within one-half semitone;
- the draft is `score_draft_v1`, `needs_review`, session-only, and `audioRetained=false`;
- reviewed audio requests remain approximate and preserve medium confidence through the backend contract.

Smoke Target:
- Target type: local
- Result type: browser smoke plus deterministic in-process transcription tests
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-audio-transcription-20260711-3`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-audio-transcription-20260711-3`
- Exact URL the user should use: protected-preview URL to be recorded after commit/restart
- Auth required: yes
- Auth provider: local dev scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: `5342032` before implementation commit
- Version endpoint: not used for the temporary local server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local server ran from the tested worktree
- Whether app root `/` works: not repeated; direct Studio URL was the smoke target
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: covered by same-origin tests
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: production; unversioned Studio route
- Known caveats: browser automation cannot select a host audio file or approve microphone permission; real-device capture/upload is reserved for user smoke after protected verification

Local browser verification proved:

- Record or upload audio is a visible starting choice;
- the selected workspace exposes tempo, microphone, audio-file, analyze, and privacy controls;
- the file picker accepts the documented audio formats;
- the loaded controller uses the final audio-transcription cache key;
- session-only/no-upload copy is visible;
- horizontal overflow is zero and `[object Object]` is absent.

## Integration notes

- No new server endpoint or dependency was added. Audio never crosses the network.
- Both microphone and file workflows normalize through `createAudioTranscriptionDraft` into the existing score editor.
- `buildMelodyRequest` sends `accuracy=approximate`, transcription confidence, an accuracy note, and non-audio transcription metadata.
- `melody_exercise_response` now honors validated low/medium/high confidence and a bounded accuracy note for non-exact structured requests.
- Controller asset key: `melody-audio-transcription-20260711-2`.

## Risk assessment

Medium. The data/privacy boundary is low risk and local-only, but real microphone and codec behavior varies by browser/device. The correction-first score screen, confidence labels, strict 15-second limit, and explicit user smoke mitigate this.

Rollback is the implementation commit created from this exact file list.

## Human decision needed

No before commit/protected automated smoke. After those pass, the user must perform one real-device microphone or audio-file smoke because browser automation cannot grant permission or choose a host file.

## Safe-to-stage exact file list

- `docs/melody-exercise-v0.md`
- `steel_guitar_rag/melody_assistant.py`
- `ui/melody-score.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_assistant.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1705-05-06-melody-audio-transcription.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 protected-preview refresh and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact files above, verify the protected workspace/version/accuracy contract, and then hand the user one microphone-or-file smoke checklist.
