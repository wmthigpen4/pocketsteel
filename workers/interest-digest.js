const MAX_PUSHOVER_MESSAGE_LENGTH = 950;
const PUSHOVER_ENDPOINT = "https://api.pushover.net/1/messages.json";
const OBVIOUS_TEST_EMAILS = new Set([
  "test@example.com",
  "ops-smoke@example.com",
  "smoke-test@example.com",
  "example@example.com"
]);
const OBVIOUS_SPAM_RULES = [
  {
    reason: "SEO/search-marketing solicitation",
    pattern: /\b(?:seo|search engine optimization|backlinks?|googlesearchindex|searchregister|google maps rankings?|organic traffic|online visibility)\b/i
  },
  {
    reason: "social-media growth solicitation",
    pattern: /\b(?:instagram presence|instagram followers|targeted instagram followers)\b/i
  },
  {
    reason: "video-production solicitation",
    pattern: /\b(?:our videos cost|30 second video|60 second video)\b/i
  },
  {
    reason: "AI/lead-generation solicitation",
    pattern: /\b(?:ai automation systems?|competitor clients?|lead generation|discovery call)\b/i
  },
  {
    reason: "contact-form outreach solicitation",
    pattern: /\b(?:website contact pages?|platform supports outreach)\b/i
  },
  {
    reason: "website-services solicitation",
    pattern: /\b(?:website audit|proposal and pricing|send (?:you )?(?:a )?(?:quote|price list|pricing|proposal|audit report|screenshot))\b/i
  }
];

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

