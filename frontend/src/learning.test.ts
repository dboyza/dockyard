import { expect, test } from "vitest";
import type { Progress } from "./api";
import { currentPractice, learningStatus, reviewDue } from "./learning";

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
  const practised = { ...base, practiced: 1 };
  expect(learningStatus(1, practised)).toBe("Practiced");
  expect(currentPractice(1, practised)).toBe(true);
  expect(learningStatus(1, { ...practised, demonstrated: 1 })).toBe(
    "Passed without help",
  );
  expect(learningStatus(2, practised)).toBe("Review needed");
  expect(currentPractice(2, practised)).toBe(false);
  const due = { ...practised, review_at: "2026-09-30T11:00:00Z" };
  expect(reviewDue(1, due, now)).toBe(true);
  expect(reviewDue(1, { ...due, review_at: "2026-10-01T00:00:00Z" }, now)).toBe(
    false,
  );
});
