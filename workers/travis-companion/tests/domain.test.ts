import { describe, expect, it } from "vitest";

import {
  buildCompanionPdf,
  contentHash,
  DomainError,
  signLessonToken,
  validateCompanion,
  verifyLessonToken,
} from "../src/domain";

function fixture(): Record<string, unknown> {
  return {
    schemaVersion: "lesson_companion_v3",
    companionId: "fixture",
    revision: "fixture-draft-1",
    state: "review_ready",
    lesson: { slug: "fixture", title: "Fixture", key: "D", meter: "4/4", teachable: { courseId: "course-1", lessonId: "lesson-1" } },
    copedentSnapshot: {
      id: "travis-e9",
      stringsHighToLow: ["F#4", "D#4", "G#3", "E3", "B2", "G#2", "F#2", "E2", "D2", "B1"].map((openPitch, index) => ({ string: index + 1, openPitch })),
      controls: [{ code: "A", changes: [{ string: 5, semitones: 2 }] }],
    },
    media: {
      lessonVideo: { assetId: "video-1", durationMs: 2_000 },
      backingTracks: [{ assetId: "track-1", durationMs: 1_000, primary: true, visibleToLearners: true, downloadable: false }],
    },
    primaryTrackId: "track-1",
    songChordTimeline: [{ id: "chord-1", startMs: 0, endMs: 1_000, symbol: null, nns: "1", reviewStatus: "uncertain" }],
    passages: [{
      id: "passage-1",
      label: "Passage",
      videoRange: { startMs: 200, endMs: 1_200 },
      trackRange: { startMs: 0, endMs: 1_000 },
      alignment: { status: "manual", confidence: 1 },
      tabEvents: [{ id: "event-1", startMs: 0, endMs: 500, notes: [{ string: 3, fret: 0, controls: [], pitchValue: 56 }], reviewStatus: "generated_unconfirmed" }],
    }],
    analysis: { models: {} },
  };
}

describe("lesson_companion_v3", () => {
  it("allows visible uncertainty in a technically valid artifact", () => {
    expect(validateCompanion(fixture())).toBeTruthy();
  });

  it("requires publication metadata only at the publish boundary", () => {
    expect(() => validateCompanion(fixture(), { publishing: true })).toThrow(/Publication/u);
    const published = fixture();
    published.state = "published";
    published.publication = { publishedAt: "2026-08-17T00:00:00Z", contentSha256: "fixture" };
    expect(validateCompanion(published, { publishing: true })).toBeTruthy();
  });

  it("rejects impossible controls and gaps", () => {
    const invalid = fixture();
    const passages = invalid.passages as Record<string, unknown>[];
    const events = passages[0]?.tabEvents as Record<string, unknown>[];
    const notes = events[0]?.notes as Record<string, unknown>[];
    notes[0]!.controls = ["A"];
    expect(() => validateCompanion(invalid)).toThrow(DomainError);

    const gap = fixture();
    const chords = gap.songChordTimeline as Record<string, unknown>[];
    chords[0]!.startMs = 1;
    expect(() => validateCompanion(gap)).toThrow(/contiguous/u);
  });

  it("produces deterministic immutable hashes", async () => {
    const artifact = fixture();
    artifact.publication = { publishedAt: "2026-08-17T00:00:00Z", contentSha256: "one" };
    const first = await contentHash(artifact);
    (artifact.publication as Record<string, unknown>).contentSha256 = "two";
    expect(await contentHash(artifact)).toBe(first);
  });

  it("signs lesson-scoped tokens and rejects forgery or expiry", async () => {
    const claims = { sub: "student", projectId: "project", slug: "fixture", courseId: "course-1", revision: "r1", exp: Math.floor(Date.now() / 1000) + 60 };
    const token = await signLessonToken("secret", claims);
    await expect(verifyLessonToken(token, "secret")).resolves.toMatchObject(claims);
    await expect(verifyLessonToken(`${token.slice(0, -1)}x`, "secret")).rejects.toThrow(/Invalid lesson token/u);
    const expired = await signLessonToken("secret", { ...claims, exp: 1 });
    await expect(verifyLessonToken(expired, "secret")).rejects.toThrow(/expired/u);
  });

  it("generates a structurally complete PDF", () => {
    const pdf = new TextDecoder().decode(buildCompanionPdf(fixture()));
    expect(pdf.startsWith("%PDF-1.4")).toBe(true);
    expect(pdf).toContain("/Root 1 0 R");
    expect(pdf).toContain("/Pages 2 0 R");
    expect(pdf.endsWith("%%EOF\n")).toBe(true);
  });
});
