import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
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
  temporary = await mkdtemp(path.join(os.tmpdir(), 'dockyard-terminal-layout-'));
  server = spawn(path.join(root, '.runtime/installed/bin/dockyard'), ['--data-dir', temporary, 'launch', '--port', '0', '--no-open'], { cwd: root });
  url = await new Promise<string>((resolve, reject) => {
    let output = '';
    const timeout = setTimeout(() => reject(new Error('Terminal launcher did not become ready')), 15000);
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
test('active exam terminal controls remain usable in both themes and narrow layouts', async ({ page }) => {
  // Presentation fixture only; actual lab shell execution is covered by journey.spec.ts.
  await page.route('**/api/state', async route => {
    const response = await route.fetch();
    const state = await response.json();
    state.exams = [{ id: 'terminal-layout', exam_id: 'ckad-release', unit_id: 'exam-ckad-a', lab_id: 'layout', revision: 1, state: 'active', started_at: new Date().toISOString(), deadline: new Date(Date.now() + 3600000).toISOString(), selected_task: '', flagged: [], assessment_id: null, score: null, task_scores: {} }];
    await route.fulfill({ json: state });
  });
  await page.route('**/api/units/exam-ckad-a/terminal', route => route.fulfill({ json: {
    options: [{ id: 'terminal', label: 'Terminal' }, { id: 'iterm', label: 'iTerm2' }], selected: 'auto', automatic: 'Terminal', wsl: false,
    command: "'/home/learner/project with spaces/.runtime/installed/bin/python' -m dockyard --data-dir '/home/learner/long profile directory/dockyard' lab shell exam-ckad-a",
  } }));
  await page.route('**/api/events', route => route.abort());
  await page.goto(url);
  await page.getByRole('button', { name: 'Exam practice', exact: true }).click();
  await page.getByRole('button', { name: 'Continue timed attempt' }).click();
  const controls = page.getByRole('region', { name: 'Exam controls' });
  await expect(controls.getByRole('button', { name: 'Open terminal' })).toBeEnabled();
  await controls.getByText('Use an existing terminal', { exact: true }).click();
  for (const theme of ['dark', 'light']) {
    if (theme === 'light') await page.getByRole('button', { name: 'Use light theme' }).click();
    for (const width of [1440, 480]) {
      await page.setViewportSize({ width, height: 1000 });
      await expect(controls.getByRole('button', { name: 'Copy lab command' })).toBeVisible();
      await expect(controls.getByRole('button', { name: 'Submit attempt' })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await page.evaluate(async () => { await Promise.all(document.getAnimations().map(animation => animation.finished.catch(() => undefined))); });
      const scan = await new AxeBuilder({ page }).include('.exam-toolbar').withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      expect(scan.violations).toEqual([]);
      await controls.screenshot({ path: path.join(root, `.artifacts/terminals/exam-${theme}-${width}.png`) });
    }
  }
});
