const MAX_PUSHOVER_MESSAGE_LENGTH = 950;
const PUSHOVER_ENDPOINT = "https://api.pushover.net/1/messages.json";
const DELIVERY_LEASE_MS = 10 * 60 * 1000;
const ACCESS_JWKS_TTL_MS = 5 * 60 * 1000;
const MAX_ACCESS_JWKS_CACHE_ENTRIES = 4;
const MAX_ACCESS_JWKS_KEYS = 10;
const accessJwksCache = new Map();
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

function logEvent(level, event, fields = {}) {
  const entry = JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    event,
    ...fields
  });
  const logger = level === "error" ? console.error : level === "warn" ? console.warn : console.log;
  logger(entry);
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

function weeklyDigestWindow(now) {
  const current = new Date(now);
  const daysSinceMonday = (current.getUTCDay() + 6) % 7;
  const start = new Date(Date.UTC(
    current.getUTCFullYear(),
    current.getUTCMonth(),
    current.getUTCDate() - daysSinceMonday
  ));
  const end = new Date(start.getTime() + (7 * 24 * 60 * 60 * 1000));
  return { start: start.toISOString(), end: end.toISOString() };
}

function statementChanges(result) {
  return Number(result?.meta?.changes || 0);
}

async function queryFirst(statement) {
  const result = await statement.all();
  return result?.results?.[0] || null;
}

async function fetchDeliveryState(db, deliveryId) {
  const delivery = await queryFirst(
    db.prepare(
      `select id, window_start, window_end, content_hash, title,
              included_row_ids_json, status, claim_token, claimed_at,
              lease_expires_at, completed_at, last_error
         from interest_digest_deliveries
        where id = ?`
    ).bind(deliveryId)
  );
  if (!delivery) {
    return null;
  }
  const partsResult = await db.prepare(
    `select delivery_id, part_index, part_count, content_hash, title, message,
            status, attempts, attempt_started_at, sent_at, last_error
       from interest_digest_delivery_parts
      where delivery_id = ?
      order by part_index asc`
  ).bind(deliveryId).all();
  return { delivery, parts: partsResult?.results || [] };
}

async function fetchOldestUnfinishedDeliveryId(db) {
  const row = await queryFirst(
    db.prepare(
      `select id
         from interest_digest_deliveries
        where status != 'sent'
        order by window_start asc
        limit 1`
    ).bind()
  );
  return cleanString(row?.id, 200);
}

async function claimDigestDelivery(db, digest, classifiedRows, now) {
  const window = weeklyDigestWindow(now);
  const unfinishedDeliveryId = await fetchOldestUnfinishedDeliveryId(db);
  const deliveryId = unfinishedDeliveryId || `interest-digest:${window.start}`;
  const claimToken = crypto.randomUUID();
  const nowIso = now.toISOString();
  const leaseExpiresAt = new Date(now.getTime() + DELIVERY_LEASE_MS).toISOString();
  const includedRowIds = classifiedRows.filter((row) => row.include && row.id).map((row) => row.id);
  const messages = Array.isArray(digest.messages) && digest.messages.length
    ? digest.messages
    : splitDigestMessage(digest.message);
  const contentHash = await sha256Hex(JSON.stringify({
    title: digest.title,
    messages,
    includedRowIds
  }));
  const parts = await Promise.all(messages.map(async (message, partIndex) => {
    const title = messages.length > 1
      ? `${digest.title} (${partIndex + 1}/${messages.length})`
      : digest.title;
    return {
      partIndex,
      partCount: messages.length,
      title,
      message,
      contentHash: await sha256Hex(`${title}\n${message}`)
    };
  }));

  const statements = [];
  if (!unfinishedDeliveryId) {
    statements.push(db.prepare(
      `insert into interest_digest_deliveries
        (id, window_start, window_end, content_hash, title, included_row_ids_json,
         status, created_at, updated_at)
       values (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
       on conflict(window_start, window_end) do nothing`
    ).bind(
      deliveryId,
      window.start,
      window.end,
      contentHash,
      digest.title,
      JSON.stringify(includedRowIds),
      nowIso,
      nowIso
    ));
    statements.push(...parts.map((part) => db.prepare(
      `insert into interest_digest_delivery_parts
        (delivery_id, part_index, part_count, content_hash, title, message,
         status, created_at, updated_at)
       values (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
       on conflict(delivery_id, part_index) do nothing`
    ).bind(
      deliveryId,
      part.partIndex,
      part.partCount,
      part.contentHash,
      part.title,
      part.message,
      nowIso,
      nowIso
    )));
  }
  statements.push(db.prepare(
      `update interest_digest_deliveries
          set status = 'sending',
              claim_token = ?,
              claimed_at = ?,
              lease_expires_at = ?,
              last_error = null,
              updated_at = ?
        where id = ?
          and status != 'sent'
          and (claim_token is null or lease_expires_at is null or lease_expires_at <= ?)
          and not exists (
            select 1
              from interest_digest_delivery_parts
             where delivery_id = ?
               and status in ('sending', 'ambiguous')
          )`
    ).bind(
      claimToken,
      nowIso,
      leaseExpiresAt,
      nowIso,
      deliveryId,
      nowIso,
      deliveryId
    ));
  const results = await db.batch(statements);
  const acquired = statementChanges(results[results.length - 1]) === 1;
  const state = await fetchDeliveryState(db, deliveryId);
  return { acquired, claimToken, deliveryId, state, contentHash, window };
}

