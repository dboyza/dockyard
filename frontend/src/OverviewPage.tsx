import type { Workbench } from "./useWorkbench";
import { currentPractice, reviewDue } from "./learning";
import { ArrowRight, Clock3, Terminal } from "lucide-react";

export function OverviewPage({ model }: { model: Workbench }) {
  const { state, busy, navigate, openLesson, continueUnit } = model;
  const returning = !!state.last_unit;
  const courseUnits = model.units.filter(
    (unit) => unit.kind === "lesson" || unit.kind === "mission",
  );
  const practised = courseUnits.filter((unit) =>
    currentPractice(unit.revision, state.progress[unit.id]),
  ).length;
  const due = model.units.filter((unit) =>
    reviewDue(unit.revision, state.progress[unit.id]),
  ).length;
  const continueCard = (
    <section className="continue-card">
      <div>
        <div className="eyebrow">
          {state.last_unit ? "PICK UP WHERE YOU LEFT OFF" : "YOUR FIRST STEP"}
        </div>
        <h2>{continueUnit?.title}</h2>
        <p>{continueUnit?.summary}</p>
        <div className="metadata">
          <span>
            <Clock3 size={14} />
            {continueUnit?.minutes} minutes
          </span>
          <span>
            <Terminal size={14} />
            Your terminal
          </span>
        </div>
        <button
          className="primary"
          disabled={!!busy || !continueUnit}
          onClick={() => continueUnit && void openLesson(continueUnit.id)}
        >
          {state.last_unit ? "Continue lesson" : "Open the first lesson"}
          <ArrowRight size={17} />
        </button>
      </div>
      {returning ? (
        <div className="lesson-rhythm overview-progress">
          <h3>Your progress</h3>
          <p className="overview-progress-count">
            <strong>{practised}</strong> of {courseUnits.length} lessons and
            missions practised
          </p>
          <span className="module-progress-bar wide" aria-hidden="true">
            <span
              style={{
                width: `${(practised / Math.max(courseUnits.length, 1)) * 100}%`,
              }}
            />
          </span>
          <div className="overview-links">
            {due > 0 && (
              <button
                className="text-button"
                onClick={() => navigate("review")}
              >
                {due} due for review <ArrowRight size={14} />
              </button>
            )}
            <button className="text-button" onClick={() => navigate("course")}>
              See the full course <ArrowRight size={14} />
            </button>
          </div>
        </div>
      ) : (
        <div className="lesson-rhythm">
          <h3>One lesson at a time</h3>
          <p>
            <strong>Understand.</strong> Learn the idea and predict what will
            happen.
          </p>
          <p>
            <strong>Try it.</strong> Prepare a lab and work in your terminal.
          </p>
          <p>
            <strong>Check and explain.</strong> Check the result, then explain
            why it worked.
          </p>
        </div>
      )}
    </section>
  );
  const foundations = courseUnits.filter((unit) => unit.module === 0);
  const introduction = (
    <section
      className="course-introduction"
      aria-labelledby="foundations-title"
    >
      <div>
        <div className="eyebrow">START WITH THE FOUNDATIONS</div>
        <h2 id="foundations-title">What a container really is.</h2>
        <p>
          No Docker experience needed. Each foundations lab explains one idea
          with pictures you can step through, then you try it in your own
          terminal.
        </p>
        <p className="muted">
          You’ll run small, throwaway programs so you can focus on how
          containers work. After that, you’ll put the same skills to work on a
          real application and grow it, module by module, until it runs on a
          Kubernetes cluster you build yourself.
        </p>
      </div>
      <ol className="course-steps" aria-label="Foundations labs">
        {foundations.map((unit, index) => (
          <li key={unit.id}>
            <span>{index + 1}</span>
            <div>
              <button
                className="text-button course-step-link"
                disabled={!!busy}
                onClick={() => void openLesson(unit.id)}
              >
                {unit.title}
              </button>
              <p>{unit.summary}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
  return (
    <>
      <div className="page-heading welcome-heading">
        <div className="eyebrow">
          {returning ? "Overview" : "WELCOME TO DOCKYARD"}
        </div>
        <h1>
          {returning ? "Welcome back." : "Learn to run a real application."}
        </h1>
        <p className="intro">
          {returning
            ? "Pick up your last lesson, or review something you practised earlier."
            : "Start with what a container is and how to reach one, then build up to running and recovering a Kubernetes cluster. You’ll read a short, illustrated lesson here and try it in your own terminal."}
        </p>
        {!returning && (
          <div className="button-row hero-actions">
            <button
              className="primary"
              disabled={!!busy || !continueUnit}
              onClick={() => continueUnit && void openLesson(continueUnit.id)}
            >
              Start learning
              <ArrowRight size={17} />
            </button>
            <button onClick={() => navigate("placement")}>
              I already know some Docker
            </button>
          </div>
        )}
      </div>
      {returning ? continueCard : introduction}
      {!returning && continueCard}
      <p className="placement-invitation">
        Already know the basics?{" "}
        <button className="text-button" onClick={() => navigate("placement")}>
          Find your starting point <ArrowRight size={15} />
        </button>
      </p>
      <section className="course-preview">
        <h2>Where the course takes you</h2>
        <p className="muted">
          Learn the foundations → run a real application in containers → deploy
          it to Kubernetes → secure it and recover a cluster.
        </p>
        <button className="text-button" onClick={() => navigate("course")}>
          Explore your course <ArrowRight size={16} />
        </button>
      </section>
    </>
  );
}
