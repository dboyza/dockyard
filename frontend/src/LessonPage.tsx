import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Circle,
  Clock3,
  Container,
  LoaderCircle,
  Play,
  RotateCcw,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import { api, type UnitSummary } from "./api";
import {
  currentPractice,
  learningStatus,
  reviewDue,
  reviewNeeded,
} from "./learning";
import { Results, Task, Understand } from "./LessonParts";
import type { Workbench } from "./useWorkbench";
import { Workspace } from "./Workspace";

const KINDS: Record<string, string> = {
  lesson: "Guided lab",
  mission: "Independent mission",
  incident: "Incident scenario",
};
const RUNTIMES: Record<string, string> = {
  docker: "Docker",
  kubernetes: "Kubernetes",
  linux: "Linux VMs",
};

export function LessonPage({ model }: { model: Workbench }) {
  const { state, lesson, lab, busy, panel, setPanel, navigate, perform } =
    model;
  // Hiding the panel lasts until a new result or the other view asks for it again.
  const panelKey = `${lesson?.id}:${panel}:${model.assessment?.id}`;
  const [hiddenPanel, setHiddenPanel] = useState("");
  const panelOpen = hiddenPanel !== panelKey;
  const setPanelOpen = (open: boolean) => setHiddenPanel(open ? "" : panelKey);
  const task = useRef<HTMLElement>(null);
  const working = !!lab && lab.state !== "absent";
  if (!lesson) return null;
  const incident = lesson.kind === "incident";
  const sequence = model.units
    .filter((unit) =>
      incident
        ? unit.kind === "incident"
        : unit.kind === "lesson" || unit.kind === "mission",
    )
    .sort((a, b) => a.module - b.module || a.order - b.order);
  const position = sequence.findIndex((unit) => unit.id === lesson.id);
  const previousUnit = position > 0 ? sequence[position - 1] : undefined;
  const nextUnit =
    position >= 0 && position < sequence.length - 1
      ? sequence[position + 1]
      : undefined;
  const progress = state.progress[lesson.id];
  const status = (
    <span className="lesson-status">
      {progress?.practiced && reviewDue(lesson.revision, progress) ? (
        <RotateCcw size={13} />
      ) : currentPractice(lesson.revision, progress) ? (
        <Check size={13} className="status-done" />
      ) : (
        <Circle size={12} />
      )}
      {learningStatus(
        lesson.revision,
        progress,
        !!state.checked[lesson.id] || (!!lab && lab.state !== "absent"),
      )}
    </span>
  );
  const eyebrow = `Module ${String(lesson.module).padStart(2, "0")} · ${KINDS[lesson.kind] ?? "Activity"}`;
  const back = (
    <button
      className="text-button muted"
      onClick={() => navigate(incident ? "incidents" : "course")}
    >
      <ArrowLeft size={15} />
      {incident ? "Incident scenarios" : "Course map"}
    </button>
  );
  const review = reviewNeeded(lesson.revision, progress) && (
    <p className="notice" role="status">
      This lesson has changed since your last passing assessment. Your earlier
      evidence is preserved. Check the current revision to update your skills
      record.
    </p>
  );
  const openTask = () => {
    setPanel("task");
    setPanelOpen(true);
    requestAnimationFrame(() => {
      task.current?.scrollIntoView({ block: "start" });
      task.current?.focus({ preventScroll: true });
    });
  };
  const results = <Results model={model} lesson={lesson} onTask={openTask} />;

  if (working)
    return (
      <Workspace
        model={model}
        unitId={lesson.id}
        runtime={lesson.runtime}
        retake={lesson.kind !== "lesson"}
        panelOpen={panelOpen}
        header={
          <div className="lesson-bar">
            {back}
            <div className="lesson-bar-title">
              <span className="eyebrow">{eyebrow}</span>
              <h1>{lesson.title}</h1>
            </div>
            {status}
            <Stepper
              label={incident ? "Incident navigation" : "Lesson navigation"}
              position={position}
              total={sequence.length}
              previous={previousUnit}
              next={nextUnit}
              open={model.openLesson}
            />
          </div>
        }
        panel={
          <section
            className="task-panel"
            ref={task}
            tabIndex={-1}
            aria-label="Your task and results"
          >
            <header>
              <div
                className="tabs"
                role="tablist"
                aria-label="Task and results"
              >
                {(["task", "results"] as const).map((item) => (
                  <button
                    key={item}
                    role="tab"
                    id={`tab-${item}`}
                    aria-controls="task-panel-body"
                    aria-selected={panel === item}
                    tabIndex={panel === item ? 0 : -1}
                    onKeyDown={(event) => {
                      if (!["ArrowRight", "ArrowLeft"].includes(event.key))
                        return;
                      event.preventDefault();
                      const other = item === "task" ? "results" : "task";
                      setPanel(other);
                      document.getElementById(`tab-${other}`)?.focus();
                    }}
                    onClick={() => {
                      setPanel(item);
                      setPanelOpen(true);
                    }}
                  >
                    {item === "task" ? "Your task" : "Results"}
                    {item === "results" && model.assessment && (
                      <span className={`dot ${model.assessment.status}`} />
                    )}
                  </button>
                ))}
              </div>
              <button
                className="icon"
                aria-expanded={panelOpen}
                aria-controls="task-panel-body"
                aria-label={panelOpen ? "Hide the task" : "Show the task"}
                onClick={() => setPanelOpen(!panelOpen)}
              >
                {panelOpen ? (
                  <ChevronDown size={17} />
                ) : (
                  <ChevronUp size={17} />
                )}
              </button>
            </header>
            <div
              className="task-panel-body"
              id="task-panel-body"
              role="tabpanel"
              aria-labelledby={`tab-${panel}`}
              tabIndex={0}
              hidden={!panelOpen}
            >
              {panel === "task" ? (
                <Task key={lesson.id} model={model} lesson={lesson} />
              ) : (
                results
              )}
            </div>
          </section>
        }
        footer={
          <LabBar
            model={model}
            next={
              !incident && currentPractice(lesson.revision, progress)
                ? nextUnit
                : undefined
            }
          />
        }
      >
        {review}
        <Understand model={model} lesson={lesson} onTask={openTask} />
      </Workspace>
    );

  return (
    <div className="lesson-read">
      <header className="lesson-heading">
        {back}
        <div className="eyebrow">{eyebrow}</div>
        <h1>{lesson.title}</h1>
        <p className="intro">{lesson.summary}</p>
        <div className="metadata">
          <span>
            <Clock3 size={14} />
            {lesson.minutes} min
          </span>
          <span>
            <Container size={14} />
            {RUNTIMES[lesson.runtime] ?? lesson.runtime}
          </span>
          {status}
          {position >= 0 && (
            <span>
              {position + 1} of {sequence.length}
            </span>
          )}
        </div>
      </header>
      {review}
      <div className="lesson-layout">
        <article className="lesson-document">
          <section aria-labelledby="understand-heading">
            <h2 className="lesson-step" id="understand-heading">
              <span aria-hidden="true">1</span> Understand
            </h2>
            <Understand model={model} lesson={lesson} onTask={openTask} />
          </section>
          <section ref={task} tabIndex={-1} aria-labelledby="task-heading">
            <h2 className="lesson-step" id="task-heading">
              <span aria-hidden="true">2</span> Your task
            </h2>
            <Task key={lesson.id} model={model} lesson={lesson} />
          </section>
          {model.assessment && (
            <section aria-labelledby="results-heading">
              <h2 className="lesson-step" id="results-heading">
                <span aria-hidden="true">3</span> Results from your last check
              </h2>
              {results}
            </section>
          )}
          {position >= 0 && (
            <nav
              className="lesson-pager"
              aria-label={
                incident ? "Incident navigation" : "Lesson navigation"
              }
            >
              {previousUnit ? (
                <button onClick={() => void model.openLesson(previousUnit.id)}>
                  <ArrowLeft size={16} />
                  <span>
                    <span className="pager-label">Previous</span>
                    <span className="pager-title">{previousUnit.title}</span>
                  </span>
                </button>
              ) : (
                <span />
              )}
              {nextUnit ? (
                <button
                  className="pager-next"
                  onClick={() => void model.openLesson(nextUnit.id)}
                >
                  <span>
                    <span className="pager-label">Next</span>
                    <span className="pager-title">{nextUnit.title}</span>
                  </span>
                  <ArrowRight size={16} />
                </button>
              ) : (
                <span />
              )}
            </nav>
          )}
        </article>
        <aside className="context-panel">
          <section className="lab-card" id="lab-controls">
            <div className="eyebrow">Your lab</div>
            <h3>
              <Terminal size={18} /> {RUNTIMES[lesson.runtime]} lab
            </h3>
            <p className="small muted">
              Prepare the lab when you are ready to try the task. A real shell
              opens beside the lesson.
              {lesson.runtime !== "docker" &&
                " Another running cluster is paused first to save memory."}
            </p>
            <DownloadEstimate key={lesson.id} unitId={lesson.id} />
            <button
              className="primary full"
              disabled={!!busy}
              onClick={() => void perform("prepare")}
            >
              {busy ? (
                <LoaderCircle className="spin" size={16} />
              ) : (
                <Play size={16} />
              )}
              Prepare lab
            </button>
            {busy === "prepare" && <OperationStatus model={model} />}
            {lab?.error && <p className="diagnostic">{lab.error}</p>}
          </section>
        </aside>
      </div>
    </div>
  );
}

