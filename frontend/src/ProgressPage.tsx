import { currentPractice, reviewDue } from "./learning";
import { ArrowRight, ChevronDown } from "lucide-react";
import { UnitRow } from "./UnitRow";
import type { Workbench } from "./useWorkbench";
import type { UnitSummary } from "./api";
export function ProgressPage({ model }: { model: Workbench }) {
  const {
    state,
    units,
    catalog,
    completed,
    demonstrated,
    openLesson,
    navigate,
  } = model;
  const touched = units.filter(
    (unit) =>
      state.progress[unit.id]?.viewed || state.progress[unit.id]?.practiced,
  );
  const due = units.filter((unit) =>
    reviewDue(unit.revision, state.progress[unit.id]),
  ).length;
  const groups = (catalog?.modules || [])
    .map((module) => ({
      module,
      all: units.filter((unit) => unit.module === module.id),
      shown: touched.filter((unit) => unit.module === module.id),
    }))
    .filter((group) => group.shown.length);
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
        <div className="eyebrow">YOUR LEARNING RECORD</div>
        <h1>See what you’ve practised.</h1>
        <p className="intro">
          A passing check means your lab met the task’s requirements. Missions
          passed without in-app hints are recorded separately. These results do
          not grade your reasoning or guarantee that you can repeat a task
          later.
        </p>
      </div>
      <div className="stats-grid">
        <div className="stat">
          <span>Practised</span>
          <strong>
            {completed}
            <small> of {units.length}</small>
          </strong>
        </div>
        <div className="stat">
          <span>Passed without in-app help</span>
          <strong>{demonstrated}</strong>
        </div>
        <button
          className="stat stat-link"
          onClick={() => navigate("review")}
          disabled={!due}
        >
          <span>Due for review</span>
          <strong>{due}</strong>
          {!!due && (
            <span className="stat-action">
              Review now <ArrowRight size={14} />
            </span>
          )}
        </button>
      </div>
      <section className="progress-groups" aria-label="Your activity">
        <h2>Your activity by module</h2>
        {groups.length ? (
          groups.map(({ module, all, shown }) => {
            const done = all.filter((unit) =>
              currentPractice(unit.revision, state.progress[unit.id]),
            ).length;
            return (
              <details className="module" key={module.id}>
                <summary>
                  <span className="module-id">
                    {String(module.id).padStart(2, "0")}
                  </span>
                  <span>
                    <strong>{module.title}</strong>
                    <span className="muted small">
                      {shown.length} of {all.length} activities opened
                    </span>
                  </span>
                  <span
                    className="module-progress"
                    aria-label={`${done} of ${all.length} activities practised`}
                  >
                    <span className="module-progress-bar" aria-hidden="true">
                      <span
                        style={{ width: `${(done / all.length) * 100}%` }}
                      />
                    </span>
                    {done}/{all.length}
                  </span>
                  <ChevronDown size={17} />
                </summary>
                <div className="module-lessons">{shown.map(unitRow)}</div>
              </details>
            );
          })
        ) : (
          <div className="empty-state">
            <h3>Nothing here yet.</h3>
            <p>Open a lesson, prepare its lab, and check your work.</p>
            <button className="primary" onClick={() => navigate("course")}>
              Browse the course <ArrowRight size={16} />
            </button>
          </div>
        )}
      </section>
    </>
  );
}
