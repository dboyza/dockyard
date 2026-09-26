import { LiveLabMap } from "./LiveLabMap";
import type { Workbench } from "./useWorkbench";
import { api } from "./api";
import { Markdown, referenceTitle } from "./teaching";
import { ReconciliationModel } from "./ReconciliationModel";
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
  if (!lesson) return null;
  return (
    <>
      <div className="lesson-heading">
        <button
          className="text-button muted"
          onClick={() => navigate("course")}
        >
          <ArrowLeft size={15} />
          Course map
        </button>
        <div className="eyebrow">
          MODULE {String(lesson.module).padStart(2, "0")} /{" "}
          {lesson.kind === "lesson" ? "GUIDED LAB" : "INDEPENDENT MISSION"}
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
            {lesson.runtime}
          </span>
          <span>
            <Circle size={12} />
            {learningStatus(lesson.revision, state.progress[lesson.id])}
          </span>
        </div>
      </div>
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
                {lesson.module === 7 && <ReconciliationModel key={lesson.id} />}
                {lesson.module === 11 && <StorageModel key={lesson.id} />}
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
                          : "A useful distinction."}
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
                  <h3>Keep these observations separate</h3>
                  <p>
                    A process can be running while its application is
                    unreachable. Use inspection, logs, and a real request to
                    establish what is happening.
                  </p>
                </div>
                <div className="hint-area">
                  <h3>Need a nudge?</h3>
                  <p className="muted small">
                    Hints reveal one step at a time. Using them records
                    supported practice.
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
                          <pre>
                            <code>{content}</code>
                          </pre>
                        </section>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
            {tab === "evidence" && (
              <>
                <LiveLabMap
                  key={lesson.id}
                  unitId={lesson.id}
                  labState={lab?.state}
                />
                {assessment ? (
                  <>
                    <div className={`assessment-summary ${assessment.status}`}>
                      <ShieldCheck size={25} />
                      <div>
                        <h2>
                          {assessment.revision !== lesson.revision
                            ? "Evidence from an earlier lesson revision."
                            : assessment.status === "pass"
                              ? "The required behavior is working."
                              : assessment.status === "blocked"
                                ? "The environment needs attention."
                                : assessment.status === "stale"
                                  ? "Your work changed during the check."
                                  : "Here is what the lab observed."}
                        </h2>
                        <p>
                          {assessment.independent
                            ? "Independent assessment"
                            : "Supported practice"}{" "}
                          ·{" "}
                          {new Date(
                            assessment.finished_at,
                          ).toLocaleTimeString()}{" "}
                          · Revision {assessment.revision} · Attempt{" "}
                          {assessment.attempt}
                        </p>
                      </div>
                    </div>
                    {assessment.evidence.map((item) => (
                      <article className="evidence-card" key={item.criterion}>
                        <div className="evidence-title">
                          <span className={`status-label ${item.status}`}>
                            {item.status}
                          </span>
                          <h3>{item.title}</h3>
                        </div>
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
                        {item.details && (
                          <details>
                            <summary>Measured state</summary>
                            <pre>{item.details}</pre>
                          </details>
                        )}
                        {item.status !== "pass" && (
                          <p className="diagnostic">{item.diagnostic}</p>
                        )}
                      </article>
                    ))}
                    {assessment.status === "pass" && (
                      <section className="debrief">
                        <h3>Connect what you observed</h3>
                        <Markdown>{lesson.debrief}</Markdown>
                      </section>
                    )}
                  </>
                ) : (
                  <div className="empty-state">
                    <ShieldCheck size={36} />
                    <h2>Evidence comes from your lab.</h2>
                    <p>
                      Prepare the environment, work in WezTerm, then check the
                      actual result. Reading the instructions alone does not
                      mark the skill as demonstrated.
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
              </>
            )}
          </div>
        </section>
        <aside className="context-panel">
          <section className="lab-card">
            <div className="eyebrow">YOUR PRACTICE ENVIRONMENT</div>
            <h3>
              <Terminal size={18} />{" "}
              {lesson.runtime === "docker"
                ? "Docker lab"
                : lesson.runtime === "linux"
                  ? "Native Linux lab"
                  : "Kubernetes lab"}
            </h3>
            <div className="lab-state">
              <span className={`dot ${lab?.state === "ready" ? "pass" : ""}`} />
              {lab?.state || "Not prepared"}
            </div>
            {lab && <p className="mono small muted">{lab.id.slice(0, 12)}</p>}
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
                ? "Commands run in a dedicated WezTerm session with this lab’s environment."
                : "Prepare the application files and runtime, then do the work in your terminal."}
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
                <button
                  className="primary full"
                  disabled={!!busy}
                  onClick={() => void perform("terminal")}
                >
                  <Terminal size={16} />
                  Open in WezTerm
                </button>
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
                {busy}…
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
            {lab && (
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
              onChange={(event) => setNote(event.target.value)}
              placeholder="What did you notice? What would you investigate next?"
            />
            <button
              className="text-button"
              onClick={() =>
                api(`/units/${lesson.id}/note`, { body: note })
                  .then(() =>
                    setNotice("Your observations were saved locally."),
                  )
                  .catch((e) => setError(e.message))
              }
            >
              Save observations
            </button>
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
