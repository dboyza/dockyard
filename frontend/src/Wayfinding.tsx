import { ChevronRight } from "lucide-react";
import { currentPractice } from "./learning";
import { navigationSection, pageLabels } from "./navigation";
import type { Workbench } from "./useWorkbench";

const two = (value: number) => String(value).padStart(2, "0");

/** The path to the current page: the course, its phase, and the module for a lesson. */
export function Breadcrumb({ model }: { model: Workbench }) {
  const { page, lesson, catalog, navigate } = model;
  const section = navigationSection(page, lesson?.kind === "incident");
  const module =
    page === "lesson" && lesson?.kind !== "incident"
      ? catalog?.modules.find((item) => item.id === lesson?.module)
      : undefined;
  const crumbs =
    page === "lesson"
      ? module
        ? [module.phase_title, `${two(module.id)} ${module.title}`]
        : ["Incident scenarios"]
      : section === page
        ? []
        : [pageLabels[page]];
  const root = section === "incidents" ? "Practice" : pageLabels[section];
  return (
    <nav className="breadcrumb" aria-label="Where you are">
      {crumbs.length ? (
        <button className="text-button" onClick={() => navigate(section)}>
          {root}
        </button>
      ) : (
        <strong aria-current="page">{root}</strong>
      )}
      {crumbs.map((crumb, index) => {
        const last = index === crumbs.length - 1;
        return (
          // Narrow screens keep the ends of the path and drop the middle.
          <span className={`crumb ${last ? "" : "wide-only"}`} key={crumb}>
            <ChevronRight size={14} aria-hidden="true" />
            {last ? <strong aria-current="page">{crumb}</strong> : crumb}
          </span>
        );
      })}
    </nav>
  );
}

/** The learner's place in the course, always one click away in the sidebar. */
export function NowLearning({ model }: { model: Workbench }) {
  const { continueUnit, catalog, units, state, page, lesson } = model;
  if (!continueUnit) return null;
  const module = catalog?.modules.find(
    (item) => item.id === continueUnit.module,
  );
  const siblings = units.filter(
    (unit) =>
      unit.module === continueUnit.module &&
      (unit.kind === "lesson" || unit.kind === "mission"),
  );
  const done = siblings.filter((unit) =>
    currentPractice(unit.revision, state.progress[unit.id]),
  ).length;
  const here = page === "lesson" && lesson?.id === continueUnit.id;
  return (
    <button
      className="now-learning"
      aria-label={`${here ? "Now learning" : state.last_unit ? "Continue" : "Start"}: ${continueUnit.title}`}
      onClick={() => void model.openLesson(continueUnit.id)}
    >
      <span className="eyebrow">
        {here ? "Now learning" : state.last_unit ? "Continue" : "Start here"}
      </span>
      <strong>{continueUnit.title}</strong>
      {module && siblings.length > 0 && (
        <>
          <span className="small muted">
            {two(module.id)} {module.title}
          </span>
          <span className="module-progress-bar wide" aria-hidden="true">
            <span style={{ width: `${(done / siblings.length) * 100}%` }} />
          </span>
          <span className="small muted">
            {done} of {siblings.length} done in this module
          </span>
        </>
      )}
    </button>
  );
}
