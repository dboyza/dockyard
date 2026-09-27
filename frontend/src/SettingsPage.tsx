import { useState } from "react";
import { Download, FileArchive, Sun, Moon, Upload } from "lucide-react";
import { api } from "./api";
import type { Workbench } from "./useWorkbench";

type Preview = {
  digest: string;
  created_at: string;
  progress_units: number;
  new_progress_units: number;
  assessments: number;
  exams: number;
  checkpoints: number;
  draft_files: number;
  notes: number;
  preserved_local_notes: number;
  older_revisions: number;
  policy: string;
};
type Receipt = Preview & {
  directory: string;
  backup: string;
  already_imported: boolean;
};

export function SettingsPage({ model }: { model: Workbench }) {
  const {
    theme,
    setTheme,
    busy,
    setBusy,
    setError,
    setDialog,
    refresh,
    opened,
  } = model;
  const [preview, setPreview] = useState<Preview | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [filename, setFilename] = useState("");
  const inspect = async (file: File | undefined) => {
    if (!file) return;
    const sequence = opened.current;
    setError("");
    setPreview(null);
    setReceipt(null);
    setFilename(file.name);
    if (file.size > 64 * 1024 ** 2) {
      setError("Choose a progress archive no larger than 64 MiB.");
      return;
    }
    setBusy("Inspecting progress archive");
    try {
      const response = await fetch("/api/progress/preview", {
        method: "POST",
        headers: { "Content-Type": "application/zip", "X-Dockyard": "1" },
        body: file,
      });
      const result = await response.json();
      if (!response.ok)
        throw new Error(result.detail || "The archive could not be inspected.");
      if (sequence === opened.current) setPreview(result);
    } catch (error) {
      if (sequence === opened.current) setError((error as Error).message);
    } finally {
      if (sequence === opened.current) setBusy("");
    }
  };
  const merge = async () => {
    if (!preview) return;
    const sequence = opened.current;
    setDialog(null);
    setBusy("Merging historical progress");
    setError("");
    try {
      const result = await api<Receipt>("/progress/import", {
        digest: preview.digest,
        confirmed: true,
      });
      if (sequence === opened.current) {
        setReceipt(result);
        setPreview(null);
      }
      await refresh();
    } catch (error) {
      if (sequence === opened.current) setError((error as Error).message);
    } finally {
      if (sequence === opened.current) setBusy("");
    }
  };
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">PERSONAL, LOCAL, PORTABLE</div>
        <h1>Keep your work yours.</h1>
        <p className="intro">
          Choose your reading theme and keep a portable copy of your learning
          history, observations, and infrastructure source.
        </p>
      </div>
      <section className="panel" aria-label="Appearance settings">
        <h2>Reading theme</h2>
        <div className="button-row">
          <button
            aria-pressed={theme === "dark"}
            onClick={() => setTheme("dark")}
          >
            <Moon size={16} /> Dark workbench
          </button>
          <button
            aria-pressed={theme === "light"}
            onClick={() => setTheme("light")}
          >
            <Sun size={16} /> Light workbench
          </button>
        </div>
      </section>
      <div className="placement-grid">
        <section className="panel" aria-label="Export progress">
          <FileArchive className="settings-icon" size={24} />
          <h2>A portable learning archive</h2>
          <p className="muted">
            Includes progress, assessment evidence, exam history, notes, mission
            checkpoints, and portable source drafts. Each archive records its
            file hashes and source exclusions.
          </p>
          <p className="muted">
            Live containers, VM disks, image caches, kubeconfigs, private keys,
            and known lab credentials are excluded. Database recovery remains a
            separate lab skill.
          </p>
          <a
            className="button-link"
            href="/api/progress/export"
            download="dockyard-progress.zip"
          >
            <Download size={16} /> Export progress archive
          </a>
        </section>
        <section className="panel" aria-label="Import progress">
          <Upload className="settings-icon" size={24} />
          <h2>Bring your history forward</h2>
          <p className="muted">
            Inspect an archive before merging it. Existing notes and active
            workspace files stay in place. Imported drafts and conflicting notes
            go into a separate folder.
          </p>
          <label className="archive-picker">
            <span>Choose a Dockyard progress archive</span>
            <input
              type="file"
              accept=".zip,application/zip"
              disabled={!!busy}
              onChange={(event) => {
                void inspect(event.target.files?.[0]);
                event.target.value = "";
              }}
            />
          </label>
          <p className="small muted">
            Up to 64 MiB compressed. Importing historical evidence does not
            recreate a running lab or restart an exam timer.
          </p>
        </section>
      </div>
      {preview && (
        <section
          className="panel import-preview"
          aria-label="Progress import preview"
        >
          <div className="eyebrow">REVIEW BEFORE MERGING</div>
          <h2>{filename}</h2>
          <p className="muted">
            Created {new Date(preview.created_at).toLocaleString()}
          </p>
          <dl className="import-counts">
            <div>
              <dt>Units with progress</dt>
              <dd>{preview.progress_units}</dd>
            </div>
            <div>
              <dt>Recorded assessments</dt>
              <dd>{preview.assessments}</dd>
            </div>
            <div>
              <dt>Exam attempts</dt>
              <dd>{preview.exams}</dd>
            </div>
            <div>
              <dt>Mission checkpoints</dt>
              <dd>{preview.checkpoints}</dd>
            </div>
            <div>
              <dt>Portable draft files</dt>
              <dd>{preview.draft_files}</dd>
            </div>
            <div>
              <dt>Saved notes</dt>
              <dd>{preview.notes}</dd>
            </div>
          </dl>
          <p>{preview.policy}</p>
          {preview.preserved_local_notes > 0 && (
            <p className="muted">
              {preview.preserved_local_notes} existing notes differ and will be
              preserved. The imported versions remain available in the import
              folder.
            </p>
          )}
          {preview.older_revisions > 0 && (
            <p className="muted">
              {preview.older_revisions} progress records use earlier lesson
              revisions and will remain due for reassessment.
            </p>
          )}
          <button
            className="primary"
            disabled={!!busy}
            onClick={() =>
              setDialog({
                title: "Merge this learning archive?",
                body: `Import ${preview.assessments} historical assessments and ${preview.checkpoints} checkpoints. Dockyard backs up the progress database first and preserves your current workspaces and existing notes.`,
                action: () => void merge(),
              })
            }
          >
            Merge reviewed archive
          </button>
        </section>
      )}
      {receipt && (
        <section
          className="panel import-receipt"
          aria-label="Progress import result"
        >
          <div className="eyebrow">
            {receipt.already_imported ? "ALREADY IMPORTED" : "HISTORY MERGED"}
          </div>
          <h2>Your current work is preserved.</h2>
          <p>
            Review imported evidence in Skill evidence, saved exams in Exam
            practice, and mission archives in Project checkpoints.
          </p>
          <h3>Imported drafts and observations</h3>
          <pre>{receipt.directory}</pre>
          <h3>Database backup from before the merge</h3>
          <pre>{receipt.backup}</pre>
          <p className="muted">
            Source drafts are separate from active labs. Prepare a fresh lab
            before adapting or checking that work.
          </p>
        </section>
      )}
    </>
  );
}
