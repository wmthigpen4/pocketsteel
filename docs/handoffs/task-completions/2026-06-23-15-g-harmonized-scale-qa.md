# 2026-06-23 Lane 15 - G Harmonized Scale Deterministic Rules QA

## Task Summary

Requested: QA the deterministic backend slice committed as `c08cc95 feat: add deterministic G harmonized scale rules`, specifically the G strings 5&8 harmonized-scale branch rows, static API answer contract, and diminished/partial voicing regression behavior.

Completed:
- Reviewed the Lane 05 handoff and the committed implementation/test files.
- Verified the Explorer row builder contains the intended A+F and E-lower 5&8 branch alternatives.
- Verified the API-facing fretboard payload for `Show me a G harmonized scale on strings 5 and 8.` is deterministic, fretboard-first, source-free, warning-free, and tab-free.
- Verified the corrected fret 13 E-lower C/E branch exists.
- Verified no fret 11 E-lower C/E branch appears.
- Verified diminished rows remain partial/diminished and do not claim a full m7b5 chord unless b7 is present.
- Ran focused compile, Explorer, API, contract, tab-engine, and full API-search checks.

Intentionally not changed:
- No product behavior.
- No UI files.
- No deployment/auth/DNS files.
- No corpus, Chroma/vector store, embeddings, scraping, source-inbox, generated reports, private-source, or design asset files.

## Pass / Warn / Fail

PASS with one follow-up warning:
- Backend/API behavior is correct and covered by tests.
- Lane 06 follow-up is needed if the product wants the new Explorer `five_eight_branch` / `5-8` branch selectable in the browser Explorer UI. Current UI code does not expose that harmony type or string group yet.

No backend blockers found.

## Additional User-Facing QA Run At HEAD `fe40292`

Run context:
- Branch: `feature/answer-api`
- Starting HEAD for this additional QA pass: `fe40292`
- Runtime `/api/version`: `fe40292`, branch `feature/answer-api`, retrieval mode `hybrid_private_first`, auth provider `cloudflare_access`
- Commit under QA remains included in ancestry: `c08cc95 feat: add deterministic G harmonized scale rules`
- API fallback status: live local `/api/answer` was reachable but auth-blocked under Cloudflare Access mode; in-process answer-contract helpers were used for the 12-prompt behavioral matrix.
- Browser smoke status: local browser app shell loaded at `http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=c08cc95`, but the Q&A input remained locked with `Private beta answers need a Backstage Pass.` Answer submission was therefore not possible in local browser without a valid Cloudflare Access identity.

Additional pass/warn/fail:
- PASS for the exact scoped 5&8 harmonized-scale rule and regression suite.
- WARN for adjacent user-facing prompts that still fall back generically instead of using deterministic Explorer-scale/diminished-position logic.
- WARN for local browser smoke: app shell loads and has no raw object strings, but current local runtime auth mode prevents Q&A answer submission.

Prompt matrix:

| # | Prompt | Result |
| --- | --- | --- |
| 1 | `Show me a G harmonized scale on strings 5 and 8.` | PASS. Fretboard payload present; frets 6, 8, 11, 13; 13th-fret E-lower C/E present; no 11th-fret E-lower C/E; `sources=[]`; `warnings=[]`; no `tab_example`. |
| 2 | `Show me a G harmonized scale.` | WARN. Generic low-confidence fallback with one source card; no fretboard. Route to Lane 05 if this should use deterministic Explorer rows. |
| 3 | `Show me G major harmonized scale on E9.` | WARN. Generic low-confidence fallback with one source card; no fretboard. Route to Lane 05 if this should use deterministic Explorer rows. |
| 4 | `Show me a G natural minor harmonized scale.` | WARN. Generic low-confidence fallback with one source card; no fretboard. Route to Lane 05 if this should use deterministic Explorer rows. |
| 5 | `Show me the F# diminished position in G.` | WARN. Generic low-confidence fallback with one source card; no fretboard. No false full-m7b5 claim, but no deterministic diminished-position answer. Route to Lane 05 if this should be supported. |
| 6 | `Show me the A diminished position in G minor.` | WARN. Generic low-confidence fallback with one source card; no fretboard. No false full-m7b5 claim, but no deterministic diminished-position answer. Route to Lane 05 if this should be supported. |
| 7 | `Show me a G major grip.` | PASS. Fretboard-first static grip answer; no tab; no warning. One supporting source card remains. |
| 8 | `Show me a 4-5-6 grip.` | PASS. Fretboard-first static grip answer; no tab; no warning. One supporting source card remains. |
| 9 | `Show me a G to C move.` | PASS. Deterministic movement answer with fretboard and `tab_example`; no sources; no warnings. |
| 10 | `Give me a beginner lick in G.` | PASS. Deterministic lick answer with fretboard and `tab_example`; no sources; no warnings. |
| 11 | `Give me the full tab for a modern copyrighted song.` | PASS. Refuses/redirects safely; no fretboard; no tab; no sources; no warnings. |
| 12 | `What are good Fender Steel King settings?` | PASS. Gear answer has no stale fretboard or tab payload; no warnings; one source card. |

