import { test, expect } from '@playwright/test';
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { mkdirSync, mkdtempSync } from 'node:fs';
import path from 'node:path';
import { once } from 'node:events';

const root = path.resolve(import.meta.dirname, '../..');
const binary = path.join(root, '.runtime/installed/bin/dockyard');
let server: ChildProcess;
let url: string;
let profile: string;

test.beforeAll(async () => {
  mkdirSync(path.join(root, '.runtime/e2e'), { recursive: true });
  profile = mkdtempSync(path.join(root, '.runtime/e2e/profile-'));
  server = spawn(binary, ['--data-dir', profile, 'launch', '--port', '0', '--no-open'], { cwd: root });
  url = await new Promise<string>((resolve, reject) => {
    let output = '';
    const timeout = setTimeout(() => reject(new Error('Launcher did not announce its sign-in URL')), 15_000);
    server.stdout!.on('data', data => {
      output += data.toString();
      const match = output.match(/http:\/\/127\.0\.0\.1:\d+\/#session=[A-Za-z0-9_-]+/);
      if (match) { clearTimeout(timeout); resolve(match[0]); }
    });
    server.on('error', reject);
    server.on('exit', code => { clearTimeout(timeout); reject(new Error(`Launcher exited: ${code}`)); });
  });
});

test.afterAll(async () => {
  if (process.env.DOCKYARD_INTEGRATION === '1') {
    execFileSync(binary, ['--data-dir', profile, 'lab', 'clean', 'm01-processes', '--yes']);
  }
  if (server && server.exitCode === null) { server.kill('SIGINT'); await once(server, 'exit'); }
});

test('installed workbench teaches, remembers observations, and handles real lab lifecycle', async ({ page }) => {
  const failures: string[] = [];
  page.on('pageerror', error => failures.push(error.message));
  await page.goto(url);
  await expect(page.getByRole('heading', { name: 'Build understanding. Then build the system.' })).toBeVisible();
  expect(page.url()).not.toContain('session=');
  await page.getByRole('button', { name: 'Start learning' }).click();
  await expect(page.getByRole('heading', { name: 'A container is a running process', exact: true })).toBeVisible();
  const understand = page.getByRole('tab', { name: 'Understand' });
  await understand.focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('tab', { name: 'Your task' })).toBeFocused();
  await page.getByRole('button', { name: 'Reveal hint 1' }).click();
  await expect(page.getByText('HINT 1', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Reveal reference', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button', { name: 'Keep working' }).click();
  await expect(page.getByRole('dialog')).not.toBeVisible();
  const notes = page.getByRole('textbox', { name: 'Notes for this lesson' });
  await notes.fill('The process and its published port are separate observations.');
  await page.getByRole('button', { name: 'Save observations' }).click();
  await page.reload();
  await page.getByRole('button', { name: 'Continue lesson' }).click();
  await expect(notes).toHaveValue('The process and its published port are separate observations.');
  for (const width of [760, 480]) {
    await page.setViewportSize({ width, height: 1000 });
    await expect(notes).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole('button', { name: 'Use light theme' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  if (process.env.DOCKYARD_INTEGRATION === '1') {
    await page.getByRole('button', { name: 'Prepare lab' }).click();
    await expect(page.getByRole('button', { name: 'Open in WezTerm' })).toBeEnabled();
    await page.getByRole('button', { name: 'Check work', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Here is what the lab observed.' })).toBeVisible();
    await page.getByRole('button', { name: 'Stop', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Resume', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Check work', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'The environment needs attention.' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Resume', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Resume', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Stop', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Reset', exact: true }).click();
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    await expect(page.getByText('Reset completed.', { exact: true })).toBeVisible();
  }
  await page.getByRole('textbox', { name: 'Search lessons' }).fill('reconciliation');
  await page.getByRole('button', { name: /Let a controller maintain the application/ }).click();
  const model = page.getByRole('region', { name: 'Explore reconciliation' });
  await model.getByRole('button', { name: 'Delete model Pod 1', exact: true }).click();
  await expect(model.getByRole('status')).toContainText('1 observed / 2 desired');
  await model.getByRole('button', { name: 'Advance controller' }).click();
  await expect(model.getByRole('status')).toContainText('Created Pod 3');
  await expect(model.getByRole('status')).toContainText('2 observed / 2 desired');
  await page.setViewportSize({ width: 480, height: 1000 });
  await model.scrollIntoViewIfNeeded();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(failures).toEqual([]);
  // Keep the browser and its SSE connection open while verifying foreground shutdown.
  const stopped = once(server, 'exit');
  server.kill('SIGINT');
  const result = await Promise.race([stopped, new Promise((_, reject) => setTimeout(() => reject(new Error('Launcher did not stop with an open event stream')), 8_000))]);
  expect(result).toEqual([0, null]);
});
