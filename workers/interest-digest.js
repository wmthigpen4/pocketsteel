const DEFAULT_LOOKBACK_DAYS = 7;
const MAX_DIGEST_LENGTH = 950;
const PUSHOVER_ENDPOINT = "https://api.pushover.net/1/messages.json";
const OBVIOUS_TEST_EMAILS = new Set([
  "test@example.com",
  "ops-smoke@example.com",
  "smoke-test@example.com",
  "example@example.com"
]);

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store"
    }
  });
}

function cleanString(value, maxLength = 2000) {
  return String(value || "").trim().slice(0, maxLength);
}

function normalizeEmail(value) {
  return cleanString(value, 320).toLowerCase();
}

function parseInterests(value) {
  if (Array.isArray(value)) {
    return value.map((item) => cleanString(item, 80)).filter(Boolean);
  }

  const text = cleanString(value, 1000);
  if (!text) {
    return [];
  }

  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) {
      return parsed.map((item) => cleanString(item, 80)).filter(Boolean);
    }
  } catch (_error) {
    // Fall back to a plain comma-separated display below.
  }

  return text.split(",").map((item) => cleanString(item, 80)).filter(Boolean);
}

function normalizeRow(row) {
  return {
    id: cleanString(row.id, 120),
    created_at: cleanString(row.created_at, 80),
    name: cleanString(row.name, 200),
    email: normalizeEmail(row.email),
    player_level: cleanString(row.player_level, 80),
    interests: parseInterests(row.interests),
    message: cleanString(row.message, 2000),
    status: cleanString(row.status || "new", 40).toLowerCase(),
    spam_score: Number.isFinite(Number(row.spam_score)) ? Number(row.spam_score) : 0,
    admin_notes: cleanString(row.admin_notes, 2000),
    notified_at: cleanString(row.notified_at, 80),
    source: cleanString(row.source || "landing_page", 80)
  };
}

function isObviousTestEmail(email) {
  if (OBVIOUS_TEST_EMAILS.has(email)) {
    return true;
  }

  return /^(test|testing|smoke|ops-smoke|example)([+._-].*)?@example\.(com|net|org)$/i.test(email);
}

function countUrlSignals(text) {
  const matches = cleanString(text, 3000).match(/\b(?:https?:\/\/|www\.|[a-z0-9-]+\.[a-z]{2,})(?:[^\s]*)/gi);
  return matches ? matches.length : 0;
}

function mergeAdminNotes(existingNotes, newNotes) {
  const existing = cleanString(existingNotes, 2000);
  const additions = newNotes.filter((note) => note && !existing.includes(note));
  if (additions.length === 0) {
    return existing;
  }

  const suffix = `interest-digest: ${additions.join("; ")}`;
  return [existing, suffix].filter(Boolean).join("\n").slice(0, 2000);
}

function classifySubmission(row, duplicateCount = 1) {
  const submission = normalizeRow(row);
  const reasons = [];
  let include = true;
  let status = submission.status || "new";
  let spamScore = submission.spam_score;

  if (isObviousTestEmail(submission.email)) {
    include = false;
    status = "spam";
    spamScore = Math.max(spamScore, 100);
    reasons.push("obvious test email");
  }

  const urlSignals = countUrlSignals(`${submission.name} ${submission.message}`);
  if (include && urlSignals >= 2) {
    status = "review";
    spamScore = Math.max(spamScore, 60);
    reasons.push("URL-heavy message");
  }

  if (
    include &&
    !submission.name &&
    !submission.message &&
    submission.interests.length === 0
  ) {
    status = "review";
    spamScore = Math.max(spamScore, 20);
    reasons.push("blank submission apart from email");
  }

  if (include && duplicateCount > 1) {
    reasons.push(`duplicate email group: ${duplicateCount} submissions`);
  }

  return {
    ...submission,
    include,
    status,
    spam_score: spamScore,
    admin_notes: mergeAdminNotes(submission.admin_notes, reasons),
    review_reasons: reasons
  };
}

function classifySubmissions(rows) {
  const normalized = rows.map(normalizeRow);
  const counts = new Map();
  for (const row of normalized) {
    counts.set(row.email, (counts.get(row.email) || 0) + 1);
  }

  return normalized.map((row) => classifySubmission(row, counts.get(row.email) || 1));
}

