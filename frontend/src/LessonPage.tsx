import { useState } from "react";
import { TerminalLauncher } from "./TerminalLauncher";
import { LiveLabMap } from "./LiveLabMap";
import type { Workbench } from "./useWorkbench";
import { api } from "./api";
import { CodeBlock, Markdown, referenceTitle } from "./teaching";
import { ReconciliationModel } from "./ReconciliationModel";
import { QuorumModel } from "./QuorumModel";
import { StorageModel } from "./StorageModel";
import { learningStatus, reviewNeeded } from "./learning";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Circle,
  Clock3,
  Container,
  Copy,
  ExternalLink,
  FileText,
  LoaderCircle,
  Play,
  RefreshCw,
  ShieldCheck,
  Square,
  Terminal,
} from "lucide-react";
export function LessonPage({ model }: { model: Workbench }) {
  const {
    state,
    lesson,
    tab,
    setTab,
    setError,
    setNotice,
    busy,
    hints,
    reference,
    prediction,
    setPrediction,
    predictionSubmitted,
    setPredictionSubmitted,
    assessment,
    note,
    setNote,
    navigate,
    lab,
    activeOperation,
    perform,
    revealHint,
    revealReference,
  } = model;
  const [saved, setSaved] = useState({
    id: lesson?.id,
    text: note,
    status: "",
  });
  if (lesson && saved.id !== lesson.id)
    setSaved({ id: lesson.id, text: note, status: "" });
  if (!lesson) return null;
  const saveNote = (announce: boolean) =>
    api(`/units/${lesson.id}/note`, { body: note })
      .then(() => {
        setSaved({ id: lesson.id, text: note, status: "Saved" });
        if (announce) setNotice("Your observations were saved locally.");
      })
      .catch((e) => setError(e.message));
  const prerequisites = model.units.filter((unit) =>
    lesson.prerequisites.includes(unit.id),
  );
  const nextLesson = model.units.find(
    (unit) =>
      (unit.kind === "lesson" || unit.kind === "mission") &&
      (unit.module > lesson.module ||
        (unit.module === lesson.module && unit.order > lesson.order)),
  );
  return (
    <>
      <div className="lesson-heading">
        <button
          className="text-button muted"
          onClick={() =>
            navigate(lesson.kind === "incident" ? "incidents" : "course")
          }
        >
          <ArrowLeft size={15} />
          {lesson.kind === "incident" ? "Incident scenarios" : "Course map"}
        </button>
        <div className="eyebrow">
          MODULE {String(lesson.module).padStart(2, "0")} /{" "}
          {lesson.kind === "lesson"
            ? "GUIDED LAB"
            : lesson.kind === "incident"
              ? "INCIDENT SCENARIO"
              : "INDEPENDENT MISSION"}
        </div>
        <h1>{lesson.title}</h1>
        <p className="intro">{lesson.summary}</p>
        <div className="metadata">
          <span>
            <Clock3 size={14} />
            {lesson.minutes} min
          </span>
          <span>
            <Container size={14} />
            {lesson.runtime === "docker"
              ? "Docker"
              : lesson.runtime === "linux"
                ? "Linux VMs"
                : "Kubernetes"}
          </span>
          <span>
            <Circle size={12} />
            {learningStatus(lesson.revision, state.progress[lesson.id])}
          </span>
        </div>
      </div>
      <a className="mobile-lab-link" href="#lab-controls">
        Open lab controls <ArrowRight size={15} />
      </a>
      {reviewNeeded(lesson.revision, state.progress[lesson.id]) && (
        <p className="notice" role="status">
          This lesson has changed since your last passing assessment. Your
          earlier evidence is preserved. Check the current revision to update
          your skills record.
        </p>
      )}
      <div className="lesson-layout">
        <section className="lesson-content">
          <div className="tabs" role="tablist" aria-label="Lesson sections">
            {(["learn", "mission", "evidence"] as const).map((item) => (
              <button
                key={item}
                role="tab"
                id={`tab-${item}`}
                aria-controls={`panel-${item}`}
                tabIndex={tab === item ? 0 : -1}
                onKeyDown={(event) => {
                  const sections = ["learn", "mission", "evidence"] as const;
                  const position = sections.indexOf(item);
                  const next =
                    event.key === "ArrowRight"
                      ? (position + 1) % 3
                      : event.key === "ArrowLeft"
                        ? (position + 2) % 3
                        : event.key === "Home"
                          ? 0
                          : event.key === "End"
                            ? 2
                            : null;
                  if (next !== null) {
                    event.preventDefault();
                    setTab(sections[next]);
                    document.getElementById(`tab-${sections[next]}`)?.focus();
                  }
                }}
                aria-selected={tab === item}
                onClick={() => setTab(item)}
              >
                {item === "learn"
                  ? "Understand"
                  : item === "mission"
                    ? "Your task"
                    : "Evidence"}
                {item === "evidence" && assessment && (
                  <span className={`dot ${assessment.status}`} />
                )}
              </button>
            ))}
          </div>
          <div
            className="lesson-panel"
            role="tabpanel"
            id={`panel-${tab}`}
            aria-labelledby={`tab-${tab}`}
            tabIndex={0}
          >
            {tab === "learn" && (
              <>
                <aside
                  className="prerequisite-help"
                  aria-label="Before you begin"
                >
                  <strong>Before you begin</strong>
                  {prerequisites.length ? (
                    <>
                      <p className="small muted">
                        This lesson builds on the work below. If it feels
                        unfamiliar, start there. You can still try this lesson
                        now.
                      </p>
                      <div className="button-row">
                        {prerequisites.map((unit) => (
                          <button
                            className="text-button"
                            key={unit.id}
                            onClick={() => void model.openLesson(unit.id)}
                          >
                            {unit.title}
                            <ArrowRight size={14} />
                          </button>
                        ))}
                      </div>
                    </>
                  ) : (
                    <p className="small muted">
                      No Docker experience needed. You’ll use a terminal to run
                      the commands below. Open the short terminal guide if
                      commands, files, or variables are new to you.
                    </p>
                  )}
                  <button
                    className="text-button"
                    onClick={() =>
                      model.openReference(
                        `primer/${lesson.runtime === "docker" ? "terminal" : lesson.runtime === "linux" ? "linux" : "yaml"}`,
                      )
                    }
                  >
                    {lesson.runtime === "docker"
                      ? "Terminal and file basics"
                      : lesson.runtime === "linux"
                        ? "Linux basics"
                        : "How to read YAML"}
                    <ArrowRight size={14} />
                  </button>
                </aside>
                <div className="outcomes">
                  <h2>By the end of this lab</h2>
                  <ul>
                    {lesson.outcomes.map((outcome) => (
                      <li key={outcome}>
                        <Check size={15} />
                        {outcome}
                      </li>
                    ))}
                  </ul>
                </div>
                <Markdown>{lesson.concept}</Markdown>
                <aside className="reference-links" aria-label="Background help">
                  <strong>Need a term explained?</strong>
                  <p className="muted small">
                    These short guides can help if something in the lesson is
                    unfamiliar.
                  </p>
                  <div className="button-row">
                    {model.library?.glossary
                      .filter((term) => term.units.includes(lesson.id))
                      .slice(0, 6)
                      .map((term) => (
                        <button
                          key={term.id}
                          onClick={() => model.openReference(`term/${term.id}`)}
                        >
                          {term.term}
                        </button>
                      ))}
                    <button
                      className="text-button"
                      onClick={() => model.openReference()}
                    >
                      Open reference desk <ArrowRight size={15} />
                    </button>
                  </div>
                </aside>
                {lesson.module === 7 && <ReconciliationModel key={lesson.id} />}
                {lesson.module === 11 && <StorageModel key={lesson.id} />}
                {lesson.id === "m20-ha" && <QuorumModel key={lesson.id} />}
                <section className="prediction">
                  <div className="eyebrow">PAUSE AND PREDICT</div>
                  <h3>{lesson.prediction.question}</h3>
                  <fieldset disabled={predictionSubmitted}>
                    <legend className="sr-only">Choose an answer</legend>
                    {lesson.prediction.options.map((option, index) => (
                      <label key={option}>
                        <input
                          type="radio"
                          name="prediction"
                          checked={prediction === index}
                          onChange={() => setPrediction(index)}
                        />
                        {option}
                      </label>
                    ))}
                  </fieldset>
                  {predictionSubmitted ? (
                    <div className="prediction-feedback">
                      <strong>
                        {prediction === lesson.prediction.correct
                          ? "Exactly."
                          : "Not quite. Let’s work through it."}
                      </strong>
                      <p>{lesson.prediction.explanation}</p>
                      <button
                        className="text-button"
                        onClick={() => {
                          setPredictionSubmitted(false);
                          setPrediction(null);
                        }}
                      >
                        Try again
                      </button>
                    </div>
                  ) : (
                    <button
                      disabled={prediction === null}
                      onClick={() => setPredictionSubmitted(true)}
                    >
                      Check prediction
                    </button>
                  )}
                </section>
                <button className="primary" onClick={() => setTab("mission")}>
                  Move to the task
                  <ArrowRight size={16} />
                </button>
              </>
            )}
            {tab === "mission" && (
              <>
                <div className="eyebrow">WORK IN YOUR REAL TERMINAL</div>
                <Markdown>{lesson.brief}</Markdown>
                <div className="task-checklist">
                  <h3>Before you check your work</h3>
                  <p>
                    Predict the result, try the task, then compare what happened
                    with your prediction. If they differ, choose one observation
                    that could explain why.
                  </p>
                  <p className="small muted">
                    Check work tests the lab’s current behavior. Your notes and
                    predictions are for your own reflection; they are not
                    automatically graded.
                  </p>
                </div>
                <div className="hint-area">
                  <h3>Need a nudge?</h3>
                  <p className="muted small">
                    Try one hint at a time, then return to the task. Using a
                    hint marks this attempt as practice with help.
                  </p>
                  {hints.map((hint, index) => (
                    <div className="hint" key={index}>
                      <span>HINT {index + 1}</span>
                      <Markdown>{hint}</Markdown>
                    </div>
                  ))}
                  <div className="button-row">
                    <button
                      onClick={() => void revealHint()}
                      disabled={hints.length >= lesson.hint_count}
                    >
                      Reveal hint{" "}
                      {Math.min(hints.length + 1, lesson.hint_count)}
                    </button>
                    <button className="text-button" onClick={revealReference}>
                      Reveal reference
                    </button>
                  </div>
                  {reference && (
                    <div className="references">
                      {Object.entries(reference).map(([name, content]) => (
                        <section key={name}>
                          <h4>
                            <FileText size={15} />
                            {name}
                          </h4>
                          <CodeBlock>
                            <code>{content}</code>
                          </CodeBlock>
                        </section>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
            {tab === "evidence" && (
              <>
                {assessment ? (
                  <>
                    <div className={`assessment-summary ${assessment.status}`}>
                      <ShieldCheck size={25} />
                      <div>
                        <h2>
                          {assessment.revision !== lesson.revision
                            ? "Evidence from an earlier lesson revision."
                            : assessment.status === "pass"
                              ? "The required behavior passed this check."
                              : assessment.status === "blocked"
                                ? "The environment needs attention."
                                : assessment.status === "stale"
                                  ? "The lab changed while it was being checked. Wait for rollouts to finish, then check again."
                                  : "Here is what the lab observed."}
                        </h2>
                        <p>
                          {assessment.independent
                            ? "Attempt without in-app hints or reference"
                            : lesson.kind === "lesson"
                              ? "Guided practice"
                              : "Practice with help"}{" "}
                          · {new Date(assessment.finished_at).toLocaleString()}{" "}
                          · Revision {assessment.revision} · Attempt{" "}
                          {assessment.attempt}
                        </p>
                        <p className="small">
                          This records what worked at the time of the check. It
                          does not grade your explanation or prove that you can
                          repeat the task. Check again after making changes.
                        </p>
                      </div>
                    </div>
                    {assessment.status === "fail" && (
                      <p className="notice">
                        Start with the first item that needs attention below.
                        Try its suggested check, make one change, then check
                        your work again.
                      </p>
                    )}
                    {[...assessment.evidence]
                      .sort(
                        (a, b) =>
                          Number(a.status === "pass") -
                          Number(b.status === "pass"),
                      )
                      .map((item) => (
                        <article
                          className={`evidence-card ${item.status}`}
                          key={item.criterion}
                        >
                          <div className="evidence-title">
                            <span className={`status-label ${item.status}`}>
                              {item.status === "pass"
                                ? "Passed"
                                : item.status === "fail"
                                  ? "Needs attention"
                                  : "Could not check"}
                            </span>
                            <h3>{item.title}</h3>
                          </div>
                          {item.status !== "pass" && (
                            <p className="diagnostic">{item.diagnostic}</p>
                          )}
                          <details>
                            <summary>Check details</summary>
                            <dl>
                              <dt>Expected</dt>
                              <dd>{item.expected}</dd>
                              <dt>Observed</dt>
                              <dd>
                                <pre>
                                  {item.observed || "No output was returned."}
                                </pre>
                              </dd>
                            </dl>
                          </details>
                          {item.details && (
                            <details>
                              <summary>Measured state</summary>
                              <pre>{item.details}</pre>
                            </details>
                          )}
                        </article>
                      ))}
                    {assessment.status === "pass" && (
                      <section className="debrief">
                        <div className="eyebrow">Debrief</div>
                        <Markdown>{lesson.debrief}</Markdown>
                        <p className="small muted">
                          Try answering without looking back at the lesson. If
                          you can’t explain a result yet, revisit that part
                          before moving on.
                        </p>
                        {nextLesson && lesson.kind !== "incident" && (
                          <div className="next-lesson">
                            <span className="eyebrow">UP NEXT</span>
                            <button
                              className="primary"
                              onClick={() =>
                                void model.openLesson(nextLesson.id)
                              }
                            >
                              {nextLesson.title}
                              <ArrowRight size={16} />
                            </button>
                          </div>
                        )}
                      </section>
                    )}
                  </>
                ) : (
                  <div className="empty-state">
                    <ShieldCheck size={36} />
                    <h2>Evidence comes from your lab.</h2>
                    <p>
                      Prepare the environment, work in your terminal, then check
                      the actual result. A passing result records what your lab
                      did. You’ll also be asked to explain what happened.
                    </p>
                    <button
                      className="primary"
                      onClick={() => setTab("mission")}
                    >
                      Review your task
                      <ArrowRight size={16} />
                    </button>
                  </div>
                )}
                <LiveLabMap
                  key={lesson.id}
                  unitId={lesson.id}
                  labState={lab?.state}
                />
              </>
            )}
          </div>
        </section>
        <aside className="context-panel">
          <section className="lab-card" id="lab-controls">
            <div className="eyebrow">YOUR LAB</div>
            <h3>
              <Terminal size={18} />{" "}
              {lesson.runtime === "docker"
                ? "Docker lab"
                : lesson.runtime === "linux"
                  ? "Native Linux lab"
                  : "Kubernetes lab"}
            </h3>
            <div className={`lab-state ${labTone(lab?.state)}`}>
              <span className="dot" />
              {labStateLabel(lab?.state)}
            </div>
            {lab?.state === "preparing" && lab.resources?.stage && (
              <p className="small" role="status">
                {lab.resources?.stage}
              </p>
            )}
            {lesson.runtime !== "docker" && (
              <p className="small muted">
                {lesson.runtime === "linux"
                  ? "Owned Linux guests, private kubeconfig, and no host mounts. "
                  : "Private cluster and kubeconfig. "}
                Preparing this lab pauses other active clusters in this profile
                to keep memory use bounded.
              </p>
            )}
            <p className="small muted">
              {lab
                ? "Open the lab terminal before running commands. It starts in the right folder with this lesson’s settings."
                : "First, prepare the lab. Dockyard creates the files and resources you’ll need for this task."}
            </p>
            {!lab || lab.state === "absent" || lab.state === "failed" ? (
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
            ) : (
              <>
                <TerminalLauncher
                  key={lesson.id}
                  model={model}
                  unitId={lesson.id}
                />
                <button
                  className="full"
                  disabled={!!busy}
                  onClick={() => void perform("check")}
                >
                  {busy === "check" ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <ShieldCheck size={16} />
                  )}
                  Check work
                </button>
              </>
            )}
            {busy && (
              <div className="operation" role="status">
                <LoaderCircle size={14} className="spin" />
                {operationLabel(busy)}
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
            )}
            {lab && lab.state !== "absent" && (
              <>
                <div className="lab-tools">
                  <button
                    className="text-button muted"
                    disabled={!!busy}
                    onClick={() =>
                      void perform(lab.state === "stopped" ? "resume" : "stop")
                    }
                  >
                    <Square size={12} />
                    {lab.state === "stopped" ? "Resume" : "Stop"}
                  </button>
                  <button
                    className="text-button muted"
                    disabled={!!busy}
                    onClick={() => void perform("reset")}
                  >
                    <RefreshCw size={13} />
                    Reset
                  </button>
                </div>
                {lesson.kind !== "lesson" && (
                  <button
                    className="full"
                    disabled={!!busy}
                    onClick={() => void perform("retake")}
                  >
                    <RefreshCw size={14} /> Independent retake
                  </button>
                )}
                <details className="workspace-location">
                  <summary>Workspace location</summary>
                  <p className="mono">{lab.workspace}</p>
                  <p className="small muted">Lab ID {lab.id.slice(0, 12)}</p>
                  <button
                    className="small-button"
                    onClick={() =>
                      navigator.clipboard
                        .writeText(lab.workspace)
                        .then(() => setNotice("Workspace path copied."))
                        .catch(() =>
                          setError(
                            "Clipboard unavailable. Select and copy the displayed path.",
                          ),
                        )
                    }
                  >
                    <Copy size={13} />
                    Copy path
                  </button>
                </details>
              </>
            )}
          </section>
          <section className="notes-card">
            <h3>
              <FileText size={16} />
              Your observations
            </h3>
            <label className="sr-only" htmlFor="notes">
              Notes for this lesson
            </label>
            <textarea
              id="notes"
              value={note}
              onChange={(event) => {
                setNote(event.target.value);
              }}
              onBlur={() => {
                if (note !== saved.text) void saveNote(false);
              }}
              placeholder="What did you notice? What would you investigate next?"
            />
            <div className="notes-actions">
              <button
                className="text-button"
                onClick={() => void saveNote(true)}
              >
                Save observations
              </button>
              <span className="small muted" role="status">
                {note !== saved.text
                  ? "Saves when you click away"
                  : saved.status}
              </span>
            </div>
          </section>
          <section className="source-card">
            <h3>Go deeper</h3>
            {lesson.sources.map((source) => (
              <a href={source} key={source} target="_blank" rel="noreferrer">
                {referenceTitle(source)}
                <ExternalLink size={13} />
              </a>
            ))}
          </section>
        </aside>
      </div>
    </>
  );
}

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

function labStateLabel(state?: string) {
  return LAB_STATES[state || "absent"] || state || "Not prepared";
}

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

function operationLabel(action: string) {
  return OPERATIONS[action] || `${action}…`;
}
