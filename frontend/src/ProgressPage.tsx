import { reviewNeeded } from "./learning";
import { UnitRow } from "./UnitRow";
import type { Workbench } from "./useWorkbench";
import type { UnitSummary } from "./api";
export function ProgressPage({ model }: { model: Workbench }) {
  const { state, units, completed, demonstrated, openLesson } = model;
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
        <div className="eyebrow">UNDERSTANDING WITH EVIDENCE</div>
        <h1>Your skills, honestly measured.</h1>
        <p className="intro">
          Practice and independent demonstration are different milestones. Your
          evidence shows which you have achieved.
        </p>
      </div>
      <div className="stats-grid">
        <div className="stat">
          <span>Practiced</span>
          <strong>{completed}</strong>
        </div>
        <div className="stat">
          <span>Demonstrated independently</span>
          <strong>{demonstrated}</strong>
        </div>
        <div className="stat">
          <span>Due for review</span>
          <strong>
            {
              units.filter((unit) => {
                const item = state.progress[unit.id];
                return (
                  reviewNeeded(unit.revision, item) ||
                  (item?.review_at && new Date(item.review_at) <= new Date())
                );
              }).length
            }
          </strong>
        </div>
      </div>
      <section className="panel">
        <h2>Learning evidence</h2>
        {units.filter(
          (unit) =>
            state.progress[unit.id]?.viewed ||
            state.progress[unit.id]?.practiced,
        ).length ? (
          units.filter((unit) => state.progress[unit.id]).map(unitRow)
        ) : (
          <p className="muted">
            Your first observation starts here. Open a lesson, run its lab, and
            check the result.
          </p>
        )}
      </section>
    </>
  );
}
