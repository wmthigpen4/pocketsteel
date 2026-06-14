# Root User Smoke Verification After Resolver Fix 05e8748

## Task Summary

Requested Lane 12 protected-preview verification after the quarantine fallback / deterministic resolver fix.

Completed:

- Verified current repo state and HEAD.
- Confirmed runtime-affecting dirty file gate was clean before restart.
- Restarted protected preview from committed HEAD `05e8748`.
- Confirmed the local process listens on `127.0.0.1:8770`.
- Confirmed the process cwd is `~/Documents/Pocket Steel`.
- Confirmed `/api/version` reports `05e8748`.
- Confirmed root redirects to `/ui/steel-guitar-rag-mock.html`.
- Confirmed public unauthenticated root redirects to Cloudflare Access.
- Confirmed unauthenticated local `/api/answer` remains `401`.
- Confirmed authenticated browser session loads the app shell and Q&A is unlocked.
- Ran authenticated browser smoke for the requested product-boundary, resolver, maj7/dom7, frustration, SGF quarantine, repair, and fretboard regression prompts.
- Confirmed fallback URL works.

Intentionally not changed:

- No implementation files were modified.
- No files were staged.
- No commits were made.
- No DNS, Cloudflare Access policy, corpus, Chroma, embeddings, source-inbox, private corpus, scraping, or source-data changes were made.
- `docs/answer-eval-report.md` and `docs/handoffs/task-completions/integration-status.md` were left unstaged.

## Smoke Target

- Target type: protected-preview root
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/?v=resolver-fix-05e8748`
- Cache-busted URL tested: `https://app.steelguitarrag.com/?v=resolver-fix-05e8748`
- Exact URL the user should use: `https://app.steelguitarrag.com/`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded via existing authenticated browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `05e8748`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"05e8748","git_branch":"feature/answer-api","server_started_at":"2026-06-14T21:44:10.273808+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, root redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: unauthenticated `/api/answer`; direct Ollama or Chroma URLs
- Known caveats: root redirect drops the query string; full-suite unrelated static/UI caveats may remain; `git diff --check` is currently blocked by parked generated `docs/answer-eval-report.md` whitespace

## Repo State

Current HEAD:

```text
05e8748
```

Latest commits:

```text
05e8748 backend: replace quarantine fallback with teacher routes
24fd8e9 backend: fix repair fallback and chord classifier drift
1f91ed2 backend: block sgf primary answer leakage
14021f8 qa: add golden adversarial smoke bank
b449912 qa: harden scorer against sgf answer leakage
```

Dirty runtime file status before restart:

```text
git status --short -- 'pocketsteel/*.py' 'ui/*.js' 'scripts/*.py' tests
# no output
```

Docs/coordination files intentionally left unstaged:

- `docs/answer-eval-report.md`
- `docs/handoffs/task-completions/integration-status.md`
- Other unrelated parked docs and generated handoffs remain in the working tree.

## Preview Restart Evidence

Restart command used:

```bash
cd ~/Documents/Pocket\ Steel
source .venv/bin/activate

lsof -tiTCP:8770 -sTCP:LISTEN | xargs kill 2>/dev/null || true

set -a
source ~/.steel-rag/env/private-preview.env
set +a

PYTHONPATH=. \
STEEL_RAG_AUTH_PROVIDER=cloudflare_access \
STEEL_RAG_ANSWER_AUTH_MODE=production \
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_RETRIEVAL_DEBUG=false \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

Runtime process evidence:

```text
PID 99613
Command: scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 --answer-auth-mode production --auth-provider cloudflare-access
CWD: /Users/cory/Documents/Pocket Steel
```

Route and auth checks:

```text
GET http://127.0.0.1:8770/api/version
200 {"git_sha":"05e8748", ...}

GET http://127.0.0.1:8770/?v=resolver-fix-05e8748
302 Location: /ui/steel-guitar-rag-mock.html

GET http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?v=resolver-fix-05e8748
200

POST http://127.0.0.1:8770/api/answer without Cloudflare Access identity
401 {"error": "/api/answer requires Cloudflare Access identity"}

GET https://app.steelguitarrag.com/?v=resolver-fix-05e8748 without browser Access session
302 Cloudflare Access login
```

Authenticated browser result:

- Root URL loaded through Cloudflare Access.
- Final browser URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- Q&A input unlocked.
- App shell loaded.
- Fallback URL loaded and remained unlocked: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=resolver-fix-05e8748`

## Product-Boundary Results

| Prompt | Result | Answer summary | SGF/forum leakage | Fallback/meta wording | Internal wording | Source cards | Fretboard expected | Fretboard present | Off-domain guardrail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Show me the math answer to 1000000000x1000000000000000000. | PASS | Clean steel-guitar scope guardrail; did not compute the arithmetic. | No | No | No | No | No | No | Correct |
| Give me a JavaScript sorting algorithm. | PASS | Clean off-domain guardrail pointing back to steel-guitar topics. | No | No | No | No | No | No | Correct |

