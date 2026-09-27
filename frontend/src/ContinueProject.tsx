import { useState } from "react";
import { ArrowRight, GitBranch } from "lucide-react";
import { api } from "./api";
import type { Workbench } from "./useWorkbench";

type Preview = {
  checkpoint_id: string;
  checkpoint_digest: string;
  source_title: string;
  target_id: string;
  target_revision: number;
  target_title: string;
  supported: boolean;
  policy: string;
  files: {
    path: string;
    relationship: "unchanged" | "replace" | "add";
    diff: string;
  }[];
};

export function ContinueProject({
  model,
  checkpoint,
  module,
}: {
  model: Workbench;
  checkpoint: string;
  module: number;
}) {
  const [target, setTarget] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const {
    catalog,
    state,
    opened,
    setBusy,
    busy,
    setError,
    setDialog,
    refresh,
    openLesson,
  } = model;
  const choices = (catalog?.units ?? []).filter(
    (u) =>
      u.kind === "mission" &&
      u.module > module &&
      !state.labs.some((l) => l.unit_id === u.id),
  );
  const inspect = async () => {
    const sequence = opened.current;
    setBusy("Comparing checkpoint source");
    setError("");
    try {
      const result = await api<Preview>(
        `/checkpoints/${checkpoint}/continue?target_id=${encodeURIComponent(target)}`,
      );
      if (sequence === opened.current) {
        setPreview(result);
        setSelected([]);
      }
    } catch (error) {
      if (sequence === opened.current) setError((error as Error).message);
    } finally {
      if (sequence === opened.current) setBusy("");
    }
  };
  const carry = async () => {
    if (!preview) return;
    const sequence = opened.current;
    setDialog(null);
    setError("");
    setBusy("Creating project continuation");
    try {
      await api(`/checkpoints/${checkpoint}/continue`, {
        target_id: preview.target_id,
        target_revision: preview.target_revision,
        checkpoint_digest: preview.checkpoint_digest,
        selected,
        confirmed: true,
      });
      await refresh();
      if (sequence === opened.current) {
        setPreview(null);
        await openLesson(preview.target_id);
      }
    } catch (error) {
      if (sequence === opened.current) setError((error as Error).message);
    } finally {
      if (sequence === opened.current) setBusy("");
    }
  };
  return (
    <div className="project-continuation">
      <h3>
        <GitBranch size={17} /> Continue your Dispatch project
      </h3>
      <p className="muted small">
        Choose an unstarted later mission, compare its scaffold with your saved
        source, and carry only the files you want to adapt.
      </p>
      {choices.length ? (
        <div className="button-row">
          <label className="continuation-target">
            Later mission
            <select
              value={target}
              onChange={(event) => {
                setTarget(event.target.value);
                setPreview(null);
                setSelected([]);
              }}
              disabled={!!busy}
            >
              <option value="">Choose a later mission</option>
              {choices.map((u) => (
                <option key={u.id} value={u.id}>
                  Module {u.module}: {u.title}
                </option>
              ))}
            </select>
          </label>
          <button disabled={!target || !!busy} onClick={() => void inspect()}>
            Compare source <ArrowRight size={15} />
          </button>
        </div>
      ) : (
        <p className="muted">
          There are no unstarted later missions. You can download this
          checkpoint and adapt individual files in an existing terminal
          workspace.
        </p>
      )}
      {preview && (
        <section
          className="continuation-preview"
          aria-label="Checkpoint source comparison"
        >
          <h4>{preview.target_title}</h4>
          <p>{preview.policy}</p>
          {preview.supported && (
            <p className="callout">
              This checkpoint used learning support. Its continuation stays
              marked as supported practice until an independent retake.
            </p>
          )}
          <p className="small muted">
            No files are selected automatically. Differences compare the new
            mission scaffold with your checkpoint; review application and script
            changes carefully before carrying them forward.
          </p>
          {preview.files.map((file) => (
            <div className="continuation-file" key={file.path}>
              <label>
                <input
                  type="checkbox"
                  checked={selected.includes(file.path)}
                  onChange={(event) =>
                    setSelected((old) =>
                      event.target.checked
                        ? [...old, file.path]
                        : old.filter((name) => name !== file.path),
                    )
                  }
                />{" "}
                <code>{file.path}</code>
                <span className="small muted">
                  {file.relationship === "replace"
                    ? "Replaces new scaffold file"
                    : file.relationship === "add"
                      ? "Adds saved file"
                      : "Same content"}
                </span>
              </label>
              {file.diff && (
                <details>
                  <summary>Review source differences</summary>
                  <pre>{file.diff}</pre>
                </details>
              )}
            </div>
          ))}
          <button
            className="primary"
            disabled={!!busy || !selected.length}
            onClick={() =>
              setDialog({
                title: "Create a project continuation?",
                body: `Create a fresh workspace for ${preview.target_title} using ${selected.length} selected checkpoint files. No environment or source script will run yet. Existing workspaces stay intact.`,
                action: () => void carry(),
              })
            }
          >
            Carry {selected.length} selected{" "}
            {selected.length === 1 ? "file" : "files"} forward
          </button>
        </section>
      )}
    </div>
  );
}
