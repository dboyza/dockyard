import type { Progress } from "./api";

export function currentPractice(revision: number, progress?: Progress) {
  return !!progress?.practiced && progress.revision === revision;
}

export function reviewNeeded(revision: number, progress?: Progress) {
  return !!progress?.practiced && progress.revision !== revision;
}

export function learningStatus(revision: number, progress?: Progress) {
  if (reviewNeeded(revision, progress)) return "Review needed";
  if (progress?.demonstrated) return "Demonstrated";
  if (progress?.practiced) return "Practiced";
  return progress?.viewed ? "In progress" : "Not started";
}
