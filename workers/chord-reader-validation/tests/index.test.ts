import { describe, expect, it } from "vitest";

import { normalizeTrackPayload, parseByteRange } from "../src/validation";

function fixture() {
  return {
    trackId: "nothing-s-news-no-steel",
    title: "Nothing's News (No Steel)",
    audioSha256: "a".repeat(64),
    songNotes: "Check the turnaround.",
    suggestedKey: "C",
    songKey: "G",
    keySource: "reviewer",
    displayMode: "nns",
    songMeter: "4/4" as const,
    meterSource: "detected" as const,
    tempoBpm: 118,
    timingOffsetSeconds: 0.1,
    reviewComplete: false,
    reviewedAt: null,
    segments: {
      4: { status: "corrected", correctedChord: "D7", note: "split chord" },
    },
    boxMerges: [
      {
        startBox: 5,
        endBox: 6,
        status: "merged",
        correctedChord: "G7",
        note: "One musical bar",
        createdAt: "2026-08-26T12:00:00.000Z",
      },
    ],
  };
}

describe("Travis validation backend", () => {
  it("normalizes a bounded track feedback document", () => {
    expect(normalizeTrackPayload(fixture(), "nothing-s-news-no-steel")).toEqual(
      fixture(),
    );
  });

  it("rejects route/body track mismatches and oversized notes", () => {
    expect(() => normalizeTrackPayload(fixture(), "different-track")).toThrow(
      /trackId/u,
    );
    expect(() =>
      normalizeTrackPayload(
        { ...fixture(), songNotes: "x".repeat(10_001) },
        fixture().trackId,
      ),
    ).toThrow(/songNotes/u);
  });

  it("rejects unknown statuses and keys", () => {
    expect(() =>
      normalizeTrackPayload({ ...fixture(), songKey: "H" }, fixture().trackId),
    ).toThrow(/Song key/u);
    expect(() =>
      normalizeTrackPayload(
        {
          ...fixture(),
          segments: {
            4: { status: "approved_by_magic", correctedChord: "", note: "" },
          },
        },
        fixture().trackId,
      ),
    ).toThrow(/status/u);
  });

  it("rejects an out-of-range timing offset", () => {
    expect(() =>
      normalizeTrackPayload(
        { ...fixture(), timingOffsetSeconds: 2.1 },
        fixture().trackId,
      ),
    ).toThrow(/timingOffsetSeconds/u);
  });

  it("rejects overlapping or inverted structural merges", () => {
    expect(() =>
      normalizeTrackPayload(
        {
          ...fixture(),
          boxMerges: [
            fixture().boxMerges[0],
            { ...fixture().boxMerges[0], startBox: 6, endBox: 8 },
          ],
        },
        fixture().trackId,
      ),
    ).toThrow(/overlap/u);
    expect(() =>
      normalizeTrackPayload(
        {
          ...fixture(),
          boxMerges: [{ ...fixture().boxMerges[0], startBox: 9, endBox: 8 }],
        },
        fixture().trackId,
      ),
    ).toThrow(/range/u);
  });

  it("parses bounded audio byte ranges", () => {
    expect(parseByteRange("bytes=100-199", 1_000)).toEqual({
      offset: 100,
      length: 100,
      end: 199,
    });
    expect(parseByteRange("bytes=900-", 1_000)).toEqual({
      offset: 900,
      length: 100,
      end: 999,
    });
    expect(() => parseByteRange("bytes=1000-", 1_000)).toThrow(/satisfiable/u);
    expect(() => parseByteRange("bytes=0-1,4-5", 1_000)).toThrow(
      /one byte range/u,
    );
  });
});
