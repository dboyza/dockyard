import { useState } from "react";
import {
  ArrowRight,
  Check,
  ExternalLink,
  FileText,
  Lightbulb,
  ShieldCheck,
} from "lucide-react";
import { api, type Lesson } from "./api";
import { LiveLabMap } from "./LiveLabMap";
import { CodeBlock, Markdown, referenceTitle } from "./teaching";
import type { Workbench } from "./useWorkbench";

const PRIMERS: Record<string, [string, string]> = {
  docker: ["terminal", "Terminal and file basics"],
  linux: ["linux", "Linux basics"],
  kubernetes: ["yaml", "How to read YAML"],
};

/** The idea behind the lab: goals, the illustrated explanation, and a prediction. */
export function Understand({
  model,
  lesson,
  onTask,
}: {
  model: Workbench;
  lesson: Lesson;
  onTask: () => void;
}) {
  const {
    prediction,
    setPrediction,
    predictionSubmitted,
    setPredictionSubmitted,
  } = model;
  const prerequisites = model.units.filter((unit) =>
    lesson.prerequisites.includes(unit.id),
  );
  const glossary = model.library?.glossary ?? [];
  // This activity's own terms first, then those of the lessons it builds on,
  // so missions offer help too.
  const terms = [
    ...glossary.filter((term) => term.units.includes(lesson.id)),
    ...glossary.filter(
      (term) =>
        !term.units.includes(lesson.id) &&
        term.units.some((unit) => lesson.prerequisites.includes(unit)),
    ),
  ].slice(0, 6);
  const [primer, primerTitle] = PRIMERS[lesson.runtime] ?? PRIMERS.kubernetes;
  const correct = prediction === lesson.prediction.correct;
  return (
    <>
      <section className="lesson-goals" aria-label="Before you begin">
        <h3 className="eyebrow">By the end of this lab</h3>
        <ul>
          {lesson.outcomes.map((outcome) => (
            <li key={outcome}>
              <Check size={15} />
              {outcome}
            </li>
          ))}
        </ul>
        <p className="lesson-builds-on small muted">
          {prerequisites.length ? "Builds on" : "No Docker experience needed."}
          {prerequisites.map((unit) => (
            <button
              className="text-button"
              key={unit.id}
              onClick={() => void model.openLesson(unit.id)}
            >
              {unit.title}
            </button>
          ))}
          <span>New to this?</span>
          <button
            className="text-button"
            onClick={() => model.openReference(`primer/${primer}`)}
          >
            {primerTitle}
            <ArrowRight size={13} />
          </button>
        </p>
      </section>
      <Markdown key={lesson.id}>{lesson.concept}</Markdown>
      <aside className="reference-links" aria-label="Background help">
        <strong>Need a term explained?</strong>
        <div className="button-row">
          {terms.map((term) => (
            <button
              className="chip"
              key={term.id}
              onClick={() => model.openReference(`term/${term.id}`)}
            >
              {term.term}
            </button>
          ))}
          <button className="text-button" onClick={() => model.openReference()}>
            Open reference desk <ArrowRight size={15} />
          </button>
        </div>
      </aside>
      <section className="prediction">
        <div className="eyebrow">Pause and predict</div>
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
            className={`prediction-feedback ${correct ? "correct" : "incorrect"}`}
            role="status"
          >
            <strong>
              {correct ? "Exactly." : "Not quite. Let’s work through it."}
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
      <section className="source-card">
        <h3>Go deeper</h3>
        {lesson.sources.map((source) => (
          <a href={source} key={source} target="_blank" rel="noreferrer">
            {referenceTitle(source)}
            <ExternalLink size={13} />
          </a>
        ))}
      </section>
      <button className="primary" onClick={onTask}>
        Move to the task
        <ArrowRight size={16} />
      </button>
    </>
  );
}

