# 2026-06-23 - Lane 18 - E9 Copedent Selector Contract

## Pass / Warn / Fail

Warn.

Reason: the product/architecture contract is complete and docs-only, but the worktree has broad unrelated dirty files. The contract is safe to stage as an exact-path docs file only.

## Branch And HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `102a4ad`
- Final HEAD / commit hash if committed: pending at handoff creation

## Task Summary

Requested: define a concise product/architecture contract for E9 copedent selection and visual copedent display. The app should stop treating E9 as one universal copedent and should let the user choose a basic setup that drives Explorer labels, pedal/lever impact preview, deterministic answer guidance, and future Backstage customization.

Completed:

- Defined first supported E9 setup options.
- Defined Emmons vs Day behavior for the app.
- Defined selector placement and copy.
- Defined visual copedent chart requirements.
- Defined deterministic data/provenance rules.
- Defined out-of-scope items and lane routing.

Intentionally not changed:

- No backend code.
- No UI code.
- No tests.
- No C6 implementation.
- No custom copedent editor.
- No corpus, scraping, embeddings, Chroma/vector stores, private-source, auth, DNS, deployment, or asset work.

Task type: docs-only product architecture.

Lane: `18 Product / Architecture`.

Task mode: GREEN for this handoff. Future backend/API and UI implementation are YELLOW because they change data contracts and user-facing behavior.

## Source Guidance Inspected

Repo/local:

- `AGENTS.md`
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-24-1036-05-e9-pedal-lever-impact-preview-contract.md`
- `docs/handoffs/task-completions/2026-06-24-1045-06-e9-pedal-lever-impact-preview-ui.md`
- `docs/handoffs/task-completions/2026-06-24-15-e9-pedal-lever-impact-preview-local-smoke.md`

External source/context pages:

- b0b Pedal Steel Pages: `Understanding E9th`
  - URL: `https://b0b.com/wp/copedents/understanding-e9th/`
  - Relevant source guidance: E9 has a common denominator of 3 pedals and 3 knee levers; instructional materials commonly name pedals A/B/C and knee levers D/E/F; the page shows basic A/B/C and E raise/lower style changes and explains that positions move up the neck.
- b0b Pedal Steel Pages: `Some E9th Copedents`
  - URL: `https://b0b.com/wp/copedents/e9th/`
  - Relevant source guidance: E9 is common on S-10 and D-10 front necks; builders settled around 3 pedals and 4 knee levers by the mid-1970s; basic string tuning varies less than personal pedal/lever preferences.
- b0b Pedal Steel Pages: `Buddy Emmons' E9th Copedent`
  - URL: `https://b0b.com/wp/copedents/buddy-emmons-e9th/`
  - Relevant source guidance: the Buddy Emmons split-pedal setup became a standard E9 pedal arrangement; the page notes most sources agree with the basic chart while also acknowledging personal evolution over time.
- b0b Pedal Steel Pages: `Jimmy Day's E9th Copedent`
  - URL: `https://b0b.com/wp/copedents/jimmy-day-e9th/`
  - Relevant source guidance: useful as contextual source support for Day setup naming, but comments on the page show why the app should not blindly treat a historical chart as universal runtime truth.
- b0b Pedal Steel Pages: `Some C6th Copedents`
  - URL: `https://b0b.com/wp/copedents/c6th/`
  - Relevant source guidance: C6 has its own copedent family and should be explicitly excluded from this E9 selector MVP.

## Product Decisions

### Supported Options For First Slice

The E9 copedent selector should expose exactly these options:

1. `Emmons E9`
   - Enabled.
   - Default selection unless a later user profile or saved preference says otherwise.
   - Represents the common E9 pedal order with A, B, C pedals left to right.
2. `Day E9`
   - Enabled.
   - Represents the common Day pedal order where the A and C pedal positions are reversed around B.
   - Same musical changes as Emmons for the named A/B/C pedals; different physical pedal order.
3. `My Copedent (E9)`
   - Disabled.
   - Display state: `Coming soon in Backstage`.
   - Does not affect payloads or guidance until a future Backstage custom copedent editor exists.

Do not expose C6, universal, extended E9, named-player variants, or arbitrary imports in this first selector.

### What Emmons Means For App Behavior

`Emmons E9` means:

