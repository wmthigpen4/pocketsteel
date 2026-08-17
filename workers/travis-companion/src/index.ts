import { WorkflowEntrypoint, type WorkflowEvent, type WorkflowStep, type WorkflowStepEvent } from "cloudflare:workers";

import {
  buildCompanionPdf,
  contentHash,
  decodeBase64Url,
  DomainError,
  randomToken,
  sha256,
  signLessonToken,
  timingSafeSecret,
  validateCompanion,
  verifyLessonToken,
} from "./domain";
import { authorHtml, embedHtml, oauthCallbackHtml } from "./ui";

type DbProject = {
  id: string;
  slug: string;
  title: string;
  course_id: string;
  lesson_id: string;
  state: string;
  draft_version: number;
  draft_json: string;
  primary_track_asset_id: string | null;
  current_published_revision: string | null;
  workflow_instance_id: string | null;
  created_at: string;
  updated_at: string;
};

type DbAsset = {
  id: string;
  project_id: string;
  kind: "lesson_video" | "backing_track";
  file_name: string;
  content_type: string;
  declared_size: number;
  actual_size: number | null;
  expected_sha256: string | null;
  actual_sha256: string | null;
  duration_ms: number | null;
  r2_key: string;
  upload_id: string | null;
  status: string;
  label: string | null;
  is_primary: number;
  visible_to_learners: number;
  downloadable: number;
  created_at: string;
  updated_at: string;
};

type WorkflowParams = {
  projectId: string;
  jobId: string;
  videoAssetId: string;
  primaryTrackAssetId: string;
};

type RunnerResult = {
  status: "complete" | "failed";
  resultKey?: string;
  sourceHashes?: Record<string, string>;
  error?: string;
  retryable?: boolean;
};

const JSON_LIMIT = 1024 * 1024;
const AUTHOR_HEADER = "CF-Access-Jwt-Assertion";
const ALLOWED_MEDIA: Record<string, { kind: DbAsset["kind"]; extensions: string[] }> = {
  "video/mp4": { kind: "lesson_video", extensions: [".mp4"] },
  "video/quicktime": { kind: "lesson_video", extensions: [".mov"] },
  "audio/mpeg": { kind: "backing_track", extensions: [".mp3"] },
};

function now(): string {
  return new Date().toISOString();
}

function json(payload: unknown, init: ResponseInit = {}): Response {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json; charset=utf-8");
  headers.set("Cache-Control", "no-store");
  headers.set("X-Content-Type-Options", "nosniff");
  return Response.json(payload, { ...init, headers });
}

function html(body: string, nonce: string, frameAncestors: string, init: ResponseInit = {}): Response {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "text/html; charset=utf-8");
  headers.set("Cache-Control", "no-store");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("Referrer-Policy", "no-referrer");
  headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  headers.set(
    "Content-Security-Policy",
    `default-src 'none'; base-uri 'none'; frame-ancestors ${frameAncestors}; script-src 'nonce-${nonce}'; style-src 'nonce-${nonce}'; connect-src 'self'; media-src 'self' blob:; img-src 'self' data:; form-action 'self' https://sso.teachable.com`,
  );
  return new Response(body, { ...init, headers });
}

function frameAncestors(value: string): string {
  if (value === "'none'") return value;
  const origins = value.trim().split(/\s+/u);
  if (!origins.length) throw new DomainError("FRAME_ANCESTORS must list exact school origins.", 500);
  for (const origin of origins) {
    const parsed = new URL(origin);
    const localHttp = parsed.protocol === "http:" && ["127.0.0.1", "localhost"].includes(parsed.hostname);
    if ((parsed.protocol !== "https:" && !localHttp) || parsed.origin !== origin) {
      throw new DomainError("FRAME_ANCESTORS must list exact HTTPS school origins.", 500);
    }
  }
  return origins.join(" ");
}

async function body<T>(request: Request): Promise<T> {
  const declared = Number(request.headers.get("Content-Length") || 0);
  if (declared > JSON_LIMIT) throw new DomainError("JSON payload is too large.", 413);
  const value: unknown = await request.json();
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new DomainError("JSON object required.");
  return value as T;
}

function nonce(): string {
  return randomToken(18);
}

function cleanSlug(value: unknown): string {
  const slug = String(value ?? "").trim().toLowerCase();
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/u.test(slug)) throw new DomainError("Lesson slug must contain lowercase letters, numbers, and hyphens.");
  return slug;
}

function cleanFileName(value: unknown): string {
  const name = String(value ?? "").trim().replace(/[^a-zA-Z0-9._-]/gu, "-").slice(0, 160);
  if (!name || name.startsWith(".")) throw new DomainError("A safe media filename is required.");
  return name;
}

function assetView(asset: DbAsset): Record<string, unknown> {
  return {
    id: asset.id,
    projectId: asset.project_id,
    kind: asset.kind,
    fileName: asset.file_name,
    contentType: asset.content_type,
    declaredSize: asset.declared_size,
    actualSize: asset.actual_size,
    expectedSha256: asset.expected_sha256,
    actualSha256: asset.actual_sha256,
    durationMs: asset.duration_ms,
    status: asset.status,
    label: asset.label,
    isPrimary: asset.is_primary === 1,
    visibleToLearners: asset.visible_to_learners === 1,
    downloadable: asset.downloadable === 1,
  };
}

function projectView(project: DbProject): Record<string, unknown> {
  return {
    id: project.id,
    slug: project.slug,
    title: project.title,
    courseId: project.course_id,
    lessonId: project.lesson_id,
    state: project.state,
    draftVersion: project.draft_version,
    draft: JSON.parse(project.draft_json),
    primaryTrackAssetId: project.primary_track_asset_id,
    currentPublishedRevision: project.current_published_revision,
    workflowInstanceId: project.workflow_instance_id,
    createdAt: project.created_at,
    updatedAt: project.updated_at,
  };
}

async function project(env: Env, id: string): Promise<DbProject> {
  const row = await env.DB.prepare("SELECT * FROM projects WHERE id = ?").bind(id).first<DbProject>();
  if (!row) throw new DomainError("Lesson project not found.", 404);
  return row;
}

async function projectBySlug(env: Env, slug: string): Promise<DbProject> {
  const row = await env.DB.prepare("SELECT * FROM projects WHERE slug = ?").bind(slug).first<DbProject>();
  if (!row) throw new DomainError("Published lesson companion not found.", 404);
  return row;
}

async function asset(env: Env, id: string): Promise<DbAsset> {
  const row = await env.DB.prepare("SELECT * FROM media_assets WHERE id = ?").bind(id).first<DbAsset>();
  if (!row) throw new DomainError("Media asset not found.", 404);
  return row;
}

async function assetsForProject(env: Env, projectId: string): Promise<DbAsset[]> {
  const result = await env.DB.prepare("SELECT * FROM media_assets WHERE project_id = ? ORDER BY created_at").bind(projectId).all<DbAsset>();
  return result.results;
}

