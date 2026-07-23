# Lane 20 — Independent tab-cell cross-check

## Task summary

Diagnosed the final pitch outlier in the first complete 14-event licks validation line. The guided full-line reader misplaced one token onto a different string and changed the token, while the independently generated per-cell reader cache had captured the source cell correctly.

Completed:

- Added exact-lineage loading for the extraction-time per-cell vision cache.
- Deterministic candidate geometry, after one system-wide row-origin calibration, is now authoritative for string rows.
- Removed the prior behavior that could move a token to the full-line model's reported row merely because that move made the token mechanically valid.
- A confident, non-uncertain, hash-pinned per-cell token may replace a mechanically invalid full-line token on the authoritative row.
- If both independent tokens are mechanically valid but disagree, the line fails closed.
- Recorded per-cell cache digests and override counts in private remediation evidence.

Intentionally not changed:

- No validation correction was applied yet.
- No validation truth or sealed-test data was opened.
- No training example, production model, source asset, embedding, vector, auth, deployment, or public runtime behavior was changed.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2116-20-independent-tab-cell-crosscheck.md`

## Tests and checks

- Python compile checks — pass.
- Lane 20 suite: **204 passed**.
- `git diff --check` — pass.

## Integration notes

- The per-cell cache is accepted only when its sheet hash, exact label list, model, and prompt version match the extraction record.
- This is machine-machine corroboration, not validation ground truth and not new training evidence.
- The challenger must be rebuilt after this commit before replaying validation.

## Risk assessment

Medium. The change replaces an unsafe row-override heuristic with stricter independent evidence. Ambiguous valid disagreements are withheld.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2116-20-independent-tab-cell-crosscheck.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Unrelated handoffs
- `corpus-private/**`
- Raw images, models, validation reports, or sealed-test artifacts

## Recommended next lane

Lane 20: exact-path commit, rebuild exact challenger, rerun licks validation remediation, and apply only passed machine-complete lines.

## Commit readiness

Safe to commit

## Suggested next step

Commit this three-file slice and rerun the first licks validation line under the exact new challenger lineage before processing the remaining withheld lines.
