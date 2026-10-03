import type { Page } from "./useWorkbench";

/**
 * Workbench locations as URL fragments, so the browser's Back and Forward
 * buttons, reloading, and bookmarks keep the learner's place. Every route
 * starts with "#/", which keeps it apart from the launcher's one-time
 * "#session=" sign-in fragment.
 */
export type Route =
  | { page: Exclude<Page, "lesson" | "exams" | "reference"> }
  | { page: "lesson"; unit: string }
  | { page: "exams"; exam: string | null }
  | { page: "reference"; focus: string };

const simplePages = [
  "home",
  "course",
  "placement",
  "incidents",
  "progress",
  "review",
  "checkpoints",
  "labs",
  "settings",
] as const;

const segment = (value: string) => encodeURIComponent(value);

export function routeHash(route: Route): string {
  switch (route.page) {
    case "home":
      return "#/";
    case "lesson":
      return `#/lesson/${segment(route.unit)}`;
    case "exams":
      return route.exam ? `#/exams/${segment(route.exam)}` : "#/exams";
    case "reference": {
      const { focus } = route;
      if (focus.startsWith("primer/"))
        return `#/reference/primers/${segment(focus.slice("primer/".length))}`;
      if (focus.startsWith("term/?"))
        return `#/reference/glossary?q=${segment(focus.slice("term/?".length))}`;
      if (focus.startsWith("term/") && focus.length > "term/".length)
        return `#/reference/glossary/${segment(focus.slice("term/".length))}`;
      return focus.startsWith("term/") ? "#/reference/glossary" : "#/reference";
    }
    default:
      return `#/${route.page}`;
  }
}

/** Reads a fragment back into a route, or null when it is not a workbench route. */
export function parseRoute(hash: string): Route | null {
  if (!hash.startsWith("#/")) return null;
  const [path, search = ""] = hash.slice(2).split("?", 2);
  let parts: string[];
  try {
    parts = path.split("/").filter(Boolean).map(decodeURIComponent);
  } catch {
    return null;
  }
  const [page, ...rest] = parts;
  if (page === undefined) return { page: "home" };
  if (page === "lesson" && rest.length === 1)
    return { page: "lesson", unit: rest[0] };
  if (page === "exams" && rest.length <= 1)
    return { page: "exams", exam: rest[0] ?? null };
  if (page === "reference") {
    if (rest.length === 0)
      return { page: "reference", focus: "primer/terminal" };
    if (rest[0] === "primers" && rest.length === 2)
      return { page: "reference", focus: `primer/${rest[1]}` };
    if (rest[0] === "glossary" && rest.length === 2)
      return { page: "reference", focus: `term/${rest[1]}` };
    if (rest[0] === "glossary" && rest.length === 1) {
      const query = new URLSearchParams(search).get("q");
      return { page: "reference", focus: query ? `term/?${query}` : "term/" };
    }
    return null;
  }
  return rest.length === 0 && (simplePages as readonly string[]).includes(page)
    ? { page: page as (typeof simplePages)[number] }
    : null;
}
