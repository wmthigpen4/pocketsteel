# Answer API Contract

The frontend answer UI talks to the backend retrieval/RAG layer through two JSON endpoints:

- `GET /api/search`
- `GET /api/session`
- `POST /api/answer`

This contract is for the Steel Guitar RAG frontend and local backend API. The API reads from existing retrieval indexes only. It must not run SGF scraping, rebuild embeddings, reset vector stores, or mutate source corpus files.

## Shared Types

Backend shared type definitions live in `steel_guitar_rag/api_contract.py`.

### AccessRole

The private beta access scaffold uses three roles. These names are contract
values only; there is no real auth provider connected yet.

```json
"anonymous" | "beta_user" | "admin"
```

- `anonymous`: may view public landing content and canned examples, but must
  not call live `/api/answer` in production.
- `beta_user`: logged-in/private beta member. May use the live answer UI.
- `admin`: developer/admin role for local testing and future management tools.
  Admin may use the live answer UI.

The matching backend constants live in `steel_guitar_rag/access_control.py`.

### AnswerMode

`AnswerMode` is one of:

```json
"ask" | "gear" | "copedent" | "tab" | "practice"
```

Unknown modes are normalized to `ask`.

### SearchResult

`SearchResult` is the canonical retrieval result returned by `/api/search` and consumed internally by `/api/answer`.

Required fields:

- `score`: number from `0` to `1`, higher is stronger
- `excerpt`: short source text excerpt safe for display
- `source_system`: source system ID, such as `sgf_phpbb_current`
- `forum_name`: display forum name
- `thread_title`: source thread title
- `thread_url`: canonical source thread URL
- `chunk_id`: retrieval chunk ID
- `post_uid`: source post ID when available
- `source_kind`: source type, such as `forum_post`
- `forum_id`: current phpBB forum ID when available
- `legacy_forum_number`: legacy UBB forum number when available
- `thread_id`: current phpBB thread ID when available
- `legacy_thread_uid`: legacy UBB thread ID when available
- `thread_category`: source category label
- `thread_quality_score`: numeric quality score or `null`
- `chunk_index`: numeric chunk index or `null`
- `warnings`: per-result metadata fallback warnings

### SourceCitation

`SourceCitation` is the smaller source card shape returned by `/api/answer` for frontend display.

Required fields:

- `title`
- `forumName`
- `url`
- `excerpt`
- `score`
- `chunkId`
- `postUid`

The answer UI also accepts older snake_case aliases while normalizing live responses, but the backend should emit this canonical citation shape.

### AnswerResponse

`AnswerResponse` is the canonical response from `/api/answer`.

Required fields:

- `answer`: source-grounded answer text
- `mode`: `AnswerMode`
- `sources`: `SourceCitation[]`
- `warnings`: response-level warnings
- `sections`: display sections derived from the answer text

Optional fields include `tab_example`, `fretboard`, `progression_guide`, and
`melody_exercise`. `melody_exercise` is emitted only when Melody Exercise v0 is
enabled and the request routes to melody/arrangement teaching. Its events are
the canonical shared sequence used to derive tab and fretboard output.

An answer request may include an optional `melodyRequest` object:

```json
{
  "question": "Teach the opening phrase",
  "melodyRequest": {
    "kind": "artist_solo_lesson",
    "artist": "Artist name",
    "song": "Song title",
    "recording": "Album or performance version",
    "section": "Intro",
    "sourceUrl": "https://example.com/recording",
    "renderingMode": "e9_adaptation",
    "accuracy": "approximate",
    "key": "G",
    "tokens": ["G", "A", "B", "D"]
  }
}
```

Supported `kind` values are `original_exercise`, `user_melody`,
`artist_solo_lesson`, and `song_arrangement_lesson`. Rendering modes are
`transcription`, `e9_adaptation`, and `teaching_simplification`; accuracy labels
are `exact`, `approximate`, and `interpretive`. Deterministic placement in v0 is
limited to E9 in G or C major. Longer material is returned section-by-section.

## GET /api/search

Request:

```text
GET /api/search?q=why+does+touching+the+changer+reduce+hum
```

Response:

```json
{
  "query": "why does touching the changer reduce hum",
  "results": [
    {
      "score": 0.8125,
      "excerpt": "Touching the changer can change the ground reference, so check the cable, jack, pickup ground, volume pedal, and amp input before replacing parts.",
      "source_system": "sgf_phpbb_current",
      "forum_name": "Electronics",
      "thread_title": "Grounding a pedal steel",
      "thread_url": "https://bb.steelguitarforum.com/viewtopic.php?t=123",
      "chunk_id": "sgf_phpbb_current:electronics:123:0",
      "post_uid": "p12345",
      "source_kind": "forum_post",
      "forum_id": "11",
      "legacy_forum_number": "",
      "thread_id": "123",
      "legacy_thread_uid": "",
      "thread_category": "Electronics",
      "thread_quality_score": 0.92,
      "chunk_index": 0,
      "warnings": []
    }
  ],
  "warnings": []
}
```