function starterCopedent(env: Env): Record<string, unknown> {
  const fallback = {
    id: "travis-e9-v1",
    label: "Travis E9 — confirm before first publish",
    stringsHighToLow: [
      [1, "F#4"], [2, "D#4"], [3, "G#4"], [4, "E4"], [5, "B3"],
      [6, "G#3"], [7, "F#3"], [8, "E3"], [9, "D3"], [10, "B2"],
    ].map(([string, openPitch]) => ({ string, openPitch })),
    controls: [
      { code: "A", label: "A pedal", changes: [{ string: 5, semitones: 2 }, { string: 10, semitones: 2 }] },
      { code: "B", label: "B pedal", changes: [{ string: 3, semitones: 1 }, { string: 6, semitones: 1 }] },
      { code: "E", label: "E lower", changes: [{ string: 4, semitones: -1 }, { string: 8, semitones: -1 }] },
      { code: "H1", label: "First-string half raise", changes: [{ string: 1, semitones: 1 }] },
    ],
  };
  if (!env.TRAVIS_COPEDENT_JSON) return fallback;
  try {
    const configured: unknown = JSON.parse(env.TRAVIS_COPEDENT_JSON);
    if (!configured || typeof configured !== "object" || Array.isArray(configured)) throw new Error("not an object");
    return structuredClone(configured) as Record<string, unknown>;
  } catch {
    throw new DomainError("TRAVIS_COPEDENT_JSON is not a valid copedent snapshot.", 500);
  }
}

function starterDraft(env: Env, input: { id: string; slug: string; title: string; courseId: string; lessonId: string; key: string; meter: string }): Record<string, unknown> {
  return {
    schemaVersion: "lesson_companion_v3",
    companionId: `travis-toy-tutorials-${input.slug}`,
    revision: `${input.slug}-draft-1`,
    state: "draft",
    lesson: {
      slug: input.slug,
      title: input.title,
      subtitle: "Travis Toy Tutorials lesson companion",
      key: input.key,
      meter: input.meter,
      teachable: { school: "Travis Toy Tutorials", courseId: input.courseId, lessonId: input.lessonId },
    },
    copedentSnapshot: starterCopedent(env),
    media: { lessonVideo: { assetId: "", fileName: "", durationMs: 0, sha256: null }, backingTracks: [] },
    primaryTrackId: null,
    songChordTimeline: [],
    passages: [],
    analysis: { status: "not_started", modelVersions: {}, sourceHashes: {} },
    publication: { publishedAt: null, contentSha256: null, uncertaintyVisible: true },
  };
}

async function syncDraftMedia(env: Env, projectRow: DbProject, editor = "system"): Promise<DbProject> {
  const mediaAssets = await assetsForProject(env, projectRow.id);
  const draft = JSON.parse(projectRow.draft_json) as Record<string, unknown>;
  const media = draft.media as Record<string, unknown>;
  const uploadedVideo = mediaAssets.find((item) => item.kind === "lesson_video" && item.status === "uploaded");
  const tracks = mediaAssets.filter((item) => item.kind === "backing_track" && item.status === "uploaded");
  if (uploadedVideo) {
    media.lessonVideo = {
      assetId: uploadedVideo.id,
      fileName: uploadedVideo.file_name,
      durationMs: uploadedVideo.duration_ms ?? 1,
      sha256: uploadedVideo.actual_sha256 ?? uploadedVideo.expected_sha256,
    };
  }
  media.backingTracks = tracks.map((item) => ({
    assetId: item.id,
    fileName: item.file_name,
    label: item.label ?? item.file_name,
    durationMs: item.duration_ms ?? 1,
    sha256: item.actual_sha256 ?? item.expected_sha256,
    primary: item.is_primary === 1,
    visibleToLearners: item.visible_to_learners === 1,
    downloadable: item.downloadable === 1,
    synchronized: item.is_primary === 1,
  }));
  const primary = tracks.find((item) => item.is_primary === 1);
  draft.primaryTrackId = primary?.id ?? null;
  const version = projectRow.draft_version + 1;
  draft.revision = `${projectRow.slug}-draft-${version}`;
  await env.DB.batch([
    env.DB.prepare("UPDATE projects SET draft_json = ?, draft_version = ?, primary_track_asset_id = ?, updated_at = ? WHERE id = ?")
      .bind(JSON.stringify(draft), version, primary?.id ?? null, now(), projectRow.id),
    env.DB.prepare("INSERT INTO edit_events (id, project_id, from_version, to_version, editor_email, summary, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)")
      .bind(crypto.randomUUID(), projectRow.id, projectRow.draft_version, version, editor, "Synchronized media metadata", now()),
  ]);
  return project(env, projectRow.id);
}

async function verifyAccessJwt(token: string, env: Env): Promise<string> {
  const parts = token.split(".");
  if (parts.length !== 3 || !parts[0] || !parts[1] || !parts[2]) throw new DomainError("Author access required.", 401);
  const header = JSON.parse(new TextDecoder().decode(decodeBase64Url(parts[0]))) as { kid?: string; alg?: string };
  const claims = JSON.parse(new TextDecoder().decode(decodeBase64Url(parts[1]))) as { aud?: string[] | string; email?: string; exp?: number; iss?: string };
  const audiences = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  if (header.alg !== "RS256" || !header.kid || !audiences.includes(env.ACCESS_AUD) || !claims.exp || claims.exp <= Date.now() / 1000) {
    throw new DomainError("Author access required.", 401);
  }
  const team = env.ACCESS_TEAM_DOMAIN.replace(/^https?:\/\//u, "").replace(/\/$/u, "");
  const expectedIssuer = `https://${team}`;
  if (claims.iss !== expectedIssuer) throw new DomainError("Author access issuer is invalid.", 401);
  const certRequest = new Request(`${expectedIssuer}/cdn-cgi/access/certs`);
  let certResponse = await caches.default.match(certRequest);
  if (!certResponse) {
    certResponse = await fetch(certRequest);
    if (!certResponse.ok) throw new DomainError("Author identity verification is unavailable.", 503);
    const cached = new Response(certResponse.body, certResponse);
    cached.headers.set("Cache-Control", "public, max-age=3600");
    await caches.default.put(certRequest, cached.clone());
    certResponse = cached;
  }
  const certs = await certResponse.json<{ keys?: (JsonWebKey & { kid?: string })[] }>();
  const jwk = certs.keys?.find((key) => key.kid === header.kid);
  if (!jwk) throw new DomainError("Author identity key is unavailable.", 401);
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const valid = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, decodeBase64Url(parts[2]), new TextEncoder().encode(`${parts[0]}.${parts[1]}`));
  if (!valid || !claims.email) throw new DomainError("Author access required.", 401);
  return claims.email;
}

async function author(request: Request, env: Env): Promise<string> {
  const localPreview = new URL(request.url).searchParams.get("local") === "1";
  if (env.ENVIRONMENT === "development" && (request.headers.get("X-Travis-Local-Author") === "1" || localPreview)) return "local-author@development.invalid";
  const token = request.headers.get(AUTHOR_HEADER) ?? "";
  return verifyAccessJwt(token, env);
}

async function runner(request: Request, env: Env): Promise<void> {
  const token = request.headers.get("Authorization")?.replace(/^Bearer\s+/iu, "") ?? "";
  if (!(await timingSafeSecret(token, env.RUNNER_TOKEN))) throw new DomainError("Runner access required.", 401);
}