function groupIncludedSubmissions(classifiedRows) {
  const groups = new Map();
  for (const row of classifiedRows) {
    if (!row.include) {
      continue;
    }

    if (!groups.has(row.email)) {
      groups.set(row.email, []);
    }
    groups.get(row.email).push(row);
  }

  return [...groups.entries()].map(([email, submissions]) => ({ email, submissions }));
}

function formatSubmission(row, index, groupSize) {
  const label = groupSize > 1 ? `Submission ${index + 1}/${groupSize}` : "Submission";
  const interests = row.interests.length ? row.interests.join(", ") : "none selected";
  const message = row.message || "(no message)";
  const review = row.status === "review" ? `\nReview: ${row.review_reasons.join("; ") || "manual review"}` : "";

  return [
    `${label}: ${row.created_at || "unknown date"}`,
    `Name: ${row.name || "(blank)"}`,
    `Email: ${row.email}`,
    `Level: ${row.player_level || "(blank)"}`,
    `Interests: ${interests}`,
    `Message: ${message}${review}`
  ].join("\n");
}

function truncateDigest(body) {
  if (body.length <= MAX_DIGEST_LENGTH) {
    return body;
  }

  return `${body.slice(0, MAX_DIGEST_LENGTH - 80).trimEnd()}\n\n[Digest truncated. View D1 for full messages.]`;
}

function buildDigestBody(classifiedRows, now = new Date()) {
  const groups = groupIncludedSubmissions(classifiedRows);
  const includedCount = groups.reduce((total, group) => total + group.submissions.length, 0);
  const skippedCount = classifiedRows.filter((row) => !row.include).length;
  const reviewCount = classifiedRows.filter((row) => row.include && row.status === "review").length;

  if (includedCount === 0) {
    return {
      title: "The Turnaround interest list",
      message: `No new real interest-list submissions for the weekly digest.\nChecked: ${now.toISOString()}`,
      includedCount,
      skippedCount,
      reviewCount
    };
  }

  const sections = groups.map((group) => {
    const heading = group.submissions.length > 1
      ? `${group.email} (${group.submissions.length} submissions)`
      : group.email;
    const entries = group.submissions.map((row, index) => formatSubmission(row, index, group.submissions.length));
    return [`Email group: ${heading}`, ...entries].join("\n");
  });

  const message = [
    `Weekly interest-list digest for The Turnaround`,
    `Included: ${includedCount}`,
    `Needs review: ${reviewCount}`,
    `Skipped as test/spam: ${skippedCount}`,
    "",
    sections.join("\n\n---\n\n")
  ].join("\n");

  return {
    title: `The Turnaround: ${includedCount} new interest ${includedCount === 1 ? "submission" : "submissions"}`,
    message: truncateDigest(message),
    includedCount,
    skippedCount,
    reviewCount
  };
}

function getDatabase(env) {
  if (!env?.STEEL_RAG_INTEREST_D1?.prepare) {
    throw new Error("Missing STEEL_RAG_INTEREST_D1 binding.");
  }
  return env.STEEL_RAG_INTEREST_D1;
}

async function fetchCandidateRows(db, now = new Date(), lookbackDays = DEFAULT_LOOKBACK_DAYS) {
  const cutoff = new Date(now.getTime() - lookbackDays * 24 * 60 * 60 * 1000).toISOString();
  const result = await db
    .prepare(
      `select id, created_at, name, email, player_level, interests, message,
              coalesce(status, 'new') as status,
              coalesce(spam_score, 0) as spam_score,
              admin_notes, notified_at, coalesce(source, 'landing_page') as source
         from interest_submissions
        where (created_at >= ? or notified_at is null)
          and lower(coalesce(status, 'new')) in ('new', 'review')
        order by created_at asc`
    )
    .bind(cutoff)
    .all();

  return result?.results || [];
}

async function applyModerationUpdates(db, classifiedRows) {
  for (const row of classifiedRows) {
    if (!row.id || row.review_reasons.length === 0) {
      continue;
    }

    await db
      .prepare(
        `update interest_submissions
            set status = ?,
                spam_score = ?,
                admin_notes = ?
          where id = ?`
      )
      .bind(row.status, row.spam_score, row.admin_notes, row.id)
      .run();
  }
}

