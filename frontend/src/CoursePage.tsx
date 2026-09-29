import { currentPractice } from "./learning";
import { UnitRow } from "./UnitRow";
import type { Workbench } from "./useWorkbench";
import { ChevronDown } from "lucide-react";
import type { UnitSummary } from "./api";
export function CoursePage({ model }: { model: Workbench }) {
  const { catalog, lesson, search, units, filtered, state, openLesson } = model;
  const unitRow = (unit: UnitSummary) => (
    <UnitRow
      key={unit.id}
      unit={unit}
      progress={state.progress[unit.id]}
      onOpen={openLesson}
    />
  );
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">THE COMPLETE LEARNING PATH</div>
        <h1>Your course</h1>
        <p className="intro">
          Start with the first lesson, or choose a topic you want to practise.
          Each module ends with a mission where you try the skills without
          step-by-step instructions.
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
              .map((module) => {
                const moduleUnits = units.filter(
                  (unit) =>
                    unit.module === module.id &&
                    (unit.kind === "lesson" || unit.kind === "mission"),
                );
                const done = moduleUnits.filter((unit) =>
                  currentPractice(unit.revision, state.progress[unit.id]),
                ).length;
                return (
                  <details
                    className="module"
                    key={module.id}
                    open={module.id === (lesson?.module ?? 1)}
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
                      {moduleUnits.length > 0 && (
                        <span
                          className="module-progress"
                          aria-label={`${done} of ${moduleUnits.length} activities practised`}
                        >
                          <span
                            className="module-progress-bar"
                            aria-hidden="true"
                          >
                            <span
                              style={{
                                width: `${(done / moduleUnits.length) * 100}%`,
                              }}
                            />
                          </span>
                          {done}/{moduleUnits.length}
                        </span>
                      )}
                      <ChevronDown size={17} />
                    </summary>
                    <div className="module-lessons">
                      {moduleUnits.map(unitRow)}
                      {!units.some((unit) => unit.module === module.id) && (
                        <p className="development-note">
                          This module is being authored in the current
                          development build.
                        </p>
                      )}
                    </div>
                  </details>
                );
              })}
          </section>
        ))
      )}
    </>
  );
}