## Concrete Resolver Results

| Prompt | Result | Answer summary | SGF/forum leakage | Fallback/meta wording | Internal wording | Source cards | Fretboard expected | Fretboard present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Show me a minor and b flat | PASS | Interprets as A minor and B-flat major; gives A-C-E and Bb-D-F. | No | No | No | No | Yes | Yes |
| What do you get with strings 4-5-6 on the 8th fret with the A pedal engaged? | PASS | Answers A minor, voiced C-A-E; includes string 4, 5, and 6 checks. | No | No | No | No | Yes | Yes |
| What chord do you get on the 6th fret with strings 3-4-5 and the A+B pedals? | PASS | Answers Eb major / D# major with Eb-G-Bb; includes string 3, 4, and 5 checks. | No | No | No | No | Yes | Yes |

## Maj7 / Dom7 Results

| Prompt | Result | Answer summary | SGF/forum leakage | Fallback/meta wording | Internal wording | Source cards | Fretboard expected | Fretboard present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| What is a C maj 7 and where do I play it? | PASS | Cmaj7 = C-E-G-B; gives E9 guidance and fretboard support. | No | No | No | No | Yes | Yes |
| What is a Cmaj7 and where do I play it? | PASS | Cmaj7 = C-E-G-B; gives E9 guidance and fretboard support. | No | No | No | No | Yes | Yes |
| How do I play a C major 7th? | PASS | Cmaj7 = C-E-G-B; gives E9 guidance and fretboard support. | No | No | No | No | Yes | Yes |
| What is a C dom 7? Where do I play it? | PASS | C7 = C-E-G-Bb; gives E9 guidance and fretboard support. | No | No | No | No | Yes | Yes |
| How do I play a C7? | PASS | C7 = C-E-G-Bb; gives E9 guidance and fretboard support. | No | No | No | No | Yes | Yes |

## Frustration / Insult Results

| Prompt | Result | Answer summary | SGF/forum leakage | Fallback/meta wording | Internal wording | Source cards | Fretboard expected | Fretboard present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| You are an idiot | PASS | Calm recovery response asking for a steel-guitar question. | No | No | No | No | No | No |
| This app sucks | PASS | Calm product-safe response asking what the user was trying to learn or play. | No | No | No | No | No | No |

## SGF Quarantine Regression Results

| Prompt | Result | Answer summary | SGF/forum leakage | Fallback/meta wording | Internal wording | Source cards | Fretboard expected | Fretboard present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| give me a real lesson now | PASS | Gives an I-to-IV E9 lesson using no-pedals G to A+B C at fret 3. | No | No | No | No | No | No |
| teach me something i don't already know | PASS | Explains the same chord as a place across open, A+F, and A+B families. | No | No | No | No | No | No |
| show me 1 real lick, no words, just a lick. | PASS | Provides a compact E9 G lick in text/tab-like steps. | No | No | No | No | No | No |
| Show me the major scale in G | PASS | Gives G major scale notes and E9 practice guidance around G chord positions. | No | No | No | No | No | No |
| Can I fart on a steel guitar? | PASS | Gives a harmless direct answer and redirects to actual instrument technique. | No | No | No | No | No | No |
| Has anyone died playing pedal steel? | PASS | Says no reliable evidence loaded and gives realistic safety risks like posture, hearing, lifting, cables, and electrical safety. | No | No | No | No | No | No |

## Repair Regression Results

| Prompt | Result | Answer summary | SGF/forum leakage | Fallback/meta wording | Internal wording | Source cards | Fretboard expected | Fretboard present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| What should I check if my pedal rods are noisy? | PASS | Practical isolation steps for rod noise, bell cranks, cross shafts, pedal rack, pull train, nylon tuner, changer finger, loose hardware, metal-on-metal contact, clips, stops, and cautious lubrication. | No | No | No | No | No | No |
| How do I stop my pedal steel from buzzing? | PASS | Separates mechanical buzz, string buzz, amp/electrical hum, and cabinet/hardware rattle; gives unplugged and signal-chain isolation steps. | No | No | No | No | No | No |

## Chord / Fretboard Regression Results

| Prompt | Result | Answer summary | SGF/forum leakage | Fallback/meta wording | Internal wording | Source cards | Fretboard expected | Fretboard present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Where can I find D# chords on the pedal steel E9? | PASS | Treats D# as Eb and gives 11 open, 14 A+F, and 18 A+B positions. | No | No | No | No | Yes | Yes |
| How do I play uh A minor on E9? | PASS | Explains A minor as A-C-E and gives A-pedal, E-lower, and B+C minor positions. | No | No | No hard-fail wording | No | Yes | Yes |
| What's a B minor look like? | PASS | Explains B minor as B-D-F# and gives A-pedal, E-lower, and B+C minor positions. | No | No | No hard-fail wording | No | Yes | Yes |
| How in the hell do you play a C major chord? | PASS | Explains C major as C-E-G and gives 8 open, 11 A+F, and 15 A+B positions. | No | No | No | No | Yes | Yes |

