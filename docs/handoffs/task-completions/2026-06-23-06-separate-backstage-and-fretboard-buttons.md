# 2026-06-23 06 Separate Backstage And Fretboard Buttons

## Task Summary

Lane 06 UX/UI Design verified and locked the corrected product decision for the app header actions.

Completed:
- Confirmed the current app header has two distinct upper-right controls:
  - `Explore Fretboard`, linking to `/ui/e9-fretboard-explorer.html`.
  - The separate backstage/settings button, whose runtime label becomes `Go Backstage` for live access and otherwise starts as `Get a Backstage Pass`.
- Confirmed the fretboard control is not labeled `Go Backstage`.
- Confirmed the old large Explorer feature card remains removed.
- Confirmed the vague prompt chips remain absent:
  - `Explain this lick like a steel player would`
  - `Show me a smoother turnaround`
- Added focused frontend assertions so the QA expectation cannot regress back to using `Go Backstage` for the fretboard entry.

Intentionally not changed:
- No backend files.
- No Explorer data.
- No prompt routing.
- No auth, DNS, launchd, tunnel, corpus, Chroma, embeddings, scraping, secrets, private-source files, or assets.

## Files Changed

- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-separate-backstage-and-fretboard-buttons.md`

Deleted files:
- None.

Generated artifacts:
- None.

## Tests And Checks

Commands run:
- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -8 --oneline`
- `git diff --name-only`
- `git diff --cached --name-only`
- `git diff --check`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`

Results:
- `git diff --check`: passed.
- JS syntax checks: passed.
- `tests/test_frontend_answer_ui.py`: 23 passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 32 passed.

## Integration Notes

- The implementation from commit `2d3d662` already had the corrected product behavior.
- This slice adds regression coverage only.
- `Explore Fretboard` remains the virtual-fretboard control.
- `Go Backstage` remains reserved for the backstage/settings flow.
- The two controls coexist in the header action area.

## Risk Assessment

Risk: Low.

Reason:
- Test/handoff-only change.
- No runtime implementation changed.
- Focused checks passed.

Rollback notes:
- Revert this commit to remove the extra regression assertions and handoff only.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-separate-backstage-and-fretboard-buttons.md`

## Files That Must Not Be Staged

Do not stage unrelated parked work shown by `git status`, including but not limited to:
- `README.md`
- `corpus_metadata/`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/`
- `ui/brand/`
- `public/brand/`
- `Neon Sign/`
- corpus/private/source/generated/deployment/auth/DNS/secrets/vector/scraper artifacts.

## Recommended Next Lane

Lane 15 QA / Answer Eval.

Suggested next step:
Run focused Lane 15 QA for MAIN-01 and the previously passing smoke-feedback matrix status. If QA passes, run Lane 12 protected-preview restart/smoke.

## Commit Readiness

Safe to commit.
