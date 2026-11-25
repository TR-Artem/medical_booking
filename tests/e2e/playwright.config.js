const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: ".",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: process.env.BASE_URL || "http://127.0.0.1:8000",
    channel: process.env.PW_CHANNEL || undefined,
    headless: true,
    locale: "ru-RU",
    viewport: { width: 1440, height: 900 },
  },
});
