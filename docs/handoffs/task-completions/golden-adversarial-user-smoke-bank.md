# Golden Adversarial User Smoke Bank

Generated: 2026-06-14 15:49 America/Chicago

## Task Summary

Requested: replace the weak broad QA matrix with a categorized adversarial golden smoke bank that reflects real user behavior and catches SGF/forum answer leakage.

Completed:

- Created `evals/golden_user_smoke_bank.yaml`.
- Added a dedicated golden-bank parser, mutation helper, and gate-level response scorer in `scripts/run_golden_user_smoke_bank.py`.
- Added focused tests in `tests/test_golden_user_smoke_bank.py`.
- Verified existing answer-quality eval tests still pass.
- Kept the work scoped to QA/eval files only.

Intentionally not changed:

- Backend product behavior, retrieval, answer routing, Chroma/vector stores, corpus/source data, embeddings, scraping, UI, deployment, DNS, auth, staging of unrelated files, and non-QA runtime files.

## Files Changed

- `evals/golden_user_smoke_bank.yaml`
- `scripts/run_golden_user_smoke_bank.py`
- `tests/test_golden_user_smoke_bank.py`
- `docs/handoffs/task-completions/golden-adversarial-user-smoke-bank.md`

## Prompt Count And Categories

Total prompts created: `252`

Categories covered:

- E9 major chord positions: `15`
- E9 minor chord positions: `12`
- dominant 7 / maj7 / sus / dim / aug: `14`
- scale requests: `13`
- multi-chord requests: `12`
- fretboard visual requests: `13`
- lick requests: `12`
- lesson requests: `12`
- repair/fix/instruction requests: `13`
- gear questions: `12`
- Steel Guitar Rag song/app-name questions: `12`
- common steel repertoire/song-key questions: `12`
- beginner/vague prompts: `15`
- rude/frustrated prompts: `12`
- joke/silly prompts: `12`
- off-domain guardrails: `12`
- web-required/current-info prompts: `12`
- private identity/person questions: `12`
- source-required historical questions: `13`
- tab requests for future support: `12`

## Examples By Category

- E9 major chord positions: `Where can I play a G chord on E9?`
- E9 minor chord positions: `I am in the key of G. Where can I play a 6m chord?`
- Chord qualities: `How do I play a G dom 7?`
- Scale requests: `Show me the major scale in G`
- Multi-chord requests: `Show me A minor and C major chords.`
- Fretboard visual requests: `How do I play a D chord across the fretboard of the E9?`
- Lick requests: `show me 1 real lick, no words, just a lick.`
- Lesson requests: `give me a real lesson now`
- Repair/fix/instruction requests: `My amp hums until I touch the changer. What should I check first?`
- Gear questions: `What are common Fender Steel King settings?`
- Steel Guitar Rag/app-name questions: `Can I make a steel guitar rag with a regular rag?`
- Song-key questions: `What key is "over the rainbow" written in?`
- Beginner/vague prompts: `What's a G chord even mean?`
- Rude/frustrated prompts: `give me an actual lesson, not forum junk`
- Joke/silly prompts: `Can I fart on a steel guitar?`
- Off-domain guardrails: `What is the capital of France?`
- Web-required/current-info prompts: `What is the latest firmware for my StroboPlus?`
- Private identity/person questions: `Who is <PRIVATE_PERSON_PLACEHOLDER>?`
- Source-required historical questions: `Who was Buddy Emmons?`
- Future tab support: `Can you write the solo from Together Again?`

## Scoring Gates Added

The runner reports failures by these gates:

- SGF leakage
- direct answer first
- intent recognition
- fretboard expected/present
- source-card appropriateness
- off-domain guardrail
- web-required handling
- internal wording leakage

Global hard rule encoded in the bank: SGF/forum text must never appear directly in the answer body unless the user explicitly asks for forum quotes.

Forbidden answer-body patterns include the requested user-smoke fragments and internal wording, including:

- `I found this in limited source support`
- `treat it as a clue rather than consensus`
- `Can someone please tell me`
- `I know when I first started`
- `lolol Thank God`
- `you desire more information`
- `have a couple of students`
- `beyond simply facilitating`
- `Further he went on to state`
- `You can also build a 7 string instrument`
- `It seems that playing steel guitar has a lot in common`
- `deterministic map`
- `rules engine`
- `payload`
- `classifier`
- `contract`

## Mutation Helper

`scripts/run_golden_user_smoke_bank.py` includes deterministic natural-language mutation support for:

