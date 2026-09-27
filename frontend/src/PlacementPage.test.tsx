import { expect, test, vi } from "vitest";
import { placementEvidence } from "./PlacementPage";
import type { Progress, UnitSummary } from "./api";

test("placement counts current independent evidence and returns changed or failed skills to review", () => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse("2026-09-26T12:00:00Z"));
  const unit = { revision: 2 } as UnitSummary;
  const progress: Progress = {
    viewed: 1,
    practiced: 1,
    demonstrated: 1,
    hints: 0,
    reference: 0,
    revision: 2,
    review_at: "2026-10-01T12:00:00Z",
  };
  expect(placementEvidence(unit, undefined)).toBe(false);
  expect(placementEvidence(unit, { ...progress, demonstrated: 0 })).toBe(false);
  expect(placementEvidence(unit, { ...progress, revision: 1 })).toBe(false);
  expect(
    placementEvidence(unit, { ...progress, review_at: "2026-09-26T11:59:59Z" }),
  ).toBe(false);
  expect(placementEvidence(unit, progress)).toBe(true);
  vi.restoreAllMocks();
});
