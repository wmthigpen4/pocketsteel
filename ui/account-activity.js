const STEEL_RAG_ACCOUNT_ACTIVITY = (() => {
  const ENDPOINT = "/api/account/activity";
  const CLIENT_DEDUPE_MS = 30_000;
  const EVENT_TYPES = new Set([
    "explorer.position_selected",
    "explorer.chord_grip_selected",
    "explorer.scale_path_selected",
    "explorer.movement_compared",
    "melody.session_started",
    "melody.edited",
    "melody.playback_completed",
    "lesson.started",
    "lesson.section_completed",
    "lesson.exercise_completed",
    "connected.answer_to_explorer",
    "connected.lesson_to_explorer",
    "connected.lesson_to_melody",
    "connected.explorer_to_melody"
  ]);
  const recentEvents = new Map();

  function cleanKey(value, fallback) {
    const cleaned = String(value || fallback || "activity")
      .replace(/[\u0000-\u001f\u007f]/g, " ")
      .trim()
      .slice(0, 160);
    return cleaned || fallback || "activity";
  }

  function eventId() {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    const random = Math.random().toString(36).slice(2);
    return `event-${Date.now().toString(36)}-${random}`;
  }

  function accessHeaders() {
    const role = new URLSearchParams(globalThis.location?.search || "").get("access");
    const helper = globalThis.STEEL_RAG_ANSWER_UI?.devAccessHeaders;
    return typeof helper === "function" ? helper(role) : {};
  }

  async function track(eventType, { dedupeKey = eventType, fetchImpl = globalThis.fetch } = {}) {
    if (!EVENT_TYPES.has(eventType) || typeof fetchImpl !== "function") return false;
    const safeKey = cleanKey(dedupeKey, eventType);
    const localKey = `${eventType}:${safeKey}`;
    const now = Date.now();
    if (now - (recentEvents.get(localKey) || 0) < CLIENT_DEDUPE_MS) return false;
    recentEvents.set(localKey, now);
    try {
      const response = await fetchImpl(ENDPOINT, {
        method: "POST",
        credentials: "same-origin",
        keepalive: true,
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          ...accessHeaders()
        },
        body: JSON.stringify({ eventType, eventId: eventId(), dedupeKey: safeKey })
      });
      if (!response.ok) return false;
      const payload = await response.json();
      return Boolean(payload?.recorded);
    } catch (_error) {
      return false;
    }
  }

  return Object.freeze({ ENDPOINT, EVENT_TYPES, track });
})();
