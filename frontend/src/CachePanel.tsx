import { useState } from "react";
import { Download, RefreshCw, HardDrive } from "lucide-react";
import { api } from "./api";
import type { Workbench } from "./useWorkbench";

type CacheReport = {
  scope: string;
  units: {
    unit_id: string;
    title: string;
    missing: string[];
    limitations: string[];
    status: "missing" | "network-required" | "cached";
  }[];
  tools: { name: string; ready: boolean }[];
  images: { name: string; ready: boolean }[];
  packages: { name: string; ready: boolean }[];
  scanner_ready: boolean | null;
  private_cache_gib: number;
  soft_budget_gib: number;
  over_soft_budget: boolean;
  free_disk_gib: number;
  policy: string;
};

export function CachePanel({ model }: { model: Workbench }) {
  const [scope, setScope] = useState("module:1");
  const [report, setReport] = useState<CacheReport | null>(null);
  const { catalog, state, setError, setBusy, busy, opened, refresh } = model;
  const active = state.operations.find(
    (item) =>
      item.lab_id === "cache" &&
      ["running", "queued", "canceling"].includes(item.state),
  );
  const inspect = async (prefetch: boolean) => {
    const sequence = opened.current;
    setError("");
    setBusy(
      prefetch ? "Prefetching dependencies" : "Inspecting dependency cache",
    );
    try {
      const result = await api<CacheReport>(
        prefetch
          ? "/cache/prepare"
          : `/cache?scope=${encodeURIComponent(scope)}`,
        prefetch ? { scope } : undefined,
      );
      if (sequence === opened.current) setReport(result);
      await refresh();
    } catch (error) {
      if (sequence === opened.current) setError((error as Error).message);
    } finally {
      if (sequence === opened.current) setBusy("");
    }
  };
  const limitations = [
    ...new Set(report?.units.flatMap((unit) => unit.limitations) ?? []),
  ];
  return (
    <section className="panel cache-panel" aria-label="Dependency cache">
      <div className="section-heading">
        <h2>
          <HardDrive size={20} /> Prepare your learning cache
        </h2>
      </div>
      <p className="muted">
        Prefetch a module, a learning track, or the complete course. Downloads
        are pinned and verified; restarting a canceled preparation keeps
        completed downloads.
      </p>
      <div className="cache-controls">
        <label>
          Cache scope
          <select
            value={scope}
            disabled={!!busy || !!active}
            onChange={(event) => {
              setScope(event.target.value);
              setReport(null);
            }}
          >
            <option value="all">Complete course, incidents, and exams</option>
            <optgroup label="Learning tracks">
              {[1, 2, 3, 4].map((phase) => (
                <option key={phase} value={`track:${phase}`}>
                  {
                    catalog?.modules.find((module) => module.phase === phase)
                      ?.phase_title
                  }
                </option>
              ))}
            </optgroup>
            <optgroup label="Modules">
              {catalog?.modules.map((module) => (
                <option key={module.id} value={`module:${module.id}`}>
                  {String(module.id).padStart(2, "0")} · {module.title}
                </option>
              ))}
            </optgroup>
            <optgroup label="Individual activities">
              {catalog?.units.map((unit) => (
                <option key={unit.id} value={`unit:${unit.id}`}>
                  {unit.title}
                </option>
              ))}
            </optgroup>
          </select>
        </label>
        <div className="button-row">
          <button
            disabled={!!busy || !!active}
            onClick={() => void inspect(false)}
          >
            <RefreshCw size={15} /> Inspect cache
          </button>
          <button
            disabled={!!busy || !!active}
            onClick={() => void inspect(true)}
          >
            <Download size={15} /> Prefetch dependencies
          </button>
        </div>
      </div>
      {active && (
        <div className="cache-operation" role="status">
          <span>{active.detail || "Preparing the selected dependencies…"}</span>
          <button
            disabled={active.state === "canceling"}
            onClick={() =>
              void api(`/operations/${active.id}/cancel`, {})
                .then(refresh)
                .catch((error) => setError(error.message))
            }
          >
            {active.state === "canceling" ? "Canceling…" : "Cancel prefetch"}
          </button>
        </div>
      )}
      {report && (
        <div className="cache-report" aria-label="Cache readiness report">
          <dl className="import-counts">
            <div>
              <dt>Activities with declared dependencies cached</dt>
              <dd>
                {report.units.filter((unit) => unit.status === "cached").length}{" "}
                / {report.units.length}
              </dd>
            </div>
            <div>
              <dt>Pinned tools verified</dt>
              <dd>
                {report.tools.filter((tool) => tool.ready).length} /{" "}
                {report.tools.length}
              </dd>
            </div>
            <div>
              <dt>ARM64 images cached</dt>
              <dd>
                {report.images.filter((image) => image.ready).length} /{" "}
                {report.images.length}
              </dd>
            </div>
            <div>
              <dt>Native packages verified</dt>
              <dd>
                {report.packages.filter((pkg) => pkg.ready).length} /{" "}
                {report.packages.length}
              </dd>
            </div>
            <div>
              <dt>Private download cache</dt>
              <dd>{report.private_cache_gib} GiB</dd>
            </div>
            <div>
              <dt>Free host disk</dt>
              <dd>{report.free_disk_gib} GiB</dd>
            </div>
          </dl>
          <p className="small muted">{report.policy}</p>
          {report.over_soft_budget && (
            <p className="diagnostic">
              The private cache exceeds its {report.soft_budget_gib} GiB soft
              budget. No files were deleted automatically. Review disk use
              before prefetching more tracks.
            </p>
          )}
          {limitations.length > 0 && (
            <div className="cache-limitations">
              <h3>Steps that can still need a network</h3>
              {limitations.map((message) => (
                <p key={message}>{message}</p>
              ))}
            </div>
          )}
          <details>
            <summary>Readiness for each selected activity</summary>
            <div className="cache-activities">
              {report.units.map((unit) => (
                <article key={unit.unit_id}>
                  <div>
                    <strong>{unit.title}</strong>
                    <span
                      className={`status-label ${unit.status === "cached" ? "pass" : ""}`}
                    >
                      {unit.status === "cached"
                        ? "Dependencies cached"
                        : unit.status === "missing"
                          ? "Missing dependencies"
                          : "Network step remains"}
                    </span>
                  </div>
                  {unit.missing.length > 0 && (
                    <p className="small muted">
                      Missing: {unit.missing.join(", ")}
                    </p>
                  )}
                </article>
              ))}
            </div>
          </details>
        </div>
      )}
      <p className="small muted">
        Lessons, references, and saved progress are available offline. Runtime
        checks still require Docker or the owned VM environment to be running.
        Editing dependency versions can introduce additional downloads.
      </p>
    </section>
  );
}