async function markRowsNotified(db, classifiedRows, notifiedAt) {
  for (const row of classifiedRows) {
    if (!row.include || !row.id) {
      continue;
    }

    await db
      .prepare(
        `update interest_submissions
            set notified_at = ?,
                status = case
                  when lower(coalesce(status, 'new')) = 'review' then status
                  else 'notified'
                end
          where id = ?`
      )
      .bind(notifiedAt, row.id)
      .run();
  }
}

async function sendPushoverDigest(env, digest, fetchImpl = fetch) {
  const token = cleanString(env?.PUSHOVER_APP_TOKEN, 200);
  const user = cleanString(env?.PUSHOVER_USER_KEY, 200);
  if (!token || !user) {
    throw new Error("Missing Pushover credentials.");
  }

  const body = new URLSearchParams({
    token,
    user,
    title: digest.title,
    message: digest.message
  });

  const response = await fetchImpl(PUSHOVER_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body
  });

  if (!response.ok) {
    throw new Error(`Pushover send failed with status ${response.status}.`);
  }
}

async function runInterestDigest({ env, now = new Date(), dryRun = false, fetchImpl = fetch }) {
  const db = getDatabase(env);
  const rows = await fetchCandidateRows(db, now);
  const classifiedRows = classifySubmissions(rows);
  const digest = buildDigestBody(classifiedRows, now);
  const includedRows = classifiedRows.filter((row) => row.include);

  if (dryRun) {
    return {
      ok: true,
      dryRun: true,
      sent: false,
      ...digest,
      rows: classifiedRows.map((row) => ({
        id: row.id,
        email: row.email,
        status: row.status,
        spam_score: row.spam_score,
        include: row.include,
        review_reasons: row.review_reasons
      }))
    };
  }

  await applyModerationUpdates(db, classifiedRows);

  if (includedRows.length === 0) {
    return { ok: true, dryRun: false, sent: false, ...digest };
  }

  await sendPushoverDigest(env, digest, fetchImpl);
  await markRowsNotified(db, includedRows, now.toISOString());

  return { ok: true, dryRun: false, sent: true, ...digest };
}

async function sha256Hex(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function tokenMatches(provided, expected) {
  const providedText = cleanString(provided, 500);
  const expectedText = cleanString(expected, 500);
  if (!providedText || !expectedText) {
    return false;
  }

  const [providedHash, expectedHash] = await Promise.all([sha256Hex(providedText), sha256Hex(expectedText)]);
  let difference = providedHash.length ^ expectedHash.length;
  for (let index = 0; index < Math.max(providedHash.length, expectedHash.length); index += 1) {
    difference |= providedHash.charCodeAt(index) ^ expectedHash.charCodeAt(index);
  }
  return difference === 0;
}

async function handleDryRunRequest(request, env) {
  const configuredToken = cleanString(env?.INTEREST_DIGEST_ADMIN_TOKEN, 500);
  if (!configuredToken) {
    return jsonResponse({ ok: false, error: "dry_run_disabled" }, 403);
  }

  const header = request.headers.get("authorization") || "";
  const bearer = header.toLowerCase().startsWith("bearer ") ? header.slice(7) : "";
  const token = bearer || request.headers.get("x-interest-digest-token") || "";

  if (!(await tokenMatches(token, configuredToken))) {
    return jsonResponse({ ok: false, error: "forbidden" }, 403);
  }

  const result = await runInterestDigest({ env, dryRun: true });
  return jsonResponse(result);
}

export default {
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(runInterestDigest({ env }));
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/dry-run" || url.searchParams.get("dry_run") === "1") {
      return handleDryRunRequest(request, env);
    }

    return jsonResponse({ ok: false, error: "not_found" }, 404);
  }
};

export const __test = {
  buildDigestBody,
  classifySubmission,
  classifySubmissions,
  countUrlSignals,
  fetchCandidateRows,
  groupIncludedSubmissions,
  handleDryRunRequest,
  isObviousTestEmail,
  markRowsNotified,
  runInterestDigest,
  sendPushoverDigest
};
