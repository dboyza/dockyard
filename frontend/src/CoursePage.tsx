import type { Workbench } from "./useWorkbench";
import { Check, ChevronDown, ChevronRight, Circle } from "lucide-react";
import type { UnitSummary } from "./api";
export function CoursePage({ model }: { model: Workbench }) {
  const { catalog, lesson, search, units, filtered, state, openLesson } = model;
  const unitRow = (unit: UnitSummary) => (
    <button
      className="unitrow"
      key={unit.id}
      onClick={() => void openLesson(unit.id)}
    >
      <span
        className={`unitstatus ${state.progress[unit.id]?.practiced ? "done" : ""}`}
      >
        {state.progress[unit.id]?.practiced ? (
          <Check size={17} />
        ) : (
          <Circle size={15} />
        )}
      </span>
      <span>
        <strong>{unit.title}</strong>
        <span className="muted small">{unit.summary}</span>
      </span>
      <span className="unitmeta">
        <span>{unit.minutes} min</span>
        <ChevronRight size={17} />
      </span>
    </button>
  );
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">THE COMPLETE LEARNING PATH</div>
        <h1>Your course</h1>
        <p className="intro">
          Build the model, apply it to Dispatch, and prove it independently.
        </p>
      </div>
      {search ? (
        <section className="panel">
          <h2>Search results</h2>
          {filtered.length ? (
            filtered.map(unitRow)
          ) : (
            <p className="muted">
              No lessons match “{search}”. Try a concept such as container,
              storage, or networking.
            </p>
          )}
        </section>
      ) : (
        [1, 2, 3, 4].map((phase) => (
          <section className="course-phase" id={`phase-${phase}`} key={phase}>
            <div className="section-heading">
              <h2>
                <span className="phase-number">0{phase}</span>
                {
                  catalog?.modules.find((item) => item.phase === phase)
                    ?.phase_title
                }
              </h2>
            </div>
            {catalog?.modules
              .filter((module) => module.phase === phase)
              .map((module) => (
                <details
                  className="module"
                  key={module.id}
                  open={module.id === lesson?.module || module.id === 1}
                >
                  <summary>
                    <span className="module-id">
                      {String(module.id).padStart(2, "0")}
                    </span>
                    <span>
                      <strong>{module.title}</strong>
                      <span className="muted small">
                        {module.topics.join(" · ")}
                      </span>
                    </span>
                    <ChevronDown size={17} />
                  </summary>
                  <div className="module-lessons">
                    {units
                      .filter((unit) => unit.module === module.id)
                      .map(unitRow)}
                    {!units.some((unit) => unit.module === module.id) && (
                      <p className="development-note">
                        This module is being authored in the current development
                        build.
                      </p>
                    )}
                  </div>
                </details>
              ))}
          </section>
        ))
      )}
    </>
  );
}
