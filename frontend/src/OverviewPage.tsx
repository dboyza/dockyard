import {
  ArrowRight,
  BookOpenText,
  Clock3,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import { HeroScene } from "./HeroScene";
import { coursePhases, currentPractice, reviewDue } from "./learning";
import type { Workbench } from "./useWorkbench";

const RHYTHM = [
  {
    icon: BookOpenText,
    title: "Understand",
    text: "Read a short, illustrated idea and predict what will happen.",
  },
  {
    icon: Terminal,
    title: "Try it",
    text: "Type real commands in the lab terminal beside the lesson.",
  },
  {
    icon: ShieldCheck,
    title: "Check and explain",
    text: "Check what your lab does, then explain why it worked.",
  },
];

export function OverviewPage({ model }: { model: Workbench }) {
  const { state, busy, catalog, navigate, openLesson, continueUnit } = model;
  const returning = !!state.last_unit;
  const practised = (id: string, revision: number) =>
    currentPractice(revision, state.progress[id]);
  const course = model.units.filter(
    (unit) => unit.kind === "lesson" || unit.kind === "mission",
  );
  const done = course.filter((unit) => practised(unit.id, unit.revision));
  const independent = done.filter(
    (unit) => state.progress[unit.id]?.demonstrated,
  ).length;
  const due = model.units.filter((unit) =>
    reviewDue(unit.revision, state.progress[unit.id]),
  ).length;
  const modules = catalog?.modules ?? [];
  const here = modules.find((module) => module.id === continueUnit?.module);
  const phases = coursePhases(modules).map((phase) => {
    const ids = new Set(
      modules.filter((m) => m.phase === phase.phase).map((m) => m.id),
    );
    const units = course.filter((unit) => ids.has(unit.module));
    return {
      ...phase,
      modules: ids.size,
      total: units.length,
      done: units.filter((unit) => practised(unit.id, unit.revision)).length,
    };
  });
  const facts = [
    `${course.length} hands-on labs`,
    `${modules.length} modules`,
    `${catalog?.exams.length ?? 0} timed practice exams`,
    "Runs entirely on this computer",
  ];
  const open = () => continueUnit && void openLesson(continueUnit.id);
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow">
            {returning ? "Welcome back" : "Welcome to Dockyard"}
          </div>
          <h1>
            {returning ? (
              <>
                Pick up where you <em>left off.</em>
              </>
            ) : (
              <>
                Learn to run a <em>real application.</em>
              </>
            )}
          </h1>
          <p className="intro">
            {returning
              ? "Your next lesson is ready. Each one pairs a short explanation with a real terminal."
              : "Start with what a container is, then build up to running and recovering a Kubernetes cluster. Every lesson pairs a short explanation with a real terminal."}
          </p>
          {returning && continueUnit && (
            <div className="hero-next">
              <span className="eyebrow">
                {here
                  ? `Module ${String(here.id).padStart(2, "0")} · ${here.title}`
                  : "Up next"}
              </span>
              <h2>{continueUnit.title}</h2>
              <p>{continueUnit.summary}</p>
            </div>
          )}
          <div className="button-row hero-actions">
            <button
              className="primary large"
              disabled={!!busy || !continueUnit}
              onClick={open}
            >
              {returning ? "Continue lesson" : "Start learning"}
              <ArrowRight size={17} />
            </button>
            {returning ? (
              <span className="metadata">
                <span>
                  <Clock3 size={14} />
                  {continueUnit?.minutes} minutes
                </span>
              </span>
            ) : (
              <button onClick={() => navigate("placement")}>
                I already know some Docker
              </button>
            )}
          </div>
          <ul className="hero-facts">
            {facts.map((fact) => (
              <li key={fact}>{fact}</li>
            ))}
          </ul>
        </div>
        <HeroScene />
      </section>

      {returning && (
        <section className="stats-grid" aria-label="Your progress">
          <button
            className="stat stat-link"
            onClick={() => navigate("progress")}
          >
            <span>Practised</span>
            <strong>
              {done.length}
              <small> of {course.length}</small>
            </strong>
            <span className="module-progress-bar wide" aria-hidden="true">
              <span
                style={{
                  width: `${(done.length / Math.max(course.length, 1)) * 100}%`,
                }}
              />
            </span>
          </button>
          <button
            className="stat stat-link"
            onClick={() => navigate("progress")}
          >
            <span>Passed without in-app help</span>
            <strong>{independent}</strong>
          </button>
          <button className="stat stat-link" onClick={() => navigate("review")}>
            <span>Due for review</span>
            <strong>{due}</strong>
          </button>
        </section>
      )}

      {!returning && (
        <section className="foundations" aria-labelledby="foundations-title">
          <div>
            <div className="eyebrow">Start with the foundations</div>
            <h2 id="foundations-title">What a container really is.</h2>
            <p className="muted">
              No Docker experience needed. Each foundations lab explains one
              idea with pictures you can step through. Then you try it in a real
              terminal beside the lesson.
            </p>
          </div>
          <ol aria-label="Foundations labs">
            {course
              .filter((unit) => unit.module === 0)
              .map((unit, index) => (
                <li key={unit.id}>
                  <button
                    className="foundation"
                    disabled={!!busy}
                    onClick={() => void openLesson(unit.id)}
                  >
                    <span className="journey-marker">{index + 1}</span>
                    <strong>{unit.title}</strong>
                    <span className="small muted">{unit.summary}</span>
                  </button>
                </li>
              ))}
          </ol>
        </section>
      )}

      <section className="journey" aria-labelledby="journey-title">
        <div className="section-heading">
          <h2 id="journey-title">Where the course takes you</h2>
          <button className="text-button" onClick={() => navigate("course")}>
            Explore your course <ArrowRight size={16} />
          </button>
        </div>
        <ol>
          {phases.map((phase) => (
            <li key={phase.phase}>
              <button
                className={`journey-stop ${here?.phase === phase.phase ? "here" : ""} ${phase.total > 0 && phase.done === phase.total ? "done" : ""}`}
                onClick={() => model.openCourse(phase.phase)}
              >
                <span className="journey-marker">0{phase.phase}</span>
                <strong>{phase.title}</strong>
                <span className="small muted">
                  {phase.modules} {phase.modules === 1 ? "module" : "modules"} ·{" "}
                  {phase.done} of {phase.total} practised
                </span>
                {here?.phase === phase.phase && (
                  <span className="journey-here">You are here</span>
                )}
              </button>
            </li>
          ))}
        </ol>
      </section>

      {!returning && (
        <section className="rhythm" aria-labelledby="rhythm-title">
          <h2 id="rhythm-title">One lesson at a time</h2>
          <div className="rhythm-grid">
            {RHYTHM.map((step, index) => (
              <article key={step.title}>
                <span className="rhythm-icon">
                  <step.icon size={18} />
                </span>
                <h3>
                  <span>{index + 1}</span>
                  {step.title}
                </h3>
                <p>{step.text}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      <p className="placement-invitation">
        Already know the basics?{" "}
        <button className="text-button" onClick={() => navigate("placement")}>
          Find your starting point <ArrowRight size={15} />
        </button>
      </p>
    </>
  );
}
