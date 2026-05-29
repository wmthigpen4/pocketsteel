# Answer Guardrails

The Turnaround treats retrieved forum text as evidence, not as text to copy into an answer. The final answer path uses a last-pass lint and fallback layer before `/api/answer` returns content to the UI.

## Final Lint

The answer body must not expose:

- internal implementation phrases such as `source cards as supporting evidence`, `Useful distilled points`, or `The cleanest source-backed answer`
- raw SGF parser junk such as standalone `Top`
- raw email addresses or `e-mail` contact prompts unless the user specifically asks for contact information
- orphan headings such as `Practical answer` without useful content
- empty sections where a heading is followed by another heading or the end of the answer
- obvious source typos currently caught by deterministic patterns, such as `tje`
- unapproved URLs in answer prose

Source cards may still show concise excerpts and URLs. The answer body should remain assistant-written, direct, and clean.

## Fallback Categories

The fallback layer uses named categories so weak retrieval does not become raw source dumping:

- `not_enough_source_evidence`: the corpus match is too weak; say so and ask for one useful narrowing detail.
- `current_info_not_in_corpus`: current rosters or time-sensitive facts are not reliable in old forum evidence; point to official tour/session credits.
- `sensitive_identity_speculation`: do not speculate about private identity traits.
- `copyrighted_song_guardrail`: discuss approach, key, style, and user-provided excerpts, but do not provide full copyrighted lyrics or note-for-note tab by default.
- `ask_for_more_context`: ask for song, key, tuning, or target skill when the request is too broad.
- `rules_layer_answer_available`: use stable E9/theory rules when available instead of falling back to noisy retrieval.

## Maintenance Notes

Add new blocked phrases only when they represent a class of user-facing failure, not one isolated typo. Prefer adding stable rules to `pocketsteel/steel_rules.py` for E9/theory facts, and use answer contracts for intent-level expectations.
