import { Check, ChevronRight, Circle, RotateCcw } from "lucide-react";
import type { Progress, UnitSummary } from "./api";
import { currentPractice, learningStatus, reviewDue } from "./learning";

export function UnitRow({
  unit,
  progress,
  onOpen,
  showModule = false,
}: {
  unit: UnitSummary;
  progress?: Progress;
  onOpen: (id: string) => Promise<void>;
  showModule?: boolean;
}) {
  const current = currentPractice(unit.revision, progress);
  const review = reviewDue(unit.revision, progress);
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
        {showModule && (
          <span className="unit-context">
            Module {String(unit.module).padStart(2, "0")} ·{" "}
            {unit.kind === "mission"
              ? "Mission"
              : unit.kind === "incident"
                ? "Incident"
                : unit.kind === "exam"
                  ? "Practice exam"
                  : "Lesson"}
          </span>
        )}
        <strong>{unit.title}</strong>
        <span className="muted small">{unit.summary}</span>
      </span>
      <span className="unitmeta">
        {!!progress?.practiced && (
          <span>{learningStatus(unit.revision, progress)}</span>
        )}
        <span>{unit.minutes} min</span>
        <ChevronRight size={17} />
      </span>
    </button>
  );
}
