const TRACK_ID_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/u;
const KEY_NAMES = new Set([
  "C",
  "Db",
  "D",
  "Eb",
  "E",
  "F",
  "F#",
  "G",
  "Ab",
  "A",
  "Bb",
  "B",
]);
const STATUSES = new Set([
  "assumed_correct",
  "pending_assumed_correct",
  "corrected",
  "timing",
  "unsure",
  "comment",
]);

export class HttpError extends Error {
  constructor(
    message: string,
    readonly status = 400,
  ) {
    super(message);
  }
}

export type StoredTrack = {
  trackId: string;
  title: string;
  audioSha256: string;
  songNotes: string;
  suggestedKey: string;
  songKey: string;
  keySource: "suggested" | "reviewer";
  displayMode: "chords" | "nns";
  reviewComplete: boolean;
  reviewedAt: string | null;
  segments: Record<
    string,
    { status: string; correctedChord: string; note: string }
  >;
};

function text(value: unknown, field: string, limit: number): string {
  if (typeof value !== "string" || value.length > limit)
    throw new HttpError(`${field} is invalid.`);
  return value;
}

function nullableIso(value: unknown): string | null {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value !== "string" || !Number.isFinite(Date.parse(value)))
    throw new HttpError("reviewedAt is invalid.");
  return value;
}

export function plainObject(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new HttpError("JSON object required.");
  return value as Record<string, unknown>;
}

export function normalizeTrackPayload(
  value: unknown,
  routeTrackId: string,
): StoredTrack {
  const input = plainObject(value);
  const trackId = text(input.trackId, "trackId", 120);
  if (trackId !== routeTrackId || !TRACK_ID_PATTERN.test(trackId))
    throw new HttpError("trackId is invalid.");
  const suggestedKey = text(input.suggestedKey, "suggestedKey", 4);
  const songKey = text(input.songKey, "songKey", 4);
  if (!KEY_NAMES.has(suggestedKey) || !KEY_NAMES.has(songKey))
    throw new HttpError("Song key is invalid.");
  if (input.keySource !== "suggested" && input.keySource !== "reviewer")
    throw new HttpError("keySource is invalid.");
  if (input.displayMode !== "chords" && input.displayMode !== "nns")
    throw new HttpError("displayMode is invalid.");
  if (typeof input.reviewComplete !== "boolean")
    throw new HttpError("reviewComplete is invalid.");

  const segmentInput = plainObject(input.segments ?? {});
  const entries = Object.entries(segmentInput);
  if (entries.length > 500) throw new HttpError("Too many segment edits.");
  const segments: StoredTrack["segments"] = {};
  for (const [index, rawSegment] of entries) {
    if (!/^\d{1,4}$/u.test(index))
      throw new HttpError("Segment index is invalid.");
    const segment = plainObject(rawSegment);
    const status = text(segment.status, "segment status", 32);
    if (!STATUSES.has(status))
      throw new HttpError("Segment status is invalid.");
    segments[index] = {
      status,
      correctedChord: text(segment.correctedChord ?? "", "correctedChord", 24),
      note: text(segment.note ?? "", "segment note", 240),
    };
  }

  return {
    trackId,
    title: text(input.title, "title", 240),
    audioSha256: text(input.audioSha256, "audioSha256", 128),
    songNotes: text(input.songNotes ?? "", "songNotes", 10_000),
    suggestedKey,
    songKey,
    keySource: input.keySource,
    displayMode: input.displayMode,
    reviewComplete: input.reviewComplete,
    reviewedAt: nullableIso(input.reviewedAt),
    segments,
  };
}

export function parseByteRange(
  header: string | null,
  size: number,
): { offset: number; length: number; end: number } | null {
  if (!header) return null;
  const match = header.match(/^bytes=(\d+)-(\d*)$/u);
  if (!match) throw new HttpError("Only one byte range is supported.", 416);
  const offset = Number(match[1]);
  const requestedEnd = match[2] ? Number(match[2]) : size - 1;
  const end = Math.min(requestedEnd, size - 1);
  if (
    !Number.isSafeInteger(offset) ||
    !Number.isSafeInteger(end) ||
    offset < 0 ||
    offset > end ||
    offset >= size
  ) {
    throw new HttpError("Requested range is not satisfiable.", 416);
  }
  return { offset, length: end - offset + 1, end };
}
