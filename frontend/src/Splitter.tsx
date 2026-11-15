import { useRef, useState } from "react";

/** A draggable, keyboard-operable divider that reports a fraction of its container. */
export function Splitter({
  orientation,
  value,
  min,
  max,
  fallback,
  label,
  className,
  measure,
  onChange,
  onCommit,
}: {
  orientation: "vertical" | "horizontal";
  value: number;
  min: number;
  max: number;
  fallback: number;
  label: string;
  className: string;
  /** Turns a pointer position into the fraction this divider controls. */
  measure: (event: React.PointerEvent) => number | null;
  onChange: (value: number, dragging: boolean) => void;
  onCommit: (value: number) => void;
}) {
  const [dragging, setDragging] = useState(false);
  const latest = useRef(value);
  const clamp = (next: number) => Math.min(max, Math.max(min, next));
  const [back, forward] =
    orientation === "vertical"
      ? ["ArrowLeft", "ArrowRight"]
      : ["ArrowDown", "ArrowUp"];
  return (
    <div
      className={`${className} ${dragging ? "dragging" : ""}`}
      role="separator"
      aria-orientation={orientation}
      aria-label={label}
      aria-valuemin={Math.round(min * 100)}
      aria-valuemax={Math.round(max * 100)}
      aria-valuenow={Math.round(value * 100)}
      tabIndex={0}
      onDoubleClick={() => onCommit(fallback)}
      onKeyDown={(event) => {
        const step =
          event.key === back ? -0.02 : event.key === forward ? 0.02 : 0;
        if (step) {
          event.preventDefault();
          onCommit(clamp(value + step));
        } else if (event.key === "Home") onCommit(min);
        else if (event.key === "End") onCommit(max);
        else if (event.key === "Enter") onCommit(fallback);
      }}
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture(event.pointerId);
        setDragging(true);
        onChange(value, true);
      }}
      onPointerMove={(event) => {
        if (!dragging) return;
        const next = measure(event);
        if (next === null) return;
        latest.current = clamp(next);
        onChange(latest.current, true);
      }}
      onPointerUp={(event) => {
        if (!dragging) return;
        setDragging(false);
        event.currentTarget.releasePointerCapture(event.pointerId);
        onCommit(latest.current);
      }}
    />
  );
}