Empty or whitespace-only search queries return `200 OK` with no results:

```json
{
  "query": "",
  "results": [],
  "warnings": []
}
```

## POST /api/answer

Access requirement:

`/api/answer` requires `beta_user` or `admin` access. Anonymous requests must be
rejected before retrieval, answer generation, or source-card construction.

Auth scaffold modes:

- `production`: production-like mode. The app reads only the trusted placeholder
  header `X-Steel-Rag-Access-Role`. Missing access returns `401 Unauthorized`.
  Explicit non-live roles such as `anonymous` return `403 Forbidden`.
- `local_dev`: local/test mode. The app also accepts the explicit dev mock
  header `X-Steel-Rag-Dev-Access-Role`. This is how the local frontend mock
  Backstage selector previews beta/admin access. The dev mock header is ignored
  in `production` mode.

Auth mode is selected by passing `answer_auth_mode` when creating the WSGI app,
by the `--answer-auth-mode` CLI flag, or by `STEEL_RAG_ANSWER_AUTH_MODE`.
Unknown or unset mode defaults to `production`.

Auth provider is selected by passing `auth_provider` when creating the WSGI app,
by the `--auth-provider` CLI flag, or by `STEEL_RAG_AUTH_PROVIDER`.

Provider values:

- `scaffold`: reads `X-Steel-Rag-Access-Role` in production-like mode. This is
  only a pre-Cloudflare scaffold and must not be used for public beta.
- `cloudflare_access`: reads `Cf-Access-Jwt-Assertion`, or the browser
  `CF_Authorization` Access cookie when the origin header is absent, then
  validates the Access JWT issuer, audience, expiry/not-before, and RS256
  signature against the Access JWKS. It maps the verified email to `beta_user`
  or `admin` from allowlists. Browser-supplied role headers, email headers, and
  local-dev mock headers are ignored in this provider unless
  `STEEL_RAG_ANSWER_AUTH_MODE=local_dev`.

Cloudflare Access provider configuration:

- `STEEL_RAG_AUTH_PROVIDER=cloudflare_access`
- `STEEL_RAG_CF_ACCESS_ISSUER`: expected Access issuer, for example
  `https://<team>.cloudflareaccess.com`
- `STEEL_RAG_CF_ACCESS_AUD`: Access application audience/AUD tag
- `STEEL_RAG_CF_ACCESS_JWKS_URL`: optional override; defaults to
  `<issuer>/cdn-cgi/access/certs`
- `STEEL_RAG_BETA_USER_EMAILS`: comma-separated beta allowlist
- `STEEL_RAG_ADMIN_EMAILS`: comma-separated admin allowlist

These role headers are scaffolding only. Before public beta, the trusted role
must come from real server-side auth/session validation, not directly from a
browser-controlled header.

Usage logging scaffold:

Each `/api/answer` attempt records a local structured event with timestamp,
role, hashed identity key when a verified Cloudflare identity is available,
access status, authorized/blocked state, question length, mode, source count
when an answer succeeds, warning count, and error status when blocked or
failed. It does not log full email addresses, Cloudflare JWTs, cookies, auth
headers, or private environment values. The current implementation keeps these
events in process memory and emits them through Python logging.

Rate-limit scaffold:

The API uses an in-memory process-local limiter before retrieval. When a
verified identity is available, the temporary quota key uses the same hashed
identity key used in logs. Otherwise it falls back to role/IP. It is configured
by:

- `STEEL_RAG_ANSWER_RATE_LIMIT_ENABLED`: defaults to enabled.
- `STEEL_RAG_ANSWER_RATE_LIMIT_MAX_REQUESTS`: defaults to `120`.
- `STEEL_RAG_ANSWER_RATE_LIMIT_WINDOW_SECONDS`: defaults to `60`.

TODO before production quotas:

- Replace process memory with a persistent usage store.
- Move the hashed verified-user quota key into the persistent usage store.
- Define per-user quotas.
- Decide whether admin bypasses quota or receives a separate quota.
- Add paid/free tier budgets later.

Request:

```http
POST /api/answer
Content-Type: application/json
Cf-Access-Jwt-Assertion: <Cloudflare Access JWT>
```

