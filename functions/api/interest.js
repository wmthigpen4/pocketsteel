const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_FIELD_LENGTH = 2000;
const SOURCE = "landing_page";
const SUSPICIOUS_MESSAGE_LENGTH = 1500;

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store"
    }
  });
}

function cleanString(value, maxLength = MAX_FIELD_LENGTH) {
  return String(value || "").trim().slice(0, maxLength);
}

function cleanInterestList(value) {
  const raw = Array.isArray(value) ? value : [];
  return raw
    .map((item) => cleanString(item, 80))
    .filter(Boolean)
    .slice(0, 12);
}

function countUrlSignals(text) {
  const matches = cleanString(text, 3000).match(/\b(?:https?:\/\/|www\.|[a-z0-9-]+\.[a-z]{2,})(?:[^\s]*)/gi);
  return matches ? matches.length : 0;
}

function emailDomain(email) {
  return cleanString(email, 320).split("@").pop() || "";
}

function statusRank(status) {
  return { new: 0, review: 1, test: 2, spam: 3 }[status] ?? 0;
}

function applyStatus(currentStatus, nextStatus) {
  return statusRank(nextStatus) > statusRank(currentStatus) ? nextStatus : currentStatus;
}

function classifySubmission(submission) {
  const domain = emailDomain(submission.email);
  const notes = [];
  let status = "new";
  let spamScore = 0;

  if (submission.email === "test@example.com") {
    status = "test";
    spamScore = Math.max(spamScore, 100);
    notes.push("obvious test email");
  } else if (domain === "example.com" || domain.endsWith(".example.com") || domain.endsWith(".test")) {
    status = applyStatus(status, "test");
    spamScore = Math.max(spamScore, 80);
    notes.push("reserved test/example email domain");
  } else if (domain.includes("test")) {
    status = applyStatus(status, "review");
    spamScore = Math.max(spamScore, 30);
    notes.push("email domain contains test");
  }

  if (countUrlSignals(`${submission.name} ${submission.message}`) >= 2) {
    status = applyStatus(status, "review");
    spamScore = Math.max(spamScore, 60);
    notes.push("URL-heavy message");
  }

  if (!submission.name && !submission.message) {
    status = applyStatus(status, "review");
    spamScore = Math.max(spamScore, 20);
    notes.push("blank name and message");
  }

  if (submission.message.length >= SUSPICIOUS_MESSAGE_LENGTH) {
    status = applyStatus(status, "review");
    spamScore = Math.max(spamScore, 40);
    notes.push("very long message");
  }

  return {
    status,
    spamScore,
    adminNotes: notes.length ? `interest filter: ${notes.join("; ")}` : ""
  };
}

async function sha256Hex(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function ipHashFromRequest(request) {
  const ip = cleanString(request.headers.get("cf-connecting-ip"), 120);
  return ip ? sha256Hex(ip) : "";
}

async function parseRequestBody(request) {
  const contentType = request.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return request.json();
  }

  const formData = await request.formData();
  return {
    name: formData.get("name"),
    email: formData.get("email"),
    playerLevel: formData.get("playerLevel"),
    interests: formData.getAll("interests"),
    message: formData.get("message"),
    turnstileToken: formData.get("turnstileToken")
  };
}

function normalizeSubmission(input, now = new Date()) {
  const email = cleanString(input.email, 320).toLowerCase();
  if (!email) {
    return { ok: false, error: "Email is required." };
  }
  if (!EMAIL_PATTERN.test(email)) {
    return { ok: false, error: "Enter a valid email address." };
  }

  const submission = {
    id: crypto.randomUUID(),
    createdAt: now.toISOString(),
    name: cleanString(input.name, 200),
    email,
    playerLevel: cleanString(input.playerLevel, 80),
    interests: cleanInterestList(input.interests),
    message: cleanString(input.message, 2000),
    turnstileTokenPresent: Boolean(cleanString(input.turnstileToken, 2048)),
    userAgent: "",
    ipHash: "",
    source: SOURCE
  };
  const classification = classifySubmission(submission);

  return {
    ok: true,
    submission: {
      ...submission,
      status: classification.status,
      spamScore: classification.spamScore,
      adminNotes: classification.adminNotes
    }
  };
}

async function verifyTurnstilePlaceholder(_submission, _env) {
  return { ok: true, skipped: true };
}

function createInterestStorage(env) {
  if (env?.STEEL_RAG_INTEREST_D1?.prepare) {
    return {
      type: "d1",
      async save(submission) {
        await env.STEEL_RAG_INTEREST_D1
          .prepare(
            `insert into interest_submissions
              (id, created_at, name, email, player_level, interests, message, user_agent, ip_hash,
               status, spam_score, admin_notes, source)
             values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
          )
          .bind(
            submission.id,
            submission.createdAt,
            submission.name,
            submission.email,
            submission.playerLevel,
            JSON.stringify(submission.interests),
            submission.message,
            submission.userAgent,
            submission.ipHash,
            submission.status,
            submission.spamScore,
            submission.adminNotes,
            submission.source
          )
          .run();
      }
    };
  }

  if (env?.STEEL_RAG_INTEREST_KV?.put) {
    return {
      type: "kv",
      async save(submission) {
        await env.STEEL_RAG_INTEREST_KV.put(
          `interest:${submission.createdAt}:${submission.id}`,
          JSON.stringify(submission),
          { metadata: { email: submission.email, createdAt: submission.createdAt } }
        );
      }
    };
  }

  return {
    type: "missing",
    async save() {
      return undefined;
    }
  };
}

async function handleInterestRequest({ request, env = {} }) {
  if (request.method !== "POST") {
    return jsonResponse({ ok: false, error: "Method not allowed." }, 405);
  }

  let input;
  try {
    input = await parseRequestBody(request);
  } catch (_error) {
    return jsonResponse({ ok: false, error: "Invalid request body." }, 400);
  }

  const normalized = normalizeSubmission(input);
  if (!normalized.ok) {
    return jsonResponse({ ok: false, error: normalized.error }, 400);
  }

  const submission = {
    ...normalized.submission,
    userAgent: cleanString(request.headers.get("user-agent"), 300),
    ipHash: await ipHashFromRequest(request)
  };

  const turnstile = await verifyTurnstilePlaceholder(submission, env);
  if (!turnstile.ok) {
    return jsonResponse({ ok: false, error: "Spam check failed." }, 400);
  }

  const storage = createInterestStorage(env);
  try {
    await storage.save(submission);
  } catch (error) {
    console.error("interest storage error", {
      storage: storage.type,
      name: error?.name || "Error",
      message: error?.message || String(error)
    });
    return jsonResponse({ ok: false, error: "storage_error" }, 500);
  }

  return jsonResponse({
    ok: true,
    stored: storage.type !== "missing",
    storage: storage.type,
    id: submission.id
  });
}

export async function onRequestPost(context) {
  return handleInterestRequest(context);
}

export async function onRequest(context) {
  return context.request.method === "POST"
    ? handleInterestRequest(context)
    : jsonResponse({ ok: false, error: "Method not allowed." }, 405);
}

export const __test = {
  classifySubmission,
  createInterestStorage,
  countUrlSignals,
  handleInterestRequest,
  normalizeSubmission,
  ipHashFromRequest,
  verifyTurnstilePlaceholder
};
