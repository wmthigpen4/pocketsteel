# Lane 20 — Corrected canonical validation scoring

## Task summary

Closed the nine-line correction-confirmation loop for challenger
`at-90360274fad075f6` and reran the exact 21-feature ranker against the corrected
human truth rather than reusing the incomplete pre-correction metrics.

The corrected truth contains 124 movement decisions across both authoritative
validation cohorts. Results before the remaining preference adjudication are:

- Strict top-choice accuracy: 113/124, 91.13%.
- Top-three coverage: 124/124, 100%.
- Source mechanical validity: 124/124, 100%.
- Predicted-top mechanical validity: 124/124, 100%.
- Score-supported strict accuracy: 25/25, 100%.
- Tab-only strict accuracy: 88/99, 88.89%.
- Exact prior disagreements carried without rereview: 3.
- New, non-equivalent preference ambiguities requiring review: 8.

Implemented a corrected-canonical scorer and a focused packet builder. The
scorer:

- Verifies the exact model, corrected report, original packet, copedents,
  corrected lines, original candidates, and source adjudication.
- Rebuilds one ranker decision for every confirmed movement transition.
- Forces human-confirmed, mechanically valid movements into evaluation even
  when their earlier unreviewed derived-movement gate was conservative.
- Carries prior human preference verdicts only for byte-equivalent complete
  disagreement signatures.
- Keeps new ambiguities unresolved rather than silently accepting or rejecting
  the challenger.
- Writes no validation decisions to discovery or training and leaves sealed
  tests unopened.

The focused review is split into one licks choice and seven main-packet choices.
No corrected source line is being rereviewed; the reviewer sees only cases
where the exact challenger prefers a different mechanically valid steel
solution with the same pitches.

## Files changed

- `pocketsteel/amazing_tablature_training.py`
- `pocketsteel/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- This handoff

Ignored private score reports, disagreement reports, packets, crops, and
renderings remain beneath `corpus-private/melody-decisions/` and must not be
staged.

## Tests and checks

- Python compilation: PASS.
- Ruff on changed implementation and CLI: PASS.
- Focused Lane 20 training/extraction/model/validation suite: PASS, 242 tests.
- Corrected nine-line private scorer execution: PASS.
- Corrected disagreement packet generation: PASS, 8 choices in 2 packets.
- Local browser smoke, licks packet: PASS, 1 complete choice.
- Local browser smoke, main packet: PASS, 7 complete choices across 3 lines.
- Source crops load, exact movement context renders, submit gates work, and
  browser console has no warnings or errors: PASS.
- `git diff --check`: PASS.
- Full repository suite: PASS, 1,446 tests.

## Integration notes

The corrected scorer and packets must be regenerated after this implementation
commit so their lineage pins the clean repository HEAD and final code digests.
The eight review outcomes can then be scored without changing the challenger.

The fixed overall gate remains strictly greater than 95%. At least six of the
eight new challenger alternatives would need to be judged valid for the
accepted-choice metric to clear that floor; the exact result must be computed
from the actual review, not assumed.

If the accepted-choice gate passes, the next step is an independent Lane 15
review of the exact report and no-training/no-rereview accounting before the
rules freeze. If it fails, sealed tests remain closed and a new discovery-only
challenger cycle is required; validation verdicts must not train that cycle.

## Risk assessment

Risk: medium. Corrected scoring exposes a materially more demanding and honest
validation set. Mechanics and top-three coverage are perfect, but top-one
preference is below the fixed floor until the eight distinct alternatives are
adjudicated. No runtime behavior changed.

## Human decision needed

Yes. Review the one-choice licks packet and seven-choice main packet after they
are regenerated from the committed HEAD.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_training.py`
- `pocketsteel/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `docs/handoffs/task-completions/2026-07-23-1656-20-corrected-canonical-scoring.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- Modified prior checkpoint handoffs
- Unrelated historical untracked handoffs

## Recommended next lane

Lane 20 Amazing Tablature Training for exact adjudication, followed by Lane 15
independent QA only if the corrected gate passes.

## Commit readiness

Safe to commit

## Suggested next step

After the full suite passes, commit only the four exact files above, regenerate
the corrected score and two compact packets from that HEAD, run browser smoke,
and hand off the exact local URLs.
