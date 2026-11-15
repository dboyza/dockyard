/** The overview illustration: a container yard at night, drawn in isometric projection. */

type Box = {
  x: number;
  y: number;
  z: number;
  tone: keyof typeof TONES;
  /** Hangs from the crane and sways gently. */
  lifted?: boolean;
  /** A small status light on its door end. */
  light?: boolean;
};

const TONES = {
  blue: "#3d74ff",
  cyan: "#1fb8d4",
  violet: "#7b6cf6",
  amber: "#f0a63c",
  slate: "#44537a",
};
const LENGTH = 3;
const WIDTH = 1.25;
const HEIGHT = 1.15;

// Three lanes of stacked containers, back lane first.
const YARD: Box[] = [
  { x: 0, y: 0, z: 0, tone: "slate" },
  { x: 0, y: 0, z: HEIGHT, tone: "blue" },
  { x: 0, y: 0, z: HEIGHT * 2, tone: "violet", light: true },
  { x: 3.3, y: 0, z: 0, tone: "cyan" },
  { x: 3.3, y: 0, z: HEIGHT, tone: "slate" },
  { x: 0, y: 1.7, z: 0, tone: "violet" },
  { x: 0, y: 1.7, z: HEIGHT, tone: "cyan", light: true },
  { x: 3.3, y: 1.7, z: 0, tone: "blue" },
  { x: 3.3, y: 1.7, z: HEIGHT * 2.6, tone: "amber", lifted: true },
  { x: 0, y: 3.4, z: 0, tone: "blue" },
  { x: 3.3, y: 3.4, z: 0, tone: "slate", light: true },
];

const point = (x: number, y: number, z: number) =>
  `${(260 + (x - y) * 27).toFixed(1)},${(214 + (x + y) * 13.5 - z * 27).toFixed(1)}`;

function mix(hex: string, target: number, amount: number) {
  const channel = (index: number) => {
    const value = parseInt(hex.slice(1 + index * 2, 3 + index * 2), 16);
    return Math.round(value + (target - value) * amount)
      .toString(16)
      .padStart(2, "0");
  };
  return `#${channel(0)}${channel(1)}${channel(2)}`;
}

function Container({ box }: { box: Box }) {
  const { x, y, z } = box;
  const tone = TONES[box.tone];
  const [far, near, top] = [x + LENGTH, y + WIDTH, z + HEIGHT];
  const ribs = Array.from({ length: 11 }, (_, index) => x + 0.25 * (index + 1));
  return (
    <g className={box.lifted ? "hero-lifted" : undefined}>
      {box.lifted && (
        <path
          className="hero-cable"
          d={`M${point(x + LENGTH / 2, y + WIDTH / 2, top)} L${point(x + LENGTH / 2, y + WIDTH / 2, 6.6)}`}
        />
      )}
      <polygon
        fill={mix(tone, 0, 0.18)}
        points={[
          point(x, near, z),
          point(far, near, z),
          point(far, near, top),
          point(x, near, top),
        ].join(" ")}
      />
      <polygon
        fill={mix(tone, 0, 0.42)}
        points={[
          point(far, y, z),
          point(far, near, z),
          point(far, near, top),
          point(far, y, top),
        ].join(" ")}
      />
      <polygon
        fill={mix(tone, 255, 0.16)}
        points={[
          point(x, y, top),
          point(far, y, top),
          point(far, near, top),
          point(x, near, top),
        ].join(" ")}
      />
      <path
        className="hero-ribs"
        d={ribs
          .map(
            (rib) =>
              `M${point(rib, near, z + 0.14)} L${point(rib, near, top - 0.14)}`,
          )
          .join(" ")}
      />
      <path
        className="hero-doors"
        d={`M${point(far, y + WIDTH / 2, z + 0.1)} L${point(far, y + WIDTH / 2, top - 0.1)}`}
      />
      {box.light && (
        <circle
          className="hero-light"
          r="2.4"
          cx={point(far, y + 0.3, top - 0.3).split(",")[0]}
          cy={point(far, y + 0.3, top - 0.3).split(",")[1]}
        />
      )}
    </g>
  );
}

export function HeroScene() {
  const drawn = [...YARD].sort((a, b) => a.x + a.y - (b.x + b.y) || a.z - b.z);
  const grid = Array.from({ length: 9 }, (_, index) => index - 1);
  return (
    <svg className="hero-scene" viewBox="24 30 492 330" aria-hidden="true">
      <defs>
        <radialGradient id="hero-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0" stopColor="var(--blue)" stopOpacity="0.34" />
          <stop offset="1" stopColor="var(--blue)" stopOpacity="0" />
        </radialGradient>
      </defs>
      <ellipse cx="270" cy="286" rx="240" ry="96" fill="url(#hero-glow)" />
      <path
        className="hero-grid"
        d={grid
          .flatMap((line) => [
            `M${point(line, -1.4, 0)} L${point(line, 5.9, 0)}`,
            `M${point(-1.2, line * 0.9, 0)} L${point(7.6, line * 0.9, 0)}`,
          ])
          .join(" ")}
      />
      <path
        className="hero-crane"
        d={[
          `M${point(-0.9, 2.3, 0)} L${point(-0.9, 2.3, 6.6)} L${point(7.4, 2.3, 6.6)} L${point(7.4, 2.3, 0)}`,
          `M${point(-0.9, 2.3, 5.6)} L${point(0.2, 2.3, 6.6)}`,
          `M${point(7.4, 2.3, 5.6)} L${point(6.3, 2.3, 6.6)}`,
        ].join(" ")}
      />
      {drawn.map((box) => (
        <Container key={`${box.x}-${box.y}-${box.z}`} box={box} />
      ))}
    </svg>
  );
}