async function listProjects(env: Env): Promise<Response> {
  const result = await env.DB.prepare("SELECT id, slug, title, state, draft_version, current_published_revision, created_at, updated_at FROM projects ORDER BY updated_at DESC").all();
  return json({ projects: result.results.map((row) => ({
    id: row.id, slug: row.slug, title: row.title, state: row.state, draftVersion: row.draft_version,
    currentPublishedRevision: row.current_published_revision, createdAt: row.created_at, updatedAt: row.updated_at,
  })) });
}

async function createProject(request: Request, env: Env): Promise<Response> {
  const input = await body<{ title?: string; slug?: string; courseId?: string; lessonId?: string; key?: string; meter?: string }>(request);
  const id = crypto.randomUUID();
  const slug = cleanSlug(input.slug);
  const title = String(input.title ?? "").trim().slice(0, 180);
  const courseId = String(input.courseId ?? "").trim().slice(0, 100);
  const lessonId = String(input.lessonId ?? "").trim().slice(0, 100);
  if (!title || !courseId || !lessonId) throw new DomainError("Title, course ID, and lesson ID are required.");
  const created = now();
  const draft = starterDraft(env, { id, slug, title, courseId, lessonId, key: String(input.key ?? "D"), meter: String(input.meter ?? "4/4") });
  try {
    await env.DB.prepare("INSERT INTO projects (id, slug, title, course_id, lesson_id, state, draft_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?)")
      .bind(id, slug, title, courseId, lessonId, JSON.stringify(draft), created, created).run();
  } catch (error) {
    if (error instanceof Error && error.message.includes("UNIQUE")) throw new DomainError("That lesson slug is already in use.", 409);
    throw error;
  }
  return json({ project: projectView(await project(env, id)) }, { status: 201 });
}

async function getProject(env: Env, id: string): Promise<Response> {
  const row = await project(env, id);
  const [media, revisions, jobs] = await Promise.all([
    assetsForProject(env, id),
    env.DB.prepare("SELECT revision, content_sha256, published_at, published_by FROM published_revisions WHERE project_id = ? ORDER BY published_at DESC").bind(id).all(),
    env.DB.prepare("SELECT id, status, attempt, progress, progress_message, error, retryable, created_at, updated_at FROM analysis_jobs WHERE project_id = ? ORDER BY created_at DESC LIMIT 20").bind(id).all(),
  ]);
  return json({
    project: projectView(row),
    assets: media.map(assetView),
    revisions: revisions.results.map((item) => ({ revision: item.revision, contentSha256: item.content_sha256, publishedAt: item.published_at, publishedBy: item.published_by })),
    jobs: jobs.results.map((item) => ({ id: item.id, status: item.status, attempt: item.attempt, progress: item.progress, progressMessage: item.progress_message, error: item.error, retryable: item.retryable === 1, createdAt: item.created_at, updatedAt: item.updated_at })),
  });
}

async function jobStatus(env: Env, projectId: string, jobId: string): Promise<Response> {
  const row = await env.DB.prepare("SELECT id, project_id, status, attempt, progress, progress_message, error, retryable, created_at, updated_at FROM analysis_jobs WHERE id = ? AND project_id = ?")
    .bind(jobId, projectId).first<Record<string, unknown>>();
  if (!row) throw new DomainError("Analysis job not found.", 404);
  return json({ job: { id: row.id, status: row.status, attempt: row.attempt, progress: row.progress, progressMessage: row.progress_message, error: row.error, retryable: row.retryable === 1, createdAt: row.created_at, updatedAt: row.updated_at } });
}

async function initializeUpload(request: Request, env: Env, projectId: string): Promise<Response> {
  const row = await project(env, projectId);
  const input = await body<{ kind?: string; fileName?: string; contentType?: string; size?: number; sha256?: string; label?: string }>(request);
  const contentType = String(input.contentType ?? "").toLowerCase();
  const allowed = ALLOWED_MEDIA[contentType];
  if (!allowed || allowed.kind !== input.kind) throw new DomainError("Upload an MP4/MOV lesson video or MP3 backing track.");
  const size = Number(input.size);
  if (!Number.isInteger(size) || size <= 0) throw new DomainError("Media size is required.");
  const expectedSha256 = input.sha256 ? String(input.sha256).toLowerCase() : null;
  if (expectedSha256 && !/^[a-f0-9]{64}$/u.test(expectedSha256)) throw new DomainError("Expected SHA-256 must be 64 lowercase hexadecimal characters.");
  const fileName = cleanFileName(input.fileName);
  if (!allowed.extensions.some((extension) => fileName.toLowerCase().endsWith(extension))) throw new DomainError("Filename does not match its media type.");
  const id = crypto.randomUUID();
  const key = `raw/${row.id}/${id}/${fileName}`;
  const upload = await env.MEDIA.createMultipartUpload(key, { httpMetadata: { contentType }, customMetadata: { projectId, assetId: id } });
  const created = now();
  await env.DB.batch([
    env.DB.prepare("INSERT INTO media_assets (id, project_id, kind, file_name, content_type, declared_size, expected_sha256, r2_key, upload_id, status, label, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'uploading', ?, ?, ?)")
      .bind(id, projectId, input.kind, fileName, contentType, size, expectedSha256, key, upload.uploadId, String(input.label ?? fileName).slice(0, 180), created, created),
    env.DB.prepare("UPDATE projects SET state = 'uploading', updated_at = ? WHERE id = ?").bind(created, projectId),
  ]);
  return json({ asset: { id, kind: input.kind, fileName }, uploadId: upload.uploadId }, { status: 201 });
}

async function uploadPart(request: Request, env: Env, assetId: string, partNumber: number, uploadId: string): Promise<Response> {
  const media = await asset(env, assetId);
  if (media.status !== "uploading" || media.upload_id !== uploadId || !request.body) throw new DomainError("Upload session is invalid.", 409);
  if (!Number.isInteger(partNumber) || partNumber < 1 || partNumber > 10_000) throw new DomainError("Upload part number is invalid.");
  const part = await env.MEDIA.resumeMultipartUpload(media.r2_key, uploadId).uploadPart(partNumber, request.body);
  return json({ partNumber: part.partNumber, etag: part.etag });
}

async function completeUpload(request: Request, env: Env, assetId: string): Promise<Response> {
  const media = await asset(env, assetId);
  const input = await body<{ uploadId?: string; parts?: { partNumber: number; etag: string }[] }>(request);
  if (media.status === "uploaded") return json({ asset: assetView(media), idempotent: true });
  if (media.status !== "uploading" || input.uploadId !== media.upload_id || !Array.isArray(input.parts) || input.parts.length === 0) {
    throw new DomainError("Upload completion is invalid.", 409);
  }
  const parts = input.parts.map((part) => ({ partNumber: Number(part.partNumber), etag: String(part.etag) })).sort((left, right) => left.partNumber - right.partNumber);
  const completed = await env.MEDIA.resumeMultipartUpload(media.r2_key, input.uploadId).complete(parts);
  if (completed.size !== media.declared_size) {
    await env.DB.prepare("UPDATE media_assets SET actual_size = ?, status = 'rejected', updated_at = ? WHERE id = ?")
      .bind(completed.size, now(), media.id).run();
    throw new DomainError("Uploaded media size does not match the declared file.", 409);
  }
  const primaryCount = await env.DB.prepare("SELECT COUNT(*) AS count FROM media_assets WHERE project_id = ? AND kind = 'backing_track' AND is_primary = 1").bind(media.project_id).first<{ count: number }>();
  const makePrimary = media.kind === "backing_track" && Number(primaryCount?.count ?? 0) === 0;
  const timestamp = now();
  await env.DB.prepare("UPDATE media_assets SET actual_size = ?, status = 'uploaded', is_primary = ?, visible_to_learners = ?, updated_at = ? WHERE id = ?")
    .bind(completed.size, makePrimary ? 1 : 0, makePrimary ? 1 : 0, timestamp, media.id).run();
  let row = await syncDraftMedia(env, await project(env, media.project_id));
  const assets = await assetsForProject(env, media.project_id);
  const ready = assets.some((item) => item.kind === "lesson_video" && item.status === "uploaded") && assets.some((item) => item.kind === "backing_track" && item.status === "uploaded" && item.is_primary === 1);
  if (ready) {
    await env.DB.prepare("UPDATE projects SET state = 'ready_for_analysis', updated_at = ? WHERE id = ?").bind(timestamp, media.project_id).run();
    row = await project(env, media.project_id);
  }
  return json({ asset: assetView(await asset(env, assetId)), project: projectView(row) });
}

