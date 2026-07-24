# 2026-07-04 10:09 - Lane 05 - Progression Guide Simple Song Fix

## Task Summary

Fixed the Progression Guide v0 routing miss for natural-language simple progression prompts.

Completed:

- Routed `How do I move through a simple song progression in G?` into the deterministic Progression Guide path.
- Defaulted underspecified simple/song/practice progression wording to I-IV-V-I in the parsed key, or G when no key is supplied.
- Kept explicit progression prompts working.
- Kept movement prompts owned by Movement Lesson Card/tab behavior.
- Kept static grip prompts fretboard-first with no tab.
- Kept deterministic progression answers source-free with matching fretboard payloads.

Intentionally not changed:

- No UI files were modified.
- No SGF/RAG/corpus lookup is used to choose progression positions.
- No copyrighted song tab, public-domain arrangement, recording transcription, arbitrary melody input, Chroma, embeddings, scraping, corpus, auth, DNS, deployment, private source data, or brand assets were touched.
- Protected preview was not restarted in this Lane 05 run.

## Files Changed

- `steel_guitar_rag/progression_guide.py`
  - Added a conservative simple-song progression matcher.
  - Added direct answer wording that calls the default route an original deterministic practice route, not a transcription or source-backed arrangement.
- `tests/test_progression_guide.py`
  - Added unit coverage for the exact failed simple-song progression prompt.
- `tests/test_api_search.py`
  - Added API coverage for the exact failed prompt, source suppression, no specificity fallback, and matching fretboard payload.
- `docs/handoffs/task-completions/2026-07-04-1009-05-progression-guide-simple-song-fix.md`
  - This handoff.

Generated artifacts:

- None committed or staged by this lane.

## Routing Behavior

Before:

- `How do I move through a simple song progression in G?` fell through to the generic specificity fallback and the answer page showed an empty `No sources returned` shell.

After:

- The same prompt returns a deterministic G I-IV-V-I Progression Guide.
- Recommended route:
  - I - G: fret 3, strings 5-6-8, no pedals/no levers.
  - IV - C: fret 3, strings 5-6-8, A+B.
  - V - D: fret 5, strings 5-6-8, A+B.
  - I - G: fret 3, strings 5-6-8, no pedals/no levers.
- The response includes `progression_guide` and `fretboard`, with `sources: []`, `warnings: []`, and no `tab_example`.
- The rendered page hides the source section because the deterministic progression response is source-free.

## Local Smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8786/ui/steel-guitar-rag-mock.html?access=beta_user&v=progression-guide-simple-song-fix-local`
- Cache-busted URL tested: `http://127.0.0.1:8786/ui/steel-guitar-rag-mock.html?access=beta_user&v=progression-guide-simple-song-fix-local`
- Exact URL the user should use: protected-preview URL after Lane 12 restart/smoke, not this local URL.
- Auth required: no Cloudflare Access; local beta access query used.
- Auth provider: local dev beta access
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8786`
- Expected backend port: `8786`
- Expected git HEAD: local worktree before commit
- Version endpoint: not checked for local smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree/current HEAD
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: root URL for cache-busted validation
- Known caveats: local smoke does not prove protected-preview runtime/browser behavior

Prompt results:

- `How do I move through a simple song progression in G?` - PASS; progression guide visible, fretboard visible, no tab, no source section, no empty source shell, no specificity fallback, no `[object Object]`.
- `Show me a 1 4 5 1 progression in G.` - PASS; progression guide visible, fretboard visible, no tab, no source shell.
- `Show me a G C D G progression route.` - PASS; progression guide visible, fretboard visible, no tab, no source shell.
- `Show me a G to C move.` - PASS; Movement Lesson Card/tab visible, fretboard visible, no progression guide, no source shell.
- `Show me a G major grip.` - PASS; static fretboard-first response, no tab, no progression guide, no source shell.
- `Show me a 5-7-8 G grip.` - PASS; partial/color/no-3rd wording, fretboard visible, no inert A+B, no tab, no source shell.
- `What are good Fender Steel King settings?` - PASS; concrete source-backed answer with source cards; no fretboard/tab/progression guide.

## Tests And Checks

Run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `.venv/bin/python -m py_compile steel_guitar_rag/progression_guide.py steel_guitar_rag/api.py` - passed.
- `.venv/bin/python -m pytest tests/test_progression_guide.py -q` - `7 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'progression or tab_example or static_g_location or copyright or transcribe or steel_king or 578' -q` - `29 passed, 261 deselected`.
- `.venv/bin/python -m pytest tests/test_api_search.py -q` - `290 passed`.
- `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q` - `64 passed`.
- `.venv/bin/python -m pytest` - `890 passed`.
- `git diff --check` - passed.
- Local in-app browser smoke at the URL above - passed.

## Integration Notes

- No API schema changes were needed; this uses the existing optional `progression_guide` response field.
- No frontend source-shell change was needed; once the prompt routes to `progression_guide`, the existing source-section hiding logic applies.
- The parser remains conservative:
  - It requires `progression` plus simple/beginner/basic/song/practice wording or `move through`.
  - It does not handle minor/simple copyrighted/transcription prompts.
  - Existing two-chord movement prompts stay with the Movement Lesson Card/tab route.

## Risk Assessment

Risk: low to medium.

Why:

- The code change is a small parser/default-route addition in `steel_guitar_rag/progression_guide.py`.
- Full pytest and local browser smoke passed.
- The change touches answer routing, so protected-preview runtime smoke is still required before user smoke.

Rollback:

- Revert the parser helper and its call in `steel_guitar_rag/progression_guide.py`, plus the two focused tests.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/progression_guide.py`
- `tests/test_progression_guide.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-07-04-1009-05-progression-guide-simple-song-fix.md`

## Files That Must Not Be Staged

All unrelated parked files shown by `git status --short`, especially:

- `README.md`
- `corpus_metadata/**`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_*.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/**`
- `Neon Sign/**`
- existing untracked handoffs/assets not listed above

## Recommended Next Lane

Lane 01 exact-path commit, then Lane 12 protected-preview restart/smoke for:

`https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=progression-guide-simple-song-fix`

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit this scoped fix with exact-path staging:

`fix: route simple song progression prompts`

Then run Lane 12 protected-preview smoke on the exact prompt matrix from the task.
