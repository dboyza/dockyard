import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Flag,
  Play,
  Terminal,
  Timer,
} from "lucide-react";
import { api } from "./api";
import type { Assessment, ExamAttempt } from "./contracts.gen";
import type { Workbench } from "./useWorkbench";
import { Markdown } from "./teaching";

export function ExamsPage({ model }: { model: Workbench }) {
  const {
    catalog,
    state,
    examId,
    openExam,
    openLesson,
    perform,
    refresh,
    busy,
    setBusy,
    setError,
    setDialog,
    opened,
  } = model;
  const [now, setNow] = useState(() => Date.now());
  const [reviewTask, setReviewTask] = useState<string | null>(null);
  const [reportId, setReportId] = useState<string | null>(null);
  const [reference, setReference] = useState<Record<string, string> | null>(
    null,
  );
  const [evidence, setEvidence] = useState<Assessment | null>(null);
  const exam = catalog?.exams.find((item) => item.id === examId);
  const attempts = state.exams.filter((item) => item.exam_id === examId);
  const running = attempts.find((item) =>
    ["active", "grading"].includes(item.state),
  );
  const attempt =
    running || attempts.find((item) => item.id === reportId) || attempts[0];
  const active = attempt?.state === "active" || attempt?.state === "grading";
  const lab = state.labs.find((item) => item.unit_id === exam?.unit_id);
  const operation = state.operations.find(
    (item) =>
      item.lab_id === lab?.id &&
      ["running", "queued", "canceling"].includes(item.state),
  );
  const selected =
    exam?.tasks.find(
      (item) => item.id === (active ? attempt.selected_task : reviewTask),
    ) || exam?.tasks[0];
  const remaining = attempt
    ? Math.min(
        (exam?.minutes || 120) * 60,
        Math.max(0, Math.ceil((Date.parse(attempt.deadline) - now) / 1000)),
      )
    : 0;
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    if (!attempt?.assessment_id) return;
    let alive = true;
    api<Assessment>(`/exam-attempts/${attempt.id}/evidence`)
      .then((value) => {
        if (alive) setEvidence(value);
      })
      .catch((error) => alive && setError(error.message));
    return () => {
      alive = false;
    };
  }, [attempt?.id, attempt?.assessment_id, setError]);
  const action = async (path: string, body: object = {}) => {
    const sequence = opened.current;
    setBusy("Exam operation");
    setError("");
    try {
      await api<ExamAttempt>(path, body);
      await refresh();
    } catch (error) {
      if (sequence === opened.current) setError((error as Error).message);
    } finally {
      if (sequence === opened.current) setBusy("");
    }
  };
  const choose = (id: string) => {
    if (attempt?.state === "active")
      void action(`/exam-attempts/${attempt.id}/tasks`, {
        selected_task: id,
        flagged: attempt.flagged,
      });
    else setReviewTask(id);
  };
  const confirm = (abandon: boolean) => {
    if (!attempt) return;
    setDialog({
      title: abandon
        ? "Abandon this timed attempt?"
        : "Submit your final work?",
      body: abandon
        ? "This attempt will be retained without a score. A new timed attempt requires a fresh fixture; your workspace is backed up during Independent retake."
        : "Dockyard will capture the final runtime evidence and produce your weighted task report. Leave the files and lab unchanged while grading runs.",
      action: () => {
        setDialog(null);
        void action(
          `/exam-attempts/${attempt.id}/${abandon ? "abandon" : "finish"}`,
          { action: abandon ? "abandon" : "finish", confirmed: true },
        );
      },
    });
  };
  if (!exam)
    return (
      <>
        <div className="page-heading">
          <div className="eyebrow">ORIGINAL PERFORMANCE PRACTICE</div>
          <h1>Work against a clear deadline.</h1>
          <p className="intro">
            Two CKAD-oriented and two CKA-oriented task sets. Real environments,
            explicit weights, and evidence you can use to choose your next
            practice.
          </p>
        </div>
        <section className="panel">
          <h2>A practice contract you can inspect</h2>
          <p className="muted">
            Preparation happens before the 120-minute timer starts. The deadline
            survives browser reloads, and the launcher assesses the final state
            when time expires. Keep Dockyard running through that deadline.
          </p>
          <p className="muted">
            If the launcher is unavailable at the deadline, the environment is
            unavailable, or work changes during grading, the attempt is retained
            without a score. These original exercises do not reproduce
            proctoring or predict an official exam result.
          </p>
        </section>
        <div className="placement-grid">
          {catalog?.exams.map((item) => {
            const latest = state.exams.find(
              (attempt) => attempt.exam_id === item.id,
            );
            return (
              <article className="panel" key={item.id}>
                <div className="eyebrow">
                  {item.track} ORIENTED · {item.tasks.length} TASKS
                </div>
                <h2>{item.title}</h2>
                <p className="muted">
                  {item.minutes} minutes ·{" "}
                  {item.track === "CKA"
                    ? "Native Linux administration"
                    : "Kubernetes application practice"}
                </p>
                {latest && (
                  <p className="small">
                    Latest attempt: {latest.state}
                    {latest.score !== null ? ` · ${latest.score}/100` : ""}
                  </p>
                )}
                <button onClick={() => openExam(item.id)}>
                  {latest?.state === "active"
                    ? "Continue timed attempt"
                    : "Open practice"}
                  <ArrowRight size={16} />
                </button>
              </article>
            );
          })}
        </div>
      </>
    );
  return (
    <>
      <button className="text-button" onClick={() => openExam(null)}>
        <ArrowLeft size={16} /> All practice exams
      </button>
      <div className="page-heading">
        <div className="eyebrow">{exam.track} ORIENTED · ORIGINAL TASK SET</div>
        <h1>{exam.title}</h1>
        <p className="intro">
          {exam.tasks.length} tasks · {exam.minutes} minutes · one isolated
          environment
        </p>
      </div>
      <section className="panel exam-toolbar" aria-label="Exam controls">
        {active ? (
          <>
            <div className="exam-clock">
              <Timer size={20} />
              <strong>
                {attempt.state === "grading"
                  ? "Grading"
                  : `${Math.floor(remaining / 60)
                      .toString()
                      .padStart(
                        2,
                        "0",
                      )}:${(remaining % 60).toString().padStart(2, "0")}`}
              </strong>
              <span className="muted small">
                {attempt.state === "grading"
                  ? "Keep the lab unchanged"
                  : "Remaining"}
              </span>
            </div>
            <div className="button-row">
              <button
                disabled={!!busy}
                onClick={() => void perform("terminal", false, exam.unit_id)}
              >
                <Terminal size={16} /> Open WezTerm
              </button>
              <button
                className="primary"
                disabled={
                  !!busy || attempt.state !== "active" || remaining === 0
                }
                onClick={() => confirm(false)}
              >
                Submit attempt
              </button>
              <button
                className="text-button"
                disabled={!!busy || attempt.state !== "active"}
                onClick={() => confirm(true)}
              >
                Abandon
              </button>
            </div>
          </>
        ) : (
          <>
            <div>
              <strong>
                {lab?.state === "ready"
                  ? "Environment prepared"
                  : "Prepare before starting the clock"}
              </strong>
              <p className="muted small">
                {operation
                  ? lab?.resources.stage || operation.action
                  : lab?.workspace ||
                    "Provisioning time does not count toward your attempt."}
              </p>
            </div>
            <div className="button-row">
              <button
                disabled={!!busy || !!operation}
                onClick={() =>
                  void perform(
                    attempt ? "retake" : "prepare",
                    false,
                    exam.unit_id,
                  )
                }
              >
                {attempt ? "Independent retake" : "Prepare environment"}
              </button>
              <button
                className="primary"
                disabled={
                  !!busy ||
                  !!operation ||
                  lab?.state !== "ready" ||
                  !!state.exam_readiness[exam.id]
                }
                onClick={() => void action(`/exams/${exam.id}/start`)}
              >
                <Play size={16} /> Start 120-minute attempt
              </button>
            </div>
          </>
        )}
      </section>
      {!active && state.exam_readiness[exam.id] && (
        <p className="muted small">{state.exam_readiness[exam.id]}</p>
      )}
      {!active && attempts.length > 1 && (
        <label className="field-label">
          Saved attempt
          <select
            aria-label="Saved exam attempt"
            value={attempt?.id}
            onChange={(event) => setReportId(event.target.value)}
          >
            {attempts.map((item) => (
              <option key={item.id} value={item.id}>
                {new Date(item.started_at).toLocaleString()} - {item.state}
                {item.score !== null ? ` - ${item.score}/100` : ""}
              </option>
            ))}
          </select>
        </label>
      )}
      {!active && attempt && (
        <section className="panel exam-result" aria-label="Exam report">
          <div className="eyebrow">
            {attempt.state === "finished"
              ? "FINAL PRACTICE OBSERVATION"
              : "ATTEMPT RETAINED WITHOUT A SCORE"}
          </div>
          <h2>
            {attempt.score !== null
              ? `${attempt.score} / 100`
              : "No score assigned"}
          </h2>
          <p>{attempt.reason}</p>
          <p className="muted small">
            Started {new Date(attempt.started_at).toLocaleString()} ·{" "}
            {attempt.finished_at
              ? `Finished ${new Date(attempt.finished_at).toLocaleString()}`
              : ""}
          </p>
          <button
            disabled={!!busy}
            onClick={() =>
              setDialog({
                title: "Reveal the exam reference?",
                body: "The reference is for deliberate review after an attempt. It will not overwrite your workspace. A fresh independent retake is required before another timed attempt.",
                action: () => {
                  setDialog(null);
                  const sequence = opened.current;
                  void api<Record<string, string>>(
                    `/units/${exam.unit_id}/reference`,
                    { action: "reference", confirmed: true },
                  )
                    .then((value) => {
                      if (sequence === opened.current) setReference(value);
                      return refresh();
                    })
                    .catch((error) => {
                      if (sequence === opened.current) setError(error.message);
                    });
                },
              })
            }
          >
            Review reference solution
          </button>
          <p className="muted">
            Select a task below to review its evidence and focused remediation.
          </p>
        </section>
      )}
      {reference && !active && (
        <section className="panel">
          <h2>Reference solution</h2>
          <p className="muted">
            Compare the observed boundaries with your own repair. These files
            have not replaced your workspace.
          </p>
          {Object.entries(reference).map(([name, contents]) => (
            <details key={name}>
              <summary>{name}</summary>
              <pre>{contents}</pre>
            </details>
          ))}
        </section>
      )}
      <details className="panel exam-policy">
        <summary>Allowed references and timing policy</summary>
        <Markdown>{exam.reference_policy}</Markdown>
        <p className="muted small">
          The persisted deadline keeps running when this browser is closed. Keep
          the foreground launcher running. Technical failures invalidate the
          attempt without assigning a zero; Independent retake restores a fresh
          fixture with a backup of your work.
        </p>
      </details>
      {!active && !attempt && (
        <p className="muted small">
          Task preview is available before starting. For an unseen attempt,
          prepare the environment and start the timer before reading the tasks.
        </p>
      )}
      <div className="exam-layout">
        <nav className="panel exam-tasks" aria-label="Exam tasks">
          {exam.tasks.map((task, index) => (
            <button
              key={task.id}
              className={selected?.id === task.id ? "selected" : ""}
              aria-current={selected?.id === task.id ? "step" : undefined}
              disabled={
                attempt?.state === "grading" ||
                !!busy ||
                (attempt?.state === "active" && remaining === 0)
              }
              onClick={() => choose(task.id)}
            >
              <span className="exam-task-number">{index + 1}</span>
              <span>
                <strong>{task.title}</strong>
                <small>
                  {task.weight}%
                  {attempt?.task_scores[task.id] !== undefined
                    ? ` · ${attempt.task_scores[task.id]} earned`
                    : ""}
                </small>
              </span>
              {attempt?.flagged.includes(task.id) && <Flag size={15} />}
            </button>
          ))}
        </nav>
        {selected && (
          <section className="panel exam-task">
            <div className="section-heading">
              <span className="eyebrow">
                TASK {exam.tasks.indexOf(selected) + 1} · {selected.weight}%
              </span>
              {attempt?.state === "active" && (
                <button
                  className="text-button"
                  aria-pressed={attempt.flagged.includes(selected.id)}
                  disabled={!!busy || remaining === 0}
                  onClick={() =>
                    void action(`/exam-attempts/${attempt.id}/tasks`, {
                      selected_task: selected.id,
                      flagged: attempt.flagged.includes(selected.id)
                        ? attempt.flagged.filter((id) => id !== selected.id)
                        : [...attempt.flagged, selected.id],
                    })
                  }
                >
                  <Flag size={16} />
                  {attempt.flagged.includes(selected.id)
                    ? "Flagged for review"
                    : "Flag for review"}
                </button>
              )}
            </div>
            <h2>{selected.title}</h2>
            <Markdown>{selected.brief}</Markdown>
            {!active && attempt?.state === "finished" && (
              <div className="exam-remediation">
                <h3>Observed evidence</h3>
                {evidence?.id === attempt.assessment_id ? (
                  evidence.evidence
                    .filter((item) =>
                      selected.criteria.includes(item.criterion),
                    )
                    .map((item) => (
                      <details key={item.criterion} className="exam-evidence">
                        <summary>
                          <span>
                            {item.status === "pass" && <Check size={15} />}{" "}
                            {item.title}
                          </span>
                          <strong>{item.status}</strong>
                        </summary>
                        <p className="muted">{item.diagnostic}</p>
                        <pre>{item.observed}</pre>
                        {item.details && <pre>{item.details}</pre>}
                      </details>
                    ))
                ) : (
                  <p className="muted">Loading the saved assessment.</p>
                )}
                <h3>Targeted practice</h3>
                <div className="button-row">
                  {selected.remediation.map((id) => (
                    <button key={id} onClick={() => void openLesson(id)}>
                      {catalog?.units.find((unit) => unit.id === id)?.title ||
                        id}
                      <ArrowRight size={15} />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}
      </div>
    </>
  );
}
