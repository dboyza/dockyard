import { test, expect } from '@playwright/test';
import { spawn, type ChildProcess } from 'node:child_process';
import { once } from 'node:events';
import { createServer } from 'node:net';
import path from 'node:path';
import figures from '../../src/dockyard/content/figures.json' with { type: 'json' };

// Visual regression for every figure and every step, in both themes.
// Reference images are per platform because the interface uses system fonts;
// see docs/maintenance.md for creating and reviewing them.
const frontend = path.resolve(import.meta.dirname, '..');
let server: ChildProcess;
let origin: string;

async function freePort() {
  const probe = createServer();
  probe.listen(0, '127.0.0.1');
  await once(probe, 'listening');
  const { port } = probe.address() as { port: number };
  probe.close();
  return port;
}

test.beforeAll(async () => {
  const port = await freePort();
  origin = `http://127.0.0.1:${port}`;
  server = spawn(path.join(frontend, 'node_modules/.bin/vite'), ['--host', '127.0.0.1', '--port', String(port), '--strictPort'], { cwd: frontend });
  for (let attempt = 0; ; attempt++) {
    if (server.exitCode !== null) throw new Error(`The gallery server exited with ${server.exitCode}`);
    if (await fetch(`${origin}/gallery.html`).then(response => response.ok, () => false)) break;
    if (attempt === 150) throw new Error('The gallery server did not start');
    await new Promise(resolve => setTimeout(resolve, 200));
  }
});
test.afterAll(async () => {
  if (server && server.exitCode === null) { server.kill('SIGTERM'); await once(server, 'exit'); }
});

for (const theme of ['light', 'dark']) {
  test(`every figure and step looks as reviewed in the ${theme} theme`, async ({ page }) => {
    test.setTimeout(180000);
    await page.setViewportSize({ width: 760, height: 1000 });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto(`${origin}/gallery.html?theme=${theme}`);
    await expect(page.locator('main > section')).toHaveCount(figures.length);
    await page.evaluate(() => document.fonts.ready);
    // The drawings are what this suite protects; their text is covered by unit tests.
    await page.addStyleTag({ content: 'main > section > h2, .lesson-figure header, .lesson-figure > strong, .figure-steps, figcaption, .figure-terms { visibility: hidden; }' });
    for (const figure of figures) {
      await expect.soft(page.locator(`section#${figure.id}`)).toHaveScreenshot([theme, `${figure.id}.png`], { animations: 'disabled' });
    }
  });
}
