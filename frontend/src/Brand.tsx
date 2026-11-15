/** The Dockyard mark: one shipping container, drawn as an open box. */
export function BrandMark({ size = 26 }: { size?: number }) {
  return (
    <svg
      className="brand-mark"
      width={size}
      height={size}
      viewBox="0 0 32 32"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="brand-mark-fill" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#3d74ff" />
          <stop offset="1" stopColor="#4a3fe0" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill="url(#brand-mark-fill)" />
      <g
        fill="none"
        stroke="#fff"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M7 12 16 7l9 5v8l-9 5-9-5z" />
        <path d="M7 12l9 5 9-5M16 17v8M11.5 14.5v8M20.5 14.5v8" />
      </g>
    </svg>
  );
}
