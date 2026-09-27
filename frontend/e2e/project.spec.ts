import { test, expect } from '@playwright/test';
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '../..');
const cli = path.join(root, '.runtime/installed/bin/dockyard');
const python = path.join(root, '.runtime/installed/bin/python');
let temporary: string;
let server: ChildProcess;
let url: string;
test.skip(!process.env.DOCKYARD_PROJECT_INTEGRATION, 'Requires real Docker mission fixtures and the installed candidate.');
test.beforeAll(async () => {
  test.setTimeout(180000);
  temporary = await mkdtemp(path.join(os.tmpdir(), 'dockyard-project-'));
  execFileSync(python, ['-c', `from pathlib import Path
import sys,time
from dockyard.service import Service
from dockyard.workspace import write_files
from dockyard.process import run
s=Service(Path(sys.argv[1]));u='m01-mission'
s.perform(u,'prepare');l=s.store.lab(u);w=Path(l.workspace)
write_files(w,{**s.catalog.get(u).reference,'RUNBOOK.md':'My Dispatch process and recovery handoff.\\n'},overwrite=True)
r=run(['/bin/sh','run.sh'],cwd=w,env=s.environment(l),timeout=120);assert r.ok,r.stderr
for attempt in range(10):
 result=s.perform(u,'check')
 if result['status']=='pass':break
 time.sleep(0.5)
assert result['status']=='pass',result
s.perform(u,'clean')
`, temporary], { timeout: 150000 });
  server = spawn(cli, ['--data-dir', temporary, 'launch', '--port', '0', '--no-open'], { cwd: root });
  url = await new Promise<string>((resolve, reject) => {
    let output = '';
    const timeout = setTimeout(() => reject(new Error('Project launcher did not become ready')), 15000);
    server.stdout!.on('data', data => {
      output += data.toString();
      const match = output.match(/http:\/\/127\.0\.0\.1:\d+\/#session=[A-Za-z0-9_-]+/);
      if (match) { clearTimeout(timeout); resolve(match[0]); }
    });
    server.on('error', reject);
  });
});
test.afterAll(async () => {
  test.setTimeout(120000);
  if (server && server.exitCode === null) { server.kill('SIGINT'); await once(server, 'exit'); }
  if (temporary) {
    execFileSync(python, ['-c', `from pathlib import Path
import sys
from dockyard.service import Service
s=Service(Path(sys.argv[1]))
for lab in s.store.labs():s.perform(lab.unit_id,'clean')
`, temporary], { timeout: 100000 });
    await rm(temporary, { recursive: true, force: true });
  }
});
test('a real mission checkpoint continues into an intact later scaffold and exports both missions', async ({ page }) => {
  test.setTimeout(180000);
  const failures: string[] = [];
  page.on('pageerror', error => failures.push(error.message));
  await page.goto(url);
  await page.getByRole('button', { name: 'Project checkpoints', exact: true }).click();
  await page.getByText('Continue in a later mission', { exact: true }).click();
  await page.getByLabel('Later mission').selectOption('m02-mission');
  await page.getByRole('button', { name: 'Compare source' }).click();
  const preview = page.getByRole('region', { name: 'Checkpoint source comparison' });
  await expect(preview).toContainText('Mission: a portable Dispatch release');
  await expect(preview.getByRole('checkbox', { checked: true })).toHaveCount(0);
  await preview.getByRole('checkbox', { name: /RUNBOOK.md/ }).check();
  await preview.getByText('Review source differences').last().click();
  for (const width of [1440, 480]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await page.screenshot({ path: path.join(root, `.artifacts/project-comparison-${width}.png`), fullPage: true, animations: 'disabled' });
  }
  await page.getByRole('button', { name: 'Carry 1 selected file forward' }).click();
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Mission: a portable Dispatch release', exact: true })).toBeVisible();
  execFileSync(python, ['-c', `from pathlib import Path
import sys,time
from dockyard.service import Service
from dockyard.workspace import write_files
from dockyard.process import run
s=Service(Path(sys.argv[1]));u='m02-mission';l=s.store.lab(u);w=Path(l.workspace)
assert l.state=='absent'
assert (w/'RUNBOOK.md').read_text()=='My Dispatch process and recovery handoff.\\n'
assert (w/'app.py').read_text()==s.catalog.get(u).starter['app.py']
s.perform(u,'prepare')
write_files(w,s.catalog.get(u).reference,overwrite=True)
r=run(['/bin/sh','run.sh'],cwd=w,env=s.environment(l),timeout=120);assert r.ok,r.stderr
for attempt in range(10):
 result=s.perform(u,'check')
 if result['status']=='pass':break
 time.sleep(0.5)
assert result['status']=='pass',result
assert len(s.store.checkpoints())==2
`, temporary], { timeout: 150000 });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.reload();
  await page.getByRole('button', { name: 'Project checkpoints', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Download checkpoint' })).toHaveCount(2);
  const downloaded = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Export project portfolio' }).click();
  const archive = path.join(temporary, 'portfolio.zip');
  await (await downloaded).saveAs(archive);
  execFileSync(python, ['-c', `import sys,json
from zipfile import ZipFile
with ZipFile(sys.argv[1]) as z:
 assert json.loads(z.read('manifest.json'))['missions']==2
 assert z.read('missions/m02-mission/source/RUNBOOK.md')==b'My Dispatch process and recovery handoff.\\n'
 assert json.loads(z.read('missions/m02-mission/evidence.json'))['status']=='pass'
`, archive]);
  expect(failures).toEqual([]);
});