async function configureAsset(request: Request, env: Env, id: string): Promise<Response> {
  const media = await asset(env, id);
  if (media.kind !== "backing_track") throw new DomainError("Only backing tracks have learner settings.");
  const input = await body<{ primary?: boolean; visibleToLearners?: boolean; downloadable?: boolean; label?: string }>(request);
  const statements: D1PreparedStatement[] = [];
  if (input.primary === true) {
    statements.push(env.DB.prepare("UPDATE media_assets SET is_primary = 0 WHERE project_id = ? AND kind = 'backing_track'").bind(media.project_id));
    statements.push(env.DB.prepare("UPDATE media_assets SET is_primary = 1, visible_to_learners = 1, updated_at = ? WHERE id = ?").bind(now(), id));
  }
  if (input.visibleToLearners !== undefined) statements.push(env.DB.prepare("UPDATE media_assets SET visible_to_learners = ?, updated_at = ? WHERE id = ?").bind(input.visibleToLearners ? 1 : 0, now(), id));
  if (input.downloadable !== undefined) statements.push(env.DB.prepare("UPDATE media_assets SET downloadable = ?, updated_at = ? WHERE id = ?").bind(input.downloadable ? 1 : 0, now(), id));
  if (input.label !== undefined) statements.push(env.DB.prepare("UPDATE media_assets SET label = ?, updated_at = ? WHERE id = ?").bind(String(input.label).slice(0, 180), now(), id));
  if (statements.length) await env.DB.batch(statements);
  await syncDraftMedia(env, await project(env, media.project_id));
  return json({ asset: assetView(await asset(env, id)) });
}

async function streamAsset(request: Request, env: Env, media: DbAsset, download: boolean): Promise<Response> {
  const rangeHeader = request.headers.get("Range");
  let range: { offset: number; length: number } | undefined;
  if (rangeHeader) {
    const match = /^bytes=(\d+)-(\d*)$/u.exec(rangeHeader);
    if (!match?.[1]) return new Response(null, { status: 416 });
    const offset = Number(match[1]);
    const end = match[2] ? Number(match[2]) : (media.actual_size ?? media.declared_size) - 1;
    if (end < offset) return new Response(null, { status: 416 });
    range = { offset, length: end - offset + 1 };
  }
  const object = await env.MEDIA.get(media.r2_key, range ? { range } : undefined);
  if (!object) throw new DomainError("Media object is unavailable.", 404);
  const headers = new Headers({
    "Content-Type": media.content_type,
    "Accept-Ranges": "bytes",
    "Cache-Control": "private, no-store",
    "X-Content-Type-Options": "nosniff",
  });
  if (download) headers.set("Content-Disposition", `attachment; filename="${media.file_name.replaceAll('"', "")}"`);
  if (range && object.range) {
    const total = media.actual_size ?? media.declared_size;
    const offset = Number(range.offset ?? 0);
    const length = Number(range.length ?? object.size);
    headers.set("Content-Range", `bytes ${offset}-${offset + length - 1}/${total}`);
    headers.set("Content-Length", String(length));
    return new Response(object.body, { status: 206, headers });
  }
  headers.set("Content-Length", String(object.size));
  return new Response(object.body, { headers });
}

async function patchDraft(request: Request, env: Env, projectId: string, email: string): Promise<Response> {
  const row = await project(env, projectId);
  const input = await body<{ expectedVersion?: number; draft?: unknown; summary?: string }>(request);
  if (Number(input.expectedVersion) !== row.draft_version) throw new DomainError("Draft changed in another session.", 409);
  if (!input.draft || typeof input.draft !== "object" || Array.isArray(input.draft)) throw new DomainError("Draft object required.");
  const draft = structuredClone(input.draft) as Record<string, unknown>;
  const lesson = draft.lesson as Record<string, unknown> | undefined;
  const teachable = lesson?.teachable as Record<string, unknown> | undefined;
  if (lesson?.slug !== row.slug || teachable?.courseId !== row.course_id || teachable?.lessonId !== row.lesson_id) {
    throw new DomainError("Lesson identity cannot be changed through draft edits.");
  }
  const version = row.draft_version + 1;
  draft.revision = `${row.slug}-draft-${version}`;
  const nextState = ["review_ready", "published"].includes(row.state)
    ? "review_ready"
    : row.state === "analysis_failed" ? "ready_for_analysis" : row.state;
  draft.state = nextState;
  const timestamp = now();
  const result = await env.DB.batch([
    env.DB.prepare("UPDATE projects SET draft_json = ?, draft_version = ?, state = ?, updated_at = ? WHERE id = ? AND draft_version = ?")
      .bind(JSON.stringify(draft), version, nextState, timestamp, projectId, row.draft_version),
    env.DB.prepare("INSERT INTO edit_events (id, project_id, from_version, to_version, editor_email, summary, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)")
      .bind(crypto.randomUUID(), projectId, row.draft_version, version, email, String(input.summary ?? "Edited companion draft").slice(0, 240), timestamp),
  ]);
  const projectUpdate = result[0];
  if (!projectUpdate || (projectUpdate.meta.changes ?? 0) !== 1) throw new DomainError("Draft changed in another session.", 409);
  return json({ draftVersion: version, revision: draft.revision });
}

async function startAnalysis(env: Env, projectId: string): Promise<Response> {
  const row = await project(env, projectId);
  const media = await assetsForProject(env, projectId);
  const video = media.find((item) => item.kind === "lesson_video" && item.status === "uploaded");
  const primary = media.find((item) => item.kind === "backing_track" && item.status === "uploaded" && item.is_primary === 1);
  const draft = JSON.parse(row.draft_json) as { passages?: unknown[] };
  if (!video || !primary || !draft.passages?.length) throw new DomainError("Upload a lesson video and primary MP3, then add at least one passage.");
  if (row.state === "processing") throw new DomainError("Analysis is already running.", 409);
  const jobId = crypto.randomUUID();
  const instanceId = `${projectId}-${row.draft_version}-${jobId}`;
  await env.DB.prepare("UPDATE projects SET state = 'processing', workflow_instance_id = ?, updated_at = ? WHERE id = ?").bind(instanceId, now(), projectId).run();
  try {
    await env.ANALYSIS_WORKFLOW.create({ id: instanceId, params: { projectId, jobId, videoAssetId: video.id, primaryTrackAssetId: primary.id } });
  } catch (error) {
    await env.DB.prepare("UPDATE projects SET state = 'analysis_failed', updated_at = ? WHERE id = ?").bind(now(), projectId).run();
    throw error;
  }
  return json({ status: "processing", jobId, workflowInstanceId: instanceId }, { status: 202 });
}

