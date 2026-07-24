# Repair Fallback And Chord Classifier Drift Fix

## Task Summary

Autopilot user smoke found two backend issues:

- Repair questions for noisy pedal rods and pedal-steel buzzing could fall into meta repair/quarantine language instead of practical diagnostic guidance.
- Rooted dominant/major seventh chord questions answered correctly at runtime but drifted in the no-op classifier as off-domain.

Completed the scoped backend fix. This patch does not touch UI, deployment, auth, DNS, corpus, Chroma, embeddings, scraping, source-inbox, private data, or visual assets.

## Files Changed

- `steel_guitar_rag/curated_answers.py`
  - Added practical mechanical repair curated answers for noisy pedal rods and general pedal-steel buzzing.
  - Routed those prompts before SGF quarantine/meta fallback text can become the primary answer.
  - Added narrow gear-advice detection for pedal-rod noise and steel buzz.
- `steel_guitar_rag/answer_intent_classifier.py`
  - Added deterministic rooted dominant/major seventh chord-quality classification.
  - Kept `G7`, `G dom 7`, `G dominant 7`, `Fmaj7`, `F maj 7`, and `F major 7th` in the steel-guitar/copedent-position domain.
  - Tightened the matcher so unrelated phrases such as `7-day practice plan` still classify as practice prompts.
- `tests/test_api_search.py`
  - Added regression coverage proving the two repair prompts return practical guidance, no source cards, no warnings, no fretboard, and no internal/meta wording.
- `tests/test_answer_intent_classifier.py`
  - Added regression coverage for rooted dominant/major seventh chord classifier drift.
- `docs/handoffs/task-completions/repair-fallback-and-chord-classifier-drift-fix.md`
  - This handoff.

Generated/parked artifacts not staged:

- `docs/answer-eval-report.md` remained a dirty generated eval report and was rewritten by the legacy eval script. It is outside this scoped patch and must remain unstaged.

## Root Cause

The repair prompts were steel-guitar gear/maintenance questions, but there was no specific practical answer route for noisy pedal rods or general pedal-steel buzzing. When noisy source text was not usable, the SGF evidence gate could fall back to internal meta language instead of a player-facing diagnostic answer.

The classifier drift happened because rooted seventh chord symbols were not recognized before the off-domain fallback. A first fix was too broad around bare `7`, so `7-day practice plan` was briefly misclassified as a chord request. The final matcher now requires a rooted chord-quality shape and avoids hyphenated non-chord uses.

## Behavior Before And After

### What should I check if my pedal rods are noisy?

Before: could return meta wording about forum snippets/source leakage.

After: starts with `Start by isolating exactly where the pedal-rod noise is coming from.` It tells the player to check pedal rod, bell crank, cross shaft, pedal rack, pull train, nylon tuner, changer finger, metal-on-metal contact, loose clips, rods touching, and appropriate light lubrication.

### How do I stop my pedal steel from buzzing?

Before: could return meta wording instead of repair guidance.

After: starts with `First decide what kind of buzz it is:` and separates mechanical buzz, string buzz, amp/electrical hum, and cabinet/hardware rattle. It includes unplugged testing, cable/effects isolation, bar pressure, loose hardware, and grounding/shielding clues.

### Rooted seventh chord classifier drift

Before: `How do I play a G dom 7?`, `How do I play a G7?`, `What is a G dominant 7?`, `How do I play an F maj 7?`, `How do I play an Fmaj7?`, and `How do I play an F major 7th?` could classify as off-domain even though runtime answers were usable.

After: those classify as `domain=steel_guitar`, `intent=copedent_position`, `retrieval_allowed=false`, `needs_sources=false`, and `allowed_answer_shape=copedent_position`. Play/position forms request fretboard support.

## Tests And Checks

Passed:

```bash
git diff --check -- steel_guitar_rag/answer_intent_classifier.py steel_guitar_rag/curated_answers.py tests/test_answer_intent_classifier.py tests/test_api_search.py
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_search.py tests/test_fretboard_examples.py -q
# 360 passed
.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py tests/test_api_contract.py -q
# 68 passed
.venv/bin/python scripts/run_full_answer_quality_eval.py --output /tmp/steel_guitar_rag-repair-classifier-fix.md --json-output /tmp/steel_guitar_rag-repair-classifier-fix.json
# pass: 153, warn: 33, fail: 109; broad historical quality matrix still has backlog unrelated to this narrow slice.
```

Full pytest:

```bash
.venv/bin/python -m pytest -q
# 699 passed, 2 failed
```

The two full-suite failures are the known unrelated static/UI caveats:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

Legacy eval:

```bash
.venv/bin/python scripts/run_answer_eval.py
```

This script completed against `http://127.0.0.1:8770` and rewrote `docs/answer-eval-report.md`. That generated report is parked and must not be staged with this patch.

Worktree-wide `git diff --check`:

- Fails due to trailing whitespace in the parked/generated `docs/answer-eval-report.md`.
- Scoped diff check for this patch passed.

## Integration Notes

- The repair answers are deterministic/curated and source-free.
- The classifier remains deterministic.
- Retrieval gating is not weakened.
- Off-domain/unsafe guardrails are not changed.
- No public `/api/answer` schema changes.
- No UI files changed.

## Risk Assessment

Risk: low.

The patch is narrow:

- Two practical gear/repair prompt families get curated diagnostic guidance.
- Rooted seventh chord classifier coverage improves without changing runtime answer schema.
- The regex was tightened after catching the `7-day practice plan` false positive.

Rollback: revert the four scoped source/test files in this patch. No data migration, corpus, Chroma, UI, or deployment rollback is involved.

## Commit Readiness

Safe to commit, with exact-path staging only.

Safe-to-stage list:

- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/repair-fallback-and-chord-classifier-drift-fix.md`

Must remain unstaged:

- `docs/answer-eval-report.md`
- unrelated dirty docs/corpus/deploy/source-inbox/UI/brand/generated files already present in the worktree

## Suggested Next Step

Lane 15 QA / Answer Eval should rerun the user-smoke repair/classifier subset:

```text
Verify the repair fallback and chord classifier drift patch. Test:
- What should I check if my pedal rods are noisy?
- How do I stop my pedal steel from buzzing?
- How do I play a G dom 7?
- How do I play a G7?
- What is a G dominant 7?
- How do I play an F maj 7?
- How do I play an Fmaj7?
- How do I play an F major 7th?

Confirm no internal/meta wording appears, repair prompts are practical/source-free, and rooted seventh chord questions classify as steel-guitar/copedent-position rather than off-domain.
```
