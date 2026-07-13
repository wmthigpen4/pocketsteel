import { describe, expect, it } from "vitest";

import worker, { __test } from "../../workers/interest-digest.js";

describe("interest digest in the Workers runtime", () => {
  it("keeps the root closed and non-sensitive", async () => {
    const response = await worker.fetch(new Request("https://digest.example/"), {});
    expect(response.status).toBe(404);
    expect(await response.json()).toEqual({ ok: false, error: "not_found" });
  });

  it("does not accept the shared admin token without Access identity", async () => {
    const response = await worker.fetch(
      new Request("https://digest.example/dry-run", {
        headers: { Authorization: "Bearer local-test" }
      }),
      { INTEREST_DIGEST_ADMIN_TOKEN: "local-test" }
    );
    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ ok: false, error: "forbidden" });
  });

  it("uses stable UTC Monday delivery windows", () => {
    expect(__test.weeklyDigestWindow(new Date("2026-07-15T23:59:00.000Z"))).toEqual({
      start: "2026-07-13T00:00:00.000Z",
      end: "2026-07-20T00:00:00.000Z"
    });
  });

  it("rejects expired Access claims before any key lookup", () => {
    expect(__test.validateAccessClaims(
      {
        iss: "https://steel.cloudflareaccess.com",
        aud: ["digest-aud"],
        exp: 99
      },
      {
        issuer: "https://steel.cloudflareaccess.com",
        audience: "digest-aud"
      },
      100
    )).toBe(false);
  });
});
