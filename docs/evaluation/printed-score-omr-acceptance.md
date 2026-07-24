# Printed-score OMR acceptance

This is a private, founder-reviewed acceptance suite. It is not an external
beta program.

The manifest passed to `scripts/benchmark_score_omr.py` contains cases with:

- an identifier and input class;
- the frozen reference `score_draft_v1`;
- the candidate `score_draft_v1`;
- manual-entry and correction time;
- founder correction count;
- whether the source is a clean-page gate case; and
- one failure layer when a case fails: document intake, staff selection, OMR,
  normalization, arrangement, rendering, or export.

Keep copyrighted source pages and reference scores outside the repository.
The benchmark report contains metrics and identifiers, not source pixels.

The frozen library covers digital PDFs and screenshots, sharp photos, lead
sheets, ambiguous multi-staff pages, keys and key changes, pickups, accidentals,
ties, rests, dots, triplets, repeated notes, ledger lines, and multiple voices.
It also includes handwriting, tablature, and poor images that must fail with a
specific unsupported or rescan message.

Run:

```bash
.venv/bin/python scripts/benchmark_score_omr.py /private/path/manifest.json
```

The command exits successfully only when every encoded recognition gate passes.
Run the whole suite twice after the final OMR-adapter or arranger change before
considering the technical acceptance gate satisfied.
