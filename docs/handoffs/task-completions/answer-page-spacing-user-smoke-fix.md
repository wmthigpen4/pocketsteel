# Answer Page Spacing User Smoke Fix

## Task Summary

User-smoke bug: answer pages still wasted desktop real estate because primary answer content and supporting answer sections could be constrained inside narrow columns while the card was much wider.

Completed:
- Let the primary answer body use the full answer card content width.
- Replaced the fixed three-column answer detail grid with an auto-fit grid that collapses unused columns.
- Hid empty answer detail grids so primary-only answers do not show an unnecessary divider/gap.
- Kept `Why these families matter` and `Terminology note` sections full-width.
- Tightened answer workspace, answer-card, and fretboard-card spacing slightly.
- Browser-smoked all requested prompts on protected preview and captured desktop/mobile screenshots.

Intentionally not changed:
- Backend answer text.
- Answer routing.
- `/api/answer` schema.
- Auth, deployment, DNS, corpus, Chroma, embeddings, scraping, source data, or visual assets.
- Fretboard logic, filter behavior, source-card behavior beyond layout containment.

## Files Changed

Implementation:
- `ui/steel-guitar-rag-mock.html`

Tests:
- `tests/test_frontend_answer_ui.py`

Handoff and evidence:
- `docs/handoffs/task-completions/answer-page-spacing-user-smoke-fix.md`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/before-major-scale-g.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/before-real-lesson.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-major-scale-g-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-a-minor-c-major-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-real-lesson-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-g-e9-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-e-major-minor-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-dsharp-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-steel-guitar-rag-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-g-e9-mobile.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-major-scale-g-mobile.png`

Generated but not needed for commit:
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/after-*.png`

## Root Cause

Two CSS constraints remained after the previous answer-card width fix:

1. `.answer-lead` had `max-width: 800px`, so primary answer content did not use the full `1060px` answer card on desktop.
2. `.answer-detail-grid` used fixed tracks: `1.08fr 1fr 1fr`. When only one or two supporting sections were rendered, the unused tracks still occupied visual space. This made short support sections feel trapped on the left with empty card space to the right.

Empty detail grids also still rendered a divider/gap under primary-only answers.

## Exact Layout Change

Changed:

```css
.answer-lead {
  max-width: 100%;
}

.answer-detail-grid {
  grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr));
}

.answer-detail-grid:empty {
  display: none;
}

.answer-fretboard-description {
  max-width: 100%;
}
```

Also:
- Reduced answer workspace gap from `16px` to `14px`.
- Reduced answer card padding from `24px 26px` to `22px 24px`.
- Reduced fretboard card padding from `18px 20px 20px` to `16px 18px 18px`.
- Added `Terminology note` to the conservative full-width answer-section classifier.

## Browser Smoke Target

- Target type: protected-preview root
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/?v=answer-spacing-final-fd89e2d`
- Cache-busted URL tested: `https://app.steelguitarrag.com/?v=answer-spacing-final-fd89e2d`
- Exact URL the user should use: `https://app.steelguitarrag.com/`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded via existing authenticated in-app browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `fd89e2d`
- Version endpoint: not checked during this UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: browser loaded protected root, redirected into `/ui/steel-guitar-rag-mock.html`, and DOM/CSS probes confirmed the patched rules were active
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both Codex and the user
- Do not test these URLs: public landing page, unauthenticated `/api/answer`, direct Ollama/Chroma endpoints
- Known caveats: root redirect drops query strings; this did not block the smoke because the rendered DOM showed the patched CSS rules

## Desktop Result

All requested desktop prompt smokes passed.

| Prompt | Result | Notes |
| --- | --- | --- |
| `Show me the major scale in G` | Pass | Primary answer body uses `1010px` content width inside a `1060px` card; empty detail grid hidden. |
| `Show me A minor and C major chords.` | Pass | Primary answer body uses `1010px`; no narrow trapped sections. |
| `give me a real lesson now` | Pass | Primary-only answer is compact; empty detail divider removed. |
| `How do I play a G chord on the E9?` | Pass | Fretboard visible; `Why these families matter` and `Terminology note` span full `1010px` grid width. |
| `Show me E major and E minor.` | Pass | Fretboard visible; answer body uses full card width. |
| `Where can I find D# chords on the pedal steel E9?` | Pass | Fretboard visible; family and terminology sections full-width. |
| `What is Steel Guitar Rag?` | Pass | Source-backed/non-fretboard answer renders cleanly without wasted detail-grid divider. |

