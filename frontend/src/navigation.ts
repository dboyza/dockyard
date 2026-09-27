import type { Page } from "./useWorkbench";

export const pageLabels: Record<Page, string> = {
  home: "Overview",
  course: "Your course",
  placement: "Find your starting point",
  incidents: "Troubleshooting",
  exams: "Exam practice",
  progress: "Your progress",
  review: "Review practice",
  checkpoints: "Saved projects",
  labs: "Lab manager",
  reference: "Reference desk",
  settings: "Settings and data",
  lesson: "Lesson",
};

export function navigationSection(page: Page, incident = false): Page {
  if (page === "lesson") return incident ? "incidents" : "course";
  if (page === "placement") return "course";
  if (page === "exams") return "incidents";
  if (page === "review" || page === "checkpoints") return "progress";
  return page;
}

export const sectionPages: Partial<Record<Page, Page[]>> = {
  course: ["course", "placement"],
  incidents: ["incidents", "exams"],
  progress: ["progress", "review", "checkpoints"],
};