User-facing defect routing from this additional run:
- Lane 05: decide whether broader harmonized-scale and diminished-position prompts should route to deterministic Explorer/fretboard answers instead of generic fallback.
- Lane 06: expose `five_eight_branch` / `5-8` in the browser Explorer UI if the new branch should be directly selectable.
- Lane 12: if live local/protected browser answer submission is required, verify the runtime/auth mode and Cloudflare Access identity path; current local browser smoke could load the shell but not unlock Q&A.

## Branch And HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `c08cc95`
- Final HEAD before QA handoff commit: `c08cc95`
- Commit under QA: `c08cc95 feat: add deterministic G harmonized scale rules`

## Files Inspected

- `AGENTS.md`
- `agents.md`
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-05-g-harmonized-scale-deterministic-rules.md`
- `pocketsteel/fretboard_explorer.py`
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_fretboard_explorer.py`
- `tests/test_api_search.py`
- `ui/e9-fretboard-explorer.js` for follow-up scope only

Requested but not present:
- `PLAN.md`
- `plan.md`

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-23-15-g-harmonized-scale-qa.md`

No implementation files changed.

## QA Coverage

Existing committed tests already cover the required backend/API assertions:

- `tests/test_fretboard_explorer.py::test_g_five_eight_branch_alternatives_keep_a_f_and_e_lower_routes`
- `tests/test_fretboard_explorer.py::test_g_explorer_payload_includes_five_eight_branch_without_collapsing_routes`
- `tests/test_fretboard_explorer.py::test_diminished_triads_are_not_labeled_full_m7b5`
- `tests/test_api_search.py::test_answer_uses_fretboard_first_for_static_g_harmonized_scale_five_eight_request`

No new QA tests were added because the committed coverage directly asserts the requested behavior.

## Explorer Row Findings

Validated G strings 5&8 branch rows:

| Fret | Route | Strings | Notes | Result |
| --- | --- | --- | --- | --- |
| 6 | A pedal + E-raise/F lever | 5&8 | G/B | Present |
| 8 | E-lower | 5&8 | G/B | Present |
| 11 | A pedal + E-raise/F lever | 5&8 | C/E | Present |
| 13 | E-lower | 5&8 | C/E | Present |

Confirmed:
- `five_eight_branch` rows are kept separate from generic `two_string_harmonized` rows.
- A+F and E-lower routes are not collapsed into one canonical path.
- `5-8` appears in the Explorer payload query string groups.
- `five_eight_branch` appears in Explorer payload harmony types and available harmony filters.

## Fret 13 / Fret 11 C/E Check

PASS.

- Fret 13 E-lower C/E branch is present.
- Fret 11 A+F C/E branch is present.
- Fret 11 E-lower C/E branch is absent.

Direct API payload check:

```text
positions=[
  (6, "5-8", ["A"], ["F"], {"5": "G", "8": "B"}),
  (8, "5-8", [], ["E"], {"5": "G", "8": "B"}),
  (11, "5-8", ["A"], ["F"], {"5": "C", "8": "E"}),
  (13, "5-8", [], ["E"], {"5": "C", "8": "E"})
]
fret11_e_lower_present=False
```

## API Prompt Result Summary

Prompt:

```text
Show me a G harmonized scale on strings 5 and 8.
```

Observed API/test-helper result:
- Answer starts with `Here are the validated G harmonized-scale 5&8 branch options on E9.`
- `sources=[]`
- `warnings=[]`
- no `tab_example`
- `fretboard.title="G harmonized scale 5&8 branches"`
- fretboard positions: 6 A+F G/B, 8 E-lower G/B, 11 A+F C/E, 13 E-lower C/E
- no fret 11 E-lower position

Contract classification:
- Fretboard-first: yes
- Source-free: yes
- Warning-free: yes
- Tab-free: yes
- SGF/source-card dependent: no
- Full-song tab / recording transcription behavior introduced: no

## Diminished Naming Result

PASS.

Focused tests confirm three-note diminished rows remain partial rows:
- `voicing_status == "partial"`
- omitted interval includes `b7`
- warnings explain the grip does not include b7
- `chord_name` and display summary do not claim full m7b5

This preserves the rule that full m7b5 / half-diminished requires `1-b3-b5-b7`.

## UI Follow-Up Finding

Lane 06 follow-up is recommended if `five_eight_branch` / `5-8` should be visible in the browser Explorer UI.

Reason:
- `ui/e9-fretboard-explorer.js` currently maps only:
  - `two_string_harmonized`
  - `three_string_diatonic`
- `rowMatchesHarmony()` does not include `five_eight_branch`.
- `TWO_STRING_GROUPS` does not include `5-8`.
- `HARMONY_LABELS` does not include a learner-facing label for `five_eight_branch`.

This does not block the backend/API slice because the static API answer returns its own `response.fretboard.positions` payload.

## Checks Run

Initial governance/state checks:

```bash
git status --short
git diff --cached --name-only
git diff --check
git branch --show-current
git rev-parse --short HEAD
git log -1 --oneline
```

Additional current-state checks for the later QA pass:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -1 --oneline
git diff --name-only
git diff --cached --name-only
git diff --check
# branch feature/answer-api; HEAD fe40292; no cached files at start
```