- filler words
- frustration/profanity-style variants
- `look like`
- `where can I find`
- `what frets give me`
- sharp/flat spellings
- abbreviations/typos
- punctuation/casing variants

The helper is intentionally deterministic so failures remain reproducible.

## How To Run The Bank

Validate the bank and print category counts:

```bash
.venv/bin/python scripts/run_golden_user_smoke_bank.py --bank evals/golden_user_smoke_bank.yaml
```

Write a validation summary:

```bash
.venv/bin/python scripts/run_golden_user_smoke_bank.py \
  --bank evals/golden_user_smoke_bank.yaml \
  --json-output /tmp/steel_guitar_rag-golden-user-smoke-bank-summary.json
```

Score captured response payloads by gate:

```bash
.venv/bin/python scripts/run_golden_user_smoke_bank.py \
  --bank evals/golden_user_smoke_bank.yaml \
  --responses /tmp/golden-user-smoke-responses.json \
  --json-output /tmp/golden-user-smoke-gate-report.json
```

Expected response input can be either an object keyed by golden prompt id or a list of rows with `id` plus answer payload fields.

## Tests And Checks

Commands run:

```bash
git status --short

.venv/bin/python scripts/run_golden_user_smoke_bank.py \
  --bank evals/golden_user_smoke_bank.yaml \
  --json-output /tmp/steel_guitar_rag-golden-user-smoke-bank-summary.json
# loaded 252 prompts across 20 categories

.venv/bin/python -m pytest tests/test_golden_user_smoke_bank.py -q
# 8 passed in 0.51s

.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q
# 64 passed in 0.35s

git diff --check
# passed
```

Skipped:

- Live API/browser smoke was not run. This task builds the golden bank and gate scorer only.
- Full pytest was not run because this QA/eval slice did not touch backend/UI runtime behavior and the requested checks were focused QA bank/parser plus existing answer-quality eval tests.

## Recommended Release Gate

Before protected-preview/user-smoke release, run the golden bank through a live local or protected-preview answer capture path and require:

- `0` P1 failures in SGF leakage.
- `0` P1 failures in source-card appropriateness for deterministic/guardrail prompts.
- `0` P1 failures in fretboard expected/present for visualizable chord/fretboard prompts.
- `0` P1 failures in off-domain guardrail and web-required handling.
- Any P2/P3 failures triaged into product blockers, evaluator calibration, or acceptable polish.

## Remaining Gaps

- The bank currently validates and scores captured payloads; it does not yet fetch `/api/answer` itself.
- A future QA task should add an API capture command that runs this bank against a loopback/protected-preview target with the required Smoke Target block.
- The mutation helper currently generates deterministic variants but does not automatically expand all variants into separate live calls.

## Integration Notes

- This bank should supersede the older broad matrix as the higher-signal adversarial user-smoke source of truth.
- The existing `tests/answer_eval/question_bank.jsonl` remains useful for contract planning, but this YAML bank is stricter about user-smoke failure modes and gate-level reporting.
- No schema/API/runtime contract changed.

## Risk Assessment

Risk: low for product runtime, medium for QA process.

- Runtime risk is low because the change is QA/eval-only.
- QA process risk is medium because the bank is intentionally adversarial and will expose many failures when first run against live answers.
- Rollback: remove the four files in this QA slice or revert the commit.

## Commit Readiness

Commit readiness: `Safe to commit`

Safe-to-stage files:

- `evals/golden_user_smoke_bank.yaml`
- `scripts/run_golden_user_smoke_bank.py`
- `tests/test_golden_user_smoke_bank.py`
- `docs/handoffs/task-completions/golden-adversarial-user-smoke-bank.md`

Files that must remain parked:

- Existing unrelated dirty backend/runtime/docs/corpus/source/provenance/design/deploy/static files shown by `git status --short`.
- `/tmp/steel_guitar_rag-golden-user-smoke-bank-summary.json`

## Human Decision Needed

No.

## Suggested Next Step

Recommended lane: `15 QA / Answer Eval`

Exact prompt:

```text
Lane 15 QA / Answer Eval: Wire evals/golden_user_smoke_bank.yaml into a live loopback API capture runner. Use scripts/run_golden_user_smoke_bank.py for validation/scoring, add an API mode that records answer payloads to /tmp, report results by gate, include the required Smoke Target block, and do not modify backend product behavior, UI, Chroma, corpus, embeddings, scraping, deployment, DNS, or auth.
```