/** How much preparing this lab still has to download, so the wait is no surprise. */
function DownloadEstimate({ unitId }: { unitId: string }) {
  type Estimate = { bytes: number; items: string[]; docker_ready: boolean };
  const [estimate, setEstimate] = useState<Estimate | null>(null);
  useEffect(() => {
    let alive = true;
    api<Estimate>(`/units/${unitId}/downloads`)
      .then((result) => alive && setEstimate(result))
      // The estimate is a courtesy; preparing reports any real problem.
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [unitId]);
  if (!estimate) return null;
  if (!estimate.docker_ready)
    return (
      <p className="diagnostic" role="note">
        Docker is not running. Start Docker, then choose Prepare lab.
      </p>
    );
  const megabytes = Math.round(estimate.bytes / 1024 ** 2);
  return (
    <p className="download-estimate small" role="note">
      {megabytes < 1 ? (
        "Everything this lab needs is already downloaded."
      ) : (
        <>
          First time: downloads about{" "}
          <strong>
            {megabytes >= 1024
              ? `${(megabytes / 1024).toFixed(1)} GB`
              : `${megabytes} MB`}
          </strong>{" "}
          ({estimate.items.slice(0, 3).join(", ")}
          {estimate.items.length > 3 &&
            `, and ${estimate.items.length - 3} more`}
          ).
        </>
      )}
    </p>
  );
}

/** Where this activity sits in its sequence, with the neighbors one click away. */
function Stepper({
  label,
  position,
  total,
  previous,
  next,
  open,
}: {
  label: string;
  position: number;
  total: number;
  previous?: UnitSummary;
  next?: UnitSummary;
  open: (id: string) => Promise<void>;
}) {
  if (position < 0) return null;
  return (
    <nav className="lesson-stepper" aria-label={label}>
      <button
        className="icon"
        disabled={!previous}
        aria-label={previous ? `Previous: ${previous.title}` : "Previous"}
        title={previous?.title}
        onClick={() => previous && void open(previous.id)}
      >
        <ChevronLeft size={17} />
      </button>
      <span className="small muted">
        {position + 1} of {total}
      </span>
      <button
        className="icon"
        disabled={!next}
        aria-label={next ? `Next: ${next.title}` : "Next"}
        title={next?.title}
        onClick={() => next && void open(next.id)}
      >
        <ChevronRight size={17} />
      </button>
    </nav>
  );
}

function OperationStatus({ model }: { model: Workbench }) {
  const { busy, activeOperation } = model;
  return (
    <div className="operation" role="status">
      <LoaderCircle size={14} className="spin" />
      {OPERATIONS[busy] || `${busy}…`}
      {activeOperation && (
        <button
          className="text-button"
          onClick={() =>
            void api(`/operations/${activeOperation.id}/cancel`, {})
          }
        >
          Cancel
        </button>
      )}
    </div>
  );
}

/**
 * The lab's state and Check work, kept in view at the foot of the lesson pane.
 * Once the lesson has passed, moving on becomes the main action.
 */
function LabBar({ model, next }: { model: Workbench; next?: UnitSummary }) {
  const { lab, busy, perform } = model;
  return (
    <div className="lab-bar">
      <div className={`lab-state ${labTone(lab?.state)}`}>
        <span className="dot" />
        {LAB_STATES[lab?.state || "absent"] || lab?.state}
      </div>
      {busy ? (
        <OperationStatus model={model} />
      ) : (
        <span className="small muted lab-bar-hint">
          {next
            ? "Your work passed this check."
            : "Check work tests what your lab does right now."}
        </span>
      )}
      <button
        className={next ? undefined : "primary"}
        disabled={!!busy || TRANSITIONS.has(lab?.state ?? "")}
        onClick={() => void perform("check")}
      >
        {busy === "check" ? (
          <LoaderCircle className="spin" size={16} />
        ) : (
          <ShieldCheck size={16} />
        )}
        {next ? "Check again" : "Check work"}
      </button>
      {next && (
        <button
          className="primary"
          title={next.title}
          aria-label={`Next lesson: ${next.title}`}
          onClick={() => void model.openLesson(next.id)}
        >
          Next lesson
          <ArrowRight size={16} />
        </button>
      )}
    </div>
  );
}

// A stopped or failed lab can still be checked; the evidence explains what is wrong.
const TRANSITIONS = new Set(["preparing", "stopping", "checking", "cleaning"]);

const LAB_STATES: Record<string, string> = {
  absent: "Not prepared",
  preparing: "Preparing…",
  ready: "Ready",
  stopped: "Stopped",
  stopping: "Stopping…",
  checking: "Checking…",
  cleaning: "Cleaning up…",
  failed: "Needs attention",
};

function labTone(state?: string) {
  if (state === "ready") return "pass";
  if (state === "failed") return "fail";
  if (state && state !== "absent" && state !== "stopped") return "busy";
  return "";
}

const OPERATIONS: Record<string, string> = {
  prepare: "Preparing your lab…",
  check: "Checking your work…",
  stop: "Stopping the lab…",
  resume: "Resuming the lab…",
  reset: "Resetting the lab…",
  retake: "Setting up a fresh attempt…",
  clean: "Cleaning up…",
};