Representative measurements after the fix:

- Desktop answer card width: `1060px`
- Primary answer content width: `1010px`
- `How do I play a G chord on the E9?`:
  - `Why these families matter`: `1010px`, `grid-column: 1 / -1`
  - `Terminology note`: `1010px`, `grid-column: 1 / -1`
  - Fretboard width: `1060px`
  - Page-level horizontal overflow: `0px`
- Primary-only answers:
  - Empty detail grid width: `0px`, because `.answer-detail-grid:empty` is hidden.

## Mobile Result

Mobile/narrow viewport smoke used `390 x 844`.

| Prompt | Result | Notes |
| --- | --- | --- |
| `How do I play a G chord on the E9?` | Pass | Single-column answer sections, fretboard remains visible, no page-level horizontal overflow. |
| `Show me the major scale in G` | Pass | Primary answer body uses available mobile width; no clipped cards or horizontal overflow. |

Measured mobile:
- Viewport: `390 x 844`
- Page scroll width: `390px`
- Page-level horizontal overflow: `0px`
- G/E9 answer card width: `362px`
- G/E9 answer content width: `324px`

## Screenshot Paths

Before:
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/before-major-scale-g.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/before-real-lesson.png`

After desktop:
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-major-scale-g-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-a-minor-c-major-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-real-lesson-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-g-e9-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-e-major-minor-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-dsharp-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-steel-guitar-rag-desktop.png`

After mobile:
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-g-e9-mobile.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-major-scale-g-mobile.png`

## Tests And Checks

Run:
- `git status --short`
- `git diff --check` - passed
- `node --check ui/answer-client.js` - passed
- `node --check ui/pedal-steel-fretboard.js` - passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `18 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `29 passed`

Browser smoke:
- Protected-preview root browser smoke passed for all requested desktop prompts.
- Protected-preview mobile/narrow browser smoke passed for representative fretboard and non-fretboard prompts.
- Current protected-page console errors/warnings: none for `steel-guitar-rag-mock.html`.

Full pytest:
- Not run. This task changed scoped UI/static layout and focused tests passed.
- Known unrelated full-suite caveats from the prompt remain unchanged:
  - landing static output mismatch
  - missing same-origin public fretboard background route

## Integration Notes

- UI-only layout patch.
- No backend/API/schema/component contract changes.
- No source-card behavior changes except improved layout containment.
- Fretboard rendering and filters were not changed.
- Protected root behavior remains unchanged: root redirects to `/ui/steel-guitar-rag-mock.html`.
- The large pre-existing dirty/parked worktree was left untouched.

## Risk Assessment

Risk: low.

Why:
- CSS-only presentation changes plus a small title classifier addition.
- Focused tests and protected browser smoke cover the requested layout cases.
- Mobile fallback was verified with no horizontal overflow.

Rollback:
- Revert the answer spacing CSS changes and the `Terminology note` full-width classifier addition in `ui/steel-guitar-rag-mock.html`.
- Revert the assertions added to `tests/test_frontend_answer_ui.py`.

## Commit Readiness

Safe to commit.

Exact safe-to-stage file list:
- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/answer-page-spacing-user-smoke-fix.md`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/before-major-scale-g.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/before-real-lesson.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-major-scale-g-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-a-minor-c-major-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-real-lesson-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-g-e9-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-e-major-minor-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-dsharp-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-steel-guitar-rag-desktop.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-g-e9-mobile.png`
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/final-major-scale-g-mobile.png`

Do not stage:
- `docs/handoffs/task-completions/assets/answer-page-spacing-user-smoke-fix/after-*.png`
- Existing dirty backend, corpus, source-inbox, deployment, public, `ui/brand`, `Neon Sign`, or generated/private files.

## Suggested Next Step

Lane 12 / protected-preview verification should restart or verify the protected preview from the new UI commit, then Lane 15 can continue user smoke from:

```text
https://app.steelguitarrag.com/
```

Suggested QA prompt:

```text
Verify the answer-page spacing fix in protected preview. Start at https://app.steelguitarrag.com/. Test: Show me the major scale in G; Show me A minor and C major chords.; give me a real lesson now; How do I play a G chord on the E9?; Show me E major and E minor.; Where can I find D# chords on the pedal steel E9?; What is Steel Guitar Rag? Confirm desktop answer content uses the card width, no sections are trapped in narrow columns, fretboard sections span cleanly, source notes remain secondary, mobile has no horizontal overflow, and root redirect behavior is unchanged.
```
