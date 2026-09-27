import { test, expect } from '@playwright/test';
import { spawn, type ChildProcess } from 'node:child_process';
import { once } from 'node:events';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '../..');
let server: ChildProcess;
let url: string;
test.skip(!process.env.DOCKYARD_EXAM_PROFILE, 'Requires an explicitly prepared disposable exam profile.');
test.beforeAll(async () => {
  server = spawn(path.join(root, '.runtime/installed/bin/dockyard'), ['--data-dir', process.env.DOCKYARD_EXAM_PROFILE!, 'launch', '--port', '0', '--no-open'], { cwd: root });
  url = await new Promise<string>((resolve, reject) => {
    let output = '';
    const timeout = setTimeout(() => reject(new Error('Exam launcher did not become ready')), 15000);
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
});
test('installed timed practice persists flags and deadline and reports actual runtime evidence', async ({ page }) => {
  test.setTimeout(180000);
  const failures: string[] = [];
  page.on('pageerror', error => failures.push(error.message));
  await page.goto(url);
  await page.getByRole('button', { name: 'Exam practice', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Work against a clear deadline.' })).toBeVisible();
  await expect(page.getByRole('button', { name: /^(Open practice|Continue timed attempt)$/ })).toHaveCount(4);
  await page.getByRole('article').filter({ has: page.getByRole('heading', { name: 'Dispatch release assessment', exact: true }) }).getByRole('button', { name: /^(Open practice|Continue timed attempt)$/ }).click();
  if (await page.getByRole('button', { name: 'Start 120-minute attempt' }).isVisible()) {
    await expect(page.getByRole('button', { name: 'Start 120-minute attempt' })).toBeEnabled();
    await page.getByRole('button', { name: 'Start 120-minute attempt' }).click();
  }
  await expect(page.getByRole('button', { name: 'Submit attempt' })).toBeVisible();
  if (await page.getByRole('button', { name: 'Flag for review', exact: true }).isVisible()) await page.getByRole('button', { name: 'Flag for review', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Flagged for review' })).toHaveAttribute('aria-pressed','true');
  const before = await page.request.get(new URL('/api/state', page.url()).toString()).then(r => r.json());
  const attempt = before.exams[0];
  expect(attempt.state).toBe('active');
  const blocked = await page.request.post(new URL('/api/units/exam-ckad-a/reference', page.url()).toString(), { headers: { 'X-Dockyard': '1', Origin: new URL(page.url()).origin }, data: { action: 'reference', confirmed: true } });
  expect(blocked.status()).toBe(409);
  await page.reload();
  await page.getByRole('button', { name: 'Exam practice', exact: true }).click();
  await page.getByRole('button', { name: 'Continue timed attempt' }).click();
  await expect(page.getByRole('button', { name: 'Flagged for review' })).toHaveAttribute('aria-pressed','true');
  const after = await page.request.get(new URL('/api/state', page.url()).toString()).then(r => r.json());
  expect(after.exams[0].deadline).toBe(attempt.deadline);
  for (const width of [1440, 760, 480]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: path.join(root, `.artifacts/exam-active-${width}.png`), fullPage: true, animations: 'disabled' });
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole('button', { name: 'Submit attempt' }).click();
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  const report = page.getByRole('region', { name: 'Exam report' });
  await expect(report.getByRole('heading', { name: '100 / 100', exact: true })).toBeVisible({ timeout: 90000 });
  await expect(page.getByRole('button', { name: 'Start 120-minute attempt' })).toBeDisabled();
  await page.getByRole('navigation', { name: 'Exam tasks' }).getByRole('button').nth(3).click();
  await expect(page.getByRole('heading', { name: 'Observed evidence', exact: true })).toBeVisible();
  await page.locator('.exam-evidence summary').click();
  await expect(page.locator('.exam-evidence[open]')).toContainText('true');
  await page.getByRole('button', { name: 'Use light theme' }).click();
  await page.screenshot({ path: path.join(root, '.artifacts/exam-report-light.png'), fullPage: true, animations: 'disabled' });
  await page.getByRole('button', { name: 'Review reference solution' }).click();
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Reference solution', exact: true })).toBeVisible();
  expect(failures).toEqual([]);
});

test('saved exam reports remain readable after environment cleanup', async ({ page }) => {
  await page.goto(url);
  await page.getByRole('button', { name: 'Exam practice', exact: true }).click();
  await page.getByRole('article').filter({ has: page.getByRole('heading', { name: 'Dispatch release assessment', exact: true }) }).getByRole('button', { name: 'Open practice' }).click();
  const report = page.getByRole('region', { name: 'Exam report' });
  await expect(report.getByRole('heading', { name: '100 / 100', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Start 120-minute attempt' })).toBeDisabled();
  const history = page.getByRole('combobox', { name: 'Saved exam attempt' });
  await history.selectOption({ index: 1 });
  await expect(report.getByRole('heading', { name: 'No score assigned', exact: true })).toBeVisible();
  await history.selectOption({ index: 0 });
  await expect(report.getByRole('heading', { name: '100 / 100', exact: true })).toBeVisible();
  if (await page.getByRole('button', { name: 'Use light theme' }).isVisible()) await page.getByRole('button', { name: 'Use light theme' }).click();
  await expect.poll(() => page.getByRole('button', { name: 'Review reference solution' }).evaluate(element => getComputedStyle(element).backgroundColor)).toBe('rgb(234, 240, 247)');
  for (const width of [1440, 480]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: path.join(root, `.artifacts/exam-saved-report-${width}.png`), fullPage: true, animations: 'disabled' });
  }
});
