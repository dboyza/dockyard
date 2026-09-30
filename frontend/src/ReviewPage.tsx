import { ArrowRight, CalendarClock } from "lucide-react";
import { reviewDue, reviewNeeded } from "./learning";
import type { Workbench } from "./useWorkbench";
import { UnitRow } from "./UnitRow";

export function ReviewPage({ model }: { model: Workbench }) {
  const { units, state, openLesson, navigate } = model;
  const due = units.filter((unit) =>
    reviewDue(unit.revision, state.progress[unit.id]),
  );
  const upcoming = units
    .filter(
      (unit) =>
        state.progress[unit.id]?.review_at &&
        !reviewDue(unit.revision, state.progress[unit.id]),
    )
    .sort((a, b) =>
      (state.progress[a.id].review_at || "").localeCompare(
        state.progress[b.id].review_at || "",
      ),
    );
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">Spaced review</div>
        <h1>Come back and try it again.</h1>
        <p className="intro">
          Before reopening a lesson, see what you remember. Explain why your
          last solution worked, then try the task again in a fresh lab.
        </p>
      </div>
      <section
        className="panel review-list"
        aria-label="Activities due for review"
      >
        <div className="section-heading">
          <h2>Ready to revisit</h2>
          <span className="muted small">{due.length} activities</span>
        </div>
        {due.length ? (
          due.map((unit) => (
            <div key={unit.id}>
              {reviewNeeded(unit.revision, state.progress[unit.id]) && (
                <p className="muted small">
                  The lesson revision changed; earlier evidence remains in your
                  record.
                </p>
              )}
              <UnitRow
                unit={unit}
                progress={state.progress[unit.id]}
                onOpen={openLesson}
                showModule
              />
            </div>
          ))
        ) : (
          <div className="empty-state">
            <CalendarClock size={32} />
            <h3>Nothing is due right now.</h3>
            <p>
              Your next practical assessment will create or update its review
              date.
            </p>
            <button onClick={() => navigate("course")}>
              Continue your course <ArrowRight size={16} />
            </button>
          </div>
        )}
      </section>
      <details className="explainer">
        <summary>How reviews are scheduled</summary>
        <p>
          Practice with help comes back after one day, and a mission passed
          without help comes back after seven days. A failed check, or a lesson
          that has been updated, comes back straight away. A check that could
          not run, or that ran while the lab was still changing, does not count
          as a mistake.
        </p>
        <p>
          Opening a review does not change your record: use Check work, or
          Independent retake on a mission or incident for a fresh attempt
          without earlier hints. The schedule helps you practise; it cannot
          prove you will remember something.
        </p>
      </details>
      {!!upcoming.length && (
        <section className="panel review-list" aria-label="Upcoming reviews">
          <h2>Coming back later</h2>
          {upcoming.map((unit) => (
            <div key={unit.id}>
              <p className="muted small">
                {new Date(
                  state.progress[unit.id].review_at!,
                ).toLocaleDateString(undefined, {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                })}
              </p>
              <UnitRow
                unit={unit}
                progress={state.progress[unit.id]}
                onOpen={openLesson}
                showModule
              />
            </div>
          ))}
        </section>
      )}
    </>
  );
}