/** What to do in the lab: the brief, the learner's own notes, and help on request. */
export function Task({ model, lesson }: { model: Workbench; lesson: Lesson }) {
  const { hints, reference, note, setNote, setError, setNotice } = model;
  const [saved, setSaved] = useState({ text: note, status: "" });
  const saveNote = (announce: boolean) =>
    api(`/units/${lesson.id}/note`, { body: note })
      .then(() => {
        setSaved({ text: note, status: "Saved" });
        if (announce) setNotice("Your observations were saved locally.");
      })
      .catch((error) => setError(error.message));
  return (
    <>
      <Markdown>{lesson.brief}</Markdown>
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
            {note !== saved.text
              ? "Saves when you click away"
              : saved.status ||
                "Notes are for you. Check work tests what your lab does."}
          </span>
        </div>
      </section>
      <section className="hint-area">
        <h3>
          <Lightbulb size={16} />
          Need a nudge?
        </h3>
        <p className="muted small">
          Try one hint at a time. Using a hint marks this attempt as practice
          with help.
        </p>
        {hints.map((hint, index) => (
          <div className="hint" key={index}>
            <span>HINT {index + 1}</span>
            <Markdown>{hint}</Markdown>
          </div>
        ))}
        <div className="button-row">
          <button
            onClick={() => void model.revealHint()}
            disabled={hints.length >= lesson.hint_count}
          >
            Reveal hint {Math.min(hints.length + 1, lesson.hint_count)}
          </button>
          <button className="text-button" onClick={model.revealReference}>
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
      </section>
    </>
  );
}

const VERDICTS: Record<string, string> = {
  pass: "The required behavior passed this check.",
  blocked: "The environment needs attention.",
  stale:
    "The lab changed while it was being checked. Wait for rollouts to finish, then check again.",
  fail: "Here is what the lab observed.",
};
const CRITERION_LABELS: Record<string, string> = {
  pass: "Passed",
  fail: "Needs attention",
};

/** What the last check observed, and after a pass, the debrief. */
export function Results({
  model,
  lesson,
  onTask,
}: {
  model: Workbench;
  lesson: Lesson;
  onTask: () => void;
}) {
  const { assessment, lab } = model;
  if (!assessment)
    return (
      <div className="empty-state">
        <ShieldCheck size={32} />
        <h3>Results come from your lab.</h3>
        <p>
          Work through the task in the terminal, then choose Check work. Each
          result records what your lab did at that moment.
        </p>
        <button onClick={onTask}>
          Back to the task
          <ArrowRight size={16} />
        </button>
      </div>
    );
  return (
    <>
      <div className={`assessment-summary ${assessment.status}`}>
        <ShieldCheck size={25} />
        <div>
          <h3>
            {assessment.revision !== lesson.revision
              ? "Evidence from an earlier lesson revision."
              : VERDICTS[assessment.status]}
          </h3>
          <p>
            {assessment.independent
              ? "Attempt without in-app hints or reference"
              : lesson.kind === "lesson"
                ? "Guided practice"
                : "Practice with help"}{" "}
            · {new Date(assessment.finished_at).toLocaleString()} · Revision{" "}
            {assessment.revision} · Attempt {assessment.attempt}
          </p>
          <p className="small">
            This records what worked at the time of the check. It does not grade
            your explanation or prove that you can repeat the task.
          </p>
        </div>
      </div>
      {assessment.status === "fail" && (
        <p className="notice">
          Start with the first item that needs attention. Try its suggested
          check, make one change, then check your work again.
        </p>
      )}
      {[...assessment.evidence]
        .sort(
          (a, b) => Number(a.status === "pass") - Number(b.status === "pass"),
        )
        .map((item) => (
          <article
            className={`evidence-card ${item.status}`}
            key={item.criterion}
          >
            <div className="evidence-title">
              <span className={`status-label ${item.status}`}>
                {CRITERION_LABELS[item.status] ?? "Could not check"}
              </span>
              <h4>{item.title}</h4>
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
                  <pre>{item.observed || "No output was returned."}</pre>
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
            Try answering without looking back at the lesson. If you can’t
            explain a result yet, revisit that part before moving on.
          </p>
        </section>
      )}
      {lab && lab.state !== "absent" && (
        <LiveLabMap key={lesson.id} unitId={lesson.id} labState={lab.state} />
      )}
    </>
  );
}
