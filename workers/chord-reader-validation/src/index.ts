import {
  HttpError,
  normalizeTrackPayload,
  parseByteRange,
  plainObject,
  type StoredTrack,
} from "./validation";

const APP_BASE = "/ui/chord-reader-travis-validation";
const API_BASE = "/api/travis-validation";
const REVIEW_SESSION_ID = "travis-validation-pilot-v1";
const FEEDBACK_SCHEMA = "chord_reader_travis_feedback_v1";
const TRACK_BODY_LIMIT = 256 * 1024;
type DbTrack = {
  track_id: string;
  payload_json: string;
  revision: number;
  updated_at: string;
};

function now(): string {
  return new Date().toISOString();
}

function secureHeaders(headers = new Headers()): Headers {
  headers.set("Cache-Control", "private, no-store");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("Referrer-Policy", "no-referrer");
  headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  return headers;
}

function json(payload: unknown, init: ResponseInit = {}): Response {
  const headers = secureHeaders(new Headers(init.headers));
  headers.set("Content-Type", "application/json; charset=utf-8");
  return Response.json(payload, { ...init, headers });
}

function contentType(pathname: string): string {
  if (pathname.endsWith(".html") || pathname.endsWith("/"))
    return "text/html; charset=utf-8";
  if (pathname.endsWith(".css")) return "text/css; charset=utf-8";
  if (pathname.endsWith(".js")) return "text/javascript; charset=utf-8";
  if (pathname.endsWith(".json")) return "application/json; charset=utf-8";
  if (pathname.endsWith(".mp3")) return "audio/mpeg";
  return "application/octet-stream";
}

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

async function timingSafeEqual(left: string, right: string): Promise<boolean> {
  const encoder = new TextEncoder();
  const [leftHash, rightHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(left)),
    crypto.subtle.digest("SHA-256", encoder.encode(right)),
  ]);
  return crypto.subtle.timingSafeEqual(leftHash, rightHash);
}

async function reviewerEmail(
  request: Request,
  env: Env,
  ctx: ExecutionContext,
): Promise<string> {
  const configured = env.TRAVIS_EMAIL?.trim().toLowerCase();
  const owner = env.OWNER_EMAIL?.trim().toLowerCase();
  if (!configured)
    throw new HttpError("Reviewer access is not configured.", 503);

  if (env.ENVIRONMENT === "development") {
    const local = request.headers
      .get("X-Travis-Validation-Reviewer")
      ?.trim()
      .toLowerCase();
    if (local && (await timingSafeEqual(local, configured))) return local;
  }

  if (!ctx.access)
    throw new HttpError("Cloudflare Access authentication is required.", 401);
  const identity = await ctx.access.getIdentity();
  const email = identity?.email?.trim().toLowerCase();
  if (!email)
    throw new HttpError("Cloudflare Access authentication is required.", 401);
  const isReviewer = await timingSafeEqual(email, configured);
  const isOwner = owner ? await timingSafeEqual(email, owner) : false;
  if (!isReviewer && !isOwner)
    throw new HttpError("This review is assigned to a different account.", 403);
  return email;
}

async function readBoundedJson(request: Request): Promise<unknown> {
  const declared = Number(request.headers.get("Content-Length") || 0);
  if (declared > TRACK_BODY_LIMIT)
    throw new HttpError("Feedback payload is too large.", 413);
  const body = await request.text();
  if (body.length > TRACK_BODY_LIMIT)
    throw new HttpError("Feedback payload is too large.", 413);
  try {
    return JSON.parse(body) as unknown;
  } catch {
    throw new HttpError("Feedback payload is not valid JSON.");
  }
}

async function feedback(env: Env): Promise<Response> {
  const result = await env.DB.prepare(
    "SELECT track_id, payload_json, revision, updated_at FROM track_feedback WHERE session_id = ? ORDER BY updated_at",
  )
    .bind(REVIEW_SESSION_ID)
    .all<DbTrack>();
  const tracks: Record<string, unknown> = {};
  for (const row of result.results) {
    tracks[row.track_id] = {
      ...JSON.parse(row.payload_json),
      serverRevision: row.revision,
      serverUpdatedAt: row.updated_at,
    };
  }
  return json({
    schemaVersion: FEEDBACK_SCHEMA,
    sessionId: REVIEW_SESSION_ID,
    tracks,
  });
}

