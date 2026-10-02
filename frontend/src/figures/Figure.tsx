import { createContext, useContext, useId, useState } from "react";
import { BookOpen, ChevronLeft, ChevronRight } from "lucide-react";
import type { Figure, FigureId } from "../contracts.gen";
import { drawings, isFigureId } from "./registry";

export const FigureText = createContext<Record<string, Figure>>({});

/**
 * Glossary links beneath each figure. Without `openTerm`, as in the review
 * gallery, the terms are listed as plain text.
 */
export type FigureLinkOptions = {
  glossary: Record<string, string>;
  openTerm?: (term: string, figure: FigureId, step: number) => void;
  /** The figure and step to show again when the learner comes back to it. */
  restore?: { figure: string; step: number } | null;
};
export const FigureLinks = createContext<FigureLinkOptions>({ glossary: {} });

export function LessonFigure({ id }: { id: string }) {
  const text = useContext(FigureText)[id];
  if (!isFigureId(id) || !text) {
    return (
      <p className="figure-missing" role="note">
        This figure is not available in this version of Dockyard.
      </p>
    );
  }
  const Drawing = drawings[id];
  return text.interactive ? (
    <div
      className="lesson-figure interactive"
      id={`figure-${id}`}
      tabIndex={-1}
    >
      <Drawing />
      <FigureTerms id={id} terms={text.terms} step={0} />
    </div>
  ) : (
    <DrawnFigure id={id} text={text} />
  );
}

function DrawnFigure({ id, text }: { id: FigureId; text: Figure }) {
  const Drawing = drawings[id];
  const { restore } = useContext(FigureLinks);
  const [step, setStep] = useState(() =>
    restore?.figure === id
      ? Math.min(restore.step, Math.max(text.steps.length - 1, 0))
      : 0,
  );
  const label = useId();
  const description = useId();
  const steps = text.steps;
  const current = steps[step];
  return (
    <figure
      className="lesson-figure"
      id={`figure-${id}`}
      tabIndex={-1}
      aria-labelledby={label}
    >
      <header>
        <span className="eyebrow">
          {steps.length ? "Step through" : "Picture it"}
        </span>
        <h4 id={label}>{text.title}</h4>
      </header>
      <div
        className="figure-canvas"
        role="img"
        aria-labelledby={label}
        aria-describedby={description}
      >
        <Drawing step={steps.length ? step : undefined} />
      </div>
      <p className="sr-only" id={description}>
        {text.description}
      </p>
      {current && (
        <div className="figure-steps">
          <div className="figure-step-text" aria-live="polite">
            <span className="figure-step-count">
              Step {step + 1} of {steps.length}
            </span>
            <strong>{current.label}</strong>
            <p>{current.text}</p>
          </div>
          <div className="figure-step-controls">
            <button
              type="button"
              aria-label="Previous step"
              disabled={step === 0}
              onClick={() => setStep(step - 1)}
            >
              <ChevronLeft size={16} />
            </button>
            <ol aria-label="Steps">
              {steps.map((item, index) => (
                <li key={item.label}>
                  <button
                    type="button"
                    className={index === step ? "current" : ""}
                    aria-label={`Step ${index + 1}: ${item.label}`}
                    aria-current={index === step ? "step" : undefined}
                    onClick={() => setStep(index)}
                  />
                </li>
              ))}
            </ol>
            <button
              type="button"
              aria-label="Next step"
              disabled={step === steps.length - 1}
              onClick={() => setStep(step + 1)}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
      <figcaption>{text.caption}</figcaption>
      <FigureTerms id={id} terms={text.terms} step={step} />
    </figure>
  );
}

function FigureTerms({
  id,
  terms,
  step,
}: {
  id: FigureId;
  terms: string[];
  step: number;
}) {
  const { glossary, openTerm } = useContext(FigureLinks);
  return (
    <div className="figure-terms">
      <span className="figure-terms-label">
        <BookOpen size={14} aria-hidden="true" /> In the glossary
      </span>
      <ul aria-label="Glossary terms in this figure">
        {terms.map((term) => (
          <li key={term}>
            {openTerm ? (
              <button
                type="button"
                className="figure-term"
                aria-label={`${glossary[term] ?? term}, glossary entry`}
                onClick={() => openTerm(term, id, step)}
              >
                {glossary[term] ?? term}
              </button>
            ) : (
              <span className="figure-term">{glossary[term] ?? term}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