async function applyModerationBatch(db, classifiedRows) {
  const operations = [];
  const operationKinds = [];
  for (const row of classifiedRows) {
    if (!row.id) {
      continue;
    }
    if (!row.include && ["spam", "test"].includes(row.status)) {
      operations.push(db.prepare(
        `delete from interest_submissions
          where id = ?
            and notified_at is null`
      ).bind(row.id));
      operationKinds.push("delete");
    } else if (row.include && row.review_reasons.length > 0) {
      operations.push(db.prepare(
        `update interest_submissions
            set status = ?, spam_score = ?, admin_notes = ?
          where id = ?`
      ).bind(row.status, row.spam_score, row.admin_notes, row.id));
      operationKinds.push("moderate");
    }
  }
  if (operations.length === 0) {
    return { deletedSpamCount: 0, moderatedCount: 0 };
  }
  const results = await db.batch(operations);
  return results.reduce((counts, result, index) => {
    const changes = statementChanges(result);
    if (operationKinds[index] === "delete") {
      counts.deletedSpamCount += changes;
    } else {
      counts.moderatedCount += changes;
    }
    return counts;
  }, { deletedSpamCount: 0, moderatedCount: 0 });
}

async function sendPushoverPart(env, part, fetchImpl = fetch) {
  const token = cleanString(env?.PUSHOVER_APP_TOKEN, 200);
  const user = cleanString(env?.PUSHOVER_USER_KEY, 200);
  if (!token || !user) {
    throw new Error("Missing Pushover credentials.");
  }
  let response;
  try {
    response = await fetchImpl(PUSHOVER_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ token, user, title: part.title, message: part.message })
    });
  } catch (error) {
    const ambiguousError = error instanceof Error ? error : new Error("Pushover delivery outcome is unknown.");
    ambiguousError.deliveryAmbiguous = true;
    throw ambiguousError;
  }
  if (!response.ok) {
    const error = new Error(
      `Pushover send failed for part ${Number(part.part_index) + 1}/${part.part_count} with status ${response.status}.`
    );
    error.deliveryAmbiguous = false;
    throw error;
  }
}

async function recordPartAttempt(db, deliveryId, claimToken, partIndex, nowIso) {
  const results = await db.batch([
    db.prepare(
      `update interest_digest_delivery_parts
          set status = 'sending', attempts = attempts + 1,
              attempt_started_at = ?, last_error = null, updated_at = ?
        where delivery_id = ? and part_index = ?
          and status in ('pending', 'failed')
          and exists (
            select 1 from interest_digest_deliveries
             where id = ? and claim_token = ? and status = 'sending'
          )`
    ).bind(nowIso, nowIso, deliveryId, partIndex, deliveryId, claimToken),
    db.prepare(
      `update interest_digest_deliveries set updated_at = ?
        where id = ? and claim_token = ? and status = 'sending'`
    ).bind(nowIso, deliveryId, claimToken)
  ]);
  if (statementChanges(results[0]) !== 1) {
    throw new Error("digest_part_claim_lost");
  }
}

