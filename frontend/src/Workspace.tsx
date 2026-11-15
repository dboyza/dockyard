import { useEffect, useRef, useState, type ReactNode } from "react";
import { BookOpen, TerminalSquare } from "lucide-react";
import { Splitter } from "./Splitter";
import { TerminalDock, type DockHandle } from "./TerminalDock";
import type { Workbench } from "./useWorkbench";

type Layout = "split" | "maximized" | "collapsed";
const DEFAULT_SPLIT = 0.46;
const DEFAULT_PANEL = 0.42;

function stored<T>(
  key: string,
  fallback: T,
  valid: (value: unknown) => boolean,
) {
  try {
    const value = JSON.parse(localStorage.getItem(key) ?? "null");
    return valid(value) ? (value as T) : fallback;
  } catch {
    return fallback;
  }
}
function store(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Layout preferences are a convenience; the defaults still work.
  }
}
const fraction = (low: number, high: number) => (value: unknown) =>
  typeof value === "number" && value >= low && value <= high;

/**
 * Lesson or exam content beside the lab's embedded terminal, like a focused IDE.
 * An optional panel stays in view under the reading, so a task never hides its lesson.
 */
export function Workspace({
  model,
  unitId,
  runtime,
  retake,
  header,
  panel,
  panelOpen = true,
  footer,
  children,
}: {
  model: Workbench;
  unitId: string;
  runtime: string;
  retake: boolean;
  header?: ReactNode;
  panel?: ReactNode;
  panelOpen?: boolean;
  footer?: ReactNode;
  children: ReactNode;
}) {
  const [split, setSplit] = useState(() =>
    stored("dockyard-split", DEFAULT_SPLIT, fraction(0.25, 0.75)),
  );
  const [panelSize, setPanelSize] = useState(() =>
    stored("dockyard-task-panel", DEFAULT_PANEL, fraction(0.2, 0.75)),
  );
  const [layout, setLayout] = useState<Layout>(() =>
    stored<Layout>("dockyard-terminal-layout", "split", (value) =>
      ["split", "maximized", "collapsed"].includes(value as string),
    ),
  );
  // Narrow screens show one pane at a time.
  const [pane, setPane] = useState<"lesson" | "terminal">("lesson");
  const [dragging, setDragging] = useState(false);
  const grid = useRef<HTMLDivElement>(null);
  const lesson = useRef<HTMLElement>(null);
  const dock = useRef<DockHandle>(null);
  const live = model.state.consoles.filter(
    (item) => item.unit_id === unitId && item.alive,
  ).length;

  useEffect(() => {
    document.body.dataset.workspace = "";
    return () => {
      delete document.body.dataset.workspace;
    };
  }, []);
  useEffect(() => store("dockyard-terminal-layout", layout), [layout]);
  useEffect(() => {
    // Ctrl+` moves between the lesson and the terminal, as in many editors.
    const toggle = (event: KeyboardEvent) => {
      if (!event.ctrlKey || event.key !== "`") return;
      event.preventDefault();
      const inTerminal = !!(event.target as HTMLElement | null)?.closest(
        ".dock",
      );
      if (inTerminal && layout !== "maximized") {
        lesson.current?.focus();
        setPane("lesson");
      } else {
        if (layout === "collapsed") setLayout("split");
        setPane("terminal");
        requestAnimationFrame(() => dock.current?.focus());
      }
    };
    window.addEventListener("keydown", toggle);
    return () => window.removeEventListener("keydown", toggle);
  }, [layout]);

  return (
    <div
      ref={grid}
      className={`workspace ${layout} ${dragging ? "dragging" : ""} show-${pane}`}
      style={
        {
          "--split": `${split * 100}%`,
          "--panel": `${panelSize * 100}%`,
        } as React.CSSProperties
      }
    >
      <div className="workspace-switch" role="group" aria-label="Show">
        <button
          aria-pressed={pane === "lesson"}
          onClick={() => setPane("lesson")}
        >
          <BookOpen size={15} /> Lesson
        </button>
        <button
          aria-pressed={pane === "terminal"}
          onClick={() => setPane("terminal")}
        >
          <TerminalSquare size={15} /> Terminal
          {live > 0 && <span className="nav-count">{live}</span>}
        </button>
      </div>
      <section
        ref={lesson}
        className="workspace-lesson"
        tabIndex={-1}
        aria-label="Lesson"
      >
        {header && <div className="workspace-header">{header}</div>}
        <div className="workspace-read">
          <div className="workspace-lesson-content">{children}</div>
        </div>
        {panel && panelOpen && (
          <Splitter
            orientation="horizontal"
            className="workspace-panel-splitter"
            label="Resize the reading and the task"
            value={panelSize}
            min={0.2}
            max={0.75}
            fallback={DEFAULT_PANEL}
            measure={(event) => {
              const box = lesson.current?.getBoundingClientRect();
              return box ? (box.bottom - event.clientY) / box.height : null;
            }}
            onChange={(value, active) => {
              setPanelSize(value);
              setDragging(active);
            }}
            onCommit={(value) => {
              setPanelSize(value);
              setDragging(false);
              store("dockyard-task-panel", value);
            }}
          />
        )}
        {panel && (
          <div className={`workspace-panel ${panelOpen ? "open" : ""}`}>
            {panel}
          </div>
        )}
        {footer && <div className="workspace-footer">{footer}</div>}
      </section>
      <Splitter
        orientation="vertical"
        className="workspace-splitter"
        label="Resize the lesson and terminal"
        value={split}
        min={0.25}
        max={0.75}
        fallback={DEFAULT_SPLIT}
        measure={(event) => {
          const box = grid.current?.getBoundingClientRect();
          return box ? (event.clientX - box.left) / box.width : null;
        }}
        onChange={(value, active) => {
          setSplit(value);
          setDragging(active);
        }}
        onCommit={(value) => {
          setSplit(value);
          setDragging(false);
          store("dockyard-split", value);
        }}
      />
      {layout === "collapsed" ? (
        <button
          className="workspace-rail"
          onClick={() => {
            setLayout("split");
            requestAnimationFrame(() => dock.current?.focus());
          }}
          aria-label={`Show the terminal, ${live} ${live === 1 ? "shell" : "shells"} open`}
        >
          <TerminalSquare size={18} />
          <span>Terminal</span>
          {live > 0 && <span className="nav-count">{live}</span>}
        </button>
      ) : null}
      <div className="workspace-terminal">
        <TerminalDock
          ref={dock}
          model={model}
          unitId={unitId}
          runtime={runtime}
          retake={retake}
          maximized={layout === "maximized"}
          onMaximize={() =>
            setLayout(layout === "maximized" ? "split" : "maximized")
          }
          onCollapse={() => {
            setLayout("collapsed");
            lesson.current?.focus();
          }}
        />
      </div>
    </div>
  );
}