- Instrument: 10-string E9.
- Pedal order left-to-right: `A`, `B`, `C`.
- Named pedal semantics:
  - `A`: raises strings 5 and 10 B to C#.
  - `B`: raises strings 3 and 6 G# to A.
  - `C`: raises string 4 E to F# and string 5 B to C#.
- Common app baseline levers should be modeled as mechanical changes, not only physical knee names:
  - `E-raise`: raises E strings, normally strings 4 and 8, to F.
  - `E-lower`: lowers E strings, normally strings 4 and 8, to Eb/D#.
  - `D-lower`: lowers string 2 D# to D/C# with half/full stop behavior when represented; may also lower string 9 D to C# where included by the app profile.
  - `G-raise`: string 1 and/or 2 raise family where included by the app profile.
  - `G-lower`: string 6 lower family where included by the app profile.
  - `B-to-Bb vertical`: strings 5 and 10 B to Bb/A# where included by the app profile.
- The first backend contract should name the exact included controls. Do not let UI copy imply a control exists when the selected rules profile omits it.

### What Day Means For App Behavior

`Day E9` means:

- Instrument: 10-string E9.
- Pedal order left-to-right: `C`, `B`, `A`.
- Named pedal semantics remain stable:
  - `A` still means strings 5 and 10 B to C#.
  - `B` still means strings 3 and 6 G# to A.
  - `C` still means string 4 E to F# and string 5 B to C#.
- Physical display order changes.
- Deterministic answer guidance should use the selected setup consistently:
  - In Emmons mode, a player sees A/B/C in Emmons order.
  - In Day mode, a player sees C/B/A in Day order, but musical answer text should still refer to named changes such as "A+B" unless explicitly discussing physical pedal location.
- If a future answer needs physical location language, it must be setup-aware:
  - Emmons: A is the outside/left pedal of the A-B-C cluster.
  - Day: A is the inside/right pedal of the C-B-A cluster.

### Why The Model Must Be Explicit

The current "Standard 10-string E9" preview includes only A/B/C plus E-raise/E-lower. That is insufficient for a user-facing copedent-aware product because players also expect common second-string lowers, first/string raise variants, sixth-string lower variants, vertical B-to-Bb lowers, and setup-specific knee naming.

The MVP selector does not need to include every possible change, but it must make the exact included controls visible and deterministic.

## Selector UI Contract

Recommended placement:

- Explorer top control area, near Key / Scale / Harmony controls.
- Backstage-adjacent presentation: the disabled `My Copedent (E9)` option should make it obvious that user-specific customization belongs in Backstage later.
- Answer pages may later inherit the selected profile but should not gain a full editor.

Recommended control type:

- Segmented control or compact select labeled `E9 setup`.
- Options:
  - `Emmons E9`
  - `Day E9`
  - `My Copedent (E9)` disabled with `Coming soon in Backstage`

Required copy:

- `Choose the E9 setup that matches your guitar.`
- `Emmons and Day mainly differ in pedal order.`
- `My Copedent (E9) is coming soon in Backstage.`
- `Copedents vary. This chart shows the setup currently used for guidance.`

Required states:

- Selected setup is visually obvious.
- Disabled setup cannot be selected.
- Disabled setup explains why it is unavailable.
- Changing setup updates pedal order, chart columns, impact-preview labels, and deterministic guidance context.
- Changing setup must not mutate corpus/RAG state.

Safe fallback:

- If setup is missing or invalid, use `Emmons E9` with an explicit assumed/default status.
- UI should show a non-blocking warning rather than silently presenting "standard E9" as universal.

## Visual Copedent Chart Requirements

The selected setup should display a visible copedent chart.

Required chart structure:

- Rows: strings `1-10`, top/highest string first.
- First data column: open note for each string.
- Columns across the top:
  - Pedals in selected physical order.
  - Knee/vertical levers included in the selected app profile.
- Cells:
  - Empty if the control does not affect that string.
  - Changed note if the control affects that string.
  - Optional arrow or delta marker, such as `B -> C#`, `E -> F`, or `G# +1`.
- Raises and lowers must be distinguishable by more than color:
  - Use arrows, plus/minus markers, text labels, or iconography.
  - Color may supplement but not be the only cue.
