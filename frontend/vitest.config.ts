import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: { environment: 'jsdom', include: ['src/**/*.test.{ts,tsx}'], environmentOptions: { jsdom: { url: 'http://127.0.0.1:8768/' } } },
});
