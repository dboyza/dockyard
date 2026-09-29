import { ArrowRight, CheckCircle2, Compass } from "lucide-react";
import type { Workbench } from "./useWorkbench";
import { currentPractice, reviewDue } from "./learning";
import type { Progress, UnitSummary } from "./api";

export function placementEvidence(
  unit: UnitSummary | undefined,
  progress: Progress | undefined,
) {
  return (
    !!unit &&
    currentPractice(unit.revision, progress) &&
    !!progress?.demonstrated &&
    !reviewDue(unit.revision, progress)
  );
}

export function PlacementPage({ model }: { model: Workbench }) {
  const { catalog, state, openLesson, navigate } = model;
  const benchmarks = (catalog?.placement || []).map((item) => {
    const unit = catalog?.units.find((unit) => unit.id === item.unit_id);
    return {
      ...item,
      unit,
      demonstrated: placementEvidence(unit, state.progress[item.unit_id]),
    };
  });
  const next = benchmarks.find((item) => !item.demonstrated);
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">OPTIONAL PRACTICAL PLACEMENT</div>
        <h1>Find a good place to start.</h1>
        <p className="intro">
          Already know some Docker or Kubernetes? Try a mission from a familiar
          part of the course. Use the result to decide what to practise next;
          every lesson stays available.
        </p>
      </div>
      <section className="continue-card placement-recommendation">
        <div>
          <div className="eyebrow">
            {next ? "SUGGESTED STARTING PHASE" : "ALL FOUR MISSIONS UP TO DATE"}
          </div>
          <h2>{next?.title || "Keep practising."}</h2>
          <p>
            {next
              ? "You haven’t passed this part’s mission on your own yet, or it is due for review. Try the mission if the topic feels familiar, or start with its first lesson."
              : "You’ve passed every placement mission on your own. Incidents, practice exams, and review keep your skills fresh."}
          </p>
          <div className="button-row">
            {next ? (
              <>
                <button
                  className="primary"
                  onClick={() => void openLesson(next.unit_id)}
                >
                  Try the mission <ArrowRight size={16} />
                </button>
                <button onClick={() => void openLesson(next.start_unit)}>
                  Start the phase
                </button>
              </>
            ) : (
              <button className="primary" onClick={() => navigate("incidents")}>
                Open incident practice <ArrowRight size={16} />
              </button>
            )}
          </div>
        </div>
        <Compass className="placement-compass" size={90} strokeWidth={1} />
      </section>
      <section className="panel">
        <h2>How to use the result</h2>
        <p className="muted">
          Pick a mission from a part of the course you already know, prepare its
          lab, and try it. Hints and the reference solution are there if you
          need them, but a pass with help does not count as placing out of that
          part.
        </p>
        <p className="muted">
          A part counts as placed only when you pass its mission on your own and
          it is not due for review. If you later fail a check, or the lesson is
          updated, that part comes back into view. If you opened help earlier,
          use Independent retake for a fresh try. This is a suggestion, not a
          guarantee that you know every topic in that part.
        </p>
      </section>
      <section aria-label="Placement benchmarks" className="placement-grid">
        {benchmarks.map((item, index) => (
          <article className="panel" key={item.id}>
            <div className="section-heading">
              <span className="eyebrow">PHASE 0{index + 1}</span>
              {item.demonstrated && (
                <span className="placement-current">
                  <CheckCircle2 size={15} /> Passed on your own
                </span>
              )}
            </div>
            <h2>{item.title}</h2>
            <p>{item.summary}</p>
            <p className="muted small">{item.reason}</p>
            <p className="muted small">
              {item.unit?.minutes} minutes suggested ·{" "}
              {item.unit?.runtime === "linux"
                ? "Native Linux VMs"
                : item.unit?.runtime === "docker"
                  ? "Docker / Compose"
                  : "Kubernetes cluster"}
            </p>
            <div className="button-row">
              <button onClick={() => void openLesson(item.unit_id)}>
                Open mission <ArrowRight size={16} />
              </button>
              <button
                className="text-button"
                onClick={() => void openLesson(item.start_unit)}
              >
                Start with the lessons
              </button>
            </div>
          </article>
        ))}
      </section>
    </>
  );
}
