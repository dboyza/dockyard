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
              ? "You have not yet passed this part’s mission without in-app help, or it is due for review. Try the mission if the topic feels familiar, or start with its first lesson."
              : "Your recorded benchmarks are current. Use incidents, timed practice, and scheduled review to find the next useful challenge."}
          </p>
          <div className="button-row">
            {next ? (
              <>
                <button
                  className="primary"
                  onClick={() => void openLesson(next.unit_id)}
                >
                  Try the benchmark <ArrowRight size={16} />
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
          Choose any benchmark, prepare its actual lab, and attempt the mission
          from its outcome brief. Hints and references are available whenever
          you need them. Supported practice is useful evidence of learning, but
          it does not skip a phase here.
        </p>
        <p className="muted">
          Only an independent pass for the current revision, before its review
          date, counts toward this recommendation. A failed check or an updated
          lesson brings that part of the course back into view. Use Independent
          retake if you previously opened support. The recommendation is
          advisory and does not certify every objective in a phase.
        </p>
      </section>
      <section aria-label="Placement benchmarks" className="placement-grid">
        {benchmarks.map((item, index) => (
          <article className="panel" key={item.id}>
            <div className="section-heading">
              <span className="eyebrow">PHASE 0{index + 1}</span>
              {item.demonstrated && (
                <span className="placement-current">
                  <CheckCircle2 size={15} /> Current evidence
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
                Open benchmark <ArrowRight size={16} />
              </button>
              <button
                className="text-button"
                onClick={() => void openLesson(item.start_unit)}
              >
                Review foundations
              </button>
            </div>
          </article>
        ))}
      </section>
    </>
  );
}
