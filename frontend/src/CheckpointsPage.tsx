import { Download, FolderArchive, ArrowRight } from "lucide-react";
import type { Workbench } from "./useWorkbench";

export function CheckpointsPage({ model }: { model: Workbench }) {
  const { state, openLesson, navigate } = model;
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
      <section className="panel">
        <h2>Dispatch checkpoints</h2>
        {state.checkpoints.length ? (
          state.checkpoints.map((item) => (
            <article className="checkpoint-row" key={item.id}>
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
