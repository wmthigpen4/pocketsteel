# Printed sheet music to E9 tab

Printed-score import is a core Melody Studio input, not a replacement for the
deterministic arranger.

## System boundary

The flow has two independently validated stages:

1. OMR converts pixels into a reviewable `score_draft_v1`.
2. The existing arranger enumerates exact E9 realizations, applies pitch and
   mechanical gates, and optimizes the phrase.

Supervised learning is not required for the second stage. A learned ranker may
only reorder mechanically valid alternatives when a frozen comparison proves
that it improves the founder's preferred first result.

## Supported input

The UI accepts PDF, JPG, PNG, WebP, MusicXML/MXL, and MIDI. OMR is limited to
clean printed or digitally engraved Western notation. Handwriting, handwritten
chord charts, existing tablature, damaged images, and illegibly small images
must receive a specific unsupported response. Rescan guidance is shown only
when the provider supplies explicit image-quality evidence; a reader failure
or timeout must not be mislabeled as a bad upload.

For PDFs, `/api/melody/import` first accepts `inspectOnly: true` and returns
transient page thumbnails. A second request supplies `selectedPages`. Neither
request writes the source or draft to application storage.

Printed recognition uses a short-lived in-memory job. The UI polls
`/api/melody/import/jobs/{jobId}` and displays the provider's actual completed
page count. Source bytes exist only in the worker request and are cleared when
the job completes or fails; the retained job result contains only the
reviewable draft and progress metadata.

## Recognition provider boundary

`steel_guitar_rag.score_omr.ScoreOmrProvider` is the provider-neutral contract.
The default local adapter is Audiveris. An optional Homr command adapter can be
selected with `STEEL_RAG_SCORE_OMR_PROVIDER=homr`; it remains a private
benchmark/founder-test path until its license and production packaging are
reviewed. The provider catalog also records Flat Interactive OMR as a managed
benchmark candidate, but it is fail-closed until its commercial agreement,
credentials, retention, training, deletion, subprocessors, and beta
reliability have been reviewed.
Soundslice is not an adapter candidate because its documented API does not
expose its scanner.

The request result keeps these artifacts logically separate:

- transient source bytes and rendered pages;
- provider recognition output;
- normalized score events and structural diagnostics; and
- arranger output, which does not exist until the user approves the score.

## Review and correction

Scanned imports remain `needs_review`. MusicXML normalization separates part,
staff, and voice candidates; an ambiguous grand staff cannot proceed until the
user chooses the melody staff or voice. Low-confidence events and incomplete
or overfull measures are hard failures; the staff highlights only actionable
event uncertainty. The editor
offers direct semitone and octave corrections in addition to pitch, duration,
tie, rest, chord, and deletion controls. User edits set confidence to one and
clear that event's recognition flag. Playback is available before approval and
sustains tied continuations without repicking them.

The user must explicitly confirm the highlighted events, key signature, time
signature, octave, and selected melody part before arrangement. Structural
measure and tie warnings are hard gates.

## Privacy and rights

Image and PDF requests require the user to confirm that they own the material,
have permission, or otherwise have the legal right to process it. The returned
source metadata states:

- private by default;
- excluded from training;
- not retained; and
- request-only processing.

The implementation has no persistence call for source bytes or score drafts.
Do not add logging of request bodies, a shared song catalog, customer-upload
training, or a managed provider without a separately approved policy.

Public launch remains blocked on a music-copyright attorney's opinion, provider
agreement review, a public copyright contact/takedown procedure, and the normal
production backup, restore, and monitoring gates. Relevant background:
[U.S. Copyright Office fair-use guidance](https://www.copyright.gov/fair-use/more-info.html),
[17 U.S.C. §§ 101 and 106–107](https://www.copyright.gov/title17/92chap1.html),
and [Flat OMR documentation](https://flat.io/developers/docs/api/omr/).

## Acceptance

The private acceptance process and benchmark command are documented in
`docs/evaluation/printed-score-omr-acceptance.md`. Copyrighted test inputs stay
outside the repository. A provider can be selected only from measured pitch,
onset/duration, correction-count, correction-time, silent-error, and rejection
results on the same frozen cases.
