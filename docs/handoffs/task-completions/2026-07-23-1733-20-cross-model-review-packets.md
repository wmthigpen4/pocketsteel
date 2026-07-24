# Lane 20 — Cross-model corrected review packets

## Task summary

Completed the model-independent corrected-truth reuse path in the compact
preference review builder. A successor challenger can now use an earlier exact
model's fully confirmed score/tab truth while every artifact and digest remains
explicitly pinned.

The selected challenger produced 10 genuinely new preference disagreements:
three in the licks cohort and seven in the main cohort. The generated packets
contain only source-versus-challenger arrangement choices. They do not request
score recognition, tab capture, event-count, pitch, or mechanical correction.

No prior preference was silently transferred: none of the 10 new disagreement
signatures was byte-equivalent to a previously reviewed signature.

## Files changed

- `steel_guitar_rag/amazing_tablature_training.py`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-1733-20-cross-model-review-packets.md`

Private evaluation reports and review packets were appended beneath ignored
`corpus-private/melody-decisions/`. No source image, corrected truth record,
accepted discovery decision, model artifact, runtime file, UI, auth,
deployment, embedding, vector store, or sealed-test datum was modified.

## Tests and checks

- Python compilation — PASS.
- Ruff — PASS.
- Lane 20 extraction/training/model/validation suite — PASS, 278 tests.
- Full repository suite — PASS, 1,450 tests.
- `git diff --check` — PASS.
- Private corrected-truth scorer replay — PASS, 124 decisions.
- Compact review packet preparation — PASS, 10 choices across two cohorts.
- Validation decisions added to training — 0.
- Sealed-test data accessed — no.

## Integration notes

The current pre-commit score report is append-only history. After this slice is
committed, rerun the scorer and packet builder once so the final report and
packet digests pin the clean repository HEAD.

The reviewer should see only 10 blind arrangement preferences. After both
cohort submissions arrive, use the existing corrected-canonical adjudicator to
recompute the fixed overall, cohort, evidence-mode, top-three, and mechanical
gates. Do not retrain from those verdicts.

## Risk assessment

Medium. Cross-model source-truth reuse is intentionally strict and can block
if any source model artifact, correction report, packet, line digest, or
preference submission changes. This is desirable. The remaining uncertainty
is whether at least four of the 10 new alternatives are expert-acceptable,
which is necessary for the overall result to exceed 95%.

## Human decision needed

No for implementation or commit. Yes after final packet regeneration: the 10
new preference choices require expert judgment because deterministic mechanics
cannot decide whether an alternate arrangement is musically acceptable.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_training.py`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-1733-20-cross-model-review-packets.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- `docs/handoffs/task-completions/2026-07-23-1700-20-corrected-canonical-ambiguity-review-ready.md`
- `docs/handoffs/task-completions/integration-status.md`
- all unrelated historical untracked handoffs

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 20 clean scorer replay, packet
regeneration, and local review-server verification.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the three exact paths above, regenerate both packet digests from
the clean HEAD, verify their local URLs, and ask the user only for the 10
preference judgments.
