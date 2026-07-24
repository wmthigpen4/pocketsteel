# Lane 05/06 — Printed Sheet Music to Pedal-Steel Tab

## Outcome

Implemented direct PDF, JPG, PNG, and WebP printed-score intake for Melody
Studio. PDF uploads receive transient page thumbnails and explicit page
selection. Printed recognition now runs as a short-lived in-memory job with
real completed-page progress, then opens the existing score editor with
uncertainty and structural diagnostics before the deterministic E9 arranger is
allowed to run.

Handwriting, handwritten chord charts, existing tablature, damaged files, and
unreadably small or low-contrast images fail with specific unsupported or
rescan guidance.

This is a private founder-test implementation. It does not authorize an
external beta or public launch.

## Commits

- `241d831c` — `feat(melody): add printed score OMR intake`
- `6a508e80` — `feat(melody): stream printed score progress`

## Architecture

- `steel_guitar_rag.score_omr.ScoreOmrProvider` separates pixels-to-events from
  normalization and deterministic arrangement.
- The enabled provider wraps the existing local vision reader.
- Flat Interactive OMR is registered as a fail-closed benchmark candidate; it
  is not callable without contract, privacy, credential, beta-reliability, and
  benchmark approval.
- Soundslice is intentionally not an adapter candidate because its documented
  API does not expose its scanner.
- PDFium renders selected PDF pages in memory. Source bytes are not written to
  application storage.
- The asynchronous job retains source bytes only in its worker payload and
  clears that payload at completion or failure. Poll responses never contain
  source bytes.
- Source, provider recognition, normalized events, diagnostics, and arranger
  output have separate artifact states.

## User experience

- Drag/drop and file selection accept PDF and supported image formats.
- A rights acknowledgement is mandatory for images and PDFs.
- PDFs show bounded page thumbnails and allow up to eight selected pages.
- Recognition reports actual completed-page counts.
- The original page preview and reconstructed staff remain visible in the
  review workspace.
- Only flagged events receive the uncertainty style.
- Direct corrections include semitone, octave, pitch, duration, tie, chord,
  rest, and deletion controls.
- A next-flagged-note action advances through uncertain events.
- Playback is available before approval.
- Arrangement is gated on explicit review confirmation and clean measure/tie
  validation.
- Ambiguous recognized staff lists feed the existing melody-part selector;
  explicit part selection is passed back to the provider.
- Validated alternative tab positions can lock a melody string/fret/control
  realization and deterministically reflow the surrounding phrase.

## Privacy and legal behavior

- Uploaded printed material is private, excluded from training, not retained,
  and labeled request-only in the returned source metadata.
- Request bodies are not logged by this feature.
- No searchable or shared song catalog was added.
- No customer upload is used for training.
- Public launch remains blocked on a U.S. music-copyright opinion, managed
  provider agreement review, public copyright contact/takedown procedure, and
  normal production backup, restore, and monitoring gates.

## Acceptance tooling

- Added a private manifest scorer for exact pitch, onset/duration, correction
  count, correction/manual-entry time, silent errors, and failure-layer
  attribution.
- Failure layers are document intake, staff selection, OMR, normalization,
  arrangement, rendering, and export.
- Copyrighted acceptance inputs remain outside the repository.
- The command exits successfully only when all encoded gates pass.

## Tests and checks

- Full Python suite: `1503 passed in 68.32s`
- Focused async/API/import/UI suite: `353 passed`
- Node syntax checks for `ui/melody-workbench.js` and
  `ui/melody-score.js`: passed
- Ruff on changed Python modules and tests: passed
- `pip-audit -r requirements/runtime.lock`: no known vulnerabilities
- `git diff --check`: passed
- All five dependency locks were regenerated with the pinned compiler.
- PDF skill verification:
  - generated a clean synthetic printed staff PDF;
  - inspected it with `pdfinfo`;
  - rendered it independently through Poppler;
  - visually confirmed the rendered staff and notes.
- Disposable same-origin browser QA:
  - rights gate passed;
  - authenticated transient PDF inspection returned HTTP 200;
  - one page thumbnail appeared selected;
  - progress advanced from Read file to Select pages;
  - one-page thumbnail width resolved to 180 px after layout correction;
  - no browser console errors were observed.

## Smoke target

- Target type: disposable local same-origin preview
- Exact URL:
  `http://127.0.0.1:8789/ui/melody-workbench.html?access=beta_user`
- Auth mode: local development role header
- API result: PDF inspection HTTP 200
- Source file: synthetic, generated for this smoke only
- Browser result: PASS
- Server stopped cleanly after smoke

## Protected-preview activation

- Exact detached release:
  `/Users/cory/.steel-rag/releases/6a508e80-printed-score-omr`
- Expected implementation SHA:
  `6a508e80e5e3a0a955e80211c4745655fa38fb6e`
- Exact-release preflight: PASS
- Activation: not completed because macOS requested an administrator password
- Existing protected service was left unchanged and remains ready at
  `git_sha=001014b`

Activation command:

```bash
cd "/Users/cory/Documents/Steel Guitar RAG"
STEEL_RAG_REPO_DIR=/Users/cory/.steel-rag/releases/6a508e80-printed-score-omr \
STEEL_RAG_DATA_DIR="/Users/cory/Documents/Steel Guitar RAG" \
STEEL_RAG_EXPECTED_GIT_SHA=6a508e80e5e3a0a955e80211c4745655fa38fb6e \
deploy/macos/install-private-preview-launchdaemon.sh activate
```

## Risk assessment

Medium.

The intake and review path is well bounded and fully regression-tested, but no
OMR engine has yet passed the founder's frozen accuracy/correction benchmark.
The local reader may reject or misread real-world pages, which is why every
scanned draft remains review-gated. The managed provider and public legal gates
are intentionally inactive.

## Human decisions needed

1. Run the exact protected-preview activation command and enter the local
   administrator password if private self-testing should begin.
2. Build the private frozen score manifest and record manual-entry/correction
   timing.
3. Obtain the copyright opinion and managed-provider agreement review before
   any public launch or provider activation.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-24-1312-05-printed-score-omr-intake.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- restored untracked historical handoffs
- `corpus-private/**`
- `corpus-v2/**`
- `source-inbox/**`
- `.wrangler/**`
- private acceptance files, uploads, vector stores, embeddings, caches, and
  generated PDF smoke artifacts

## Recommended next lane

Founder acceptance testing on the exact private release, followed by Lane 15
metrics review. Do not open an external beta.

## Commit readiness

Safe to commit.
