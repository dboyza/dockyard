import type { Workbench } from "./useWorkbench";
import { ArrowRight, Clock3, Terminal } from "lucide-react";

export function OverviewPage({ model }: { model: Workbench }) {
  const { state, busy, navigate, openLesson, continueUnit } = model;
  const returning = !!state.last_unit;
  const continueCard = (
    <section className="continue-card">
      <div>
        <div className="eyebrow">
          {state.last_unit ? "PICK UP WHERE YOU LEFT OFF" : "YOUR FIRST STEP"}
        </div>
        <h2>{continueUnit?.title}</h2>
        <p>
          {state.last_unit
            ? continueUnit?.summary
            : "Start Dispatch, send it a request, and see what happens when you stop its container."}
        </p>
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
          <strong>Check and explain.</strong> Check the result, then explain why
          it worked.
        </p>
      </div>
    </section>
  );
  const introduction = (
    <section className="dispatch-introduction" aria-labelledby="dispatch-title">
      <div>
        <div className="eyebrow">THE APPLICATION YOU’LL WORK ON</div>
        <h2 id="dispatch-title">Meet Dispatch.</h2>
        <p>
          Dispatch is a small app that accepts jobs and processes them in the
          background. Think of sending a task to a service, then coming back to
          see whether it has finished.
        </p>
        <p className="muted">
          We supply the Python code. Your job is to package it, connect its
          parts, keep it running, and learn how to fix it when something breaks.
          You don’t need to write Python.
        </p>
      </div>
      <ol className="dispatch-story" aria-label="How Dispatch will work">
        <li>
          <span>1</span>
          <div>
            <strong>Send a job</strong>
            <p>
              The API, the part that receives requests, accepts a short piece of
              text.
            </p>
          </div>
        </li>
        <li>
          <span>2</span>
          <div>
            <strong>Do the work</strong>
            <p>
              A worker picks up the job, changes the text to uppercase, and
              records a result.
            </p>
          </div>
        </li>
        <li>
          <span>3</span>
          <div>
            <strong>Check the result</strong>
            <p>
              The app saves the job and its status in a database so you can ask
              for them later.
            </p>
          </div>
        </li>
      </ol>
      <p className="dispatch-start">
        <strong>We’ll build toward this gradually.</strong> In your first
        lesson, Dispatch only answers a health request. The database and worker
        come later.
      </p>
    </section>
  );
  return (
    <>
      <div className="page-heading welcome-heading">
        <div className="eyebrow">WELCOME TO DOCKYARD</div>
        <h1>Learn to run a real application.</h1>
        <p className="intro">
          We’ll start with one Docker container, then build up to running and
          recovering a Kubernetes cluster. You’ll read a short lesson here and
          try it in your own terminal.
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
      {returning && continueCard}
      {introduction}
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
          Run containers → connect services → deploy to Kubernetes → secure and
          recover a cluster.
        </p>
        <button className="text-button" onClick={() => navigate("course")}>
          Explore your course <ArrowRight size={16} />
        </button>
      </section>
    </>
  );
}