async function validationCandidate(row: DbProject): Promise<Record<string, unknown>> {
  const draft = JSON.parse(row.draft_json) as Record<string, unknown>;
  const candidate = structuredClone(draft) as Record<string, unknown>;
  candidate.state = "published";
  candidate.revision = `${row.slug}-validation`;
  candidate.publication = { publishedAt: now(), contentSha256: "pending", uncertaintyVisible: true };
  (candidate.publication as Record<string, unknown>).contentSha256 = await contentHash(candidate);
  validateCompanion(candidate, { publishing: true });
  return candidate;
}

async function publish(env: Env, row: DbProject, email: string): Promise<Response> {
  const candidate = await validationCandidate(row);
  const revision = `${row.slug}-r${row.draft_version}-${Date.now()}`;
  candidate.revision = revision;
  const publication = candidate.publication as Record<string, unknown>;
  publication.publishedAt = now();
  publication.contentSha256 = await contentHash(candidate);
  validateCompanion(candidate, { publishing: true });
  const hash = String(publication.contentSha256);
  const artifactKey = `published/${row.id}/${revision}/${hash}.json`;
  const pdfKey = `published/${row.id}/${revision}/${hash}.pdf`;
  try {
    await Promise.all([
      env.MEDIA.put(artifactKey, `${JSON.stringify(candidate)}\n`, { httpMetadata: { contentType: "application/json" }, customMetadata: { projectId: row.id, revision, sha256: hash } }),
      env.MEDIA.put(pdfKey, buildCompanionPdf(candidate), { httpMetadata: { contentType: "application/pdf", contentDisposition: `inline; filename="${row.slug}-companion.pdf"` }, customMetadata: { projectId: row.id, revision, sha256: hash } }),
    ]);
    await env.DB.batch([
      env.DB.prepare("INSERT INTO published_revisions (project_id, revision, content_sha256, artifact_key, pdf_key, published_by, published_at) VALUES (?, ?, ?, ?, ?, ?, ?)")
        .bind(row.id, revision, hash, artifactKey, pdfKey, email, publication.publishedAt),
      env.DB.prepare("UPDATE projects SET state = 'published', current_published_revision = ?, updated_at = ? WHERE id = ?")
        .bind(revision, now(), row.id),
    ]);
  } catch (error) {
    await env.DB.prepare("UPDATE projects SET state = 'publish_failed', updated_at = ? WHERE id = ?").bind(now(), row.id).run();
    throw error;
  }
  return json({ status: "published", revision, contentSha256: hash });
}

async function rollback(request: Request, env: Env, row: DbProject): Promise<Response> {
  const input = await body<{ revision?: string }>(request);
  const revision = String(input.revision ?? "");
  const exists = await env.DB.prepare("SELECT revision FROM published_revisions WHERE project_id = ? AND revision = ?").bind(row.id, revision).first();
  if (!exists) throw new DomainError("Published revision not found.", 404);
  await env.DB.prepare("UPDATE projects SET state = 'published', current_published_revision = ?, updated_at = ? WHERE id = ?").bind(revision, now(), row.id).run();
  return json({ status: "published", revision });
}

async function runnerClaim(env: Env): Promise<Response> {
  const current = now();
  const candidate = await env.DB.prepare("SELECT * FROM analysis_jobs WHERE status = 'queued' OR (status = 'leased' AND lease_expires_at < ?) ORDER BY created_at LIMIT 1").bind(current).first<Record<string, unknown>>();
  if (!candidate) return new Response(null, { status: 204 });
  const leaseToken = randomToken();
  const leaseHash = await sha256(leaseToken);
  const leaseExpires = new Date(Date.now() + 5 * 60 * 1000).toISOString();
  const updated = await env.DB.prepare("UPDATE analysis_jobs SET status = 'leased', lease_token_hash = ?, lease_expires_at = ?, attempt = attempt + 1, updated_at = ? WHERE id = ? AND (status = 'queued' OR lease_expires_at < ?)")
    .bind(leaseHash, leaseExpires, current, candidate.id, current).run();
  if ((updated.meta.changes ?? 0) !== 1) return new Response(null, { status: 204 });
  return json({ job: {
    id: candidate.id,
    projectId: candidate.project_id,
    videoAssetId: candidate.video_asset_id,
    primaryTrackAssetId: candidate.primary_track_asset_id,
    leaseToken,
    leaseExpiresAt: leaseExpires,
  } });
}

async function requireLease(request: Request, env: Env, jobId: string): Promise<Record<string, unknown>> {
  const row = await env.DB.prepare("SELECT * FROM analysis_jobs WHERE id = ?").bind(jobId).first<Record<string, unknown>>();
  if (!row || row.status !== "leased" || String(row.lease_expires_at ?? "") <= now()) throw new DomainError("Analysis job lease is invalid.", 409);
  const provided = request.headers.get("X-Job-Lease") ?? "";
  const expectedHash = String(row.lease_token_hash ?? "");
  if (!(await timingSafeSecret(await sha256(provided), expectedHash))) throw new DomainError("Analysis job lease is invalid.", 401);
  return row;
}

async function renewLease(request: Request, env: Env, jobId: string): Promise<Response> {
  await requireLease(request, env, jobId);
  const leaseExpiresAt = new Date(Date.now() + 5 * 60 * 1000).toISOString();
  await env.DB.prepare("UPDATE analysis_jobs SET lease_expires_at = ?, updated_at = ? WHERE id = ? AND status = 'leased'")
    .bind(leaseExpiresAt, now(), jobId).run();
  return json({ leaseExpiresAt });
}

async function reportRunnerProgress(request: Request, env: Env, jobId: string): Promise<Response> {
  await requireLease(request, env, jobId);
  const input = await body<{ progress?: number; message?: string }>(request);
  const progress = Number(input.progress);
  if (!Number.isFinite(progress) || progress < 0 || progress > 1) throw new DomainError("Runner progress must be between zero and one.");
  const message = String(input.message ?? "").slice(0, 240);
  await env.DB.prepare("UPDATE analysis_jobs SET progress = ?, progress_message = ?, updated_at = ? WHERE id = ? AND status = 'leased'")
    .bind(progress, message, now(), jobId).run();
  return json({ progress, message });
}

