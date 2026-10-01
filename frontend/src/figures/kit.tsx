import { createContext, useContext, useId, type ReactNode } from "react";

/**
 * Small SVG vocabulary shared by every lesson figure.
 * Drawings use a 640-unit-wide canvas so text is drawn at its real size in the
 * lesson column, and every color comes from the theme tokens in style.css.
 */

export type Tone = "default" | "focus" | "good" | "bad" | "warn" | "muted";
export type Point = readonly [number, number];

const Markers = createContext("figure");
const StepContext = createContext<number | null>(null);

export function Diagram({
  height,
  step,
  children,
}: {
  height: number;
  step?: number;
  children: ReactNode;
}) {
  const id = useId().replace(/:/g, "");
  const tones: Tone[] = ["default", "focus", "good", "bad", "warn", "muted"];
  return (
    <svg
      className="figure-drawing"
      viewBox={`0 0 640 ${height}`}
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        {tones.map((tone) => (
          <marker
            key={tone}
            id={`${id}-${tone}`}
            className={`fig-marker tone-${tone}`}
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M0 0L10 5L0 10z" />
          </marker>
        ))}
      </defs>
      <Markers.Provider value={id}>
        <StepContext.Provider value={step ?? null}>
          {children}
        </StepContext.Provider>
      </Markers.Provider>
    </svg>
  );
}

/**
 * Shows its children from step `from` (zero-based) onward and marks them as
 * current while the learner is on that step. Outside a stepped figure it
 * always shows its children.
 */
export function Reveal({
  from,
  until,
  children,
}: {
  from: number;
  until?: number;
  children: ReactNode;
}) {
  const step = useContext(StepContext);
  if (step === null) return <g>{children}</g>;
  const visible = step >= from && (until === undefined || step <= until);
  return (
    <g
      className={`fig-reveal ${visible ? "" : "fig-hidden"} ${step === from ? "fig-current" : ""}`}
    >
      {children}
    </g>
  );
}

export function Box({
  x,
  y,
  w,
  h,
  title,
  sub,
  tone = "default",
  dashed = false,
  mono = false,
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  title?: string;
  sub?: string;
  tone?: Tone;
  dashed?: boolean;
  mono?: boolean;
}) {
  const center = x + w / 2;
  const middle = y + h / 2;
  return (
    <g className={`fig-box tone-${tone} ${dashed ? "dashed" : ""}`}>
      <rect x={x} y={y} width={w} height={h} rx="7" />
      {title && (
        <text
          className={`fig-title ${mono ? "mono" : ""}`}
          x={center}
          y={sub ? middle - 4 : middle + 5}
          textAnchor="middle"
        >
          {title}
        </text>
      )}
      {sub && (
        <text
          className="fig-sub"
          x={center}
          y={middle + 15}
          textAnchor="middle"
        >
          {sub}
        </text>
      )}
    </g>
  );
}

/** A labelled boundary such as "Your computer" or "Container". */
export function Region({
  x,
  y,
  w,
  h,
  label,
  tone = "default",
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  label: string;
  tone?: Tone;
}) {
  return (
    <g className={`fig-region tone-${tone}`}>
      <rect x={x} y={y} width={w} height={h} rx="10" />
      <text x={x + 12} y={y + 19}>
        {label}
      </text>
    </g>
  );
}

export function Arrow({
  points,
  label,
  labelAt,
  tone = "default",
  dashed = false,
  both = false,
}: {
  points: Point[];
  label?: string;
  labelAt?: Point;
  tone?: Tone;
  dashed?: boolean;
  both?: boolean;
}) {
  const id = useContext(Markers);
  const d = points
    .map(([px, py], index) => `${index ? "L" : "M"}${px} ${py}`)
    .join(" ");
  const [first, second] = [points[0], points[points.length - 1]];
  const at = labelAt ?? [
    (first[0] + second[0]) / 2,
    (first[1] + second[1]) / 2 - 8,
  ];
  return (
    <g className={`fig-arrow tone-${tone} ${dashed ? "dashed" : ""}`}>
      <path
        d={d}
        markerEnd={`url(#${id}-${tone})`}
        markerStart={both ? `url(#${id}-${tone})` : undefined}
      />
      {label && (
        <text x={at[0]} y={at[1]} textAnchor="middle">
          {label}
        </text>
      )}
    </g>
  );
}

export function Label({
  x,
  y,
  children,
  anchor = "start",
  tone = "default",
  size = "normal",
  mono = false,
}: {
  x: number;
  y: number;
  children: ReactNode;
  anchor?: "start" | "middle" | "end";
  tone?: Tone;
  size?: "small" | "normal" | "large";
  mono?: boolean;
}) {
  return (
    <text
      className={`fig-label tone-${tone} size-${size} ${mono ? "mono" : ""}`}
      x={x}
      y={y}
      textAnchor={anchor}
    >
      {children}
    </text>
  );
}

