import type { ITheme } from "@xterm/xterm";

export const TERMINAL_FONT = '"JetBrainsMono Nerd Font"';

// Tuned beside the workbench palette; xterm also enforces a minimum contrast ratio.
const dark: ITheme = {
  background: "#0b0f14",
  foreground: "#d6dde6",
  cursor: "#58a6ff",
  cursorAccent: "#0b0f14",
  selectionBackground: "#1f6feb59",
  selectionInactiveBackground: "#1f6feb2e",
  scrollbarSliderBackground: "#8b949e33",
  scrollbarSliderHoverBackground: "#8b949e55",
  scrollbarSliderActiveBackground: "#8b949e77",
  black: "#484f58",
  red: "#ff7b72",
  green: "#3fb950",
  yellow: "#d29922",
  blue: "#58a6ff",
  magenta: "#bc8cff",
  cyan: "#39c5cf",
  white: "#b1bac4",
  brightBlack: "#6e7681",
  brightRed: "#ffa198",
  brightGreen: "#56d364",
  brightYellow: "#e3b341",
  brightBlue: "#79c0ff",
  brightMagenta: "#d2a8ff",
  brightCyan: "#56d4dd",
  brightWhite: "#f0f6fc",
};

const light: ITheme = {
  background: "#fbfcfd",
  foreground: "#1f2328",
  cursor: "#0969da",
  cursorAccent: "#fbfcfd",
  selectionBackground: "#0969da33",
  selectionInactiveBackground: "#0969da1f",
  scrollbarSliderBackground: "#59636e33",
  scrollbarSliderHoverBackground: "#59636e55",
  scrollbarSliderActiveBackground: "#59636e77",
  black: "#24292f",
  red: "#cf222e",
  green: "#116329",
  yellow: "#7d4e00",
  blue: "#0969da",
  magenta: "#8250df",
  cyan: "#1b7c83",
  white: "#6e7781",
  brightBlack: "#57606a",
  brightRed: "#a40e26",
  brightGreen: "#1a7f37",
  brightYellow: "#633c01",
  brightBlue: "#218bff",
  brightMagenta: "#a475f9",
  brightCyan: "#3192aa",
  brightWhite: "#8c959f",
};

export function terminalTheme(theme: string): ITheme {
  return theme === "light" ? light : dark;
}
