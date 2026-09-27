import { test, expect } from '@playwright/test';
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, rm, readFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '../..');
const cli = path.join(root, '.runtime/installed/bin/dockyard');
const python = path.join(root, '.runtime/installed/bin/python');
let temporary: string;
let server: ChildProcess;
let url: string;
let archive: string;
test.skip(!process.env.DOCKYARD_INTEGRATION, 'Requires the installed release candidate.');
test.beforeAll(async () => {
  temporary = await mkdtemp(path.join(os.tmpdir(), 'dockyard-portability-'));
  const source = path.join(temporary, 'source');
  const destination = path.join(temporary, 'browser');
  archive = path.join(temporary, 'source.zip');
  execFileSync(python, ['-c', `from pathlib import Path
import sys
from dockyard.service import Service
s = Service(Path(sys.argv[1]))
s.store.save_note('m01-processes', 'My portable process observation.')
s.store.mark('m01-processes', 'viewed', 1)
`, source]);
  execFileSync(cli, ['--data-dir', source, 'progress', 'export', archive]);
  server = spawn(cli, ['--data-dir', destination, 'launch', '--port', '0', '--no-open'], { cwd: root });
  url = await new Promise<string>((resolve, reject) => {
    let output = '';
    const timeout = setTimeout(() => reject(new Error('Portable profile launcher did not become ready')), 15000);
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
test('installed CLI and browser exchange portable history through a reviewed merge', async ({ page }) => {
  const failures: string[] = [];
  page.on('pageerror', error => failures.push(error.message));
  await page.goto(url);
  await page.getByRole('button', { name: 'Settings and data', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Keep your work yours.' })).toBeVisible();
  await page.getByLabel('Choose a Dockyard progress archive').setInputFiles(archive);
  const preview = page.getByRole('region', { name: 'Progress import preview' });
  await expect(preview).toContainText('source.zip');
  const noteURL = new URL('/api/units/m01-processes', page.url()).toString();
  const before = await page.request.get(noteURL).then(r => r.json());
  expect(before.note).not.toBe('My portable process observation.');
  await page.getByRole('button', { name: 'Light workbench', exact: true }).click();
  for (const width of [1440, 480]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: path.join(root, `.artifacts/portability-preview-${width}.png`), fullPage: true, animations: 'disabled' });
  }
  await page.getByRole('button', { name: 'Merge reviewed archive' }).click();
  await expect(page.getByRole('dialog')).toContainText('backs up the progress database');
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Progress import result' })).toContainText('Your current work is preserved.');
  const state = await page.request.get(new URL('/api/state', page.url()).toString()).then(r => r.json());
  expect(state.labs).toEqual([]);
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Export progress archive' }).click();
  const downloaded = await downloadPromise;
  const result = path.join(temporary, 'browser-export.zip');
  await downloaded.saveAs(result);
  expect((await readFile(result)).byteLength).toBeGreaterThan(100);
  const cliProfile = path.join(temporary, 'cli-restored');
  const review = execFileSync(cli, ['--data-dir', cliProfile, 'progress', 'import', result], { encoding: 'utf8' });
  expect(review).toContain('"notes": 1');
  execFileSync(cli, ['--data-dir', cliProfile, 'progress', 'import', result, '--yes']);
  const note = execFileSync(python, ['-c', `from pathlib import Path
import sys
from dockyard.service import Service
s = Service(Path(sys.argv[1]))
assert not s.store.labs()
print(s.store.note('m01-processes'))
`, cliProfile], { encoding: 'utf8' });
  expect(note.trim()).toBe('My portable process observation.');
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole('button', { name: 'Lab manager', exact: true }).click();
  await page.getByRole('button', { name: 'Inspect cache', exact: true }).click();
  const cache = page.getByRole('region', { name: 'Dependency cache' });
  await expect(cache).toContainText('5 / 5');
  await page.getByRole('button', { name: 'Prefetch dependencies', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Inspect cache', exact: true })).toBeEnabled({ timeout: 30000 });
  await cache.getByText('Readiness for each selected activity').click();
  await expect(cache.locator('.cache-activities article')).toHaveCount(5);
  for (const width of [1440, 480]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: path.join(root, `.artifacts/cache-manager-${width}.png`), fullPage: true, animations: 'disabled' });
  }
  expect(failures).toEqual([]);
});
