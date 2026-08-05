# Canonical Frontier Protected-Preview Plan

Status: prepared, not authorized, not deployed

This plan moves the owner-corrected canonical-frontier candidate from local implementation to an isolated protected preview. It does not authorize a service install, environment change, restart, Cloudflare change, protected-holdout run, or public activation.

## Current boundary

The application adapter is committed and defaults off. The independently tested Python service currently lives in `/Users/cory/Documents/sgf-scrape-test`; its canonical lexical/vector index contains 1,948,039 passages and remains outside the application repository. Do not enable the application flag until the service has an immutable, fingerprint-verified launch configuration. Running the service directly from the mutable exploration workspace is not an acceptable long-lived deployment.

## Protected topology

```text
Authenticated browser
  -> existing Cloudflare Access and Tunnel
  -> application on http://127.0.0.1:8770
  -> bearer-authenticated canonical service on http://127.0.0.1:8771
  -> read-only canonical lexical/vector index
  -> loopback Ollama embedding endpoint
  -> OpenAI Terra, with Luna only for claims not proven deterministically
```

Only port 8770 remains tunneled. Port 8771, Ollama, the index, credentials, and corpus files remain loopback/local and are never public routes.

## Required deployment slice

Before activation, create and review:

1. An immutable canonical-service code release or manifest-verified bundle derived from frozen candidate `canonical-frontier-implementation-ready-v931.json`.
2. A dedicated `com.steelguitarrag.canonical-frontier` LaunchDaemon definition and wrapper, running as the existing application user and binding only to `127.0.0.1:8771`.
3. A preflight verifier that checks every frozen runtime/policy fingerprint, the full canonical index manifest/count, read-only access, required Python dependencies, Ollama embedding readiness, and OpenAI credential presence without printing secrets.
4. Separate rotating service logs that omit questions, prompts, authorization headers, source excerpts, and environment values.
5. A shared random bearer token stored only in the existing non-repository protected environment. The same value is supplied to the service and application.

The protected application environment then requires:

```text
STEEL_RAG_CANONICAL_FRONTIER_ENABLED=true
STEEL_RAG_CANONICAL_FRONTIER_URL=http://127.0.0.1:8771/v1/answer
STEEL_RAG_CANONICAL_FRONTIER_TOKEN=<shared server-side secret>
STEEL_RAG_CANONICAL_FRONTIER_TIMEOUT_SECONDS=20
```

Do not print or commit the token or OpenAI key. Do not copy them into a plist.

## Activation order

1. Freeze and verify the canonical-service release while both services remain unchanged.
2. Start the canonical service on loopback with the application flag still false.
3. Verify `/health/live` and `/health/ready`; verify that an unauthorized `/v1/answer` request returns 401.
4. Run one authorized loopback answer request and confirm cited claims, source cards, neutral source voice, and no model-generated tablature.
5. Create an exact detached application release containing `9e6ac02a` and later coordination commits.
6. Add the three canonical-frontier settings to the protected environment without changing Access, Tunnel, DNS, corpus, or index data.
7. Run the existing application LaunchDaemon preflight, then perform the separately authorized exact-release activation.
8. Verify the application version, authenticated session, candidate routing, and fallback behavior.

## Required smoke matrix

- Direct factual steel question: answer contains only verified cited claims.
- Equipment-identification uncertainty: answer preserves attributed guesses and remains `partial`.
- Underspecified forum-style title: clarification, not invented advice.
- Unsupported question: safe abstention with no claims or sources.
- Conversation follow-up: tuning/equipment constraints retained.
- Candidate service unavailable: application falls back to the existing path within its bounded timeout.
- Malformed candidate response: application rejects it and falls back.
- Deterministic E9 fretboard question: deterministic route wins before the candidate.
- Tablature request: deterministic tablature engine remains authoritative; no model-generated tab appears.
- Authentication: unauthenticated content requests fail before retrieval or paid generation.
- Browser: source cards render without raw prompts, private paths, tokens, or console errors.

Record median and p95 latency, timeout/fallback count, Terra/Luna call count, per-answer cost, claim/citation rejection count, and service error count. Do not log question bodies or source excerpts.

## Release evaluation

Only after the preview candidate and deployment configuration are immutable:

1. Run the untouched protected release set once.
2. Require Recall@10 at least 90%, displayed claim entailment at least 95%, expert 4/5 correctness-and-usefulness rate at least 80%, conversational constraint retention at least 90%, zero mechanically invalid playable tablature, and median end-to-end latency under 10 seconds in the protected environment.
3. Preserve the protected result as release evidence; do not tune on it.
4. If a gate fails, return to development evidence and create a new candidate rather than repeatedly consuming the protected set.

## Rollback

The immediate rollback is to set `STEEL_RAG_CANONICAL_FRONTIER_ENABLED=false` and reactivate the prior exact application release. The site then uses its existing answer path. The canonical service may be stopped only through its supervised service command after the application flag is confirmed false.

Rollback must not delete or mutate the canonical index, corpus, evaluation evidence, saved owner receipt, API spend records, or existing application data. It must not change Cloudflare Access, Tunnel, or DNS.

## Stop conditions

Stop and keep the feature false if any of these occur:

- A runtime or index fingerprint differs from the frozen candidate.
- The service cannot bind exclusively to loopback.
- Credentials would need to be printed, committed, or placed in the plist.
- The application cannot fall back safely when the service is unavailable.
- A displayed claim lacks a valid source or drops source uncertainty.
- Any model-generated tablature is presented as playable.
- Median protected-preview latency is 10 seconds or higher.
- The protected release set misses any formal goal gate.

## Authorization boundary

The next authorized action should name the exact scope: build the immutable service bundle and LaunchDaemon support without activation, or deploy that reviewed bundle to protected preview. Public activation is a later, separate decision.
