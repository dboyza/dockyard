import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { spawn, type ChildProcess } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '../..');
let temporary: string;
let server: ChildProcess;
let url: string;
test.beforeAll(async () => {
  temporary = await mkdtemp(path.join(os.tmpdir(), 'dockyard-accessibility-'));
  server = spawn(path.join(root, '.runtime/installed/bin/dockyard'), ['--data-dir', temporary, 'launch', '--port', '0', '--no-open'], { cwd: root });
  url = await new Promise<string>((resolve, reject) => {
    let output = '';
    const timeout = setTimeout(() => reject(new Error('Accessibility launcher did not become ready')), 15000);
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
test('all workbench destinations and lesson interactions meet automated accessibility checks', async ({ page }) => {
  test.setTimeout(300000);
  await page.goto(url);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  const failures: { screen: string; id: string; impact: string | null | undefined; nodes: string[][] }[] = [];
  const scan = async (screen: string) => {
    await page.evaluate(async () => { await Promise.all(document.getAnimations().map(animation => animation.finished.catch(() => undefined))); });
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    failures.push(...results.violations.map(issue => ({ screen, id: issue.id, impact: issue.impact, nodes: issue.nodes.map(node => node.target as string[]) })));
    await writeFile(path.join(root, ".artifacts/accessibility.json"), JSON.stringify(failures, null, 2));
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  };
  for (const theme of ['dark', 'light']) {
    if (theme === 'light') await page.getByRole('button', { name: 'Use light theme' }).click();
    for (const destination of ['Overview', 'Your course', 'Practical placement', 'Incident scenarios', 'Exam practice', 'Skill evidence', 'Spaced review', 'Project checkpoints', 'Lab manager', 'Reference desk', 'Settings and data']) {
      await page.getByRole('button', { name: destination, exact: true }).click();
      await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
      await scan(`${theme}/${destination}`);
    }
    await page.getByRole('button', { name: 'Your course', exact: true }).click();
    await page.getByRole('textbox', { name: 'Search lessons' }).fill('m01-processes');
    await page.getByRole('button', { name: /A container is a running process/ }).click();
    await scan(`${theme}/lesson`);
    if (theme === 'dark') {
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
      await page.screenshot({ path: path.join(root, 'docs/assets/workbench.png'), animations: 'disabled' });
    }
    await page.getByRole('tab', { name: 'Your task' }).click();
    await page.getByRole('button', { name: 'Reveal reference', exact: true }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await scan(`${theme}/confirmation`);
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).not.toBeVisible();
  }
  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (const width of [760, 480, 320]) {
    await page.setViewportSize({ width, height: 800 });
    await scan(`narrow/${width}/lesson`);
  }
  await writeFile(path.join(root, '.artifacts/accessibility.json'), JSON.stringify(failures, null, 2));
  expect(failures).toEqual([]);
});
