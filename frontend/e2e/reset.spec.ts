import { releaseProfile } from './profiles';
import { navigateTo } from './navigation';
import { test, expect } from '@playwright/test';
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '../..');
const cli = path.join(root, '.runtime/installed/bin/dockyard');
const python = path.join(root, '.runtime/installed/bin/python');
let temporary: string;
let server: ChildProcess;
let url: string;
test.skip(!process.env.DOCKYARD_INTEGRATION, 'Requires the installed app and local Docker.');
test.beforeAll(async () => {
  temporary = await mkdtemp(path.join(os.tmpdir(), 'dockyard-reset-'));
  execFileSync(python, ['-c', `from pathlib import Path
import sys
from dockyard.service import Service
s = Service(Path(sys.argv[1]))
s.store.save_note('m01-processes', 'A note that should be erased.')
s.store.mark('m01-processes', 'viewed', 1)
s.store.set_setting('theme', 'light')
`, temporary]);
  execFileSync(cli, ['--data-dir', temporary, 'lab', 'prepare', 'm01-processes']);
  server = spawn(cli, ['--data-dir', temporary, 'launch', '--port', '0', '--no-open'], { cwd: root });
  url = await new Promise<string>((resolve, reject) => {
    let output = '';
    const timeout = setTimeout(() => reject(new Error('Launcher did not become ready')), 15000);
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
test('start fresh cleans every lab, erases learning data, and keeps the theme', async ({ page }) => {
  const failures: string[] = [];
  page.on('pageerror', error => failures.push(error.message));
  await page.goto(url);
  await navigateTo(page, 'Settings and data');
  const panel = page.getByRole('region', { name: 'Start fresh' });
  await expect(panel).toContainText('Kept:');
  for (const theme of ['Dark', 'Light']) {
    await page.getByRole('button', { name: theme, exact: true }).click();
    await panel.screenshot({ path: path.join(root, `.artifacts/reset-panel-${theme.toLowerCase()}.png`), animations: 'disabled' });
  }
  await panel.getByRole('button', { name: 'Erase all local data' }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toContainText('First, 1 lab is cleaned up');
  await expect(dialog).toContainText('1 activity, 0 check results, 0 exam attempts, 1 note');
  const erase = dialog.getByRole('button', { name: 'Erase everything' });
  await expect(erase).toBeDisabled();
  await dialog.getByLabel('Type erase to confirm').fill('erase');
  await expect(erase).toBeEnabled();
  for (const width of [1440, 480]) {
    await page.setViewportSize({ width, height: 900 });
    await page.screenshot({ path: path.join(root, `.artifacts/reset-dialog-${width}.png`), animations: 'disabled' });
  }
  await erase.click();
  await expect(page.getByRole('status')).toContainText('Dockyard was reset.', { timeout: 120000 });
  const state = await page.request.get(new URL('/api/state', page.url()).toString()).then(r => r.json());
  expect(state.labs).toEqual([]);
  expect(state.progress).toEqual({});
  expect(state.theme).toBe('light');
  const unit = await page.request.get(new URL('/api/units/m01-processes', page.url()).toString()).then(r => r.json());
  expect(unit.note).toBe('');
  expect(execFileSync(cli, ['--data-dir', temporary, 'lab', 'status'], { encoding: 'utf8' })).toContain('No prepared labs.');
  expect(failures).toEqual([]);
});