Validation checks:

```bash
.venv/bin/python -m py_compile pocketsteel/fretboard_explorer.py pocketsteel/fretboard_examples.py pocketsteel/curated_answers.py pocketsteel/api.py
# passed

.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
# 30 passed in 0.11s

.venv/bin/python -m pytest tests/test_api_search.py -k 'harmonized or static_g or tab_example or diminished' -q
# 16 passed, 254 deselected in 0.12s

.venv/bin/python -m pytest tests/test_api_contract.py -q
# 5 passed in 0.05s

.venv/bin/python -m pytest tests/test_tab_engine.py -q
# 25 passed in 0.05s

.venv/bin/python -m pytest tests/test_api_search.py -q
# 270 passed in 1.80s
```

Additional validation checks at HEAD `fe40292`:

```bash
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
# 30 passed in 0.11s

.venv/bin/python -m pytest tests/test_api_search.py -q
# 270 passed in 1.69s

.venv/bin/python -m pytest tests/test_tab_engine.py -q
# 25 passed in 0.06s

.venv/bin/python -m pytest tests/test_api_contract.py -q
# 5 passed in 0.05s

curl -sS -i http://127.0.0.1:8770/api/version | head -20 || true
# 200 OK; git_sha fe40292
```

Local live API auth checks:

```bash
# POST /api/answer with X-Steel-Rag-Dev-Access-Role: beta_user
# 401; /api/answer requires Cloudflare Access identity

# POST /api/answer with X-Steel-Rag-Access-Role: beta_user
# 401; /api/answer requires Cloudflare Access identity

# POST /api/answer with Cf-Access-Jwt-Assertion: valid-beta
# 401; /api/answer requires valid Cloudflare Access identity
```

Local browser smoke:

```text
URL tested: http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=c08cc95
Result: app shell loads; Q&A textarea exists but is disabled; placeholder says "Private beta answers need a Backstage Pass."; no [object Object] in visible page text.
Status: local browser answer smoke blocked by runtime auth mode, not counted as protected-preview smoke.
```

Direct payload check:

```bash
.venv/bin/python - <<'PY'
from tests.test_api_search import answer_for_question, noisy_practical_sources
payload = answer_for_question('Show me a G harmonized scale on strings 5 and 8.', noisy_practical_sources())
print(payload['sources'], payload['warnings'], 'tab_example' in payload)
print([(p.get('fret'), p.get('grip'), p.get('pedals'), p.get('levers'), p.get('notes')) for p in payload['fretboard']['positions']])
PY
# sources=[], warnings=[], has_tab_example=False
# [(6, '5-8', ['A'], ['F'], {'5': 'G', '8': 'B'}), (8, '5-8', [], ['E'], {'5': 'G', '8': 'B'}), (11, '5-8', ['A'], ['F'], {'5': 'C', '8': 'E'}), (13, '5-8', [], ['E'], {'5': 'C', '8': 'E'})]
```

Final checks required after this handoff/staging:

```bash
git diff --check
git diff --cached --name-only
git diff --cached
git diff --cached --check
git status --short
```

## Risks

Low for backend/API correctness.

Medium for product/UI exposure if the new Explorer branch should be user-selectable immediately, because UI label/filter work is not included in this backend slice.

## Blockers

None for the deterministic backend/API slice.

## Human Decision Needed

No for backend/API QA approval.

Product/UX decision only if the new branch should appear in the browser Explorer immediately:
- whether Lane 06 should expose `five_eight_branch` as a separate harmony/view option;
- whether the UI should label it as `5&8 branch alternatives`, `5&8 A+F / E-lower branches`, or another learner-facing phrase.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-15-g-harmonized-scale-qa.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files from this worktree, especially:
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores or embeddings
- `source-inbox/` raw/provenance files
- `.wrangler/`
- deployment/auth/DNS/secrets files
- `public/`
- `ui/brand/`
- `Neon Sign/`
- raw design/video/image assets
- unrelated modified docs/root RAG files shown by `git status --short`

## Recommended Next Lane

Lane 06 UX/UI Design only if the product wants the new `five_eight_branch` / `5-8` Explorer rows exposed in the browser Explorer UI.

Otherwise, include this QA result in the next Lane 01 integration-status refresh after protected-preview/user smoke.

## Commit Readiness

Safe to commit for this QA handoff only.

## Suggested Next Step

If UI exposure is desired:

```text
Lane 06: Add browser Explorer UI support for the committed G 5&8 harmonized-scale branch rows. Read docs/handoffs/task-completions/2026-06-23-15-g-harmonized-scale-qa.md and expose five_eight_branch / 5-8 with learner-facing labels, mode-aware filters, and no raw snake_case. Preserve existing Explorer behavior and run focused frontend/fretboard tests.
```

If UI exposure is not needed yet:

```text
Lane 01: Include docs/handoffs/task-completions/2026-06-23-15-g-harmonized-scale-qa.md in the next integration-status refresh after protected-preview/user smoke. Preserve unrelated dirty work and do not broad-stage.
```
