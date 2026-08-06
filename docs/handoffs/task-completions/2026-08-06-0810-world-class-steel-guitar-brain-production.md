# World-class Steel Guitar Brain production handoff

## Outcome

The selected Steel Guitar Brain architecture is deployed at `https://app.steelguitarrag.com/` and has passed the protected browser gate. The production design is now explicit:

1. **Deterministic music intelligence** handles chords, intervals, saved-copedent positions, fretboard diagrams, and generated tablature.
2. **Source-backed RAG** handles players, history, equipment, technique, courses, and community knowledge using the 1,948,039-passage public SGF hybrid index.
3. **Hybrid answers** combine deterministic musical results with independently sourced forum context when the question requires both.
4. **Guardrail/honest-unavailable responses** are used when evidence or the canonical service is unavailable; an unrelated generic fallback is not silently substituted.

The main control-layer failures reported by the owner are fixed: corpus-first entity routing replaces name whitelisting, direct questions do not inherit stale conversation state, exact entity questions have a bounded extractive fallback, and referential follow-ups resolve the prior entity before retrieval.

## Production architecture

- App: system-supervised private-preview service on loopback port 8770, exposed through the existing protected Cloudflare route.
- Canonical knowledge service: user-domain LaunchAgent `com.steelguitarrag.canonical-frontier` on loopback port 8771. A user-domain service is intentional because the OpenAI credential is stored in the login Keychain; no API key is stored in the plist or manifest.
- Service bundle: `/Users/cory/.steel-rag/services/canonical-frontier-v1034-fallback-20260806`
- Supervisor bundle: `/Users/cory/.steel-rag/supervisors/canonical-frontier-v1034`
- Index: 1,948,039 public SGF passages, relocated under the service bundle with a compatibility symlink at the former index location.
- Runtime architecture reported by `/health/ready`: `canonical-frontier-v1034-balanced-terra-normalized-attribution-independent-guard-exact-entity-fallback`.
- Bundle verifier: 76 required files fingerprinted, 1,948,039 passages confirmed, protected holdout count zero, and loopback-only binding enforced before startup.

The unsuccessful system-LaunchDaemon copy was unloaded and removed after it proved unable to access the login-Keychain credential. The verified LaunchAgent is now the only canonical-service startup path.

## Source and deployment commits

- `c4b9c113` — promote the Steel Guitar Brain to main.
- `f735124b` — isolate new questions from prior conversation context.
- `0f285cb6` — freeze the 76-file canonical v1034 service manifest.
- `b90c1699` — add the Keychain-compatible supervised LaunchAgent and force the exact v1034 runtime.
- `282cf3cf` — resolve corpus-backed course follow-ups and add that failure to the release challenge.

The canonical runtime source remains in the manifest-verified service bundle. The repository deployment manifest pins its exact SHA-256 fingerprints, so runtime drift fails closed.

## Route diagnostics

Every Ask request records a privacy-safe route event in `/Users/cory/Library/Logs/steel-guitar-rag/runtime.log` with:

`classification → corpus probe → route → retrieval → evidence → synthesis → verification → displayed answer → fallback`

The final protected follow-up recorded corpus promotion to `lesson_lookup`, one source card, `canonical_frontier_complete`, `frontier_complete`, and `frontier_contract_verified`.

## Verification evidence

- Full application suite: **1,639 passed**.
- Deployment-focused tests: **9 passed**.
- Routing/challenge/deployment focused tests: **21 passed**.
- Canonical-frontier tests: **22 passed**.
- Canonical bundle verification: **76 files**, **1,948,039 passages**, **0 protected holdout cases used**.
- Service health/readiness and unauthenticated-request rejection: **pass**.
- Protected browser console warnings/errors: **0**.

Protected browser cases passed:

- `Where can I play an F major 7?` — exact F-A-C-E explanation, complete E9 grips, and fretboard payload.
- `What causes cabinet drop?` — stress/tension explanation with the SGF Cabinet Drop source.
- `What is Travis Toy Tutorials?` — corpus-first source-backed answer with Nelson Checkoway's SGF passage.
- Follow-up `What does the course cover?` — retained entity context and answered “very basics through advanced levels” with the same source.
- `Who is Travis Toy?` and the referential player follow-up — source-backed.
- `Show me a simple E9 A+B pedal lick in G.` — deterministic tablature and fretboard output.

The automated release bank now contains 11 owner-derived cases spanning deterministic, source-backed RAG, hybrid, follow-up, guardrail, player, course, gear, cabinet-drop, chord, and tablature behavior. Paid cases remain explicitly counted and require an authorization count before the runner will call an endpoint.

## Corpus boundaries

The current production index contains public Steel Guitar Forum passages only:

- `sgf_phpbb_current`: 1,527,930 passages
- `sgf_ubb_legacy`: 420,109 passages

The approximately 1,250 cleaned files in `vtt-test/guidance-cleaned` are not part of production search. A future instructional layer should ingest only reviewed, rights-cleared summaries with distinct provenance and attribution; raw private or paid-course transcripts should not be blindly indexed.

## Cost note

No dollar total is inferred here because the OpenAI billing dashboard is the authoritative ledger and this task did not log a reliable per-request charge. The challenge runner distinguishes paid from local cases and refuses paid execution beyond the explicitly authorized count.

## Continued development plan

1. Expand the owner-derived challenge bank whenever a real production miss appears; every accepted regression becomes a permanent gate.
2. Use route events to decide whether a failure is classification, retrieval, evidence, synthesis, verification, or display—avoiding another broad model bakeoff when the control layer is responsible.
3. Add a separate rights-cleared instructional-summary index and fuse it with SGF evidence without erasing source identity.
4. Grow deterministic coverage for copedent variants, chord extensions, voice leading, and parameterized tablature while keeping pitch validation exact.
5. Track answer acceptance, abstention, source opening, follow-up success, latency, and per-answer API cost in production before changing models.

This closes the architecture exploration. Further work should be product development and measured regression repair, not another open-ended search for a different RAG architecture.