function obviousSpamReason(submission) {
  const content = `${submission.name}\n${submission.message}`;
  for (const rule of OBVIOUS_SPAM_RULES) {
    if (rule.pattern.test(content)) {
      return rule.reason;
    }
  }

  if (
    /^[a-z]{8,}$/i.test(submission.name) &&
    /^[a-z]{24,}$/i.test(submission.message)
  ) {
    return "gibberish-only submission";
  }

  return "";
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

  if (status === "spam" || status === "test") {
    include = false;
    reasons.push(`existing ${status} status`);
  } else if (isObviousTestEmail(submission.email)) {
    include = false;
    status = "spam";
    spamScore = Math.max(spamScore, 100);
    reasons.push("obvious test email");
  } else {
    const spamReason = obviousSpamReason(submission);
    if (spamReason) {
      include = false;
      status = "spam";
      spamScore = Math.max(spamScore, 100);
      reasons.push(spamReason);
    }
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

function findReadableSplit(characters, maxLength) {
  const minimumReadableSplit = Math.floor(maxLength * 0.6);

  for (let index = maxLength; index >= minimumReadableSplit; index -= 1) {
    if (characters[index - 2] === "\n" && characters[index - 1] === "\n") {
      return index;
    }
  }

  for (let index = maxLength; index >= minimumReadableSplit; index -= 1) {
    if (characters[index - 1] === "\n") {
      return index;
    }
  }

  for (let index = maxLength; index >= minimumReadableSplit; index -= 1) {
    if (/\s/u.test(characters[index - 1])) {
      return index;
    }
  }

  return maxLength;
}

function splitDigestMessage(body, maxLength = MAX_PUSHOVER_MESSAGE_LENGTH) {
  if (!Number.isInteger(maxLength) || maxLength < 1) {
    throw new Error("Pushover message length must be a positive integer.");
  }

  const remaining = Array.from(String(body || ""));
  const messages = [];

  while (remaining.length > maxLength) {
    const splitAt = findReadableSplit(remaining, maxLength);
    messages.push(remaining.splice(0, splitAt).join(""));
  }

  if (remaining.length > 0 || messages.length === 0) {
    messages.push(remaining.join(""));
  }

  return messages;
}

function buildDigestBody(classifiedRows, now = new Date()) {
  const groups = groupIncludedSubmissions(classifiedRows);
  const includedCount = groups.reduce((total, group) => total + group.submissions.length, 0);
  const skippedCount = classifiedRows.filter((row) => !row.include).length;
  const reviewCount = classifiedRows.filter((row) => row.include && row.status === "review").length;

  if (includedCount === 0) {
    const message = [
      "No new real interest-list submissions for the weekly digest.",
      `Filtered as spam/test: ${skippedCount}`,
      `Checked: ${now.toISOString()}`
    ].join("\n");
    return {
      title: "Steel Guitar RAG interest list",
      message,
      messages: splitDigestMessage(message),
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
    `Weekly interest-list digest for Steel Guitar RAG`,
    `Included: ${includedCount}`,
    `Needs review: ${reviewCount}`,
    `Filtered as spam/test: ${skippedCount}`,
    "",
    sections.join("\n\n---\n\n")
  ].join("\n");

  return {
    title: `Steel Guitar RAG: ${includedCount} new interest ${includedCount === 1 ? "submission" : "submissions"}`,
    message,
    messages: splitDigestMessage(message),
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

async function fetchCandidateRows(db) {
  const result = await db
    .prepare(
      `select id, created_at, name, email, player_level, interests, message,
              coalesce(status, 'new') as status,
              coalesce(spam_score, 0) as spam_score,
              admin_notes, notified_at, coalesce(source, 'landing_page') as source
         from interest_submissions
        where notified_at is null
          and lower(coalesce(status, 'new')) in ('new', 'review', 'spam', 'test')
        order by created_at asc`
    )
    .bind()
    .all();

  return result?.results || [];
}

async function applyModerationUpdates(db, classifiedRows) {
  for (const row of classifiedRows) {
    if (!row.include || !row.id || row.review_reasons.length === 0) {
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

async function deleteSpamAndTestRows(db, classifiedRows) {
  let deletedCount = 0;
  for (const row of classifiedRows) {
    if (row.include || !row.id || !["spam", "test"].includes(row.status)) {
      continue;
    }

    const result = await db
      .prepare(
        `delete from interest_submissions
          where id = ?
            and notified_at is null`
      )
      .bind(row.id)
      .run();
    deletedCount += Number(result?.meta?.changes || 0);
  }

  return deletedCount;
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

  const messages = Array.isArray(digest.messages) && digest.messages.length
    ? digest.messages
    : splitDigestMessage(digest.message);

  for (const [index, message] of messages.entries()) {
    const title = messages.length > 1
      ? `${digest.title} (${index + 1}/${messages.length})`
      : digest.title;
    const body = new URLSearchParams({ token, user, title, message });
    const response = await fetchImpl(PUSHOVER_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body
    });

    if (!response.ok) {
      throw new Error(`Pushover send failed for part ${index + 1}/${messages.length} with status ${response.status}.`);
    }
  }

  return messages.length;
}

async function runInterestDigest({ env, now = new Date(), dryRun = false, fetchImpl = fetch }) {
  const db = getDatabase(env);
  const rows = await fetchCandidateRows(db, now);
  const classifiedRows = classifySubmissions(rows);
  const digest = buildDigestBody(classifiedRows, now);
  const includedRows = classifiedRows.filter((row) => row.include);
  const wouldDeleteCount = classifiedRows.filter(
    (row) => !row.include && ["spam", "test"].includes(row.status)
  ).length;

  if (dryRun) {
    return {
      ok: true,
      dryRun: true,
      sent: false,
      deletedSpamCount: 0,
      wouldDeleteCount,
      ...digest,
      rows: classifiedRows.map((row) => ({
        id: row.id,
        email: row.email,
        name: row.name,
        player_level: row.player_level,
        interests: row.interests,
        status: row.status,
        spam_score: row.spam_score,
        include: row.include,
        would_delete: !row.include && ["spam", "test"].includes(row.status),
        review_reasons: row.review_reasons
      }))
    };
  }

  const deletedSpamCount = await deleteSpamAndTestRows(db, classifiedRows);
  await applyModerationUpdates(db, classifiedRows);

  const sentMessageCount = await sendPushoverDigest(env, digest, fetchImpl);
  await markRowsNotified(db, includedRows, now.toISOString());

  return {
    ok: true,
    dryRun: false,
    sent: true,
    sentMessageCount,
    deletedSpamCount,
    ...digest
  };
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

async function requestHasAdminToken(request, env) {
  const configuredToken = cleanString(env?.INTEREST_DIGEST_ADMIN_TOKEN, 500);
  if (!configuredToken) {
    return false;
  }

  const header = request.headers.get("authorization") || "";
  const bearer = header.toLowerCase().startsWith("bearer ") ? header.slice(7) : "";
  const token = bearer || request.headers.get("x-interest-digest-token") || "";

  return tokenMatches(token, configuredToken);
}

async function requireAdminToken(request, env) {
  if (!(await requestHasAdminToken(request, env))) {
    return jsonResponse({ ok: false, error: "forbidden" }, 403);
  }

  return null;
}

async function handleDryRunRequest(request, env) {
  if (request.method !== "GET") {
    return jsonResponse({ ok: false, error: "Method not allowed." }, 405);
  }

  const forbidden = await requireAdminToken(request, env);
  if (forbidden) {
    return forbidden;
  }

  try {
    const result = await runInterestDigest({ env, dryRun: true });
    return jsonResponse(result);
  } catch (_error) {
    return jsonResponse({ ok: false, error: "dry_run_failed" }, 500);
  }
}

async function handleManualRunRequest(request, env) {
  if (request.method !== "POST") {
    return jsonResponse({ ok: false, error: "Method not allowed." }, 405);
  }

  const forbidden = await requireAdminToken(request, env);
  if (forbidden) {
    return forbidden;
  }

  try {
    const result = await runInterestDigest({ env, dryRun: false });
    return jsonResponse(result);
  } catch (_error) {
    return jsonResponse({ ok: false, error: "run_failed" }, 500);
  }
}

export default {
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(runInterestDigest({ env }));
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/dry-run") {
      return handleDryRunRequest(request, env);
    }
    if (url.pathname === "/run") {
      return handleManualRunRequest(request, env);
    }

    return jsonResponse({ ok: false, error: "not_found" }, 404);
  }
};

export const __test = {
  buildDigestBody,
  classifySubmission,
  classifySubmissions,
  countUrlSignals,
  deleteSpamAndTestRows,
  fetchCandidateRows,
  groupIncludedSubmissions,
  handleDryRunRequest,
  handleManualRunRequest,
  isObviousTestEmail,
  markRowsNotified,
  obviousSpamReason,
  requestHasAdminToken,
  runInterestDigest,
  sendPushoverDigest,
  splitDigestMessage
};