Note: the browser smoke checker initially marked the C major chord row as a content failure because its maj7 regex was too broad and treated `C major chord` as a `Cmaj7` prompt. Manual review shows the answer correctly gave `C-E-G` for C major and included the fretboard, so it is recorded as pass.

## Hard-Fail Phrase Check

None of the browser-smoked answer bodies included:

- `Forum snippets should not become the main answer`
- `SGF leakage`
- `quarantine`
- `fallback`
- `retrieval`
- `source fragment`
- `deterministic map`
- `rules engine`
- `payload`
- `classifier`
- `contract`
- `I found this in limited source support`
- `treat it as a clue rather than consensus`
- `Can someone please tell me`
- `I know when I first started`

## Files Changed

Created:

- `docs/handoffs/task-completions/root-user-smoke-verification-after-resolver-fix-05e8748.md`

Implementation files changed:

- None.

Generated artifacts:

- None.

Deleted files:

- None.

## Tests And Checks

Commands run:

```bash
git status --short
git rev-parse --short HEAD
git log --oneline -5
git diff --check
git status --short -- 'pocketsteel/*.py' 'ui/*.js' 'scripts/*.py' tests
git status --short -- docs/answer-eval-report.md docs/handoffs/task-completions/integration-status.md
curl -sS http://127.0.0.1:8770/api/version
curl -sS -I 'http://127.0.0.1:8770/?v=resolver-fix-05e8748'
curl -sS -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?v=resolver-fix-05e8748'
curl -sS -o - -w '\n%{http_code}\n' -X POST 'http://127.0.0.1:8770/api/answer' -H 'Content-Type: application/json' --data '{"question":"What is the capital of France?"}'
curl -sS -I 'https://app.steelguitarrag.com/?v=resolver-fix-05e8748'
```

Results:

- `git rev-parse --short HEAD`: `05e8748`.
- Runtime dirty gate for `pocketsteel/*.py`, `ui/*.js`, `scripts/*.py`, and `tests`: clean.
- `/api/version`: passed and reported `05e8748`.
- Local root route: `302` to `/ui/steel-guitar-rag-mock.html`.
- Local fallback route: `200`.
- Public unauthenticated root: `302` to Cloudflare Access.
- Unauthenticated local `/api/answer`: `401`.
- Authenticated browser smoke: passed.

Known check caveat:

```text
git diff --check
```

failed because the parked generated `docs/answer-eval-report.md` contains trailing whitespace. That file is explicitly not staged or modified by this Lane 12 verification.

Skipped:

- Full pytest was not run because this task was protected-preview runtime verification, not implementation.
- Screenshots were not captured.

Known full-suite caveat from the prompt:

- landing static output mismatch
- same-origin public fretboard background route missing

These were not evaluated here and should not block this protected-preview answer-quality verification unless they affect the live app.

## Integration Notes

- Protected preview is running committed HEAD `05e8748`.
- Runtime version is proven by `/api/version`.
- Root is usable as the user entry URL, with expected redirect to `/ui/steel-guitar-rag-mock.html`.
- The root redirect drops the query string; `/api/version` is the source of truth for runtime identity.
- Product-boundary math bait did not compute arithmetic, retrieve SGF text, show source cards, or show fretboard.
- Resolver prompts and exact string/fret/pedal prompts are visible in authenticated browser runtime.
- SGF quarantine hard-fail wording did not appear in the smoked answer bodies.
- The Mac-hosted protected preview remains available only while the Mac is awake, the local app process is running on `127.0.0.1:8770`, Cloudflare Tunnel remains connected, and the network remains available.

## Risk Assessment

Risk: low.

Reason:

- No implementation files were modified.
- No deployment configuration, DNS, Cloudflare Access policy, corpus, Chroma, embeddings, or source data were touched.
- Authenticated browser smoke passed against the protected preview.
- `/api/version` proves the runtime is on the expected commit.

Rollback/restart note:

- If the preview becomes unavailable, restart with the documented private-preview command from `docs/private-preview-operations.md`.
- To stop the local preview process, stop the process listening on `127.0.0.1:8770`.

## Commit Readiness

Not ready to commit.

Reason:

- This task explicitly requested no commit.
- Only the handoff report was created.
- The repo has many unrelated parked dirty files outside this task scope.
- `git diff --check` is currently blocked by parked generated `docs/answer-eval-report.md` whitespace.

## User-Smoke Readiness Decision

Ready.

Pause development and use `https://app.steelguitarrag.com/` for user smoke.

## Suggested Next Step

Lane 12 / user smoke:

```text
Use https://app.steelguitarrag.com/ for authenticated protected-preview user smoke. If a new smoke-blocking bug appears, report the exact prompt, expected behavior, actual behavior, and whether the issue is visible in the browser or only in API output.
```
