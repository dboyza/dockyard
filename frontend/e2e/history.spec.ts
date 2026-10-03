import { navigateTo } from './navigation';
import { test, expect } from '@playwright/test';
import { spawn, type ChildProcess } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '../..');
let temporary: string;
let server: ChildProcess;
let url: string;
test.beforeAll(async () => {
  temporary = await mkdtemp(path.join(os.tmpdir(), 'dockyard-history-'));
  server = spawn(path.join(root, '.runtime/installed/bin/dockyard'), ['--data-dir', temporary, 'launch', '--port', '0', '--no-open'], { cwd: root });
  url = await new Promise<string>((resolve, reject) => {
    let output = '';
    const timeout = setTimeout(() => reject(new Error('History launcher did not become ready')), 15000);
    server.stdout!.on('data', data => {
      output += data.toString();
      const match = output.match(/http:\/\/127\.0\.0\.1:\d+\/#session=[A-Za-z0-9_-]+/);
      if (match) { clearTimeout(timeout); resolve(match[0]); }
    });
    server.on('error', reject);
  });
});
test.afterAll(async () => {
  if (server && server.exitCode === null) { server.kill('SIGINT'); await once(server, 'exit'); }
  if (temporary) await rm(temporary, { recursive: true, force: true });
});

test('the browser Back and Forward buttons, reloads, and bookmarks keep the learner’s place', async ({ page }) => {
  const failures: string[] = [];
  page.on('pageerror', error => failures.push(error.message));
  const origin = new URL(url).origin;
  const heading = page.getByRole('heading', { level: 1 });
  const at = (hash: string) => expect.poll(() => new URL(page.url()).hash).toBe(hash);

  // Signing in leaves a clean overview address rather than the one-time token.
  await page.goto(url);
  await expect(heading).toHaveText('Learn to run a real application.');
  await at('#/');

  // Following links records each place.
  await page.getByRole('button', { name: 'Start learning' }).click();
  await expect(heading).toHaveText('Your first container');
  await at('#/lesson/m00-first-container');
  await page.getByRole('figure', { name: 'From image to finished program' }).getByRole('button', { name: 'Writable layer, glossary entry' }).click();
  await expect(page.getByRole('heading', { name: 'Writable layer', exact: true })).toBeVisible();
  await at('#/reference/glossary/writable-layer');

  // Back and Forward retrace them without adding new entries.
  await page.goBack();
  await expect(heading).toHaveText('Your first container');
  await at('#/lesson/m00-first-container');
  await page.goBack();
  await expect(heading).toHaveText('Learn to run a real application.');
  await page.goForward();
  await expect(heading).toHaveText('Your first container');
  await page.goForward();
  await expect(page.getByRole('heading', { name: 'Writable layer', exact: true })).toBeVisible();

  // Moving within the reference desk and searching are places too.
  await page.getByRole('button', { name: 'Foundations', exact: false }).click();
  await page.locator('.reference-index button').filter({ hasText: 'Reading YAML' }).click();
  await at('#/reference/primers/yaml');
  await page.getByRole('textbox', { name: 'Search lessons and terms' }).fill('volume');
  await at('#/course');
  await page.goBack();
  await expect(page.getByRole('heading', { name: 'Reading YAML' })).toBeVisible();

  // Jump links move focus without replacing the address.
  await navigateTo(page, 'Your course');
  await page.getByRole('navigation', { name: 'Course phases' }).getByRole('link').nth(1).click();
  await at('#/course');

  // Reloading keeps the place, and a saved address opens it directly.
  await page.goto(`${origin}/#/reference/primers/dns`);
  await expect(page.getByRole('heading', { name: 'Names and DNS' })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Names and DNS' })).toBeVisible();
  await page.goto(`${origin}/#/lesson/m01-processes`);
  await expect(heading).toHaveText('Meet Dispatch: run its first version');
  await page.reload();
  await expect(heading).toHaveText('Meet Dispatch: run its first version');
  await at('#/lesson/m01-processes');

  // An address that names nothing falls back to the current place.
  await page.evaluate(() => { location.hash = '#/lesson/no-such-lesson'; });
  await at('#/lesson/m01-processes');
  await expect(heading).toHaveText('Meet Dispatch: run its first version');
  expect(failures).toEqual([]);
});
