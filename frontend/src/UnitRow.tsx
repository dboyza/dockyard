import { Check, ChevronRight, Circle, RotateCcw } from "lucide-react";
import type { Progress, UnitSummary } from "./api";
import { currentPractice, learningStatus, reviewNeeded } from "./learning";

export function UnitRow({
  unit,
  progress,
  onOpen,
}: {
  unit: UnitSummary;
  progress?: Progress;
  onOpen: (id: string) => Promise<void>;
}) {
  const current = currentPractice(unit.revision, progress);
  const review = reviewNeeded(unit.revision, progress);
  return (
    <button className="unitrow" onClick={() => void onOpen(unit.id)}>
      <span className={`unitstatus ${current ? "done" : ""}`}>
        {review ? (
          <RotateCcw size={17} />
        ) : current ? (
          <Check size={17} />
        ) : (
          <Circle size={15} />
        )}
      </span>
      <span>
        <strong>{unit.title}</strong>
        <span className="muted small">{unit.summary}</span>
      </span>
      <span className="unitmeta">
        {progress?.practiced && (
          <span>{learningStatus(unit.revision, progress)}</span>
        )}
        <span>{unit.minutes} min</span>
        <ChevronRight size={17} />
      </span>
    </button>
  );
}
