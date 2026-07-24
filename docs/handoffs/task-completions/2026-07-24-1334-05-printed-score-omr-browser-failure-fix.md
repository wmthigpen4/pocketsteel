# Lane 05/06 — Printed-Score Browser Failure Fix

## Task summary

Fixed the founder-reported printed-score upload failure in the local Melody
Studio test build.

The failed path had two defects:

1. The provider catalog claimed that the local path included Audiveris, but
   image recognition called only the Ollama vision model and timed out.
2. The browser redrew even small PNG uploads through a canvas before sending
   them, changing the exact bytes of already-small notation screenshots.

The runtime now invokes the mounted Audiveris application headlessly, exports
MusicXML inside a request-scoped temporary directory, parses the export into
the existing normalized score contract, and removes the temporary files when
the request ends. Small images retain their original uploaded bytes. Small
notation screenshots receive bounded grayscale autocontrast and upscaling
inside the transient Audiveris adapter.

Audiveris gets one bounded retry for its observed intermittent batch failure.
If both attempts fail after the image passes intake validation, the UI reports
an internal recognition failure instead of incorrectly blaming image
sharpness or alignment.

## Founder smoke result

- The original failure message was reproduced in the in-app browser.
- The image shown in the failure report passed visual inspection as clean,
  straight printed notation.
- The mounted Audiveris executable was confirmed available.
- Direct Audiveris smoke produced MusicXML from the score crop.
- The corrected browser upload reached the score-review editor.
- The browser preserved the original small PNG instead of canvas re-encoding
  it.
- The review editor exposed two recognized parts and highlighted structural
  inconsistencies.

The intake/runtime failure is fixed. The recognized melody is not yet
acceptable: only eight events were produced and the default selected part was
not a reliable melody extraction. This remains an OMR and staff-selection
quality failure, not an upload failure.

## Files changed

- `steel_guitar_rag/score_omr.py`
- `steel_guitar_rag/melody_import.py`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_import.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-24-1334-05-printed-score-omr-browser-failure-fix.md`

## Tests and checks

- Full Python suite: `1504 passed`
- Focused OMR/job/UI/same-origin suite: `36 passed`
- Ruff on changed Python and test modules: passed
- Node syntax check for `ui/melody-workbench.js`: passed
- `git diff --check` on the exact change set: passed
- Live in-app browser upload smoke: reached review editor

## Risks

- Audiveris output for the founder-provided score was materially incomplete.
- The MusicXML parser exposes parts, but does not yet provide sufficiently
  reliable staff-level melody selection for this score.
- Audiveris confidence is currently treated as exact MusicXML confidence;
  this overstates certainty when Audiveris omits or misclassifies events.
- The local test URL uses the starter Emmons copedent rather than the
  founder's protected account copedent.
- The protected preview still runs the previous release.

## Human decision needed

None for this bug fix. The score should remain in the private acceptance suite
as a failing OMR/staff-selection case. No public release is justified.

## Safe-to-stage exact file list

- `steel_guitar_rag/score_omr.py`
- `steel_guitar_rag/melody_import.py`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_import.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-24-1334-05-printed-score-omr-browser-failure-fix.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- unrelated modified or untracked historical handoffs
- `corpus-private/**`
- `corpus-v2/**`
- `source-inbox/**`
- `.wrangler/**`
- uploaded score images, temporary crops, Audiveris derivatives, and logs

## Recommended next lane

Lane 15 should record this score as an OMR and staff-selection acceptance
failure. Lane 05 should then add staff-aware MusicXML normalization and honest
OMR confidence before further founder testing.

## Commit readiness

Ready for exact-path commit. Not ready for protected-preview activation or
public release.