async function completeRunnerJob(request: Request, env: Env, jobId: string, failed: boolean): Promise<Response> {
  const existing = await env.DB.prepare("SELECT status, lease_token_hash FROM analysis_jobs WHERE id = ?").bind(jobId).first<Record<string, unknown>>();
  if (existing && ["complete", "failed"].includes(String(existing.status))) {
    const provided = request.headers.get("X-Job-Lease") ?? "";
    if (!(await timingSafeSecret(await sha256(provided), String(existing.lease_token_hash ?? "")))) throw new DomainError("Analysis job lease is invalid.", 401);
    return json({ status: existing.status, idempotent: true });
  }
  const job = await requireLease(request, env, jobId);
  const input = await body<{ resultKey?: string; sourceHashes?: Record<string, string>; error?: string; retryable?: boolean }>(request);
  const workflowId = String(job.workflow_instance_id);
  const payload: RunnerResult = failed
    ? { status: "failed", error: String(input.error ?? "Analysis failed.").slice(0, 500), retryable: input.retryable === true }
    : { status: "complete", resultKey: String(input.resultKey ?? ""), sourceHashes: input.sourceHashes ?? {} };
  if (!failed && !payload.resultKey) throw new DomainError("Analysis result key is required.");
  await env.DB.prepare("UPDATE analysis_jobs SET status = ?, progress = ?, progress_message = ?, result_key = ?, error = ?, retryable = ?, updated_at = ? WHERE id = ?")
    .bind(failed ? "failed" : "complete", failed ? Number(job.progress ?? 0) : 1, failed ? "Analysis failed." : "Review draft complete.", payload.resultKey ?? null, payload.error ?? null, payload.retryable ? 1 : 0, now(), jobId).run();
  const instance = await env.ANALYSIS_WORKFLOW.get(workflowId);
  await instance.sendEvent({ type: "runner-complete", payload });
  return json({ status: payload.status });
}

async function publishedRevision(env: Env, row: DbProject): Promise<{ artifact_key: string; pdf_key: string; revision: string }> {
  if (!row.current_published_revision) throw new DomainError("This lesson companion is not published.", 404);
  const revision = await env.DB.prepare("SELECT artifact_key, pdf_key, revision FROM published_revisions WHERE project_id = ? AND revision = ?")
    .bind(row.id, row.current_published_revision).first<{ artifact_key: string; pdf_key: string; revision: string }>();
  if (!revision) throw new DomainError("Published revision is unavailable.", 404);
  return revision;
}

async function learnerClaims(request: Request, env: Env, row: DbProject): Promise<{ sub: string; projectId: string; slug: string; courseId: string; revision: string; exp: number }> {
  const url = new URL(request.url);
  const bearer = request.headers.get("Authorization")?.replace(/^Bearer\s+/iu, "") || url.searchParams.get("token") || "";
  const claims = await verifyLessonToken(bearer, env.LESSON_TOKEN_SECRET);
  if (claims.projectId !== row.id || claims.slug !== row.slug || claims.courseId !== row.course_id || claims.revision !== row.current_published_revision) {
    throw new DomainError("Lesson token does not authorize this revision.", 403);
  }
  return claims;
}

async function oauthStart(env: Env, slug: string): Promise<Response> {
  const row = await projectBySlug(env, slug);
  await publishedRevision(env, row);
  const state = randomToken();
  await env.DB.prepare("INSERT INTO oauth_states (state_hash, project_id, return_origin, expires_at) VALUES (?, ?, ?, ?)")
    .bind(await sha256(state), row.id, env.PUBLIC_ORIGIN, new Date(Date.now() + 10 * 60 * 1000).toISOString()).run();
  const authorize = new URL(env.TEACHABLE_AUTHORIZE_URL.replace("{school_id}", encodeURIComponent(env.TEACHABLE_SCHOOL_ID)));
  authorize.searchParams.set("client_id", env.TEACHABLE_CLIENT_ID);
  authorize.searchParams.set("response_type", "code");
  authorize.searchParams.set("required_scopes", "courses:read");
  authorize.searchParams.set("state", state);
  return Response.redirect(authorize.href, 302);
}

async function oauthCallback(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const state = url.searchParams.get("state") ?? "";
  const code = url.searchParams.get("code") ?? "";
  const stateRow = await env.DB.prepare("SELECT * FROM oauth_states WHERE state_hash = ? AND used_at IS NULL AND expires_at > ?")
    .bind(await sha256(state), now()).first<Record<string, unknown>>();
  if (!stateRow || !code) throw new DomainError("OAuth callback state is invalid.", 400);
  const row = await project(env, String(stateRow.project_id));
  const tokenResponse = await fetch(env.TEACHABLE_TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grant_type: "authorization_code",
      client_id: env.TEACHABLE_CLIENT_ID,
      client_secret: env.TEACHABLE_CLIENT_SECRET,
      redirect_uri: `${env.PUBLIC_ORIGIN}/auth/teachable/callback`,
      code,
    }),
  });
  if (!tokenResponse.ok) throw new DomainError("Teachable authorization failed.", 502);
  const tokens = await tokenResponse.json<{ access_token?: string }>();
  if (!tokens.access_token) throw new DomainError("Teachable did not return an access token.", 502);
  const courseUrl = env.TEACHABLE_COURSE_URL.replace("{course_id}", encodeURIComponent(row.course_id));
  const courseResponse = await fetch(courseUrl, { headers: { Authorization: `Bearer ${tokens.access_token}` } });
  if ([403, 404].includes(courseResponse.status)) throw new DomainError("This Teachable account is not enrolled in the lesson course.", 403);
  if (!courseResponse.ok) throw new DomainError("Teachable enrollment verification failed.", 502);
  const subject = `teachable:${(await sha256(tokens.access_token)).slice(0, 32)}`;
  const embedCode = randomToken();
  await env.DB.batch([
    env.DB.prepare("UPDATE oauth_states SET used_at = ? WHERE state_hash = ?").bind(now(), await sha256(state)),
    env.DB.prepare("INSERT INTO embed_codes (code_hash, project_id, subject, expires_at) VALUES (?, ?, ?, ?)")
      .bind(await sha256(embedCode), row.id, subject, new Date(Date.now() + 2 * 60 * 1000).toISOString()),
  ]);
  const pageNonce = nonce();
  return html(oauthCallbackHtml(pageNonce, env.PUBLIC_ORIGIN, embedCode), pageNonce, "'none'");
}

async function exchangeEmbedCode(request: Request, env: Env): Promise<Response> {
  const input = await body<{ code?: string; slug?: string }>(request);
  const row = await projectBySlug(env, cleanSlug(input.slug));
  const revision = await publishedRevision(env, row);
  const codeHash = await sha256(String(input.code ?? ""));
  const codeRow = await env.DB.prepare("SELECT * FROM embed_codes WHERE code_hash = ? AND project_id = ? AND used_at IS NULL AND expires_at > ?")
    .bind(codeHash, row.id, now()).first<Record<string, unknown>>();
  if (!codeRow) throw new DomainError("Embed verification code is invalid or expired.", 401);
  const updated = await env.DB.prepare("UPDATE embed_codes SET used_at = ? WHERE code_hash = ? AND used_at IS NULL").bind(now(), codeHash).run();
  if ((updated.meta.changes ?? 0) !== 1) throw new DomainError("Embed verification code has already been used.", 401);
  const token = await signLessonToken(env.LESSON_TOKEN_SECRET, {
    sub: String(codeRow.subject), projectId: row.id, slug: row.slug, courseId: row.course_id, revision: revision.revision,
    exp: Math.floor(Date.now() / 1000) + 60 * 60,
  });
  return json({ token, expiresIn: 3600 });
}

