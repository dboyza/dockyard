import { test, expect } from '@playwright/test';
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { mkdtempSync, symlinkSync, unlinkSync } from 'node:fs';
import { createServer, type Socket } from 'node:net';
import { once } from 'node:events';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '../..');
const cli = path.join(root, '.runtime/installed/bin/dockyard');
const python = path.join(root, '.runtime/installed/bin/python');
test.skip(process.env.DOCKYARD_INTEGRATION !== '1', 'Requires the installed app and local Docker.');
test('port collision, unavailable Docker, cancellation, and concurrent clients recover', async ({ page, context }) => {
  test.setTimeout(90000);
  const profile = mkdtempSync('/private/tmp/dy-recovery-');
  const socketPath = path.join(profile, 'docker.sock');
  const realEndpoint = execFileSync('docker', ['context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'], { encoding: 'utf8' }).trim();
  expect(realEndpoint.startsWith('unix://')).toBe(true);
  const environment = { ...process.env, DOCKER_HOST: `unix://${socketPath}` };
  const occupied = createServer();
  occupied.listen(0, '127.0.0.1');
  await once(occupied, 'listening');
  const occupiedPort = (occupied.address() as { port: number }).port;
  const connections = new Set<Socket>();
  const unavailable = createServer(socket => { connections.add(socket); socket.on('close', () => connections.delete(socket)); });
  unavailable.listen(socketPath);
  await once(unavailable, 'listening');
  let server: ChildProcess | undefined;
  let restored = false;
  const restoreDocker = async () => {
    for (const socket of connections) socket.destroy();
    await new Promise<void>(resolve => unavailable.close(() => resolve()));
    symlinkSync(realEndpoint.slice('unix://'.length), socketPath);
    restored = true;
  };
  try {
    server = spawn(cli, ['--data-dir', profile, 'launch', '--port', String(occupiedPort), '--no-open'], { cwd: root, env: environment });
    const url = await new Promise<string>((resolve, reject) => {
      let output = '';
      const timer = setTimeout(() => reject(new Error('Launcher did not recover from occupied port')), 15000);
      server!.stdout!.on('data', data => {
        output += data.toString();
        const match = output.match(/http:\/\/127\.0\.0\.1:\d+\/#session=[A-Za-z0-9_-]+/);
        if (match) { clearTimeout(timer); resolve(match[0]); }
      });
      server!.on('error', reject);
    });
    expect(new URL(url).port).not.toBe(String(occupiedPort));
    await page.goto(url);
    await page.getByRole('button', { name: 'Start learning', exact: true }).click();
    await page.getByRole('button', { name: 'Prepare lab', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Cancel', exact: true })).toBeVisible();
    const peer = await context.newPage();
    await peer.goto(new URL('/', url).toString());
    const headers = { 'X-Dockyard': '1', Origin: new URL(url).origin };
    const response = await peer.request.post(new URL('/api/units/m01-processes/lab', url).toString(), { headers, data: { action: 'prepare' } });
    expect(response.status()).toBe(409);
    await page.getByRole('button', { name: 'Cancel', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Prepare lab', exact: true })).toBeEnabled();
    await expect.poll(async () => {
      const state = await page.request.get(new URL('/api/state', url).toString()).then(r => r.json());
      return state.operations.some((item: { state: string }) => item.state === 'canceled');
    }).toBe(true);
    await restoreDocker();
    await page.getByRole('button', { name: 'Prepare lab', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Open in WezTerm' })).toBeEnabled();
    execFileSync(python, [path.join(root, 'frontend/e2e/repair_lab.py'), profile, 'm01-processes'], { env: environment });
    await page.getByRole('button', { name: 'Check work', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'The required behavior passed this check.' })).toBeVisible();
    unlinkSync(socketPath);
    await page.getByRole('button', { name: 'Check work', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'The environment needs attention.' })).toBeVisible();
    symlinkSync(realEndpoint.slice('unix://'.length), socketPath);
    await page.getByRole('button', { name: 'Check work', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'The required behavior passed this check.' })).toBeVisible();
    await peer.close();
  } finally {
    if (!restored) await restoreDocker();
    execFileSync(cli, ['--data-dir', profile, 'lab', 'clean', 'm01-processes', '--yes'], { env: environment });
    if (server && server.exitCode === null) { server.kill('SIGINT'); await once(server, 'exit'); }
    occupied.close();
  }
});
