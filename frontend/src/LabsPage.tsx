import { CachePanel } from "./CachePanel";
import type { Workbench } from "./useWorkbench";
import {
  ArrowRight,
  FlaskConical,
  Layers3,
  RefreshCw,
  Terminal,
} from "lucide-react";
import { api, type Doctor } from "./api";
export function LabsPage({ model }: { model: Workbench }) {
  const {
    state,
    setError,
    busy,
    doctor,
    setDoctor,
    navigate,
    openLesson,
    perform,
    units,
  } = model;
  const activeLabs = state.labs.filter((item) => item.state !== "absent");
  const runningLabs = activeLabs.filter((item) => item.state === "ready");
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">Labs and tools</div>
        <h1>Lab manager</h1>
        <p className="intro">
          See what is prepared, inspect tool readiness, and stop resources you
          are not using.
        </p>
      </div>
      <section className="lab-list" aria-labelledby="active-labs">
        <header>
          <h2 id="active-labs">Your labs</h2>
          <span className="lab-list-actions">
            <span className="small muted">
              {activeLabs.length === 1
                ? "1 lab on this computer"
                : `${activeLabs.length} labs on this computer`}
            </span>
            {runningLabs.length > 1 && (
              <button
                disabled={!!busy}
                onClick={async () => {
                  for (const item of runningLabs)
                    await perform("stop", false, item.unit_id);
                }}
              >
                Stop all
              </button>
            )}
          </span>
        </header>
        {activeLabs.length ? (
          activeLabs.map((item) => (
            <article className="resource-card" key={item.id}>
              <div>
                <h3>
                  {units.find((unit) => unit.id === item.unit_id)?.title ||
                    item.unit_id}
                </h3>
                <div className="resource-meta">
                  <span
                    className={`status-label ${
                      item.state === "ready"
                        ? "pass"
                        : item.state === "failed"
                          ? "fail"
                          : ""
                    }`}
                  >
                    {LAB_STATE_LABELS[item.state] || item.state}
                  </span>
                  <span className="mono muted small">{item.workspace}</span>
                </div>
                {item.state === "preparing" && item.resources?.stage && (
                  <p className="small" role="status">
                    {item.resources?.stage}
                  </p>
                )}
                {item.error && <p className="diagnostic">{item.error}</p>}
              </div>
              <div className="button-row">
                <button onClick={() => void openLesson(item.unit_id)}>
                  Open lesson
                  <ArrowRight size={15} />
                </button>
                <button
                  disabled={!!busy}
                  onClick={() =>
                    void perform(
                      item.state === "stopped" ? "resume" : "stop",
                      false,
                      item.unit_id,
                    )
                  }
                >
                  {item.state === "stopped" ? "Resume" : "Stop"}
                </button>
                <button
                  className="danger"
                  disabled={!!busy}
                  onClick={() => void perform("clean", false, item.unit_id)}
                >
                  Clean up
                </button>
              </div>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <FlaskConical size={32} />
            <h3>No labs on this computer right now.</h3>
            <p>
              Open a lesson and choose Prepare lab to create one. Your own
              Docker containers and clusters are never shown or changed here.
            </p>
            <button className="primary" onClick={() => navigate("course")}>
              Browse the course
              <ArrowRight size={16} />
            </button>
          </div>
        )}
      </section>
      <section className="panel doctor">
        <div className="section-heading">
          <h2>Environment readiness</h2>
          <button
            onClick={() =>
              api<Doctor>("/doctor")
                .then(setDoctor)
                .catch((e) => setError(e.message))
            }
          >
            <RefreshCw size={15} />
            Check again
          </button>
        </div>
        {doctor ? (
          <>
            <div className="readiness-grid">
              <div>
                <span
                  className={`dot ${doctor.docker_ready ? "pass" : "fail"}`}
                />
                <strong>Docker</strong>
                <span>
                  {doctor.docker_ready
                    ? doctor.docker_version
                    : "Not available"}
                </span>
              </div>
              <div>
                <Layers3 size={16} />
                <strong>Free disk</strong>
                <span>{doctor.free_disk_gib} GiB</span>
              </div>
              <div>
                <Terminal size={16} />
                <strong>External terminal</strong>
                <span>
                  {doctor.terminal || "None found; use the built-in one"}
                </span>
              </div>
            </div>
            <p className="small muted">
              {doctor.wsl ? "WSL 2" : doctor.system} {doctor.architecture} ·{" "}
              {doctor.host_memory_gib === null
                ? "Host RAM not reported"
                : `${doctor.host_memory_gib} GiB host RAM`}{" "}
              ·{" "}
              {doctor.memory_free_percent === null
                ? "Memory pressure unavailable"
                : `${doctor.memory_free_percent}% memory available reported by the host`}
            </p>
            <p className="small muted">
              {doctor.cluster_policy} Native profiles reserve up to{" "}
              {doctor.vm_budget_gib} GiB. Switching labs pauses the previous
              owned cluster in this profile; another profile must release its
              own cluster first.
            </p>
            {doctor.docker_tools_error && (
              <p className="diagnostic">{doctor.docker_tools_error}</p>
            )}
            {doctor.native_vm_blocker && (
              <p className="diagnostic">{doctor.native_vm_blocker}</p>
            )}
            {doctor.docker_error && (
              <p className="diagnostic">{doctor.docker_error}</p>
            )}
          </>
        ) : (
          <p className="muted">Checking your local environment…</p>
        )}
      </section>
      <CachePanel model={model} />
    </>
  );
}

const LAB_STATE_LABELS: Record<string, string> = {
  preparing: "Preparing",
  ready: "Ready",
  stopped: "Stopped",
  stopping: "Stopping",
  checking: "Checking",
  cleaning: "Cleaning up",
  failed: "Needs attention",
};