async function saveTrack(
  request: Request,
  env: Env,
  reviewerHash: string,
  trackId: string,
): Promise<Response> {
  const body = plainObject(await readBoundedJson(request));
  const expectedRevision = Number(body.serverRevision ?? 0);
  if (!Number.isSafeInteger(expectedRevision) || expectedRevision < 0)
    throw new HttpError("serverRevision is invalid.");
  const track = normalizeTrackPayload(body, trackId);
  const timestamp = now();
  await env.DB.prepare(
    "INSERT INTO review_sessions (id, reviewer_hash, schema_version, created_at, updated_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET reviewer_hash = excluded.reviewer_hash, updated_at = excluded.updated_at",
  )
    .bind(
      REVIEW_SESSION_ID,
      reviewerHash,
      FEEDBACK_SCHEMA,
      timestamp,
      timestamp,
    )
    .run();
  const result = await env.DB.prepare(
    "INSERT INTO track_feedback (session_id, track_id, payload_json, revision, updated_at) VALUES (?, ?, ?, 1, ?) ON CONFLICT(session_id, track_id) DO UPDATE SET payload_json = excluded.payload_json, revision = track_feedback.revision + 1, updated_at = excluded.updated_at WHERE track_feedback.revision = ?",
  )
    .bind(
      REVIEW_SESSION_ID,
      trackId,
      JSON.stringify(track),
      timestamp,
      expectedRevision,
    )
    .run();
  if ((result.meta.changes ?? 0) !== 1)
    throw new HttpError(
      "Feedback changed in another tab. Reload before continuing.",
      409,
    );
  return json({
    saved: true,
    trackId,
    revision: expectedRevision + 1,
    updatedAt: timestamp,
  });
}

function r2Key(pathname: string): string | null {
  if (pathname === APP_BASE || pathname === `${APP_BASE}/`)
    return "app/index.html";
  if (pathname === `${APP_BASE}/validation.css`) return "app/validation.css";
  if (pathname === `${APP_BASE}/phase-anchor.js`) return "app/phase-anchor.js";
  if (pathname === `${APP_BASE}/validation.js`) return "app/validation.js";
  if (pathname === `${APP_BASE}/local-data/proof.json`)
    return "proof/proof.json";
  const prefix = `${APP_BASE}/local-data/audio/`;
  if (pathname.startsWith(prefix)) {
    const fileName = decodeURIComponent(pathname.slice(prefix.length));
    if (/^[a-zA-Z0-9][a-zA-Z0-9._-]*\.mp3$/u.test(fileName))
      return `audio/${fileName}`;
  }
  return null;
}

async function media(
  request: Request,
  env: Env,
  pathname: string,
): Promise<Response> {
  const key = r2Key(pathname);
  if (!key) throw new HttpError("Not found.", 404);
  const objectHead = await env.MEDIA.head(key);
  if (!objectHead) throw new HttpError("Review asset is unavailable.", 404);
  const range = key.startsWith("audio/")
    ? parseByteRange(request.headers.get("Range"), objectHead.size)
    : null;
  const object = await env.MEDIA.get(
    key,
    range
      ? { range: { offset: range.offset, length: range.length } }
      : undefined,
  );
  if (!object) throw new HttpError("Review asset is unavailable.", 404);
  const headers = secureHeaders(new Headers());
  headers.set("Content-Type", contentType(pathname));
  headers.set("Content-Length", String(range?.length ?? objectHead.size));
  headers.set("ETag", object.httpEtag);
  if (key.startsWith("audio/")) headers.set("Accept-Ranges", "bytes");
  if (range)
    headers.set(
      "Content-Range",
      `bytes ${range.offset}-${range.end}/${objectHead.size}`,
    );
  if (pathname.endsWith(".html") || pathname.endsWith("/")) {
    headers.set(
      "Content-Security-Policy",
      "default-src 'none'; base-uri 'none'; frame-ancestors 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; media-src 'self'; img-src 'self' data:; form-action 'none'",
    );
  }
  return new Response(request.method === "HEAD" ? null : object.body, {
    status: range ? 206 : 200,
    headers,
  });
}

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<Response> {
    try {
      const url = new URL(request.url);
      if (url.pathname === "/api/version") {
        return json({
          service: "travis-validation",
          build: env.BUILD_SHA,
          environment: env.ENVIRONMENT,
        });
      }
      const reviewer = await reviewerEmail(request, env, ctx);
      const reviewerHash = await sha256(reviewer);

      if (url.pathname === "/")
        return Response.redirect(new URL(`${APP_BASE}/`, url).toString(), 302);
      if (
        (request.method === "GET" || request.method === "HEAD") &&
        r2Key(url.pathname)
      ) {
        return media(request, env, url.pathname);
      }
      if (request.method === "GET" && url.pathname === `${API_BASE}/feedback`) {
        return feedback(env);
      }
      const trackMatch = url.pathname.match(
        new RegExp(`^${API_BASE}/feedback/([a-z0-9]+(?:-[a-z0-9]+)*)$`, "u"),
      );
      if (request.method === "PUT" && trackMatch?.[1]) {
        return saveTrack(request, env, reviewerHash, trackMatch[1]);
      }
      throw new HttpError("Not found.", 404);
    } catch (error) {
      if (error instanceof HttpError)
        return json({ error: error.message }, { status: error.status });
      console.error(
        JSON.stringify({
          message: "travis_validation_request_failed",
          error: error instanceof Error ? error.message : String(error),
        }),
      );
      return json(
        { error: "The validation service encountered an error." },
        { status: 500 },
      );
    }
  },
} satisfies ExportedHandler<Env>;
