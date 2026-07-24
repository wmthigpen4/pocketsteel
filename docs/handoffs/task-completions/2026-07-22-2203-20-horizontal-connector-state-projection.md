# Lane 20 — Horizontal-connector state projection

## Task summary

Fixed a validation false-negative caused by trailing horizontal connector
marks such as `12-`.

Discovery feedback established that the horizontal stroke connects or sustains
the printed state; it does not itself change the string, fret, controls, or
sounding pitch. Validation now:

- preserves the original marked token as direct visual evidence;
- projects only its unambiguous fret/control state for mechanical and pitch
  checks;
- records that the connector meaning remains unresolved;
- never creates a movement event from the connector alone;
- still requires one unique full-line score/copedent/tab hypothesis.

The rule is local to validation state projection and does not weaken the
general parser's uncertain-modifier behavior.

Intentionally not changed:

- No validation truth or reviewer answer was opened.
- No result was applied yet.
- No sealed-test data was opened.
- No challenger was promoted or enabled.
- No production runtime, UI, corpus, embedding, vector, auth, or deployment
  behavior changed.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2203-20-horizontal-connector-state-projection.md`

## Tests and checks

- Focused validation/score tests — **5 passed**.
- Extraction suite — **161 passed**.
- Remaining Lane 20 suite — **46 passed**.
- Total Lane 20 tests — **207 passed**.
- `git diff --check` — pass.
- Exact pre-change challenger: `at-227d7e1678629c2f`, HEAD `9f30937`,
  702 discovery examples.
- Exact licks validation replay — 3 pages, 6 systems, 0 failures, sealed false.
- Pre-change v3 machine preflight — 1 pass, 4 withheld; the 13-event line
  reached complete score consensus but was rejected solely because connector
  marks prevented any complete tab-state hypothesis.

## Integration notes

The source mark remains present on the resulting action as `sourceToken` and
`validationStateProjection`. Full-line pitch containment and mechanical
validation remain mandatory after projection.

## Risk assessment

Low-to-medium. Only a horizontal-line modifier on an otherwise valid state is
projected, and no semantic connector interpretation or new event is invented.
All independent full-line gates remain in force.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2203-20-horizontal-connector-state-projection.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing unrelated untracked handoffs
- `corpus-private/**`
- Raw images, validation artifacts, sealed-test artifacts, or private models

## Recommended next lane

Lane 20: exact-path commit, rebuild the challenger, repin validation, and rerun
the v3 preflight. Apply only lines that pass every independent gate.

## Commit readiness

Safe to commit

## Suggested next step

Commit and rerun the exact machine-only validation loop; then calculate
unpublished readiness before generating any human review.