- Labels:
  - Pedals: `A`, `B`, `C`, with physical order dependent on selected setup.
  - Levers: use mechanical labels first: `E-raise`, `E-lower`, `D-lower`, `G-raise`, `G-lower`, `B-to-Bb vertical`.
  - Physical labels such as LKL/LKR/RKL/RKR/LKV may appear only if the selected rules profile defines them.

Minimum readability requirements:

- Desktop chart can be a table.
- Mobile chart should scroll horizontally or collapse by control group.
- Chart must not show raw JSON objects or internal IDs.
- Chart should be usable without the decorative guitar image.
- Chart should show the selected profile name and status, such as `Emmons E9 - app default`.

## Payload / Data Contract Implications

Future backend contract should add a selected copedent object to Explorer payloads and deterministic answer payloads where relevant.

Conceptual shape:

```json
{
  "selected_copedent": {
    "id": "emmons-e9-basic",
    "label": "Emmons E9",
    "instrument": "E9",
    "status": "app-default",
    "pedal_order": ["A", "B", "C"],
    "available_options": [
      {
        "id": "emmons-e9-basic",
        "label": "Emmons E9",
        "status": "enabled"
      },
      {
        "id": "day-e9-basic",
        "label": "Day E9",
        "status": "enabled"
      },
      {
        "id": "my-copedent-e9",
        "label": "My Copedent (E9)",
        "status": "disabled",
        "disabled_reason": "Coming soon in Backstage"
      }
    ],
    "strings": [
      {"string": 1, "open_note": "F#"},
      {"string": 2, "open_note": "D#"},
      {"string": 3, "open_note": "G#"},
      {"string": 4, "open_note": "E"},
      {"string": 5, "open_note": "B"},
      {"string": 6, "open_note": "G#"},
      {"string": 7, "open_note": "F#"},
      {"string": 8, "open_note": "E"},
      {"string": 9, "open_note": "D"},
      {"string": 10, "open_note": "B"}
    ],
    "controls": [
      {
        "id": "A",
        "label": "A pedal",
        "control_type": "pedal",
        "physical_position": "P1",
        "changes": [
          {"string": 5, "from": "B", "to": "C#", "semitones": 2},
          {"string": 10, "from": "B", "to": "C#", "semitones": 2}
        ]
      }
    ],
    "source_context": [
      {
        "kind": "context",
        "label": "b0b Pedal Steel Pages - Understanding E9th",
        "url": "https://b0b.com/wp/copedents/understanding-e9th/"
      }
    ],
    "warnings": [
      "Copedents vary. This chart shows the setup currently used for guidance."
    ]
  }
}
```

For `Day E9`, `pedal_order` changes to `["C", "B", "A"]`, and physical positions change accordingly. Named pedal changes should remain stable.

The chart should consume the same `selected_copedent.controls[*].changes` data as pedal/lever impact preview. Do not maintain separate chart-only change tables.

## Source And Provenance Handling

Rules:

- Deterministic copedent data is app rules data.
- b0b pages can be cited as explanatory/contextual source support.
- Do not imply that b0b validates every app-specific choice unless that exact choice is explicitly modeled and verified.
- Do not scrape or ingest b0b pages as part of this product contract task.
- Do not use source text to override deterministic rules data.
- Do not present source cards as stronger than the selected chart/rules data.

Recommended wording:

- `This setup is modeled by Steel Guitar RAG for deterministic guidance. Source links provide context about common E9 copedents; individual guitars may differ.`

## Out Of Scope

- C6 support.
- Universal tuning support.
- Extended E9.
- User custom copedent editor.
- Arbitrary copedent import.
- Persistence/account settings.
- Every named player copedent.
- Tuning temperament/cents offsets.
- Historical exact Buddy Emmons or Jimmy Day copedent reconstruction.
- Protected-preview restart or smoke.
- Backend/API implementation.
- UI implementation.

## Defect Routing Guidance

- Backend data/API contract: Lane 05 Backend / RAG Integration.
- Selector/chart rendering: Lane 06 UX/UI Design.
- QA matrix and local/browser smoke: Lane 15 QA / Answer Eval.
- Protected-preview restart and verification: Lane 12 Self-Hosted Deployment.
- Exact-path commit hygiene and integration-status refresh: Lane 01 Repo Steward.