async function recordPartSuccess(db, deliveryId, claimToken, partIndex, nowIso) {
  const results = await db.batch([
    db.prepare(
      `update interest_digest_delivery_parts
          set status = 'sent', sent_at = ?, last_error = null, updated_at = ?
        where delivery_id = ? and part_index = ? and status = 'sending'`
    ).bind(nowIso, nowIso, deliveryId, partIndex),
    db.prepare(
      `update interest_digest_deliveries set updated_at = ?
        where id = ? and claim_token = ? and status = 'sending'`
    ).bind(nowIso, deliveryId, claimToken)
  ]);
  if (statementChanges(results[0]) !== 1) {
    throw new Error("digest_part_success_not_recorded");
  }
}

async function recordPartFailure(db, deliveryId, claimToken, partIndex, error, nowIso) {
  const status = error?.deliveryAmbiguous ? "ambiguous" : "failed";
  const safeError = cleanString(error?.message || "delivery_failed", 500);
  await db.batch([
    db.prepare(
      `update interest_digest_delivery_parts
          set status = ?, last_error = ?, updated_at = ?
        where delivery_id = ? and part_index = ? and status = 'sending'`
    ).bind(status, safeError, nowIso, deliveryId, partIndex),
    db.prepare(
      `update interest_digest_deliveries
          set status = ?, claim_token = null, lease_expires_at = null,
              last_error = ?, updated_at = ?
        where id = ? and claim_token = ?`
    ).bind(status, safeError, nowIso, deliveryId, claimToken)
  ]);
}

function parseStoredRowIds(value) {
  try {
    const parsed = JSON.parse(String(value || "[]"));
    return Array.isArray(parsed) ? parsed.map((item) => cleanString(item, 120)).filter(Boolean) : [];
  } catch (_error) {
    return [];
  }
}

async function completeDigestDelivery(db, deliveryState, claimToken, completedAt) {
  const deliveryId = deliveryState.delivery.id;
  const includedRowIds = parseStoredRowIds(deliveryState.delivery.included_row_ids_json);
  const completionGuard = `exists (
    select 1 from interest_digest_deliveries d
     where d.id = ? and d.claim_token = ? and d.status = 'sending'
       and not exists (
         select 1 from interest_digest_delivery_parts p
          where p.delivery_id = d.id and p.status != 'sent'
       )
  )`;
  const statements = includedRowIds.map((rowId) => db.prepare(
    `update interest_submissions
        set notified_at = ?,
            status = case when lower(coalesce(status, 'new')) = 'review' then status else 'notified' end
      where id = ? and ${completionGuard}`
  ).bind(completedAt, rowId, deliveryId, claimToken));
  statements.push(db.prepare(
    `update interest_digest_deliveries
        set status = 'sent', claim_token = null, lease_expires_at = null,
            completed_at = ?, last_error = null, updated_at = ?
      where id = ? and claim_token = ? and status = 'sending'
        and not exists (
          select 1 from interest_digest_delivery_parts
           where delivery_id = ? and status != 'sent'
        )`
  ).bind(completedAt, completedAt, deliveryId, claimToken, deliveryId));
  const results = await db.batch(statements);
  if (statementChanges(results[results.length - 1]) !== 1) {
    throw new Error("digest_completion_guard_failed");
  }
}

async function runDurableInterestDigest({ env, now, dryRun, fetchImpl }) {
  const db = getDatabase(env);
  const rows = await fetchCandidateRows(db, now);
  const classifiedRows = classifySubmissions(rows);
  const digest = buildDigestBody(classifiedRows, now);
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

  const claim = await claimDigestDelivery(db, digest, classifiedRows, now);
  if (!claim.acquired) {
    const deliveryStatus = cleanString(claim.state?.delivery?.status || "unavailable", 40);
    logEvent("warn", "interest_digest_duplicate_prevented", {
      deliveryId: claim.deliveryId,
      deliveryStatus
    });
    return {
      ok: true,
      dryRun: false,
      sent: false,
      duplicatePrevented: true,
      deliveryStatus,
      sentMessageCount: 0,
      deletedSpamCount: 0,
      ...digest
    };
  }

  const moderation = await applyModerationBatch(db, classifiedRows);
  let sentMessageCount = 0;
  const pendingParts = claim.state.parts.filter((part) => ["pending", "failed"].includes(part.status));
  for (const part of pendingParts) {
    const attemptAt = new Date().toISOString();
    await recordPartAttempt(db, claim.deliveryId, claim.claimToken, part.part_index, attemptAt);
    try {
      await sendPushoverPart(env, part, fetchImpl);
      await recordPartSuccess(db, claim.deliveryId, claim.claimToken, part.part_index, new Date().toISOString());
      sentMessageCount += 1;
    } catch (error) {
      await recordPartFailure(
        db,
        claim.deliveryId,
        claim.claimToken,
        part.part_index,
        error,
        new Date().toISOString()
      );
      throw error;
    }
  }

  const refreshedState = await fetchDeliveryState(db, claim.deliveryId);
  await completeDigestDelivery(db, refreshedState, claim.claimToken, new Date().toISOString());
  logEvent("info", "interest_digest_delivery_completed", {
    deliveryId: claim.deliveryId,
    sentMessageCount,
    totalParts: refreshedState.parts.length,
    includedCount: digest.includedCount,
    deletedSpamCount: moderation.deletedSpamCount
  });
  return {
    ok: true,
    dryRun: false,
    sent: true,
    deliveryId: claim.deliveryId,
    deliveryStatus: "sent",
    sentMessageCount,
    totalMessageCount: refreshedState.parts.length,
    deletedSpamCount: moderation.deletedSpamCount,
    ...digest
  };
}

