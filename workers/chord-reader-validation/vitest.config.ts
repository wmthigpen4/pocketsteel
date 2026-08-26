import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["workers/chord-reader-validation/tests/**/*.test.ts"],
  },
});
