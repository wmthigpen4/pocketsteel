# External Chord Reference Validation

## Summary

- Added a provider-neutral chord-reference contract with a built-in,
  no-network `user-supplied` provider.
- Added a Review-page workflow for pasting an authorized/personal reference
  chart and optional attribution URL.
- The pasted text is parsed locally, cleared after use, and never stored. Only
  chord decisions, source attribution, a derived chord digest, and validation
  results are retained with the timeline.
- Measure-aligned references can confirm a low-confidence detection or select a
  different chord only when that chord is also a close acoustic alternative.
- Unaligned charts are vocabulary-only evidence and cannot auto-accept bars.
- Source disagreements stay in the attention list; strong audio evidence is not
  overwritten.
- The staging app does not fetch or scrape Ultimate Guitar. A licensed provider
  can later register through the same adapter contract.

## Terms Decision

- Ultimate Guitar's current Terms describe content access as personal,
  non-commercial use and place registered-user tablature rights solely on or
  through its service. They also restrict copying, storage, redistribution, and
  derivative use.
- Because free human access is not an explicit automated-use license, this
  release supports local user-supplied validation and leaves automated Ultimate
  Guitar access disabled pending an authorized API or written permission.

## Files Changed

- `ui/practice-reference-validation.js`
- `ui/practice-reference-validation-v1.js`
- `ui/setup-song.js`
- `ui/setup-song-review-v2-9.js`
- `ui/setup-song.html`
- `ui/play-songs.css`
- `ui/play-songs-review-v4.css`
- `tests/test_practice_reference_validation.py`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `package.json`

## Verification

- Focused reference/analyzer/UI/server suite — 30 passed.
- Full Python suite — 1,572 passed.
- JavaScript syntax checks — passed.
- Asset-size budget — passed for 1,247 tracked files and 51 Explorer chunks.
- `git diff --check` — passed.
- Staging smoke on the current 132-bar preview verified that an unaligned chord
  list auto-accepted zero bars. A measure-aligned reference confirmed 45
  attention events and reduced the temporary preview from 45 attention bars to
  zero. The deterministic suite separately covers close-alternative correction
  and disagreement behavior.

## Safety

- Imported recording audio remains local and is not sent to a reference source.
- Reference text is not saved to IndexedDB, OPFS, project exports, or the server.
- Applying a reference to an improved-analysis preview remains preview-only
  until **Use this analysis** is selected.
- Production, DNS, Cloudflare Access, and Tunnel configuration are unchanged.

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`
