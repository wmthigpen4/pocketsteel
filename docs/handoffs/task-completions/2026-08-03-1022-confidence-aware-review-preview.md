# Confidence-Aware Review Preview

## Task Summary

- Stopped classifying every preserved v1 bar as needing attention merely because
  the legacy project predates the `reviewed` field.
- Legacy projects now show a neutral **Legacy Song Map** and direct the user to
  run the improved analysis.
- A completed v2 reanalysis now renders its own temporary Song Map immediately,
  with auto-accepted and attention bars visible before **Use this analysis** is
  selected. Preview fields are read-only and the saved project remains intact.
- Added sequence-margin confidence: each decoded chord is compared with its
  strongest local rival using acoustic score, key fit, and neighboring chord
  transitions. Context-decoded chords are accepted only when that combined
  margin is strong.
- Aligned auto-acceptance with the displayed final confidence: stable in-key
  chords can be accepted after contextual decoding, while split, borrowed, and
  out-of-key events retain stricter thresholds.
- Treats agreement between both half-bar analyses on any positive-key-prior
  chord as additional confidence; split or harmonically disputed bars do not
  receive this acceptance path.
- Strong in-key full-bar decisions can be auto-accepted even when the two
  half-bar candidates disagree weakly; low-confidence, split, and out-of-key
  decisions remain review items.
- Added `sequenceConfidence` to optional v2 chord metadata.

## Files Changed

- `ui/practice-analysis-worker.js`
- `ui/practice-analysis-worker-key-aware-v2-8.js`
- `ui/practice-analysis-client.js`
- `ui/practice-analysis-client-key-aware-v2-8.js`
- `ui/setup-song.js`
- `ui/setup-song-review-v2-8.js`
- `ui/setup-song.html`
- `ui/songs.html`
- `ui/play-songs.css`
- `ui/play-songs-review-v3.css`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1022-confidence-aware-review-preview.md`

## Verification

- Focused analyzer/UI/server suite — 30 passed.
- Full Python suite — 1,568 passed.
- Asset-size budget — passed for 1,241 tracked files and 51 Explorer chunks.
- `npm run check:js` — passed.
- `git diff --check` — passed.
- Staging smoke on the current Sammy Kershaw recording produced A major, 4/4,
  140 BPM, 87 auto-accepted bars, and 45 attention bars. Every remaining
  attention bar was below 78% final confidence.
- No public chord chart was used as ground truth; this result is validated from
  local audio and musical context only.

## Safety

- Reanalysis remains preview-only until explicitly accepted.
- The staging smoke did not select **Use this analysis**.
- Existing projects, corrections, audio, production, DNS, Cloudflare Access,
  and Tunnel configuration are unchanged.

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`
