# Key-Aware Local Chord Extraction v2

## Task Summary

- Replaced independent midpoint-per-bar chord guesses with a dependency-free,
  entirely local v2 analysis pipeline: dynamic rhythm/downbeat tracking,
  tuning-corrected beat-synchronous chroma, global major/minor key estimation,
  and context-aware sequence decoding.
- Added the core country chord vocabulary: major, minor, dominant 7, minor 7,
  and `N.C.`.
- Added at-most-one half-bar split when the two-chord explanation materially
  improves the evidence.
- Added key-aware transition and duration priors, repeated-section soft
  consensus, false isolated tonic-minor suppression, possible-modulation
  warnings, confidence metadata, candidate alternatives, and concise Review
  reasons.
- Kept `practice_project_v1` unchanged while adding optional
  `timeline.analysisVersion = 2`, independent `barStartsMs`, and one or two
  chord events per bar.
- Reworked Review around a complete visual Song Map. Accepted bars are amber,
  uncertain bars are coral, and the selected bar is blue. Selecting a bar seeks
  without autoplay and opens one compact chord/downbeat editor; high-confidence
  bars are accepted automatically, corrections can be suggested across matching
  repeated bars, key changes re-decode retained candidates, and tempo/meter or
  legacy reanalysis requires a preview plus explicit acceptance.
- Updated the player to group local chord events by bar and preserve exact
  half-bar fractions through Song Map and arrangement payloads.
- Added a dormant, explicit adapter contract for a future permitted chart
  reference provider. No Ultimate Guitar retrieval or external chart request
  was added.
- Intentionally did not change production, DNS, Cloudflare Access, Tunnel,
  accounts, cloud storage, stem separation, melody behavior, or project schema.

## Files Changed

- `ui/practice-analysis-worker.js`
- `ui/practice-analysis-worker-key-aware-v2-4.js` (cache-safe symlink)
- `ui/practice-analysis-client.js`
- `ui/practice-analysis-client-key-aware-v2-4.js` (cache-safe symlink)
- `ui/songs.js`
- `ui/songs.html`
- `ui/setup-song.js`
- `ui/setup-song-key-aware-v2-3.js` (cache-safe symlink)
- `ui/setup-song.html`
- `ui/play-song.js`
- `ui/play-song.html`
- `ui/play-songs.css`
- `ui/practice-tools.js`
- `tests/test_practice_analysis_v2.py`
- `tests/test_play_songs_ui.py`
- `tests/test_practice_tools.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-0931-05-06-key-aware-chord-extraction-v2.md`

The existing cache-busted Play-Along JavaScript filenames are symlinks to the
canonical changed files, so their content updates without adding duplicate
generated assets.

## Tests And Checks

- `npm run check:js` — passed.
- `.venv/bin/pytest -q tests/test_practice_analysis_v2.py tests/test_practice_tools.py tests/test_play_songs_ui.py tests/test_same_origin_smoke_server.py`
  — `29 passed`.
- `.venv/bin/pytest -q` — `1567 passed in 80.94s` after the final analyzer and
  visual Review changes.
- `npm run check:assets` — passed for 1231 tracked files and 51 Explorer chunks.
- `npm run check:locks` — passed for five environments.
- `npm run test:worker` — attempted but unavailable because the worktree has no
  installed `vitest` executable; no dependency installation or lock change was
  made.
- `git diff --check` — passed.
- Deterministic clean, 22-cent-detuned audio fixture — C major, 4/4, 121 BPM,
  100% chord accuracy, high-confidence auto-accept, and correct half-bar split.
- Licensed Amazing Grace fixture — G major, 3/4, 75 BPM, with authored count-in
  bars recognized as `N.C.`.
- Local in-app browser upload-to-Review smoke — v2 method badges, G major,
  3/4, 75 BPM, full Song Map with accepted/attention/selected states, compact
  selected-bar editor, bar seeking without autoplay, and hidden legacy
  reanalysis action for a new v2 project.
- Protected staging preview on the user's existing country recording — A major,
  4/4, 140 BPM; common chords E7, A, F#m7, D, N.C., and G (NNS 5, 1, 6m7,
  4, N.C., and b7); no isolated tonic-minor event. The preview was not accepted,
  so the existing project and corrections remain unchanged. The current
  conservative threshold leaves 69 bars highlighted for attention.

## Integration Notes

- New optional timeline fields include `analysisVersion`, `keyMode`, independent
  tempo/meter/key confidences, `analysisState`, and `possibleModulations`.
- Each chord event may include `bar`, `startFraction`, `startMs`, `endMs`,
  `rawCandidate`, `finalSymbol`, `alternatives`, `confidence`,
  `contextualAdjusted`, `reviewReasons`, `repeatedSectionGroup`, `reviewed`, and
  `needsAttention`.
- `analysisState` retains local candidate scores so a key or mode change can
  re-run sequence decoding without decoding the original file again.
- Existing v1 projects continue opening unchanged and show the explicit
  **Reanalyze with improved method** action. The current reviewed map is not
  replaced until **Use this analysis** is selected.
- The worker and analysis client contain no fetch, XHR, beacon, import, or
  cloud fallback. OPFS and IndexedDB behavior is unchanged.

## Risk Assessment

- Medium. Automatic chord recognition remains probabilistic on dense mixes,
  modulations, weak bass, and unusual harmony. The implementation responds by
  retaining alternatives, lowering confidence, and routing uncertain/context-
  adjusted bars to Review instead of silently claiming certainty.
- Rollback is the implementation commit; existing project data is not migrated
  or overwritten automatically.

## Human Decision Needed

- No decision is needed before isolated staging smoke.
- User smoke should decide whether 69 coral bars is suitably conservative on
  the current country recording or whether a later calibration should
  auto-accept more context-decoded bars.

## Safe-To-Stage Exact File List

- `ui/practice-analysis-worker.js`
- `ui/practice-analysis-worker-key-aware-v2-4.js`
- `ui/practice-analysis-client.js`
- `ui/practice-analysis-client-key-aware-v2-4.js`
- `ui/songs.js`
- `ui/songs.html`
- `ui/setup-song.js`
- `ui/setup-song-key-aware-v2-3.js`
- `ui/setup-song.html`
- `ui/play-song.js`
- `ui/play-song.html`
- `ui/play-songs.css`
- `ui/practice-tools.js`
- `tests/test_practice_analysis_v2.py`
- `tests/test_play_songs_ui.py`
- `tests/test_practice_tools.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-0931-05-06-key-aware-chord-extraction-v2.md`

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`
- Local browser storage, temporary PCM, detached releases, LaunchAgents,
  environment files, logs, credentials, corpus/vector data, and private data.

## Recommended Next Lane

- Lane 01 exact-path commit, followed by Lane 12 isolated staging release and
  authenticated browser smoke at `test.steelguitarrag.com`.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Proceed under Repo Steward auto-approval with only the exact files above, then
deploy that commit to the staging LaunchAgent on port 8771 and smoke the
existing local-song Review/player without changing production.
