import { Download, FolderArchive, ArrowRight } from "lucide-react";
import { ContinueProject } from "./ContinueProject";
import type { Workbench } from "./useWorkbench";

export function CheckpointsPage({ model }: { model: Workbench }) {
  const { state, catalog, openLesson, navigate } = model;
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">YOUR PROJECT, WITH PROVENANCE</div>
        <h1>Work you can hand off.</h1>
        <p className="intro">
          Each successful mission preserves its source files and observed
          evidence. Later edits leave that checkpoint intact.
        </p>
      </div>
      {state.checkpoints.length > 0 && (
        <section className="panel portfolio-export">
          <div>
            <h2>Your Dispatch portfolio</h2>
            <p className="muted">
              The latest checkpoint for each completed mission, with authored
              source, observations, provenance, and runtime evidence in a
              readable handoff archive.
            </p>
          </div>
          <a className="button-link" href="/api/portfolio/export" download>
            <Download size={16} /> Export project portfolio
          </a>
        </section>
      )}
      <section className="panel">
        <h2>Dispatch checkpoints</h2>
        {state.checkpoints.length ? (
          state.checkpoints.map((item) => (
            <article className="checkpoint-item" key={item.id}>
              <div className="checkpoint-row">
                <div>
                  <span className="eyebrow">
                    {item.independent
                      ? "INDEPENDENT DEMONSTRATION"
                      : "SUPPORTED PRACTICE"}
                  </span>
                  <h3>{item.title}</h3>
                  <p className="muted small">
                    {new Date(item.created_at).toLocaleString()} · Revision{" "}
                    {item.revision} · {item.file_count} source files
                  </p>
                  <p className="muted small">
                    {item.excluded_count} files excluded. The archive manifest
                    explains removed credential documents and excluded files.
                  </p>
                </div>
                <div className="button-row">
                  <a
                    className="button-link"
                    href={`/api/checkpoints/${item.id}/download`}
                    download
                  >
                    <Download size={16} /> Download checkpoint
                  </a>
                  <button
                    className="text-button"
                    onClick={() => void openLesson(item.unit_id)}
                  >
                    Review mission <ArrowRight size={15} />
                  </button>
                </div>
              </div>
              <details className="checkpoint-continue">
                <summary>Continue in a later mission</summary>
                <ContinueProject
                  model={model}
                  checkpoint={item.id}
                  module={
                    catalog?.units.find((unit) => unit.id === item.unit_id)
                      ?.module ?? 24
                  }
                />
              </details>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <FolderArchive size={36} />
            <h3>Your first mission creates the first checkpoint.</h3>
            <p>
              Complete a mission's real behavior checks to preserve its
              infrastructure source, observations, and assessment evidence.
            </p>
            <button onClick={() => navigate("course")}>
              Explore missions <ArrowRight size={16} />
            </button>
          </div>
        )}
      </section>
      <p className="muted small">
        These archives are source portfolios. Keep database backups separately
        and verify their recovery procedures in the lab.
      </p>
    </>
  );
}
