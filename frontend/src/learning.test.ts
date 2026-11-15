import { expect, test } from "vitest";
import type { Progress } from "./api";
import {
  glossaryMatches,
  coursePhases,
  currentPractice,
  learningStatus,
  reviewDue,
} from "./learning";

const base: Progress = {
  viewed: 1,
  practiced: 0,
  demonstrated: 0,
  hints: 0,
  reference: 0,
  revision: 1,
  review_at: null,
};

test("status follows viewing, practice, independent passes, and review dates", () => {
  const now = Date.parse("2026-09-30T12:00:00Z");
  expect(learningStatus(1)).toBe("Not started");
  expect(learningStatus(1, base)).toBe("In progress");
  const practiced = { ...base, practiced: 1 };
  expect(learningStatus(1, practiced)).toBe("Practiced");
  expect(currentPractice(1, practiced)).toBe(true);
  expect(learningStatus(1, { ...practiced, demonstrated: 1 })).toBe(
    "Passed without help",
  );
  expect(learningStatus(2, practiced)).toBe("Review needed");
  expect(currentPractice(2, practiced)).toBe(false);
  const due = { ...practiced, review_at: "2026-09-30T11:00:00Z" };
  expect(reviewDue(1, due, now)).toBe(true);
  expect(reviewDue(1, { ...due, review_at: "2026-10-01T00:00:00Z" }, now)).toBe(
    false,
  );
  // A first failed check queues a review, but the lesson still reads as in progress.
  const failedFirst = { ...base, review_at: "2020-01-01T00:00:00Z" };
  expect(reviewDue(1, failedFirst, now)).toBe(true);
  expect(learningStatus(1, failedFirst)).toBe("In progress");
});

test("course phases follow their numbers, not module order", () => {
  const module = (id: number, phase: number, phase_title: string) => ({
    id,
    phase,
    phase_title,
    title: "",
    topics: [],
    mission: "",
  });
  expect(
    coursePhases([
      module(1, 1, "Containers"),
      module(0, 0, "Foundations"),
      module(7, 2, "Kubernetes"),
    ]),
  ).toEqual([
    { phase: 0, title: "Foundations" },
    { phase: 1, title: "Containers" },
    { phase: 2, title: "Kubernetes" },
  ]);
});

test("glossary search ranks exact, then leading, then other name matches, then definitions", () => {
  const term = (id: string, name: string, definition: string) => ({
    id,
    term: name,
    definition,
    watch_for: "",
    units: [],
    primer: "linux",
  });
  const terms = [
    term("limit", "Resource limit", "A cap enforced through a cgroup."),
    term("cgroup", "cgroup", "A control group."),
    term("pvc", "PersistentVolumeClaim", "A request for storage."),
  ];
  expect(glossaryMatches(terms, " CGROUP ").map((item) => item.id)).toEqual([
    "cgroup",
    "limit",
  ]);
  expect(glossaryMatches(terms, "pvc").map((item) => item.id)).toEqual(["pvc"]);
  const volumes = [
    term("pv", "PersistentVolume", "Storage in the cluster."),
    term("volume-mount", "Volume mount", "Where a volume appears."),
    term("volume", "Volume", "Storage that outlives a container."),
  ];
  expect(glossaryMatches(volumes, "volume").map((item) => item.id)).toEqual([
    "volume",
    "volume-mount",
    "pv",
  ]);
  expect(glossaryMatches(terms, "  ")).toEqual([]);
});
