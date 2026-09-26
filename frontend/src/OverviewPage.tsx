import type { Workbench } from "./useWorkbench";
import { ArrowRight, Clock3, Container, Terminal } from "lucide-react";
import { Topology } from "./teaching";
export function OverviewPage({ model }: { model: Workbench }) {
  const {
    state,
    busy,
    navigate,
    openLesson,
    completed,
    demonstrated,
    continueUnit,
  } = model;
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">YOUR ENGINEERING JOURNEY</div>
        <h1>
          Build understanding.
          <br />
          Then build the system.
        </h1>
        <p className="intro">
          From your first container to recovering a Kubernetes cluster.
          <br className="wide-only" /> One application, real infrastructure, and
          skills you can demonstrate.
        </p>
      </div>
      <section className="continue-card">
        <div>
          <div className="eyebrow">
            {state.last_unit
              ? "CONTINUE LEARNING"
              : "START WITH A REAL PROCESS"}
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
              Real terminal lab
            </span>
          </div>
          <button
            className="primary"
            disabled={!!busy || !continueUnit}
            onClick={() => continueUnit && void openLesson(continueUnit.id)}
          >
            {state.last_unit ? "Continue lesson" : "Start learning"}
            <ArrowRight size={17} />
          </button>
        </div>
        <div className="continue-visual">
          <div className="container-stack">
            <div className="stack-label">
              <Container size={20} />
              DISPATCH / API
            </div>
            <div className="stack-layer">Your application</div>
            <div className="stack-layer">Python runtime</div>
            <div className="stack-layer base">Linux environment</div>
          </div>
          <span className="small muted">
            A real application. A controlled environment.
          </span>
        </div>
      </section>
      <div className="stats-grid">
        <div className="stat">
          <span>Practiced</span>
          <strong>
            {completed}
            <small> units</small>
          </strong>
        </div>
        <div className="stat">
          <span>Independently demonstrated</span>
          <strong>
            {demonstrated}
            <small> skills</small>
          </strong>
        </div>
        <div className="stat">
          <span>Your environments</span>
          <strong>
            {state.labs.filter((item) => item.state === "ready").length}
            <small> prepared</small>
          </strong>
        </div>
      </div>
      <section className="project-panel">
        <div>
          <span className="eyebrow">MEET YOUR PROJECT</span>
          <h2>Dispatch grows with you.</h2>
          <p className="muted">
            Start with an API. Add persistence, background processing, reliable
            releases, and the operational practices that keep a system healthy.
          </p>
          <button className="text-button" onClick={() => navigate("course")}>
            Explore the learning path
            <ArrowRight size={16} />
          </button>
        </div>
        <Topology />
      </section>
      <section>
        <div className="section-heading">
          <h2>A practical path to depth</h2>
          <button className="text-button" onClick={() => navigate("course")}>
            View course
            <ArrowRight size={16} />
          </button>
        </div>
        <div className="phase-grid">
          {[
            "Container engineering",
            "Application development",
            "Platform engineering",
            "Cluster operations",
          ].map((title, index) => (
            <button
              className="phase-card"
              key={title}
              onClick={() => navigate("course")}
            >
              <span className="phase-number">0{index + 1}</span>
              <h3>{title}</h3>
              <p>
                {
                  [
                    "Images, networking, storage, and a complete Compose system.",
                    "Workloads, configuration, routing, and safe releases.",
                    "Scheduling, delivery, observability, and least privilege.",
                    "Build clusters, perform maintenance, and recover from failure.",
                  ][index]
                }
              </p>
              <ArrowRight size={19} />
            </button>
          ))}
        </div>
      </section>
    </>
  );
}