```json
{
  "question": "Why does touching the changer reduce hum?",
  "mode": "gear",
  "topK": 6,
  "sourceSystem": "sgf_phpbb_current",
  "forumName": "Electronics"
}
```

Required request field:

- `question`

Optional request fields:

- `mode`: `AnswerMode`, defaults to `ask`
- `topK`: retrieval count, clamped by the backend
- `sourceSystem`: source-system filter
- `forumName`: forum-name filter

Response:

```json
{
  "answer": "The retrieved forum sources point to a grounding or signal-chain issue. Start by bypassing the volume pedal, trying a known-good cable, and checking whether the hum changes when you touch the strings, changer, jack plate, and amp chassis. [1]",
  "mode": "gear",
  "sources": [
    {
      "title": "Grounding a pedal steel",
      "forumName": "Electronics",
      "url": "https://bb.steelguitarforum.com/viewtopic.php?t=123",
      "excerpt": "Touching the changer can change the ground reference, so check the cable, jack, pickup ground, volume pedal, and amp input before replacing parts.",
      "score": 0.8125,
      "chunkId": "sgf_phpbb_current:electronics:123:0",
      "postUid": "p12345"
    }
  ],
  "warnings": [],
  "sections": [
    {
      "title": "Answer",
      "style": "lead",
      "body": "The retrieved forum sources point to a grounding or signal-chain issue. Start by bypassing the volume pedal, trying a known-good cable, and checking whether the hum changes when you touch the strings, changer, jack plate, and amp chassis. [1]"
    }
  ]
}
```

If retrieval finds no strong source match, `/api/answer` still returns `200 OK` with an explanatory answer, an empty `sources` array, and a warning:

```json
{
  "answer": "No strong source match found in the current corpus for that question.",
  "mode": "ask",
  "sources": [],
  "warnings": ["no strong source match"],
  "sections": [
    {
      "title": "Answer",
      "style": "lead",
      "body": "No strong source match found in the current corpus for that question."
    }
  ]
}
```

Validation errors return `400 Bad Request`:

```json
{
  "error": "question is required"
}
```

Missing production auth returns `401 Unauthorized`:

```json
{
  "error": "/api/answer requires authenticated beta_user or admin access"
}
```

Missing Cloudflare Access JWT in `cloudflare_access` mode returns
`401 Unauthorized`:

```json
{
  "error": "/api/answer requires Cloudflare Access identity"
}
```

Invalid Cloudflare Access JWT in `cloudflare_access` mode returns
`401 Unauthorized`:

```json
{
  "error": "/api/answer requires valid Cloudflare Access identity"
}
```

Authenticated-but-unauthorized roles return `403 Forbidden`:

```json
{
  "error": "/api/answer requires beta_user or admin access"
}
```

Rate-limit failures return `429 Too Many Requests`:

```json
{
  "error": "/api/answer rate limit exceeded",
  "retryAfterSeconds": 60
}
```

## GET /api/session

`/api/session` lets the frontend ask the backend whether the current request is
authenticated. It uses the same auth provider boundary as `/api/answer`, but it
does not run retrieval or answer generation.

In `cloudflare_access` mode, the endpoint validates the Access JWT from
`Cf-Access-Jwt-Assertion`, or from the browser `CF_Authorization` Access cookie
when the origin header is absent, and maps the verified email to `beta_user` or
`admin`. Missing, invalid, or unlisted identities return an anonymous status in
the response body.

For private-preview diagnosis, `GET /api/session?debug=auth` may include a
non-secret `accessDebug` object. This object is limited to booleans and coarse
state such as whether an Access header or cookie reached the origin, whether the
token verified, whether an email claim was present, whether the verified
identity matched the beta/admin allowlists, the effective auth provider, and the
answer auth mode. It must not include JWTs, cookie values, auth headers, full
email addresses, secrets, private env values, or source text. The normal
frontend unlock still depends only on `authenticated`, `role`, and
`authProvider`.

In `local_dev` mode, the endpoint may accept the explicit local dev mock access
header so `?access=beta_user` and the Backstage preview controls remain useful
for local testing.

Response:

```json
{
  "authenticated": true,
  "role": "beta_user",
  "authProvider": "cloudflare_access"
}
```

Anonymous response:

```json
{
  "authenticated": false,
  "role": "anonymous",
  "authProvider": "cloudflare_access"
}
```

The session response intentionally omits full email addresses. The frontend
should use only `authenticated`, `role`, and `authProvider` to decide whether
to unlock the live Q&A UI.

## Fixture

`tests/fixtures/api_contract_mock_response.json` contains mock `/api/search` and `/api/answer` payloads that match this contract.
