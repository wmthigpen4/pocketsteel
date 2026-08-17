import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["workers/travis-companion/tests/**/*.test.ts"],
  },
});
