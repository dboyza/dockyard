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
        <div className="eyebrow">RETURN WITH FRESH EVIDENCE</div>
        <h1>Make the skill available again.</h1>
        <p className="intro">
          Recall the model before opening the explanation. Revisit your
          evidence, explain the failure boundary, and use a fresh practical
          attempt when you want to demonstrate the skill again.
        </p>
      </div>
      <section className="panel review-policy">
        <h2>A schedule you can inspect</h2>
        <p className="muted">
          Supported practice returns after one day. An independent demonstration
          returns after seven days. A failed behavior check or a changed lesson
          revision brings the activity back now. Blocked environments and checks
          invalidated by changing work do not count as mistakes.
        </p>
        <p className="muted">
          Opening a review does not earn new evidence. Use Check work to record
          current behavior, or Independent retake on a mission or incident to
          start without earlier hints. Repeated checks before a scheduled review
          do not keep moving it further away. These intervals organize practice;
          they do not certify retention or predict an exam result.
        </p>
      </section>
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
              />
            </div>
          ))}
        </section>
      )}
    </>
  );
}