async function runLegacyInterestDigest({ env, now = new Date(), dryRun = false, fetchImpl = fetch }) {
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

async function runInterestDigest({ env, now = new Date(), dryRun = false, fetchImpl = fetch }) {
  const db = getDatabase(env);
  if (typeof db.batch !== "function") {
    return runLegacyInterestDigest({ env, now, dryRun, fetchImpl });
  }
  return runDurableInterestDigest({ env, now, dryRun, fetchImpl });
}

async function sha256Hex(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function decodeBase64Url(value) {
  const normalized = String(value || "").replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
  const binary = atob(padded);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

function parseJwt(token) {
  const segments = String(token || "").split(".");
  if (segments.length !== 3 || segments.some((segment) => !segment)) {
    throw new Error("invalid_access_jwt");
  }

  const decodeJson = (segment) => JSON.parse(new TextDecoder().decode(decodeBase64Url(segment)));
  return {
    header: decodeJson(segments[0]),
    claims: decodeJson(segments[1]),
    signingInput: new TextEncoder().encode(`${segments[0]}.${segments[1]}`),
    signature: decodeBase64Url(segments[2])
  };
}

function normalizeIssuer(value) {
  return cleanString(value, 500).replace(/\/+$/, "");
}

function configuredAccess(env) {
  const issuer = normalizeIssuer(env?.INTEREST_DIGEST_ACCESS_ISSUER);
  const audience = cleanString(env?.INTEREST_DIGEST_ACCESS_AUD, 500);
  const jwksUrl = cleanString(
    env?.INTEREST_DIGEST_ACCESS_JWKS_URL || (issuer ? `${issuer}/cdn-cgi/access/certs` : ""),
    1000
  );
  return issuer && audience && jwksUrl ? { issuer, audience, jwksUrl } : null;
}

function pruneAccessJwksCache() {
  while (accessJwksCache.size > MAX_ACCESS_JWKS_CACHE_ENTRIES) {
    accessJwksCache.delete(accessJwksCache.keys().next().value);
  }
}

async function fetchAccessJwks(jwksUrl, fetchImpl = fetch, forceRefresh = false) {
  const now = Date.now();
  const cached = accessJwksCache.get(jwksUrl);
  if (!forceRefresh && cached && cached.expiresAt > now) {
    return cached.keys;
  }

  const response = await fetchImpl(jwksUrl, {
    headers: { Accept: "application/json" },
    cf: { cacheTtl: 300, cacheEverything: true }
  });
  if (!response.ok) {
    throw new Error("access_jwks_unavailable");
  }
  const payload = await response.json();
  const keys = Array.isArray(payload?.keys)
    ? payload.keys
      .filter((key) => key?.kty === "RSA" && key?.kid)
      .slice(0, MAX_ACCESS_JWKS_KEYS)
    : [];
  if (keys.length === 0) {
    throw new Error("access_jwks_empty");
  }

  accessJwksCache.delete(jwksUrl);
  accessJwksCache.set(jwksUrl, { expiresAt: now + ACCESS_JWKS_TTL_MS, keys });
  pruneAccessJwksCache();
  return keys;
}

async function verifyJwtSignature(parsed, jwk) {
  const key = await crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["verify"]
  );
  return crypto.subtle.verify(
    { name: "RSASSA-PKCS1-v1_5" },
    key,
    parsed.signature,
    parsed.signingInput
  );
}

function validateAccessClaims(claims, config, nowSeconds = Math.floor(Date.now() / 1000)) {
  const audiences = Array.isArray(claims?.aud) ? claims.aud : [claims?.aud];
  return Boolean(
    claims &&
    normalizeIssuer(claims.iss) === config.issuer &&
    audiences.includes(config.audience) &&
    Number.isFinite(Number(claims.exp)) &&
    Number(claims.exp) > nowSeconds &&
    (!claims.nbf || Number(claims.nbf) <= nowSeconds)
  );
}

async function verifyAccessJwt(token, env, fetchImpl = fetch) {
  const config = configuredAccess(env);
  if (!config) {
    return false;
  }

  let parsed;
  try {
    parsed = parseJwt(token);
  } catch (_error) {
    return false;
  }
  if (parsed.header?.alg !== "RS256" || !parsed.header?.kid || !validateAccessClaims(parsed.claims, config)) {
    return false;
  }

  for (const forceRefresh of [false, true]) {
    try {
      const keys = await fetchAccessJwks(config.jwksUrl, fetchImpl, forceRefresh);
      const jwk = keys.find((candidate) => candidate.kid === parsed.header.kid);
      if (jwk && await verifyJwtSignature(parsed, jwk)) {
        return true;
      }
    } catch (_error) {
      if (forceRefresh) {
        return false;
      }
    }
  }
  return false;
}

function isLocalDevelopmentRequest(request) {
  const hostname = new URL(request.url).hostname.toLowerCase();
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
}

async function requestHasAccessIdentity(request, env, fetchImpl = fetch) {
  if (env?.INTEREST_DIGEST_LOCAL_ACCESS_BYPASS === "1" && isLocalDevelopmentRequest(request)) {
    return true;
  }
  const token = cleanString(request.headers.get("cf-access-jwt-assertion"), 12000);
  return token ? verifyAccessJwt(token, env, fetchImpl) : false;
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

async function requireAdminAuthorization(request, env) {
  const [hasAccessIdentity, hasAdminToken] = await Promise.all([
    requestHasAccessIdentity(request, env),
    requestHasAdminToken(request, env)
  ]);
  if (!hasAccessIdentity || !hasAdminToken) {
    return jsonResponse({ ok: false, error: "forbidden" }, 403);
  }

  return null;
}

async function handleDryRunRequest(request, env) {
  if (request.method !== "GET") {
    return jsonResponse({ ok: false, error: "Method not allowed." }, 405);
  }

  const forbidden = await requireAdminAuthorization(request, env);
  if (forbidden) {
    return forbidden;
  }

  try {
    const result = await runInterestDigest({ env, dryRun: true });
    return jsonResponse(result);
  } catch (error) {
    logEvent("error", "interest_digest_dry_run_failed", {
      error: cleanString(error?.message || "dry_run_failed", 200)
    });
    return jsonResponse({ ok: false, error: "dry_run_failed" }, 500);
  }
}

async function handleManualRunRequest(request, env) {
  if (request.method !== "POST") {
    return jsonResponse({ ok: false, error: "Method not allowed." }, 405);
  }

  const forbidden = await requireAdminAuthorization(request, env);
  if (forbidden) {
    return forbidden;
  }

  try {
    const result = await runInterestDigest({ env, dryRun: false });
    return jsonResponse(result);
  } catch (error) {
    logEvent("error", "interest_digest_manual_run_failed", {
      error: cleanString(error?.message || "run_failed", 200)
    });
    return jsonResponse({ ok: false, error: "run_failed" }, 500);
  }
}

export default {
  async scheduled(controller, env, ctx) {
    const run = runInterestDigest({ env }).catch((error) => {
      logEvent("error", "interest_digest_scheduled_run_failed", {
        cron: cleanString(controller?.cron, 80),
        error: cleanString(error?.message || "scheduled_run_failed", 200)
      });
      throw error;
    });
    ctx.waitUntil(run);
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
  requestHasAccessIdentity,
  requestHasAdminToken,
  runDurableInterestDigest,
  runInterestDigest,
  sendPushoverDigest,
  splitDigestMessage,
  validateAccessClaims,
  verifyAccessJwt,
  weeklyDigestWindow
};
