import { ArrowRight, FlaskConical, Play, Square } from "lucide-react";
import { usePopover } from "./usePopover";
import type { Workbench } from "./useWorkbench";

const STATES: Record<string, string> = {
  preparing: "Preparing",
  ready: "Running",
  stopped: "Stopped",
  stopping: "Stopping",
  checking: "Checking",
  cleaning: "Cleaning up",
  failed: "Needs attention",
};

/** Every lab on this computer, one click from any page, so none is forgotten. */
export function LabsMenu({ model }: { model: Workbench }) {
  const { state, units, busy, perform, openLesson, navigate } = model;
  const { open, setOpen, anchor } = usePopover<HTMLDivElement>();
  const labs = state.labs.filter((item) => item.state !== "absent");
  if (!labs.length) return null;
  const running = labs.filter((item) => item.state !== "stopped");
  const ready = labs.filter((item) => item.state === "ready");
  const summary = running.length
    ? `${running.length} ${running.length === 1 ? "lab" : "labs"} running`
    : `${labs.length} ${labs.length === 1 ? "lab" : "labs"} stopped`;
  return (
    <div className="labs-menu" ref={anchor}>
      <button
        className={`labs-chip ${running.length ? "live" : ""}`}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen(!open)}
      >
        <FlaskConical size={15} />
        {summary}
      </button>
      {open && (
        <div
          className="popover"
          role="dialog"
          aria-label="Labs on this computer"
        >
          <div className="eyebrow">Labs on this computer</div>
          <ul>
            {labs.map((item) => (
              <li key={item.id}>
                <button
                  className="text-button"
                  onClick={() => {
                    setOpen(false);
                    void openLesson(item.unit_id);
                  }}
                >
                  {units.find((unit) => unit.id === item.unit_id)?.title ??
                    item.unit_id}
                </button>
                <span className={`labs-state ${item.state}`}>
                  {STATES[item.state] ?? item.state}
                </span>
                {(item.state === "ready" || item.state === "stopped") && (
                  <button
                    className="icon"
                    disabled={!!busy}
                    aria-label={`${item.state === "stopped" ? "Resume" : "Stop"} ${
                      units.find((unit) => unit.id === item.unit_id)?.title ??
                      "this lab"
                    }`}
                    onClick={() =>
                      void perform(
                        item.state === "stopped" ? "resume" : "stop",
                        false,
                        item.unit_id,
                      )
                    }
                  >
                    {item.state === "stopped" ? (
                      <Play size={14} />
                    ) : (
                      <Square size={13} />
                    )}
                  </button>
                )}
              </li>
            ))}
          </ul>
          <div className="popover-actions">
            {ready.length > 1 && (
              <button
                className="small-button"
                disabled={!!busy}
                onClick={async () => {
                  for (const item of ready)
                    await perform("stop", false, item.unit_id);
                }}
              >
                Stop all
              </button>
            )}
            <button
              className="text-button"
              onClick={() => {
                setOpen(false);
                navigate("labs");
              }}
            >
              Lab manager <ArrowRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