async function devToken(env: Env, slug: string): Promise<Response> {
  if (env.ENVIRONMENT !== "development") throw new DomainError("Not found.", 404);
  const row = await projectBySlug(env, slug);
  const revision = await publishedRevision(env, row);
  const token = await signLessonToken(env.LESSON_TOKEN_SECRET, {
    sub: "local-student", projectId: row.id, slug: row.slug, courseId: row.course_id, revision: revision.revision,
    exp: Math.floor(Date.now() / 1000) + 60 * 60,
  });
  return json({ token, expiresIn: 3600 });
}

async function route(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const path = url.pathname.replace(/\/$/u, "") || "/";
  const method = request.method.toUpperCase();
  if (path === "/api/environment" && method === "GET") return json({ development: env.ENVIRONMENT === "development" });
  if (path === "/" && method === "GET") return Response.redirect(`${env.PUBLIC_ORIGIN}/admin`, 302);
  if (path === "/admin" && method === "GET") {
    await author(request, env);
    const pageNonce = nonce();
    return html(authorHtml(pageNonce), pageNonce, "'none'");
  }
  const embedMatch = /^\/embed\/([a-z0-9-]+)$/u.exec(path);
  if (embedMatch?.[1] && method === "GET") {
    await projectBySlug(env, embedMatch[1]);
    const pageNonce = nonce();
    return html(embedHtml(pageNonce, embedMatch[1]), pageNonce, frameAncestors(env.FRAME_ANCESTORS));
  }
  if (path === "/auth/teachable/start" && method === "GET") return oauthStart(env, cleanSlug(url.searchParams.get("lesson")));
  if (path === "/auth/teachable/callback" && method === "GET") return oauthCallback(request, env);
  if (path === "/api/embed/exchange" && method === "POST") return exchangeEmbedCode(request, env);

  const embedApi = /^\/api\/embed\/([a-z0-9-]+)\/(artifact|pdf|dev-token)$/u.exec(path);
  if (embedApi?.[1] && embedApi[2]) {
    const row = await projectBySlug(env, embedApi[1]);
    if (embedApi[2] === "dev-token" && method === "POST") return devToken(env, row.slug);
    await learnerClaims(request, env, row);
    const revision = await publishedRevision(env, row);
    const key = embedApi[2] === "pdf" ? revision.pdf_key : revision.artifact_key;
    const object = await env.MEDIA.get(key);
    if (!object) throw new DomainError("Published companion artifact is unavailable.", 404);
    const headers = new Headers({
      "Content-Type": embedApi[2] === "pdf" ? "application/pdf" : "application/json; charset=utf-8",
      "Cache-Control": "private, no-store",
      "X-Content-Type-Options": "nosniff",
    });
    return new Response(object.body, { headers });
  }
  const embedMedia = /^\/api\/embed\/([a-z0-9-]+)\/media\/([a-f0-9-]+)$/u.exec(path);
  if (embedMedia?.[1] && embedMedia[2] && method === "GET") {
    const row = await projectBySlug(env, embedMedia[1]);
    await learnerClaims(request, env, row);
    const media = await asset(env, embedMedia[2]);
    if (media.project_id !== row.id || media.kind !== "backing_track" || media.visible_to_learners !== 1) throw new DomainError("Track is not available to learners.", 403);
    const download = url.searchParams.get("download") === "1";
    if (download && media.downloadable !== 1) throw new DomainError("Track download is disabled.", 403);
    return streamAsset(request, env, media, download);
  }

  if (path.startsWith("/api/runner/")) {
    await runner(request, env);
    if (path === "/api/runner/jobs/claim" && method === "POST") return runnerClaim(env);
    const runnerAsset = /^\/api\/runner\/jobs\/([a-f0-9-]+)\/assets\/([a-f0-9-]+)$/u.exec(path);
    if (runnerAsset?.[1] && runnerAsset[2] && method === "GET") {
      const job = await requireLease(request, env, runnerAsset[1]);
      const media = await asset(env, runnerAsset[2]);
      const allowed = new Set([String(job.video_asset_id), String(job.primary_track_asset_id)]);
      if (!allowed.has(media.id) || media.project_id !== String(job.project_id)) throw new DomainError("Asset is not part of this analysis job.", 403);
      return streamAsset(request, env, media, false);
    }
    const draftMatch = /^\/api\/runner\/jobs\/([a-f0-9-]+)\/draft$/u.exec(path);
    if (draftMatch?.[1] && method === "GET") {
      const job = await requireLease(request, env, draftMatch[1]);
      const row = await project(env, String(job.project_id));
      return json(JSON.parse(row.draft_json));
    }
    const renewMatch = /^\/api\/runner\/jobs\/([a-f0-9-]+)\/renew$/u.exec(path);
    if (renewMatch?.[1] && method === "POST") return renewLease(request, env, renewMatch[1]);
    const progressMatch = /^\/api\/runner\/jobs\/([a-f0-9-]+)\/progress$/u.exec(path);
    if (progressMatch?.[1] && method === "POST") return reportRunnerProgress(request, env, progressMatch[1]);
    const artifactMatch = /^\/api\/runner\/jobs\/([a-f0-9-]+)\/artifacts\/([a-z0-9.-]+)$/u.exec(path);
    if (artifactMatch?.[1] && artifactMatch[2] && method === "PUT") {
      await requireLease(request, env, artifactMatch[1]);
      if (!request.body) throw new DomainError("Artifact body is required.");
      const key = `analysis/${artifactMatch[1]}/${artifactMatch[2]}`;
      const stored = await env.MEDIA.put(key, request.body, { httpMetadata: { contentType: request.headers.get("Content-Type") ?? "application/octet-stream" } });
      return json({ key, size: stored.size });
    }
    const complete = /^\/api\/runner\/jobs\/([a-f0-9-]+)\/(complete|fail)$/u.exec(path);
    if (complete?.[1] && complete[2] && method === "POST") return completeRunnerJob(request, env, complete[1], complete[2] === "fail");
    throw new DomainError("Runner route not found.", 404);
  }

  if (path.startsWith("/api/author/")) {
    const email = await author(request, env);
    if (path === "/api/author/projects" && method === "GET") return listProjects(env);
    if (path === "/api/author/projects" && method === "POST") return createProject(request, env);
    const projectMatch = /^\/api\/author\/projects\/([a-f0-9-]+)$/u.exec(path);
    if (projectMatch?.[1] && method === "GET") return getProject(env, projectMatch[1]);
    const jobMatch = /^\/api\/author\/projects\/([a-f0-9-]+)\/jobs\/([a-f0-9-]+)$/u.exec(path);
    if (jobMatch?.[1] && jobMatch[2] && method === "GET") return jobStatus(env, jobMatch[1], jobMatch[2]);
    const uploadInit = /^\/api\/author\/projects\/([a-f0-9-]+)\/uploads$/u.exec(path);
    if (uploadInit?.[1] && method === "POST") return initializeUpload(request, env, uploadInit[1]);
    const partMatch = /^\/api\/author\/uploads\/([a-f0-9-]+)\/parts\/(\d+)$/u.exec(path);
    if (partMatch?.[1] && partMatch[2] && method === "PUT") return uploadPart(request, env, partMatch[1], Number(partMatch[2]), url.searchParams.get("uploadId") ?? "");
    const uploadComplete = /^\/api\/author\/uploads\/([a-f0-9-]+)\/complete$/u.exec(path);
    if (uploadComplete?.[1] && method === "POST") return completeUpload(request, env, uploadComplete[1]);
    const authorAsset = /^\/api\/author\/assets\/([a-f0-9-]+)$/u.exec(path);
    if (authorAsset?.[1] && method === "GET") return streamAsset(request, env, await asset(env, authorAsset[1]), false);
    if (authorAsset?.[1] && method === "PATCH") return configureAsset(request, env, authorAsset[1]);
    const draftMatch = /^\/api\/author\/projects\/([a-f0-9-]+)\/draft$/u.exec(path);
    if (draftMatch?.[1] && method === "PATCH") return patchDraft(request, env, draftMatch[1], email);
    const analyzeMatch = /^\/api\/author\/projects\/([a-f0-9-]+)\/analyze$/u.exec(path);
    if (analyzeMatch?.[1] && method === "POST") return startAnalysis(env, analyzeMatch[1]);
    const retryMatch = /^\/api\/author\/projects\/([a-f0-9-]+)\/retry-analysis$/u.exec(path);
    if (retryMatch?.[1] && method === "POST") return startAnalysis(env, retryMatch[1]);
    const validateMatch = /^\/api\/author\/projects\/([a-f0-9-]+)\/validate$/u.exec(path);
    if (validateMatch?.[1] && method === "POST") {
      const candidate = await validationCandidate(await project(env, validateMatch[1]));
      return json({ valid: true, contentSha256: (candidate.publication as Record<string, unknown>).contentSha256 });
    }
    const publishMatch = /^\/api\/author\/projects\/([a-f0-9-]+)\/publish$/u.exec(path);
    if (publishMatch?.[1] && method === "POST") return publish(env, await project(env, publishMatch[1]), email);
    const rollbackMatch = /^\/api\/author\/projects\/([a-f0-9-]+)\/rollback$/u.exec(path);
    if (rollbackMatch?.[1] && method === "POST") return rollback(request, env, await project(env, rollbackMatch[1]));
    throw new DomainError("Author route not found.", 404);
  }
  throw new DomainError("Not found.", 404);
}

