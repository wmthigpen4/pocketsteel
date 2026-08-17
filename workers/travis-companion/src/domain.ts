export const SCHEMA_VERSION = "lesson_companion_v3";

export class DomainError extends Error {
  constructor(message: string, public readonly status = 400) {
    super(message);
  }
}

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export function stableJson(value: Json): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key] ?? null)}`).join(",")}}`;
}

export function encodeBase64Url(value: Uint8Array): string {
  let binary = "";
  for (const byte of value) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

export function decodeBase64Url(value: string): Uint8Array {
  const padded = `${value.replaceAll("-", "+").replaceAll("_", "/")}${"=".repeat((4 - value.length % 4) % 4)}`;
  const binary = atob(padded);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

export async function sha256(value: string | Uint8Array): Promise<string> {
  const bytes = typeof value === "string" ? new TextEncoder().encode(value) : value;
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return Array.from(digest, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function timingSafeSecret(provided: string, expected: string): Promise<boolean> {
  const encoder = new TextEncoder();
  const [left, right] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(provided)),
    crypto.subtle.digest("SHA-256", encoder.encode(expected)),
  ]);
  return crypto.subtle.timingSafeEqual(left, right);
}

export function randomToken(bytes = 32): string {
  const value = new Uint8Array(bytes);
  crypto.getRandomValues(value);
  return encodeBase64Url(value);
}

export async function signLessonToken(
  secret: string,
  claims: { sub: string; projectId: string; slug: string; courseId: string; revision: string; exp: number },
): Promise<string> {
  const header = encodeBase64Url(new TextEncoder().encode(JSON.stringify({ alg: "HS256", typ: "JWT" })));
  const payload = encodeBase64Url(new TextEncoder().encode(JSON.stringify(claims)));
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${header}.${payload}`)));
  return `${header}.${payload}.${encodeBase64Url(signature)}`;
}

export async function verifyLessonToken(
  token: string,
  secret: string,
): Promise<{ sub: string; projectId: string; slug: string; courseId: string; revision: string; exp: number }> {
  const parts = token.split(".");
  if (parts.length !== 3 || !parts[0] || !parts[1] || !parts[2]) throw new DomainError("Invalid lesson token.", 401);
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );
  const valid = await crypto.subtle.verify(
    "HMAC",
    key,
    decodeBase64Url(parts[2]),
    new TextEncoder().encode(`${parts[0]}.${parts[1]}`),
  );
  if (!valid) throw new DomainError("Invalid lesson token.", 401);
  const claims = JSON.parse(new TextDecoder().decode(decodeBase64Url(parts[1]))) as {
    sub?: string; projectId?: string; slug?: string; courseId?: string; revision?: string; exp?: number;
  };
  if (!claims.sub || !claims.projectId || !claims.slug || !claims.courseId || !claims.revision || !claims.exp) {
    throw new DomainError("Incomplete lesson token.", 401);
  }
  if (claims.exp <= Math.floor(Date.now() / 1000)) throw new DomainError("Lesson token expired.", 401);
  return claims as { sub: string; projectId: string; slug: string; courseId: string; revision: string; exp: number };
}

function object(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new DomainError(`${label} must be an object.`);
  return value as Record<string, unknown>;
}

function array(value: unknown, label: string): unknown[] {
  if (!Array.isArray(value)) throw new DomainError(`${label} must be an array.`);
  return value;
}

function range(value: unknown, label: string, maximum: number): { startMs: number; endMs: number } {
  const item = object(value, label);
  const startMs = Number(item.startMs);
  const endMs = Number(item.endMs);
  if (!Number.isInteger(startMs) || !Number.isInteger(endMs) || startMs < 0 || endMs <= startMs || endMs > maximum) {
    throw new DomainError(`${label} has invalid timing.`);
  }
  return { startMs, endMs };
}

const PITCH_CLASSES: Record<string, number> = { C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5, "F#": 6, Gb: 6, G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11 };

function pitchValue(label: string): number | null {
  const match = /^([A-G])([#b]?)(-?\d+)$/u.exec(label);
  if (!match?.[1] || match[3] === undefined) return null;
  const pitchClass = PITCH_CLASSES[`${match[1]}${match[2] ?? ""}`];
  return pitchClass === undefined ? null : (Number(match[3]) + 1) * 12 + pitchClass;
}

export function validateCompanion(value: unknown, options: { publishing?: boolean } = {}): Record<string, unknown> {
  const draft = object(value, "Companion");
  if (draft.schemaVersion !== SCHEMA_VERSION) throw new DomainError(`Companion schema must be ${SCHEMA_VERSION}.`);
  const states = new Set(["draft", "uploading", "ready_for_analysis", "processing", "review_ready", "published", "analysis_failed", "publish_failed"]);
  if (!String(draft.companionId ?? "") || !String(draft.revision ?? "") || !states.has(String(draft.state ?? ""))) {
    throw new DomainError("Companion ID, revision, and state are required.");
  }
  const lesson = object(draft.lesson, "Lesson");
  const teachable = object(lesson.teachable, "Teachable lesson");
  if (!String(lesson.slug ?? "") || !String(lesson.title ?? "") || !String(teachable.courseId ?? "") || !String(teachable.lessonId ?? "")) {
    throw new DomainError("Lesson slug, title, course ID, and lesson ID are required.");
  }
  const copedent = object(draft.copedentSnapshot, "Copedent snapshot");
  const strings = array(copedent.stringsHighToLow, "Copedent strings").map((item) => object(item, "Copedent string"));
  if (strings.length !== 10) throw new DomainError("A ten-string E9 copedent snapshot is required.");
  const openPitches = new Map<number, number>();
  for (const item of strings) {
    const string = Number(item.string);
    const pitch = pitchValue(String(item.openPitch ?? ""));
    if (!Number.isInteger(string) || string < 1 || string > 10 || pitch === null) throw new DomainError("Invalid copedent open pitch.");
    openPitches.set(string, pitch);
  }
  if (openPitches.size !== 10) throw new DomainError("Copedent string numbers must be unique.");
  const controls = new Map<string, Map<number, number>>();
  for (const raw of array(copedent.controls, "Copedent controls")) {
    const control = object(raw, "Copedent control");
    const code = String(control.code ?? "");
    const changes = new Map<number, number>();
    for (const rawChange of array(control.changes, `Control ${code} changes`)) {
      const change = object(rawChange, "Control change");
      const string = Number(change.string);
      const semitones = Number(change.semitones);
      if (!Number.isInteger(string) || string < 1 || string > 10 || !Number.isInteger(semitones) || semitones === 0) {
        throw new DomainError(`Control ${code} has an invalid change.`);
      }
      changes.set(string, semitones);
    }
    if (!code || controls.has(code) || changes.size === 0) throw new DomainError("Copedent controls require unique codes and changes.");
    controls.set(code, changes);
  }

  const media = object(draft.media, "Media");
  const video = object(media.lessonVideo, "Lesson video");
  const videoDuration = Number(video.durationMs);
  const tracks = array(media.backingTracks, "Backing tracks").map((item) => object(item, "Backing track"));
  const primary = tracks.filter((track) => track.primary === true);
  if (!String(video.assetId ?? "") || !Number.isInteger(videoDuration) || videoDuration <= 0 || primary.length !== 1) {
    throw new DomainError("A lesson video and exactly one primary backing track are required.");
  }
  const primaryTrack = primary[0];
  if (!primaryTrack) throw new DomainError("Primary backing track is required.");
  const duration = Number(primaryTrack.durationMs);
  if (String(primaryTrack.assetId ?? "") !== String(draft.primaryTrackId ?? "") || !Number.isInteger(duration) || duration <= 0) {
    throw new DomainError("Primary backing-track metadata is invalid.");
  }
  if (options.publishing && primaryTrack.visibleToLearners !== true) throw new DomainError("Primary track must be learner-playable.");

  const chords = array(draft.songChordTimeline, "Chord timeline");
  if (chords.length === 0) throw new DomainError("A complete chord timeline is required.");
  let cursor = 0;
  const chordIds = new Set<string>();
  for (const raw of chords) {
    const chord = object(raw, "Chord event");
    const id = String(chord.id ?? "");
    const timing = range(chord, `Chord ${id}`, duration);
    if (!id || chordIds.has(id) || timing.startMs !== cursor) throw new DomainError("Chord timeline IDs and coverage must be contiguous.");
    if (!String(chord.symbol ?? "") && !["uncertain", "generated_unconfirmed"].includes(String(chord.reviewStatus ?? ""))) {
      throw new DomainError(`Chord ${id} needs a symbol or uncertainty marker.`);
    }
    chordIds.add(id);
    cursor = timing.endMs;
  }
  if (cursor !== duration) throw new DomainError("Chord timeline must cover the complete primary track.");

  const passages = array(draft.passages, "Passages");
  if (passages.length === 0) throw new DomainError("At least one selected passage is required.");
  const passageIds = new Set<string>();
  const eventIds = new Set<string>();
  for (const rawPassage of passages) {
    const passage = object(rawPassage, "Passage");
    const passageId = String(passage.id ?? "");
    range(passage.videoRange, `${passageId} video range`, videoDuration);
    const trackRange = range(passage.trackRange, `${passageId} track range`, duration);
    const events = array(passage.tabEvents, `${passageId} tab events`);
    if (!passageId || passageIds.has(passageId) || events.length === 0) throw new DomainError("Every passage needs a unique ID and tab events.");
    passageIds.add(passageId);
    let previous = trackRange.startMs;
    for (const rawEvent of events) {
      const event = object(rawEvent, "Tab event");
      const id = String(event.id ?? "");
      const timing = range(event, `Tab event ${id}`, trackRange.endMs);
      if (!id || eventIds.has(id) || timing.startMs < trackRange.startMs || timing.startMs < previous) {
        throw new DomainError("Tab event IDs and timing are invalid.");
      }
      previous = timing.startMs;
      eventIds.add(id);
      const notes = array(event.notes, `Tab event ${id} notes`);
      if (notes.length === 0) throw new DomainError(`Tab event ${id} needs notes.`);
      for (const rawNote of notes) {
        const note = object(rawNote, "Tab note");
        const string = Number(note.string);
        const fret = Number(note.fret);
        const open = openPitches.get(string);
        if (!Number.isInteger(string) || !Number.isInteger(fret) || fret < 0 || fret > 36 || open === undefined) {
          throw new DomainError(`Tab event ${id} has an invalid string or fret.`);
        }
        let sounding = open + fret;
        for (const rawCode of array(note.controls ?? [], "Tab controls")) {
          const code = String(rawCode);
          const change = controls.get(code)?.get(string);
          if (change === undefined) throw new DomainError(`Control ${code} does not change string ${string}.`);
          sounding += change;
        }
        if (note.pitchValue !== undefined && Number(note.pitchValue) !== sounding) throw new DomainError(`Tab event ${id} fails pitch validation.`);
      }
    }
  }
  if (options.publishing) {
    const publication = object(draft.publication, "Publication");
    if (draft.state !== "published" || !String(publication.publishedAt ?? "") || !String(publication.contentSha256 ?? "")) {
      throw new DomainError("Published companions require publication metadata.");
    }
  }
  return draft;
}

export async function contentHash(draft: Record<string, unknown>): Promise<string> {
  const clone = structuredClone(draft) as Record<string, unknown>;
  const publication = clone.publication;
  if (publication && typeof publication === "object" && !Array.isArray(publication)) delete (publication as Record<string, unknown>).contentSha256;
  return sha256(stableJson(clone as Json));
}

function pdfEscape(value: string): string {
  return value.replaceAll("\\", "\\\\").replaceAll("(", "\\(").replaceAll(")", "\\)").replace(/[^\x20-\x7E]/gu, "?");
}

export function buildCompanionPdf(draft: Record<string, unknown>): Uint8Array {
  const lesson = draft.lesson as Record<string, unknown>;
  const chords = draft.songChordTimeline as Record<string, unknown>[];
  const passages = draft.passages as Record<string, unknown>[];
  const lines = [
    String(lesson.title ?? "Lesson companion"),
    `${String(lesson.key ?? "")} | ${String(lesson.meter ?? "")} | Travis Toy Tutorials`,
    "",
    "Full-song chord chart",
    ...chords.map((chord) => `${Math.round(Number(chord.startMs) / 1000)}s  ${String(chord.symbol ?? "?")}  ${String(chord.nns ?? "")}`),
    "",
    ...passages.flatMap((passage) => [
      `Passage: ${String(passage.label ?? passage.id ?? "")}`,
      ...((passage.tabEvents as Record<string, unknown>[]) ?? []).map((event) => {
        const notes = ((event.notes as Record<string, unknown>[]) ?? []).map((note) => `S${note.string} F${note.fret}${((note.controls as string[]) ?? []).join("+") ? ` ${((note.controls as string[]) ?? []).join("+")}` : ""}`).join(" / ");
        return `${(Number(event.startMs) / 1000).toFixed(2)}s  ${notes}${event.reviewStatus === "generated_unconfirmed" ? "  [unconfirmed]" : ""}`;
      }),
      "",
    ]),
  ];
  const pageLines = 48;
  const pages = Array.from({ length: Math.max(1, Math.ceil(lines.length / pageLines)) }, (_, index) => lines.slice(index * pageLines, (index + 1) * pageLines));
  const catalogId = 1;
  const pagesId = 2;
  const fontId = 3;
  const objects: string[] = [];
  const pageIds = pages.map((_, index) => 5 + index * 2);
  objects[catalogId - 1] = `<< /Type /Catalog /Pages ${pagesId} 0 R >>`;
  objects[pagesId - 1] = `<< /Type /Pages /Count ${pages.length} /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] >>`;
  objects[fontId - 1] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>";
  pages.forEach((page, index) => {
    const commands = ["BT", "/F1 11 Tf", "52 740 Td", "14 TL", ...page.map((line) => `(${pdfEscape(line)}) Tj T*`), "ET"].join("\n");
    const contentId = 4 + index * 2;
    const pageId = 5 + index * 2;
    objects[contentId - 1] = `<< /Length ${new TextEncoder().encode(commands).length} >>\nstream\n${commands}\nendstream`;
    objects[pageId - 1] = `<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${contentId} 0 R >>`;
  });
  let output = "%PDF-1.4\n";
  const offsets = [0];
  objects.forEach((body, index) => {
    offsets.push(new TextEncoder().encode(output).length);
    output += `${index + 1} 0 obj\n${body}\nendobj\n`;
  });
  const xref = new TextEncoder().encode(output).length;
  output += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  output += offsets.slice(1).map((offset) => `${String(offset).padStart(10, "0")} 00000 n \n`).join("");
  output += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return new TextEncoder().encode(output);
}