/** A container image drawn as stacked read-only layers. */
export function ImageStack({
  x,
  y,
  w,
  layers,
  title,
  tone = "default",
}: {
  x: number;
  y: number;
  w: number;
  layers: string[];
  title?: string;
  tone?: Tone;
}) {
  const height = 26;
  return (
    <g className={`fig-image tone-${tone}`}>
      {title && (
        <text
          className="fig-title"
          x={x + w / 2}
          y={y - 10}
          textAnchor="middle"
        >
          {title}
        </text>
      )}
      {layers.map((layer, index) => (
        <g key={layer}>
          <rect
            x={x}
            y={y + index * (height + 4)}
            width={w}
            height={height}
            rx="4"
          />
          <text
            className="fig-sub"
            x={x + w / 2}
            y={y + index * (height + 4) + 17}
            textAnchor="middle"
          >
            {layer}
          </text>
        </g>
      ))}
    </g>
  );
}

/** A small terminal window showing typed commands and their output. */
export function Terminal({
  x,
  y,
  w,
  lines,
  title = "Your terminal",
}: {
  x: number;
  y: number;
  w: number;
  lines: string[];
  title?: string;
}) {
  const h = 36 + lines.length * 19;
  return (
    <g className="fig-terminal">
      <rect x={x} y={y} width={w} height={h} rx="7" />
      <path d={`M${x} ${y + 24}H${x + w}`} />
      <circle cx={x + 13} cy={y + 12} r="3.5" />
      <circle cx={x + 25} cy={y + 12} r="3.5" />
      <circle cx={x + 37} cy={y + 12} r="3.5" />
      <text
        className="fig-terminal-title"
        x={x + w / 2}
        y={y + 16}
        textAnchor="middle"
      >
        {title}
      </text>
      {lines.map((line, index) => (
        <text
          key={`${index}-${line}`}
          className={line.startsWith("$") ? "fig-command" : "fig-output"}
          xmlSpace="preserve"
          x={x + 12}
          y={y + 44 + index * 19}
        >
          {line}
        </text>
      ))}
    </g>
  );
}

/** Stored data, such as a database or a volume. */
export function Cylinder({
  x,
  y,
  w,
  h,
  title,
  sub,
  tone = "default",
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  title: string;
  sub?: string;
  tone?: Tone;
}) {
  const ry = 8;
  return (
    <g className={`fig-box tone-${tone}`}>
      <path
        d={`M${x} ${y + ry}V${y + h - ry}A${w / 2} ${ry} 0 0 0 ${x + w} ${y + h - ry}V${y + ry}`}
      />
      <ellipse cx={x + w / 2} cy={y + ry} rx={w / 2} ry={ry} />
      <text
        className="fig-title"
        x={x + w / 2}
        y={y + h / 2 + (sub ? 2 : 9)}
        textAnchor="middle"
      >
        {title}
      </text>
      {sub && (
        <text
          className="fig-sub"
          x={x + w / 2}
          y={y + h / 2 + 20}
          textAnchor="middle"
        >
          {sub}
        </text>
      )}
    </g>
  );
}

/** A small rounded tag, used for ports, labels, and states. */
export function Tag({
  x,
  y,
  text,
  tone = "default",
  anchor = "middle",
}: {
  x: number;
  y: number;
  text: string;
  tone?: Tone;
  anchor?: "start" | "middle";
}) {
  const width = text.length * 7.2 + 16;
  const left = anchor === "middle" ? x - width / 2 : x;
  return (
    <g className={`fig-tag tone-${tone}`}>
      <rect x={left} y={y - 11} width={width} height={22} rx="11" />
      <text className="mono" x={left + width / 2} y={y + 4} textAnchor="middle">
        {text}
      </text>
    </g>
  );
}

/** A page-shaped file icon with a name beneath it. */
export function File({
  x,
  y,
  name,
  tone = "default",
}: {
  x: number;
  y: number;
  name: string;
  tone?: Tone;
}) {
  return (
    <g className={`fig-file tone-${tone}`}>
      <path d={`M${x} ${y}h18l8 8v24h-26z M${x + 18} ${y}v8h8`} />
      <text className="fig-sub mono" x={x + 13} y={y + 48} textAnchor="middle">
        {name}
      </text>
    </g>
  );
}

/** A command or file shown line by line, with an optional tone per line. */
export function Code({
  x,
  y,
  w,
  lines,
  spacing = 28,
}: {
  x: number;
  y: number;
  w: number;
  lines: { text: string; tone?: Tone }[];
  spacing?: number;
}) {
  return (
    <g className="fig-code">
      <rect x={x} y={y} width={w} height={lines.length * spacing + 16} rx="7" />
      {lines.map((line, index) => (
        <text
          key={`${index}-${line.text}`}
          className={`mono tone-${line.tone ?? "default"}`}
          x={x + 14}
          y={y + 8 + spacing * (index + 0.5) + 4}
          xmlSpace="preserve"
        >
          {line.text}
        </text>
      ))}
    </g>
  );
}
