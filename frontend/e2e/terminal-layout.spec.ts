import { releaseProfile } from './profiles';
import { navigateTo } from './navigation';
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { spawn, type ChildProcess } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp } from 'node:fs/promises';
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
  if (temporary) releaseProfile(temporary);
});
test('an active exam keeps its tasks beside the lab terminal in both themes and narrow layouts', async ({ page }) => {
  // Presentation fixture only; real embedded shells are covered by journey.spec.ts.
  const now = new Date().toISOString();
  await page.route('**/api/state', async route => {
    const response = await route.fetch();
    const state = await response.json();
    state.exams = [{ id: 'terminal-layout', exam_id: 'ckad-release', unit_id: 'exam-ckad-a', lab_id: 'layout', revision: 1, state: 'active', started_at: now, deadline: new Date(Date.now() + 3600000).toISOString(), selected_task: '', flagged: [], assessment_id: null, score: null, task_scores: {} }];
    state.labs = [{ id: 'f'.repeat(32), unit_id: 'exam-ckad-a', revision: 1, runtime: 'kubernetes', state: 'preparing', workspace: '/home/learner/long profile directory/dockyard/labs/exam-ckad-a/workspace', created_at: now, updated_at: now, error: null, resources: { stage: 'Starting the exam cluster' } }];
    state.consoles = [];
    await route.fulfill({ json: state });
  });
  await page.route('**/api/events', route => route.abort());
  await page.goto(url);
  await navigateTo(page, 'Exam practice');
  await page.getByRole('button', { name: 'Continue timed attempt' }).click();
  const controls = page.getByRole('region', { name: 'Exam controls' });
  const dock = page.getByRole('region', { name: 'Lab terminal' });
  await expect(dock.getByText('Starting the exam cluster')).toBeVisible();
  await dock.getByRole('button', { name: 'Terminal and lab options' }).click();
  const options = page.getByRole('dialog', { name: 'Terminal and lab options' });
  await expect(options.getByRole('button', { name: 'Reset lab' })).toBeVisible();
  await options.getByText('Use your own terminal', { exact: true }).click();
  // The external launcher waits for the lab; journey.spec.ts exercises it on a real one.
  await expect(options.getByText('Preparing your lab…')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(options).toHaveCount(0);
  const show = page.getByRole('group', { name: 'Show' });
  for (const theme of ['dark', 'light']) {
    if (theme === 'light') await page.getByRole('button', { name: 'Use light theme' }).click();
    for (const width of [1440, 480]) {
      await page.setViewportSize({ width, height: 1000 });
      if (width < 1000) await show.getByRole('button', { name: /Lesson/ }).click();
      await expect(controls.getByRole('button', { name: 'Submit attempt' })).toBeVisible();
      if (width < 1000) await show.getByRole('button', { name: /Terminal/ }).click();
      await expect(dock.getByText('Starting the exam cluster')).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      // The preparing spinner loops forever, so wait only for animations that end.
      await page.evaluate(async () => { await Promise.all(document.getAnimations().filter(animation => animation.effect?.getTiming().iterations !== Infinity).map(animation => animation.finished.catch(() => undefined))); });
      const scan = await new AxeBuilder({ page }).include('.workspace').withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      expect(scan.violations).toEqual([]);
      await page.screenshot({ path: path.join(root, `.artifacts/terminals/exam-${theme}-${width}.png`) });
    }
  }
});
