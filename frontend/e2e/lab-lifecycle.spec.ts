import { releaseProfile } from './profiles';
import { navigateTo } from './navigation';
import { test, expect, type BrowserContext, type Page } from '@playwright/test';
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync } from 'node:fs';
import { once } from 'node:events';
import path from 'node:path';

// A learner's whole lab lifecycle through the embedded terminal, on the installed app and real runtimes.
// Terminal text is drawn on a canvas, so each shell proves its work by writing files and changing Docker.
const root = path.resolve(import.meta.dirname, '../..');
test.skip(process.env.DOCKYARD_INTEGRATION !== '1', 'Requires the installed app and local Docker.');
test.describe.configure({ mode: 'serial' });
let server: ChildProcess;
let url: string;
// The sign-in link works once, so both tests share one signed-in browser context.
let context: BrowserContext;
let page: Page;
let profile: string;
let proof: string;

test.beforeAll(async ({ browser }) => {
  mkdirSync(path.join(root, '.runtime/e2e'), { recursive: true });
  profile = mkdtempSync(path.join(root, '.runtime/e2e/lifecycle-'));
  proof = path.join(profile, 'proof');
  mkdirSync(proof);
  server = spawn(path.join(root, '.runtime/installed/bin/dockyard'), ['--data-dir', profile, 'launch', '--port', '0', '--no-open'], { cwd: root });
  url = await new Promise<string>((resolve, reject) => {
    let output = '';
    const timeout = setTimeout(() => reject(new Error('Launcher did not announce its sign-in URL')), 15_000);
    server.stdout!.on('data', data => {
      output += data.toString();
      const match = output.match(/http:\/\/127\.0\.0\.1:\d+\/#session=[A-Za-z0-9_-]+/);
      if (match) { clearTimeout(timeout); resolve(match[0]); }
    });
    server.on('error', reject);
  });
  context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  page = await context.newPage();
  await page.goto(url);
  await expect(page.getByRole('button', { name: 'Start learning', exact: true })).toBeVisible();
});
test.afterAll(async () => {
  await context?.close();
  if (server && server.exitCode === null) { server.kill('SIGINT'); await once(server, 'exit'); }
  if (profile) releaseProfile(profile);
});

type Console = { id: string; unit_id: string; lab_id: string; number: number; alive: boolean };
type Lab = { id: string; unit_id: string; state: string };
const state = async (page: Page) =>
  (await (await page.request.get(new URL('/api/state', url).toString())).json()) as { consoles: Console[]; labs: Lab[] };
const live = async (page: Page, unit: string) => (await state(page)).consoles.filter(item => item.unit_id === unit && item.alive);
const read = (name: string) => { try { return readFileSync(path.join(proof, name), 'utf8').trim(); } catch { return ''; } };
const owned = (lab: string) => execFileSync('docker', ['ps', '-aq', '--filter', `label=io.dockyard.lab=${lab}`], { encoding: 'utf8' }).trim();

function workbench(page: Page) {
  const dock = page.getByRole('region', { name: 'Lab terminal' });
  const options = page.getByRole('dialog', { name: 'Terminal and lab options' });
  return {
    dock,
    async type(command: string) {
      await dock.locator('.console-view:not([hidden]) .xterm-helper-textarea').focus();
      await page.keyboard.type(command + '\n');
    },
    // Writes the current shell's process ID, which identifies the shell across reloads.
    async shell(name: string) {
      await this.type(`echo $$ > ${proof}/${name}`);
      await expect.poll(() => read(name), { timeout: 15_000 }).toMatch(/^\d+$/);
      return read(name);
    },
    async option(name: string) {
      await dock.getByRole('button', { name: 'Terminal and lab options' }).click();
      await options.getByRole('button', { name, exact: true }).click();
    },
    async ready() {
      await expect(dock.getByRole('tab', { name: /^Terminal 1/ })).toBeVisible({ timeout: 60_000 });
      await expect(dock.getByText('Starting shell')).toHaveCount(0, { timeout: 20_000 });
    },
  };
}

test('a Docker lab starts beside its task, survives everything in between, and closes', async () => {
  test.setTimeout(300_000);
  const lab = workbench(page);
  const task = page.getByRole('tab', { name: 'Your task' });

  await test.step('start the first lab from the course', async () => {
    await page.getByRole('button', { name: 'Start learning', exact: true }).click();
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Your first container');
    await expect(page.getByRole('tab', { name: 'Understand' })).toHaveAttribute('aria-selected', 'true');
    await page.getByRole('button', { name: 'Prepare lab' }).click();
    await lab.ready();
    await expect(task).toHaveAttribute('aria-selected', 'true');
    await expect(page.locator('.lab-bar')).toContainText('Ready');
    expect(await live(page, 'm00-first-container')).toHaveLength(1);
  });

  await test.step('complete the task by typing in the terminal', async () => {
    await lab.type(`printf '%s|%s' "$DOCKYARD_UNIT" "$PWD" > ${proof}/where`);
    await expect.poll(() => read('where')).toMatch(/^m00-first-container\|.*\/workspace$/);
    await lab.type(`docker run --name "$DOCKYARD_CONTAINER" --label "io.dockyard.lab=$DOCKYARD_LAB" "$DOCKYARD_PYTHON_IMAGE" python -c "print('Hello from inside a container')"`);
    await lab.type(`docker ps -a --filter "name=$DOCKYARD_CONTAINER" --format '{{.Status}}' > ${proof}/status`);
    await expect.poll(() => read('status'), { timeout: 60_000 }).toMatch(/^Exited \(0\)/);
    await page.getByRole('button', { name: 'Check work', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'The required behavior passed this check.' })).toBeVisible();
  });

  const first = await lab.shell('pid-first');
  await test.step('the shell survives leaving the page and reloading', async () => {
    await navigateTo(page, 'Overview');
    await expect(lab.dock).toHaveCount(0);
    await page.getByRole('button', { name: 'Continue lesson' }).click();
    await lab.ready();
    await expect(task).toHaveAttribute('aria-selected', 'true');
    await expect(lab.dock.getByRole('tab')).toHaveCount(1);
    expect(await lab.shell('pid-after-visit')).toBe(first);
    await page.reload();
    await lab.ready();
    await expect(lab.dock.getByRole('tab')).toHaveCount(1);
    expect(await lab.shell('pid-after-reload')).toBe(first);
  });

  await test.step('open, switch, and close several shells', async () => {
    await lab.dock.getByRole('button', { name: 'Open another shell' }).click();
    await expect(lab.dock.getByRole('tab')).toHaveCount(2);
    await expect(lab.dock.getByRole('tab', { name: /^Terminal 2/ })).toHaveAttribute('aria-selected', 'true');
    await expect(lab.dock.getByText('Starting shell')).toHaveCount(0, { timeout: 20_000 });
    expect(await lab.shell('pid-second')).not.toBe(first);
    await lab.dock.getByRole('tab', { name: /^Terminal 2/ }).locator('.dock-close').click();
    await expect(lab.dock.getByRole('tab')).toHaveCount(1);
    await lab.dock.getByRole('button', { name: 'Open another shell' }).click();
    await expect(lab.dock.getByRole('tab')).toHaveCount(2);
    await lab.dock.getByRole('tab', { name: /^Terminal 2/ }).focus();
    await page.keyboard.press('Delete');
    await expect(lab.dock.getByRole('tab')).toHaveCount(1);
    await expect.poll(async () => (await live(page, 'm00-first-container')).length).toBe(1);
    expect(await lab.shell('pid-still-first')).toBe(first);
  });

  await test.step('an exited shell can be closed or replaced', async () => {
    await lab.type('exit 3');
    await expect(lab.dock.getByText('The shell exited with code 3.')).toBeVisible();
    await lab.dock.getByRole('button', { name: 'Close tab' }).click();
    await expect(lab.dock.getByText('No shell is open')).toBeVisible();
    await lab.dock.getByRole('button', { name: 'Open a shell' }).click();
    await lab.ready();
    await lab.type('exit');
    await expect(lab.dock.getByText('The shell exited.')).toBeVisible();
    await lab.dock.getByRole('button', { name: 'New shell' }).click();
    await expect(lab.dock.getByRole('tab')).toHaveCount(2);
    await expect(lab.dock.getByText('Starting shell')).toHaveCount(0, { timeout: 20_000 });
    expect(await lab.shell('pid-replacement')).not.toBe(first);
    await lab.dock.getByRole('tab', { name: /^Terminal 1/ }).focus();
    await page.keyboard.press('Delete');
    await expect(lab.dock.getByRole('tab')).toHaveCount(1);
  });

  await test.step('stop and resume keep the shell', async () => {
    const before = await lab.shell('pid-before-stop');
    await lab.option('Stop lab');
    await expect(lab.dock.getByRole('button', { name: 'Resume', exact: true })).toBeVisible();
    await expect(page.locator('.lab-bar')).toContainText('Stopped');
    expect(await lab.shell('pid-while-stopped')).toBe(before);
    await lab.dock.getByRole('button', { name: 'Resume', exact: true }).click();
    await expect(lab.dock.getByRole('button', { name: 'Resume', exact: true })).toHaveCount(0);
    await expect(page.locator('.lab-bar')).toContainText('Ready');
    expect(await lab.shell('pid-after-resume')).toBe(before);
  });

  await test.step('reset replaces the shell and restores the starter', async () => {
    const before = read('pid-after-resume');
    const labId = (await state(page)).labs.find(item => item.unit_id === 'm00-first-container')!.id;
    expect(owned(labId)).not.toBe('');
    await lab.option('Reset lab');
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    await expect(page.getByText('Reset completed.', { exact: true })).toBeVisible({ timeout: 60_000 });
    await expect(lab.dock.getByRole('tab')).toHaveCount(1);
    await expect(lab.dock.locator('.dock-tab .dock-dot.live')).toHaveCount(1);
    await expect(lab.dock.getByText('Starting shell')).toHaveCount(0, { timeout: 20_000 });
    expect(await lab.shell('pid-after-reset')).not.toBe(before);
    expect(owned(labId)).toBe('');
    await page.getByRole('button', { name: 'Check work', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Here is what the lab observed.' })).toBeVisible();
  });

  await test.step('layout controls keep the shell usable', async () => {
    await lab.dock.getByRole('button', { name: 'Maximize the terminal' }).click();
    await expect(page.locator('.workspace-lesson')).toBeHidden();
    await lab.dock.getByRole('button', { name: 'Show the lesson' }).click();
    await expect(page.locator('.workspace-lesson')).toBeVisible();
    await lab.dock.getByRole('button', { name: 'Hide the terminal' }).click();
    await expect(lab.dock).toBeHidden();
    await page.getByRole('button', { name: /Show the terminal, 1 shell open/ }).click();
    await expect(lab.dock).toBeVisible();
    await page.locator('.workspace-lesson').focus();
    await page.keyboard.press('Control+Backquote');
    await expect(lab.dock.locator('.xterm-helper-textarea').first()).toBeFocused();
    await page.setViewportSize({ width: 480, height: 900 });
    await page.getByRole('group', { name: 'Show' }).getByRole('button', { name: /Lesson/ }).click();
    await expect(page.getByRole('button', { name: 'Check work', exact: true })).toBeVisible();
    await page.getByRole('group', { name: 'Show' }).getByRole('button', { name: /Terminal/ }).click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const narrow = await lab.shell('pid-narrow');
    await page.setViewportSize({ width: 1440, height: 1000 });
    expect(await lab.shell('pid-wide')).toBe(narrow);
  });

  await test.step('two tabs preparing the same lab share one shell', async () => {
    const other = await context.newPage();
    for (const view of [page, other]) {
      await view.goto(new URL('/#/lesson/m00-layers', url).toString());
      await expect(view.getByRole('heading', { level: 1 })).toHaveText(/./);
    }
    await page.getByRole('button', { name: 'Prepare lab' }).click();
    await lab.ready();
    await workbench(other).ready();
    await page.waitForTimeout(2000);
    expect(await live(page, 'm00-layers')).toHaveLength(1);
    await expect(other.getByRole('region', { name: 'Lab terminal' }).getByRole('tab')).toHaveCount(1);
    await other.close();
  });

  await test.step('cleanup closes the lab and its shells', async () => {
    for (const unit of ['m00-layers', 'm00-first-container']) {
      await page.goto(new URL(`/#/lesson/${unit}`, url).toString());
      await lab.ready();
      const labId = (await state(page)).labs.find(item => item.unit_id === unit)!.id;
      await lab.option('Clean up lab');
      await expect(page.getByRole('dialog')).toContainText('closes its shells');
      await page.getByRole('button', { name: 'Continue', exact: true }).click();
      await expect(page.getByText('Lab cleaned up.', { exact: true })).toBeVisible({ timeout: 60_000 });
      await expect(lab.dock).toHaveCount(0);
      await expect(page.getByRole('button', { name: 'Prepare lab' })).toBeEnabled();
      expect(await live(page, unit)).toHaveLength(0);
      expect(owned(labId)).toBe('');
    }
  });

  await test.step('a cleaned lab starts again', async () => {
    await page.getByRole('button', { name: 'Prepare lab' }).click();
    await lab.ready();
    await expect(task).toHaveAttribute('aria-selected', 'true');
    await lab.type(`printf '%s' "$DOCKYARD_UNIT" > ${proof}/again`);
    await expect.poll(() => read('again')).toBe('m00-first-container');
  });
});

test('a Kubernetes lab starts a cluster, runs kubectl in the terminal, stops, resumes, and closes', async () => {
  test.setTimeout(900_000);
  const lab = workbench(page);
  await page.goto(new URL('/#/lesson/m07-inspection', url).toString());
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Labels, selectors, and namespaces');
  await page.getByRole('button', { name: 'Prepare lab' }).click();
  await expect(lab.dock.getByText(/Preparing the Kubernetes lab/)).toBeVisible();
  await expect(lab.dock.getByRole('tab', { name: /^Terminal 1/ })).toBeVisible({ timeout: 840_000 });
  await lab.ready();
  await expect(page.getByRole('tab', { name: 'Your task' })).toHaveAttribute('aria-selected', 'true');
  await expect(lab.dock.locator('.dock-lab')).toContainText('Kubernetes lab');
  await lab.type(`kubectl get nodes -o name > ${proof}/nodes; echo "$KUBECONFIG" > ${proof}/kubeconfig`);
  await expect.poll(() => read('nodes'), { timeout: 60_000 }).toMatch(/^node\//);
  expect(read('kubeconfig')).toContain(path.join(profile, 'labs'));
  const shell = await lab.shell('pid-kubernetes');
  await lab.option('Stop lab');
  await expect(lab.dock.getByRole('button', { name: 'Resume', exact: true })).toBeVisible({ timeout: 300_000 });
  await lab.dock.getByRole('button', { name: 'Resume', exact: true }).click();
  await expect(page.locator('.lab-bar')).toContainText('Ready', { timeout: 300_000 });
  expect(await lab.shell('pid-kubernetes-resumed')).toBe(shell);
  await lab.type(`kubectl get nodes -o name > ${proof}/nodes-resumed`);
  await expect.poll(() => read('nodes-resumed'), { timeout: 120_000 }).toMatch(/^node\//);
  await lab.option('Clean up lab');
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByText('Lab cleaned up.', { exact: true })).toBeVisible({ timeout: 300_000 });
  await expect(lab.dock).toHaveCount(0);
  expect(await live(page, 'm07-inspection')).toHaveLength(0);
});
