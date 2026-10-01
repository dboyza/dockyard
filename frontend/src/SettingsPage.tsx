import { useState } from "react";
import {
  Download,
  FileArchive,
  Moon,
  RotateCcw,
  Sun,
  Upload,
} from "lucide-react";
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
type ResetSummary = {
  labs: string[];
  activities: number;
  assessments: number;
  notes: number;
  checkpoints: number;
  exams: number;
};
type ResetResult = { cleaned_labs: string[]; remaining: string[] };
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
    navigate,
    setNotice,
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
  const erase = async () => {
    setDialog(null);
    setError("");
    setBusy("Cleaning up labs and erasing local data");
    try {
      const result = await api<ResetResult>("/profile/reset", {
        confirmed: true,
      });
      await refresh();
      navigate("home");
      setNotice("Dockyard was reset. You’re starting fresh.");
      if (result.remaining.length)
        setError(
          `Some files could not be deleted. Remove them yourself: ${result.remaining.join(", ")}`,
        );
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy("");
    }
  };
  const confirmErase = async () => {
    setError("");
    try {
      const found = await api<ResetSummary>("/profile/reset");
      const count = (n: number, one: string, many = one + "s") =>
        `${n} ${n === 1 ? one : many}`;
      const erased = `your progress on ${count(found.activities, "activity", "activities")}, ${count(found.assessments, "check result")}, ${count(found.exams, "exam attempt")}, ${count(found.notes, "note")}, and ${count(found.checkpoints, "saved mission file")}`;
      const labs = found.labs.length;
      setDialog({
        title: "Erase all local data?",
        body: `${
          labs
            ? `First, ${count(labs, "lab is", "labs are")} cleaned up, including containers, clusters, and VMs. Then ${erased} are permanently erased.`
            : `This permanently erases ${erased}.`
        } This cannot be undone.`,
        requireText: "erase",
        confirmLabel: "Erase everything",
        danger: true,
        action: () => void erase(),
      });
    } catch (error) {
      setError((error as Error).message);
    }
  };
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">Settings</div>
        <h1>Settings and data</h1>
        <p className="intro">
          Choose a theme, back up or move your progress, or start fresh.
        </p>
      </div>
      <section className="panel" aria-label="Appearance settings">
        <h2>Theme</h2>
        <div className="button-row">
          <button
            aria-pressed={theme === "dark"}
            onClick={() => setTheme("dark")}
          >
            <Moon size={16} /> Dark
          </button>
          <button
            aria-pressed={theme === "light"}
            onClick={() => setTheme("light")}
          >
            <Sun size={16} /> Light
          </button>
        </div>
      </section>
      <div className="placement-grid">
        <section className="panel" aria-label="Export progress">
          <FileArchive className="settings-icon" size={24} />
          <h2>Back up your progress</h2>
          <p className="muted">
            Download one file with your progress, check results, exam history,
            notes, and saved mission files.
          </p>
          <p className="muted">
            It never includes running labs, VM disks, cached images, cluster
            credentials, or private keys.
          </p>
          <a
            className="button-link"
            href="/api/progress/export"
            download="dockyard-progress.zip"
          >
            <Download size={16} /> Download a backup
          </a>
        </section>
        <section className="panel" aria-label="Import progress">
          <Upload className="settings-icon" size={24} />
          <h2>Restore from a backup</h2>
          <p className="muted">
            You’ll see what a backup contains before anything is merged. Your
            current notes and workspace files are kept; anything that conflicts
            is saved in a separate folder.
          </p>
          <label className="archive-picker">
            <span>Choose a backup file</span>
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
            Up to 64 MiB. Restoring history does not recreate running labs or
            restart an exam timer.
          </p>
        </section>
      </div>
      <section className="panel start-fresh" aria-label="Start fresh">
        <RotateCcw className="settings-icon" size={24} />
        <h2>Start fresh</h2>
        <p className="muted">
          Erase everything Dockyard has saved about your learning and begin
          again, as on your first launch.
        </p>
        <ul className="muted">
          <li>
            <strong>Erased:</strong> progress, check results, exam attempts,
            notes, saved mission files, backups, and every lab with its
            workspace files. Labs are cleaned up first, including their
            containers, clusters, and VMs.
          </li>
          <li>
            <strong>Kept:</strong> your theme, and the tools and images Dockyard
            downloaded, so labs start quickly again.
          </li>
        </ul>
        <p className="muted">
          Download a backup first if you might want this history later.
        </p>
        <button
          className="danger"
          disabled={!!busy}
          onClick={() => void confirmErase()}
        >
          Erase all local data
        </button>
      </section>
      <p className="small muted settings-version">
        Dockyard {model.catalog?.version}. Include this version and the output
        of <code>./dockyard doctor</code> when you report a problem.
      </p>
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
