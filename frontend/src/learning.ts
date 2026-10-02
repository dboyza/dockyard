import type { GlossaryTerm, Module, Progress } from "./api";

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

// Ranks exact names, then names that start with the query, then other name
// matches, then terms that only mention the query in their explanation.
export function glossaryMatches(terms: GlossaryTerm[], search: string) {
  const query = search.trim().toLowerCase();
  if (!query) return [];
  const rank = (term: GlossaryTerm) => {
    const names = [term.term.toLowerCase(), term.id];
    if (names.includes(query)) return 0;
    if (names.some((name) => name.startsWith(query))) return 1;
    if (names.some((name) => name.includes(query))) return 2;
    return `${term.definition} ${term.watch_for}`.toLowerCase().includes(query)
      ? 3
      : null;
  };
  return terms
    .map((term) => ({ term, rank: rank(term) }))
    .filter(
      (item): item is { term: GlossaryTerm; rank: number } =>
        item.rank !== null,
    )
    .sort((a, b) => a.rank - b.rank)
    .map((item) => item.term);
}
