import { useEffect, useState } from "react";
import { Workspace } from "./Workspace";
import { LiveLabMap } from "./LiveLabMap";
import type { Workbench } from "./useWorkbench";
import { api } from "./api";
import { CodeBlock, Markdown, referenceTitle } from "./teaching";
import {
  currentPractice,
  learningStatus,
  reviewDue,
  reviewNeeded,
} from "./learning";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Circle,
  RotateCcw,
  Clock3,
  Container,
  ExternalLink,
  FileText,
  LoaderCircle,
  Play,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import { InPageLink } from "./InPageLink";
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
  const working = !!lab && lab.state !== "absent";
  // Entering the workspace puts the task beside the terminal; later checks still show evidence.
  useEffect(() => {
    if (working) setTab("mission");
  }, [lesson?.id, working, setTab]);
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
  const sequence = model.units
    .filter((unit) =>
      lesson.kind === "incident"
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
  const nextLesson = lesson.kind === "incident" ? undefined : nextUnit;
  const heading = (
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
          {reviewDue(lesson.revision, state.progress[lesson.id]) ? (
            <RotateCcw size={13} />
          ) : currentPractice(lesson.revision, state.progress[lesson.id]) ? (
            <Check size={13} className="status-done" />
          ) : (
            <Circle size={12} />
          )}
          {learningStatus(lesson.revision, state.progress[lesson.id])}
        </span>
      </div>
    </div>
  );
  const review = reviewNeeded(lesson.revision, state.progress[lesson.id]) && (
    <p className="notice" role="status">
      This lesson has changed since your last passing assessment. Your earlier
      evidence is preserved. Check the current revision to update your skills
      record.
    </p>
  );
  const content = (
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
            <aside className="prerequisite-help" aria-label="Before you begin">
              <strong>Before you begin</strong>
              {prerequisites.length ? (
                <>
                  <p className="small muted">
                    This lesson builds on the work below. If it feels
                    unfamiliar, start there. You can still try this lesson now.
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
                  No Docker experience needed. You’ll use a terminal to run the
                  commands below. Open the short terminal guide if commands,
                  files, or variables are new to you.
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
            <Markdown key={lesson.id}>{lesson.concept}</Markdown>
            <aside className="reference-links" aria-label="Background help">
              <strong>Need a term explained?</strong>
              <p className="muted small">
                These short guides can help if something in the lesson is
                unfamiliar.
              </p>
              <div className="button-row">
                {[
                  // This activity's own terms first, then those of the
                  // lessons it builds on, so missions offer help too.
                  ...(model.library?.glossary ?? []).filter((term) =>
                    term.units.includes(lesson.id),
                  ),
                  ...(model.library?.glossary ?? []).filter(
                    (term) =>
                      !term.units.includes(lesson.id) &&
                      term.units.some((unit) =>
                        lesson.prerequisites.includes(unit),
                      ),
                  ),
                ]
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
            <section className="prediction">
              <div className="eyebrow">PAUSE AND PREDICT</div>
              <h3>{lesson.prediction.question}</h3>
              <fieldset disabled={predictionSubmitted}>
                <legend className="sr-only">Choose an answer</legend>
                {lesson.prediction.options.map((option, index) => (
                  <label
                    key={option}
                    className={
                      !predictionSubmitted
                        ? ""
                        : index === lesson.prediction.correct
                          ? "correct"
                          : index === prediction
                            ? "incorrect"
                            : ""
                    }
                  >
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
                <div
                  className={`prediction-feedback ${
                    prediction === lesson.prediction.correct
                      ? "correct"
                      : "incorrect"
                  }`}
                  role="status"
                >
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
            <div className="eyebrow">WORK IN THE LAB TERMINAL</div>
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
                Try one hint at a time, then return to the task. Using a hint
                marks this attempt as practice with help.
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
                  Reveal hint {Math.min(hints.length + 1, lesson.hint_count)}
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
                      · {new Date(assessment.finished_at).toLocaleString()} ·
                      Revision {assessment.revision} · Attempt{" "}
                      {assessment.attempt}
                    </p>
                    <p className="small">
                      This records what worked at the time of the check. It does
                      not grade your explanation or prove that you can repeat
                      the task. Check again after making changes.
                    </p>
                  </div>
                </div>
                {assessment.status === "fail" && (
                  <p className="notice">
                    Start with the first item that needs attention below. Try
                    its suggested check, make one change, then check your work
                    again.
                  </p>
                )}
                {[...assessment.evidence]
                  .sort(
                    (a, b) =>
                      Number(a.status === "pass") - Number(b.status === "pass"),
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
                      Try answering without looking back at the lesson. If you
                      can’t explain a result yet, revisit that part before
                      moving on.
                    </p>
                    {nextLesson && lesson.kind !== "incident" && (
                      <div className="next-lesson">
                        <span className="eyebrow">UP NEXT</span>
                        <button
                          className="primary"
                          onClick={() => void model.openLesson(nextLesson.id)}
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
                  Prepare the environment, work in your terminal, then check the
                  actual result. A passing result records what your lab did.
                  You’ll also be asked to explain what happened.
                </p>
                <button className="primary" onClick={() => setTab("mission")}>
                  Review your task
                  <ArrowRight size={16} />
                </button>
              </div>
            )}
            {lab && lab.state !== "absent" && (
              <LiveLabMap
                key={lesson.id}
                unitId={lesson.id}
                labState={lab.state}
              />
            )}
          </>
        )}
      </div>
      {position >= 0 && (
        <nav
          className="lesson-pager"
          aria-label={
            lesson.kind === "incident"
              ? "Incident navigation"
              : "Lesson navigation"
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
          <span className="pager-position small muted">
            {position + 1} of {sequence.length}
          </span>
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
    </section>
  );
  const notes = (
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
        <button className="text-button" onClick={() => void saveNote(true)}>
          Save observations
        </button>
        <span className="small muted" role="status">
          {note !== saved.text ? "Saves when you click away" : saved.status}
        </span>
      </div>
    </section>
  );
  const sources = (
    <section className="source-card">
      <h3>Go deeper</h3>
      {lesson.sources.map((source) => (
        <a href={source} key={source} target="_blank" rel="noreferrer">
          {referenceTitle(source)}
          <ExternalLink size={13} />
        </a>
      ))}
    </section>
  );
  if (working)
    return (
      <Workspace
        model={model}
        unitId={lesson.id}
        runtime={lesson.runtime}
        retake={lesson.kind !== "lesson"}
        footer={<LabBar model={model} />}
      >
        {heading}
        {review}
        {content}
        <div className="workspace-notes">
          {notes}
          {sources}
        </div>
      </Workspace>
    );
  return (
    <>
      {heading}
      <InPageLink className="mobile-lab-link" target="lab-controls">
        Open lab controls <ArrowRight size={15} />
      </InPageLink>
      {review}
      <div className="lesson-layout">
        {content}
        <aside className="context-panel">
          <section className="lab-card" id="lab-controls">
            <div className="eyebrow">YOUR LAB</div>
            <h3>
              <Terminal size={18} /> {RUNTIMES[lesson.runtime]}
            </h3>
            <div className="lab-state">
              <span className="dot" />
              Not prepared
            </div>
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
              Prepare the lab to begin. Dockyard creates the files and resources
              for this task, then opens a shell beside the lesson.
            </p>
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
            {busy && <OperationStatus model={model} />}
          </section>
          {notes}
          {sources}
        </aside>
      </div>
    </>
  );
}

const RUNTIMES: Record<string, string> = {
  docker: "Docker lab",
  kubernetes: "Kubernetes lab",
  linux: "Native Linux lab",
};

function OperationStatus({ model }: { model: Workbench }) {
  const { busy, activeOperation } = model;
  return (
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
  );
}

/** The lab's state and Check work, kept in view at the foot of the lesson pane. */
function LabBar({ model }: { model: Workbench }) {
  const { lab, busy, perform } = model;
  return (
    <div className="lab-bar">
      <div className={`lab-state ${labTone(lab?.state)}`}>
        <span className="dot" />
        {labStateLabel(lab?.state)}
      </div>
      {busy ? (
        <OperationStatus model={model} />
      ) : (
        <span className="small muted lab-bar-hint">
          Check work tests what your lab does right now.
        </span>
      )}
      <button
        className="primary"
        disabled={!!busy || TRANSITIONS.has(lab?.state ?? "")}
        onClick={() => void perform("check")}
      >
        {busy === "check" ? (
          <LoaderCircle className="spin" size={16} />
        ) : (
          <ShieldCheck size={16} />
        )}
        Check work
      </button>
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
