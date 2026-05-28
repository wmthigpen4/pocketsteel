const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_FIELD_LENGTH = 2000;

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

  return {
    ok: true,
    submission: {
      id: crypto.randomUUID(),
      submittedAt: now.toISOString(),
      name: cleanString(input.name, 200),
      email,
      playerLevel: cleanString(input.playerLevel, 80),
      interests: cleanInterestList(input.interests),
      message: cleanString(input.message, 2000),
      turnstileTokenPresent: Boolean(cleanString(input.turnstileToken, 2048)),
      userAgent: "",
      cfRay: ""
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
              (id, submitted_at, name, email, player_level, interests_json, message, turnstile_token_present, user_agent, cf_ray)
             values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
          )
          .bind(
            submission.id,
            submission.submittedAt,
            submission.name,
            submission.email,
            submission.playerLevel,
            JSON.stringify(submission.interests),
            submission.message,
            submission.turnstileTokenPresent ? 1 : 0,
            submission.userAgent,
            submission.cfRay
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
          `interest:${submission.submittedAt}:${submission.id}`,
          JSON.stringify(submission),
          { metadata: { email: submission.email, submittedAt: submission.submittedAt } }
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
  } catch (error) {
    return jsonResponse({ ok: false, error: "Invalid request body." }, 400);
  }

  const normalized = normalizeSubmission(input);
  if (!normalized.ok) {
    return jsonResponse({ ok: false, error: normalized.error }, 400);
  }

  const submission = {
    ...normalized.submission,
    userAgent: cleanString(request.headers.get("user-agent"), 300),
    cfRay: cleanString(request.headers.get("cf-ray"), 100)
  };

  const turnstile = await verifyTurnstilePlaceholder(submission, env);
  if (!turnstile.ok) {
    return jsonResponse({ ok: false, error: "Spam check failed." }, 400);
  }

  const storage = createInterestStorage(env);
  await storage.save(submission);

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
  createInterestStorage,
  handleInterestRequest,
  normalizeSubmission,
  verifyTurnstilePlaceholder
};