export class CompanionAnalysisWorkflow extends WorkflowEntrypoint<Env, WorkflowParams> {
  override async run(event: Readonly<WorkflowEvent<WorkflowParams>>, step: WorkflowStep): Promise<void> {
    const params = event.payload;
    await step.do("create analysis job", async () => {
      const timestamp = now();
      await this.env.DB.prepare("INSERT OR IGNORE INTO analysis_jobs (id, project_id, workflow_instance_id, status, video_asset_id, primary_track_asset_id, created_at, updated_at) VALUES (?, ?, ?, 'queued', ?, ?, ?, ?)")
        .bind(params.jobId, params.projectId, event.instanceId, params.videoAssetId, params.primaryTrackAssetId, timestamp, timestamp).run();
      return { jobId: params.jobId };
    });
    let result: Readonly<WorkflowStepEvent<RunnerResult>>;
    try {
      result = await step.waitForEvent<RunnerResult>("wait for private runner", { type: "runner-complete", timeout: "7 days" });
    } catch (error) {
      await step.do("record analysis timeout", async () => {
        await this.env.DB.prepare("UPDATE projects SET state = 'analysis_failed', updated_at = ? WHERE id = ?").bind(now(), params.projectId).run();
        await this.env.DB.prepare("UPDATE analysis_jobs SET status = 'failed', error = ?, retryable = 1, updated_at = ? WHERE id = ?")
          .bind("Private runner did not complete before the workflow timeout.", now(), params.jobId).run();
      });
      throw error;
    }
    await step.do("finalize review draft", async () => {
      if (result.payload.status === "failed") {
        await this.env.DB.prepare("UPDATE projects SET state = 'analysis_failed', updated_at = ? WHERE id = ?").bind(now(), params.projectId).run();
        return { status: "analysis_failed" };
      }
      const object = await this.env.MEDIA.get(String(result.payload.resultKey));
      if (!object || object.size > JSON_LIMIT) throw new Error("Private runner result is unavailable or too large.");
      const draft: unknown = await object.json();
      validateCompanion(draft);
      const row = await project(this.env, params.projectId);
      const [videoAsset, primaryAsset] = await Promise.all([asset(this.env, params.videoAssetId), asset(this.env, params.primaryTrackAssetId)]);
      const videoHash = result.payload.sourceHashes?.lessonVideo ?? "";
      const primaryHash = result.payload.sourceHashes?.primaryTrack ?? "";
      if (!/^[a-f0-9]{64}$/u.test(videoHash) || !/^[a-f0-9]{64}$/u.test(primaryHash)) {
        await this.env.DB.prepare("UPDATE projects SET state = 'analysis_failed', updated_at = ? WHERE id = ?").bind(now(), params.projectId).run();
        throw new Error("Private runner did not return valid source fingerprints.");
      }
      if ((videoAsset.expected_sha256 && videoAsset.expected_sha256 !== videoHash) || (primaryAsset.expected_sha256 && primaryAsset.expected_sha256 !== primaryHash)) {
        await this.env.DB.batch([
          this.env.DB.prepare("UPDATE projects SET state = 'analysis_failed', updated_at = ? WHERE id = ?").bind(now(), params.projectId),
          this.env.DB.prepare("UPDATE media_assets SET status = 'rejected', actual_sha256 = ?, updated_at = ? WHERE id = ?").bind(videoHash, now(), params.videoAssetId),
          this.env.DB.prepare("UPDATE media_assets SET status = 'rejected', actual_sha256 = ?, updated_at = ? WHERE id = ?").bind(primaryHash, now(), params.primaryTrackAssetId),
        ]);
        return { status: "analysis_failed", reason: "source_hash_mismatch" };
      }
      const nextVersion = row.draft_version + 1;
      const value = draft as Record<string, unknown>;
      value.revision = `${row.slug}-draft-${nextVersion}`;
      value.state = "review_ready";
      const media = value.media as Record<string, unknown>;
      const lessonVideo = media.lessonVideo as Record<string, unknown>;
      const backingTracks = media.backingTracks as Record<string, unknown>[];
      const primary = backingTracks.find((track) => String(track.assetId) === params.primaryTrackAssetId);
      await this.env.DB.batch([
        this.env.DB.prepare("UPDATE projects SET state = 'review_ready', draft_json = ?, draft_version = ?, updated_at = ? WHERE id = ?")
          .bind(JSON.stringify(value), nextVersion, now(), params.projectId),
        this.env.DB.prepare("UPDATE media_assets SET actual_sha256 = ?, duration_ms = ?, updated_at = ? WHERE id = ?")
          .bind(videoHash, Number(lessonVideo.durationMs), now(), params.videoAssetId),
        this.env.DB.prepare("UPDATE media_assets SET actual_sha256 = ?, duration_ms = ?, updated_at = ? WHERE id = ?")
          .bind(primaryHash, Number(primary?.durationMs), now(), params.primaryTrackAssetId),
      ]);
      return { status: "review_ready", draftVersion: nextVersion };
    });
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
      return await route(request, env);
    } catch (error) {
      const status = error instanceof DomainError ? error.status : 500;
      const message = error instanceof DomainError ? error.message : "Internal server error.";
      console.error(JSON.stringify({ message: "travis_companion_request_failed", path: new URL(request.url).pathname, status, error: error instanceof Error ? error.message : String(error) }));
      return json({ error: message }, { status });
    }
  },
} satisfies ExportedHandler<Env>;
