## Objective

<!-- One finite, testable outcome. -->

## Run charter

- Lane:
- Primary scope: `PRODUCT:RAG` | `PRODUCT:COMPANION` | `PLATFORM:SHARED` | `INFRASTRUCTURE`
- Secondary scopes: None
- Model tier: `LIGHT` | `STANDARD` | `HIGH-REASONING`
- Routing reason:
- Permitted paths:
- Forbidden paths:
- Budget:
- Terminal state: `PASS` | `BLOCKED` | `NEEDS_PRODUCT_DECISION` | `NEEDS_ARCHITECTURE_DECISION` | `REGRESSION` | `BUDGET_EXHAUSTED`

## Evidence

- Success criteria:
- Checks run:
- Known consumers:
- Shared-platform consumer matrix: Not applicable
- Staging smoke: Not applicable
- Full candidate commit:
- Rollback commit: Not applicable

## Exact-path review

- [ ] Staged paths exactly match the approved path list.
- [ ] The complete cached diff was reviewed.
- [ ] `git diff --cached --check` passed.
- [ ] No private data, credentials, generated corpus/vector data, or unrelated parked work is included.
- [ ] Production and staging were not changed, or the exact authorized promotion evidence is linked above.
