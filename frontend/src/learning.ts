import type { Module, Progress } from "./api";

export function currentPractice(revision: number, progress?: Progress) {
  return !!progress?.practiced && progress.revision === revision;
}

export function reviewNeeded(revision: number, progress?: Progress) {
  return !!progress?.practiced && progress.revision !== revision;
}

export function reviewDue(
  revision: number,
  progress?: Progress,
  now = Date.now(),
) {
  return (
    reviewNeeded(revision, progress) ||
    !!(progress?.review_at && new Date(progress.review_at).getTime() <= now)
  );
}

export function learningStatus(revision: number, progress?: Progress) {
  if (reviewNeeded(revision, progress)) return "Review needed";
  if (reviewDue(revision, progress)) return "Review due";
  if (progress?.demonstrated) return "Passed without help";
  if (progress?.practiced) return "Practiced";
  return progress?.viewed ? "In progress" : "Not started";
}

/** The course phases in order, each titled by its modules. */
export function coursePhases(modules: Module[]) {
  const phases = new Map<number, string>();
  for (const module of modules) phases.set(module.phase, module.phase_title);
  return [...phases]
    .sort(([a], [b]) => a - b)
    .map(([phase, title]) => ({ phase, title }));
}
