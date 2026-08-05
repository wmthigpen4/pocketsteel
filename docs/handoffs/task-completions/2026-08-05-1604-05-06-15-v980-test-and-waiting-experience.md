# v980 Test Candidate and Waiting Experience

- Date: 2026-08-05
- Lanes: 05 Backend / RAG Integration, 06 UX/UI Design, 15 QA / Answer Eval
- Status: local test candidate running; waiting experience browser-smoked; not public release evidence

## Task summary

The best validated canonical-frontier development candidate was restored as the loopback service used by the site adapter. The candidate uses the v932 ten-discussion tournament, local semantic passage reranking, the top 20 passages, the Terra answer compiler, deterministic entailment checks, and conditional Luna verification.

The answer page now treats inference time as a useful waiting state instead of a blank delay. It explains that discussions and citations are being checked, rotates short steel-guitar facts, and removes the waiting card on either success or error.

## Model checkpoint

- Selected test candidate: `canonical-frontier-v980-hybrid-semantic-passages`
- Development passage Recall@10: `43/47 = 91.49%`
- Scaled development result: `16/20` answered; `14/16 = 87.5%` publishable quality among answered cases; `100%` citation support; zero first-person source voice; zero invalid tablature; median `10.58s`
- A 16-passage discussion-diverse candidate and a 24-passage focused-plus-depth candidate were tested and rejected. More context did not improve answer quality reliably.
- Remaining model problem: answer coverage and synthesis on difficult questions. It is no longer being treated as a passage-count or latency-only problem.

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-08-05-1604-05-06-15-v980-test-and-waiting-experience.md`

The loopback model implementation and evaluation artifacts are in `/Users/cory/Documents/sgf-scrape-test`; they are not repository files and must not be staged here.

## Tests and checks

- `uv run --with pytest pytest tests/test_frontend_answer_ui.py -q` — PASS, `51 passed`
- `git diff --check` — PASS
- Loopback candidate health on `127.0.0.1:8771` — PASS; architecture reported `canonical-frontier-v980-hybrid-semantic-passages`
- Browser smoke URL: `http://127.0.0.1:8772/ui/steel-guitar-rag-mock.html?access=beta_user&v=v980-waiting-smoke-20260805`
- Waiting-state browser probe — PASS: waiting card visible, source-check status visible, steel fact visible
- Final-answer browser probe — PASS on the known string-winding control: correct answer, exact supporting Forum excerpt, waiting card hidden, no browser errors
- The temporary `8772` local-dev smoke server was stopped after verification
- The production-style account boundary on `8770` was preserved; no auth setting was weakened

## Risks

- The resophonic E-tuning gauge smoke abstained. This is a model coverage failure, not a UI failure, and remains part of the next evaluation slice.
- The development set is not fresh protected release evidence. The previously exposed protected set cannot be reused for promotion.
- The loopback service is a test deployment and still reports `runtime_activation_authorized: false` by design.
- The browser client is request/response rather than token-streaming; the waiting card improves perceived latency but does not stream partial answer text.

## Human decision needed

No decision is needed to continue local test use. A later public or protected-host promotion still requires a newly constructed untouched protected evaluation and an explicit release decision.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-08-05-1604-05-06-15-v980-test-and-waiting-experience.md`

## Files that must not be staged

- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md` (pre-existing unrelated untracked file)
- `.venv/` and generated dependency state
- Corpus, Chroma, vector-index, raw evaluation, credential, and environment files

## Recommended next lane

Lane 15 should construct a new source-disjoint protected evaluation that Codex pre-reviews without exposing answers to the model-development loop. Lane 05 should then improve the unanswered/abstention bucket without altering the validated citation and tablature safeguards.

## Commit readiness

Ready for an exact-path commit of the four safe files after final diff review.
