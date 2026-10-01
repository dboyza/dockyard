import { createContext, useContext, useId, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Figure, FigureId } from "../contracts.gen";
import { drawings, isFigureId } from "./registry";

export const FigureText = createContext<Record<string, Figure>>({});

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
    <div className="lesson-figure interactive">
      <Drawing />
    </div>
  ) : (
    <DrawnFigure id={id} text={text} />
  );
}

function DrawnFigure({ id, text }: { id: FigureId; text: Figure }) {
  const Drawing = drawings[id];
  const [step, setStep] = useState(0);
  const label = useId();
  const description = useId();
  const steps = text.steps;
  const current = steps[step];
  return (
    <figure className="lesson-figure" aria-labelledby={label}>
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
    </figure>
  );
}
