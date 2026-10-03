import { execFileSync } from 'node:child_process';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '../..');

/**
 * Cleans every lab a disposable profile created, then deletes the profile only if
 * nothing remains. Otherwise it throws, naming the kept profile and the command that
 * removes what is left, so a failed run never orphans a practice environment.
 * Stop any launcher using the profile first.
 */
export function releaseProfile(profile: string, { keep = false } = {}) {
  execFileSync(path.join(root, '.runtime/installed/bin/python'), [path.join(root, 'tests/release_profile.py'), profile, ...(keep ? ['--keep'] : [])], { stdio: ['ignore', 'inherit', 'inherit'], timeout: 600_000 });
}
