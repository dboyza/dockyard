import { expect, test } from "vitest";
import { parseRoute, routeHash, type Route } from "./routing";

test.each<[Route, string]>([
  [{ page: "home" }, "#/"],
  [{ page: "course" }, "#/course"],
  [{ page: "labs" }, "#/labs"],
  [{ page: "lesson", unit: "m03-ports" }, "#/lesson/m03-ports"],
  [{ page: "exams", exam: null }, "#/exams"],
  [{ page: "exams", exam: "cka-a" }, "#/exams/cka-a"],
  [{ page: "reference", focus: "primer/yaml" }, "#/reference/primers/yaml"],
  [{ page: "reference", focus: "term/" }, "#/reference/glossary"],
  [{ page: "reference", focus: "term/cgroup" }, "#/reference/glossary/cgroup"],
  [
    { page: "reference", focus: "term/?probe & port" },
    "#/reference/glossary?q=probe%20%26%20port",
  ],
])("%j is written as %s and read back", (route, hash) => {
  expect(routeHash(route)).toBe(hash);
  expect(parseRoute(hash)).toEqual(route);
});

test("fragments that are not workbench routes are left alone", () => {
  for (const hash of [
    "",
    "#session=abc",
    "#main",
    "#/unknown",
    "#/course/extra",
    "#/lesson",
    "#/reference/primers",
    "#/lesson/%E0%A4%A",
  ])
    expect(parseRoute(hash), hash).toBeNull();
});

test("short forms read as their full location", () => {
  expect(parseRoute("#/home")).toEqual({ page: "home" });
  expect(parseRoute("#/reference")).toEqual({
    page: "reference",
    focus: "primer/terminal",
  });
  expect(parseRoute("#/reference/glossary?q=")).toEqual({
    page: "reference",
    focus: "term/",
  });
});
