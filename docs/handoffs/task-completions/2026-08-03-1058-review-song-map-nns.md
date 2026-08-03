# Review Song Map NNS Toggle

## Summary

- Added a visible **Chords / NNS** segmented control to the Review Song Map.
- Song Map measure tiles project chord symbols through the existing Nashville
  Number System formatter using the active timeline key.
- The selected-measure inspector shows a dedicated Nashville-number readout.
- Chord editing remains in letter names and is labeled **Chord names (editing)**
  while NNS is active, preventing a display change from rewriting analysis.
- The notation choice is stored in the existing per-song practice session and
  is shared with the Play Along player.
- Works on legacy maps, improved-analysis previews, externally validated maps,
  and accepted v2 projects.

## Files Changed

- `ui/setup-song.html`
- `ui/setup-song.js`
- `ui/setup-song-review-v2-10.js`
- `ui/play-songs.css`
- `ui/play-songs-review-v5.css`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1058-review-song-map-nns.md`

## Verification

- Focused Review/practice/server suite — 23 passed.
- Full Python suite — 1,572 passed.
- Asset-size budget — passed for 1,250 tracked files and 51 Explorer chunks.
- JavaScript checks — passed.
- `git diff --check` — passed.
- Staging browser smoke — verified that the C# project changes Bar 1 from Ab
  to Nashville `5` and back, updates the selected-measure Nashville readout,
  retains letter-name editing, and restores the per-song NNS preference.

## Safety

- The toggle changes presentation only; project chords, confidence, timing,
  corrections, and external-validation metadata are unchanged.
- Production, DNS, Cloudflare Access, and Tunnel configuration are unchanged.

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`