## Recommended Lane 05 Implementation Contract

Lane 05 should implement the backend data contract first, with no UI changes.

Recommended scope:

- Add an explicit selected E9 copedent model to Explorer payload generation.
- Include `Emmons E9`, `Day E9`, and disabled `My Copedent (E9)` option metadata.
- Add a deterministic chart-ready `strings` and `controls` array.
- Preserve existing `control_impact_preview`, but make it read from the selected copedent model.
- Keep Emmons as default.
- Ensure Day changes pedal physical order without changing named A/B/C musical semantics.
- Return warnings/provenance context.
- Add focused tests for:
  - Emmons option metadata.
  - Day pedal order.
  - disabled My Copedent option.
  - chart-ready control changes.
  - impact-preview consistency with selected copedent.
  - C6 exclusion.

Exact suggested prompt:

```text
Lane 05 Backend / RAG Integration:
Implement the backend E9 copedent selector data contract from docs/handoffs/task-completions/2026-06-23-18-e9-copedent-selector-contract.md.
Scope to Explorer payload data only. Add Emmons E9, Day E9, and disabled My Copedent (E9) metadata. Add chart-ready strings/controls data. Preserve deterministic pitch behavior and make pedal/lever impact preview consume the selected copedent model. Emmons is default; Day changes physical pedal order to C/B/A while named A/B/C changes remain stable. Do not touch UI, corpus, Chroma, embeddings, scraping, auth, DNS, deployment, private sources, or C6. Add focused tests and write a handoff. Do not commit unless explicitly instructed.
```

## Files Touched

Created:

- `docs/handoffs/task-completions/2026-06-23-18-e9-copedent-selector-contract.md`

Changed:

- None.

Deleted:

- None.

Generated artifacts:

- None.

## Checks Run

Completed before staging:

- `git diff --check`
  - Result: passed with no output.
- `command -v markdownlint || true`
  - Result: no `markdownlint` executable available; no repo-documented lightweight markdown lint command was found.
- `git status --short -- docs/handoffs/task-completions/2026-06-23-18-e9-copedent-selector-contract.md`
  - Result: file is untracked and isolated.

Completed before commit:

- `git diff --cached --name-only`
  - Result: only `docs/handoffs/task-completions/2026-06-23-18-e9-copedent-selector-contract.md` was staged.
- `git diff --cached`
  - Result: reviewed; cached diff contains only this new handoff.
- `git diff --cached --check`
  - Result: passed with no output.

No implementation tests were required or run for this docs-only task.

## Risks

- Medium product risk if Emmons/Day are described as historical exact copedents instead of app-supported baseline setup profiles.
- Medium implementation risk if UI and backend duplicate separate copedent tables.
- Medium UX risk if Day mode changes musical names instead of only changing physical pedal order.
- Low risk for this handoff because no runtime files changed.

## Blockers

No blocker for this docs handoff.

Implementation blockers to resolve in Lane 05:

- Decide the exact initial included lever set for `Emmons E9` and `Day E9`.
- Decide whether physical knee labels are omitted entirely in MVP or included as app-default labels.
- Decide whether current `mvp-e9-standard` becomes an alias of `emmons-e9-basic` or remains a legacy fallback ID.

## Human Decision Needed

Yes.

Decisions:

- Confirm the initial common lever set beyond A/B/C/E-raise/E-lower.
- Confirm whether `Emmons E9` should replace `Standard 10-string E9` as the default user-facing label.
- Confirm whether Day mode should be implemented immediately in Lane 05 or only modeled in payload metadata first.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-18-e9-copedent-selector-contract.md`

## Files That Must Remain Unstaged

- Any pre-existing dirty/untracked files outside the safe-to-stage list.
- Backend/runtime files.
- UI files.
- Tests.
- `docs/handoffs/task-completions/integration-status.md` unless a separate integration-status task explicitly asks for it.
- Corpus, Chroma/vector stores, embeddings, scraper output, private-source data, auth/DNS/deployment files, secrets, `public/`, `ui/brand/`, `Neon Sign/`, generated reports, and visual assets.

## Recommended Next Lane

Lane 05 Backend / RAG Integration.

## Commit Readiness

Safe to commit if:

- `git diff --check` passes.
- Only the handoff file is staged.
- `git diff --cached --check` passes.
